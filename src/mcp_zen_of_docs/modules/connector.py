"""Connector module for bridging outputs and collecting missing context."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile
from mcp_zen_of_docs.modules.interaction import build_question_item
from mcp_zen_of_docs.scope import MissingContextKind
from mcp_zen_of_docs.scope import MissingContextReport
from mcp_zen_of_docs.scope import MissingContextSignal
from mcp_zen_of_docs.scope import StoryScopeContract
from mcp_zen_of_docs.scope import StoryScopeModuleOutput


__all__ = ["build_connector_module"]

_CONNECTOR_MODULE_NAME = "connector"
_DEFAULT_PROMPT = "requested documentation task"
_NO_OUTPUTS_MESSAGE = (
    "1. No module outputs were provided; connector remains pending additional context."
)
_MISSING_CONTEXT_WARNING = "Connector requires additional context from the user."

_TARGET_AUDIENCE_QUESTION = "Who is the target audience for this story?"

_CONTEXT_SIGNAL_SPECS: tuple[tuple[str, str, MissingContextKind], ...] = (
    (
        "goal",
        "What is the primary goal this story should help the reader achieve?",
        MissingContextKind.GOAL,
    ),
    (
        "scope",
        "What scope boundaries should this story explicitly include or exclude?",
        MissingContextKind.SCOPE,
    ),
    (
        "constraints",
        "Are there constraints or non-negotiables the narrative must call out?",
        MissingContextKind.CONSTRAINTS,
    ),
)


def _ordered_modules(
    request: StoryGenerationRequest, module_outputs: list[ModuleOutputContract]
) -> list[str]:
    ordered: list[str] = []
    for module_name in [*request.modules, *(output.module_name for output in module_outputs)]:
        if module_name == _CONNECTOR_MODULE_NAME or module_name in ordered:
            continue
        ordered.append(module_name)
    return ordered


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def _build_scope_contract(
    request: StoryGenerationRequest, module_outputs: list[ModuleOutputContract]
) -> StoryScopeContract:
    return StoryScopeContract(
        prompt=request.prompt,
        requested_modules=list(request.modules),
        audience=request.audience or request.context.get("audience"),
        goal=request.context.get("goal"),
        scope=request.context.get("scope"),
        constraints=request.context.get("constraints"),
        module_outputs=[
            StoryScopeModuleOutput(
                module_name=output.module_name,
                summary=output.summary,
                content=output.content,
            )
            for output in module_outputs
            if output.module_name != _CONNECTOR_MODULE_NAME
        ],
    )


def _dedupe_questions(signals: list[MissingContextSignal]) -> list[str]:
    seen: set[str] = set()
    questions: list[str] = []
    for signal in signals:
        if signal.question in seen:
            continue
        questions.append(signal.question)
        seen.add(signal.question)
    return questions


def _build_interaction_items(
    missing_context: MissingContextReport,
) -> tuple[list[QuestionItemContract], list[AnswerSlotContract]]:
    question_items: list[QuestionItemContract] = []
    answer_slots: list[AnswerSlotContract] = []
    for signal in missing_context.signals:
        target = signal.context_key or signal.module_name or "story"
        normalized_target = target.replace("_", "-")
        slot_id = f"slot-{normalized_target}"
        question_id = f"q-{signal.kind.value}-{normalized_target}"

        slot_type = AnswerSlotType.TEXT
        question_type = (
            InteractionQuestionType.CONSTRAINT
            if signal.kind == MissingContextKind.CONSTRAINTS
            else InteractionQuestionType.CLARIFICATION
        )

        answer_slots.append(
            build_answer_slot(
                slot_id=slot_id,
                slot_type=slot_type,
                prompt=signal.question,
                module_name=_CONNECTOR_MODULE_NAME,
                value=None,
            )
        )
        question_items.append(
            build_question_item(
                question_id=question_id,
                question=signal.question,
                question_type=question_type,
                module_name=_CONNECTOR_MODULE_NAME,
                answer_slot_ids=[slot_id],
            )
        )

    return question_items, answer_slots


def _build_missing_context_report(story_scope: StoryScopeContract) -> MissingContextReport:
    signals: list[MissingContextSignal] = []
    if not story_scope.audience:
        signals.append(
            MissingContextSignal(
                kind=MissingContextKind.TARGET_AUDIENCE,
                question=_TARGET_AUDIENCE_QUESTION,
                context_key="audience",
            )
        )

    for context_key, question, kind in _CONTEXT_SIGNAL_SPECS:
        if not getattr(story_scope, context_key):
            signals.append(
                MissingContextSignal(kind=kind, question=question, context_key=context_key)
            )

    output_by_module = {output.module_name: output for output in story_scope.module_outputs}
    signals.extend(
        MissingContextSignal(
            kind=MissingContextKind.MODULE_OUTPUT,
            module_name=module_name,
            question=(
                f"Can you share the '{module_name}' module output so the connector can bridge it?"
            ),
        )
        for module_name in story_scope.requested_modules
        if module_name not in output_by_module
    )

    signals.extend(
        MissingContextSignal(
            kind=MissingContextKind.MODULE_KEY_POINT,
            module_name=output.module_name,
            question=(
                f"What key point should the '{output.module_name}' module contribute "
                "to the final narrative?"
            ),
        )
        for output in story_scope.module_outputs
        if _first_non_empty(output.summary, output.content) is None
    )
    return MissingContextReport(signals=signals, follow_up_questions=_dedupe_questions(signals))


def build_connector_module(
    request: StoryGenerationRequest, module_outputs: list[ModuleOutputContract] | None = None
) -> ModuleOutputContract:
    """Build a bridge section that connects module outputs into one narrative flow."""
    outputs = module_outputs or []
    output_by_module = {
        output.module_name: output
        for output in outputs
        if output.module_name != _CONNECTOR_MODULE_NAME
    }
    module_names = _ordered_modules(request, outputs)
    prompt = request.prompt.strip() or _DEFAULT_PROMPT

    bridge_lines: list[str] = []
    for index, module_name in enumerate(module_names, start=1):
        module_output = output_by_module.get(module_name)
        detail = (
            _first_non_empty(module_output.summary, module_output.content)
            if module_output
            else f"Awaiting '{module_name}' module details."
        )
        if detail is None:
            detail = f"'{module_name}' has no usable content yet."
        bridge_lines.append(f"{index}. {module_name}: {detail}")

    if not bridge_lines:
        bridge_lines.append(_NO_OUTPUTS_MESSAGE)

    story_scope = _build_scope_contract(request, outputs)
    missing_context = _build_missing_context_report(story_scope)
    follow_up_questions = missing_context.follow_up_questions
    question_items, answer_slots = _build_interaction_items(missing_context)
    warnings = [_MISSING_CONTEXT_WARNING] if follow_up_questions else []
    content_lines = [
        "Connector bridge:",
        f'Story anchor: "{prompt}".',
        "Narrative flow:",
        *bridge_lines,
    ]
    if follow_up_questions:
        content_lines.append("Follow-up questions for the user:")
        content_lines.extend(f"- {question}" for question in follow_up_questions)

    return ModuleOutputContract(
        module_name=_CONNECTOR_MODULE_NAME,
        status="warning" if follow_up_questions else "success",
        content="\n".join(content_lines),
        summary=f"Connected {len(module_names)} module outputs into a bridge narrative.",
        metadata={
            "bridged_module_count": str(len(module_names)),
            "follow_up_question_count": str(len(follow_up_questions)),
        },
        warnings=warnings,
        follow_up_questions=follow_up_questions,
        question_items=question_items,
        answer_slots=answer_slots,
        intent_profile=build_intent_profile(
            module_name=_CONNECTOR_MODULE_NAME,
            intent_summary=(
                "Bridge module outputs into a single storyteller flow and flag missing context."
            ),
            required_context_keys=["audience", "goal", "scope", "constraints"],
            preferred_question_ids=[question.question_id for question in question_items],
            consumes_answer_slot_ids=[slot.slot_id for slot in answer_slots],
        ),
    )

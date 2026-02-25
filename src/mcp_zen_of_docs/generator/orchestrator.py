"""Deterministic orchestration for module-driven story generation."""

from __future__ import annotations

from time import perf_counter

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import DeterministicTurnPlan
from mcp_zen_of_docs.models import DeterministicTurnStep
from mcp_zen_of_docs.models import ModuleIntentProfile
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import OnboardingGuidanceContract
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StoryFeedbackLoopState
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StorySessionStateContract
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import StoryTurnTransition
from mcp_zen_of_docs.models import TurnPlanAction
from mcp_zen_of_docs.modules import build_connector_module
from mcp_zen_of_docs.modules.catalog import default_story_modules
from mcp_zen_of_docs.modules.catalog import resolve_story_module_builder
from mcp_zen_of_docs.scope import ScopeInteractionEvaluation
from mcp_zen_of_docs.scope import evaluate_scope_interaction


__all__ = [
    "advance_story_session_turn",
    "initialize_story_session_state",
    "orchestrate_story",
]


def _selected_modules(request: StoryGenerationRequest) -> list[str]:
    module_names = request.modules or list(default_story_modules())
    selected: list[str] = []
    for module_name in module_names:
        if module_name == "connector" or module_name in selected:
            continue
        selected.append(module_name)
    return selected


def _compose_narrative(module_outputs: list[ModuleOutputContract]) -> str | None:
    sections: list[str] = []
    for output in module_outputs:
        content = output.content or output.summary
        if not content:
            continue
        sections.append(f"### {output.module_name}\n{content}")
    return "\n\n".join(sections) or None


def _merge_answer_slot_values(
    answer_slots: list[AnswerSlotContract], request: StoryGenerationRequest
) -> list[AnswerSlotContract]:
    requested_values = {
        slot.slot_id: slot.value for slot in request.answer_slots if slot.value is not None
    }
    merged: list[AnswerSlotContract] = []
    seen_slot_ids: set[str] = set()
    for slot in answer_slots:
        if slot.slot_id in seen_slot_ids:
            continue
        seen_slot_ids.add(slot.slot_id)
        requested_value = requested_values.get(slot.slot_id)
        merged.append(
            slot if requested_value is None else slot.model_copy(update={"value": requested_value})
        )
    return merged


def _collect_interaction_payload(
    module_outputs: list[ModuleOutputContract],
) -> tuple[list[QuestionItemContract], list[AnswerSlotContract], list[ModuleIntentProfile]]:
    question_items: list[QuestionItemContract] = []
    seen_question_ids: set[str] = set()
    answer_slots: list[AnswerSlotContract] = []
    seen_slot_ids: set[str] = set()
    module_intent_profiles: list[ModuleIntentProfile] = []
    seen_profile_modules: set[str] = set()

    for output in module_outputs:
        for question in output.question_items:
            if question.question_id in seen_question_ids:
                continue
            seen_question_ids.add(question.question_id)
            question_items.append(question)
        for slot in output.answer_slots:
            if slot.slot_id in seen_slot_ids:
                continue
            seen_slot_ids.add(slot.slot_id)
            answer_slots.append(slot)
        if output.intent_profile and output.intent_profile.module_name not in seen_profile_modules:
            seen_profile_modules.add(output.intent_profile.module_name)
            module_intent_profiles.append(output.intent_profile)
    return question_items, answer_slots, module_intent_profiles


def _build_turn_plan(
    *,
    selected_modules: list[str],
    question_items: list[QuestionItemContract],
    answer_slots: list[AnswerSlotContract],
) -> DeterministicTurnPlan:
    slot_by_id = {slot.slot_id: slot for slot in answer_slots}
    unresolved_slot_ids = {
        slot.slot_id for slot in answer_slots if slot.required and slot.value in (None, "", [])
    }
    staged_question_ids = [
        question.question_id
        for question in question_items
        if not question.answer_slot_ids
        or any(
            slot_id in unresolved_slot_ids
            and slot_by_id.get(slot_id) is not None
            and slot_by_id[slot_id].required
            for slot_id in question.answer_slot_ids
        )
    ]
    steps: list[DeterministicTurnStep] = []
    if staged_question_ids:
        steps.extend(
            [
                DeterministicTurnStep(
                    step_id="step-ask-questions",
                    action=TurnPlanAction.ASK_QUESTIONS,
                    module_names=["connector"],
                    question_ids=staged_question_ids,
                    description="Ask required follow-up questions before final story composition.",
                ),
                DeterministicTurnStep(
                    step_id="step-wait-for-answers",
                    action=TurnPlanAction.WAIT_FOR_ANSWERS,
                    module_names=["connector"],
                    question_ids=staged_question_ids,
                    description="Wait for required answers to resolve pending context slots.",
                ),
            ]
        )
    steps.extend(
        [
            DeterministicTurnStep(
                step_id="step-execute-modules",
                action=TurnPlanAction.EXECUTE_MODULES,
                module_names=[*selected_modules, "connector"],
                question_ids=[],
                description="Execute selected story modules and connector using resolved context.",
            ),
            DeterministicTurnStep(
                step_id="step-finalize-story",
                action=TurnPlanAction.FINALIZE_STORY,
                module_names=["connector"],
                question_ids=[],
                description=(
                    "Finalize the composed story narrative and return orchestration output."
                ),
            ),
        ]
    )
    plan_suffix = "follow-up" if staged_question_ids else "single-pass"
    return DeterministicTurnPlan(
        plan_id=f"story-plan-{plan_suffix}",
        current_step_index=0,
        steps=steps,
    )


def _build_onboarding_guidance(
    request: StoryGenerationRequest, follow_up_questions: list[str]
) -> OnboardingGuidanceContract:
    prompt = request.prompt.strip() or "the requested story"
    return OnboardingGuidanceContract(
        channel="mcp",
        project_name="Story Generation",
        summary=f"Use these steps to refine and ship documentation for {prompt}.",
        setup_steps=[
            "Review generated module outputs in order.",
            "Resolve connector follow-up questions before finalizing content.",
            "Assign clear ownership for each unresolved question before continuing.",
        ],
        verification_commands=[
            "uv run pytest tests/test_orchestrator.py -q",
            "uv run ruff check .",
        ],
        next_actions=["Publish the composed narrative to your docs target."],
        metadata={
            "pillar.clear_responsibility": (
                "Question resolution and story synthesis ownership are explicit per step."
            ),
            "pillar.intuitive_workflows": (
                "Ask -> answer -> execute -> finalize progression is deterministic."
            ),
        },
        follow_up_questions=follow_up_questions,
    )


def _critical_exploration_gap_count(module_outputs: list[ModuleOutputContract]) -> int:
    count = 0
    for output in module_outputs:
        if output.module_name != "explore":
            continue
        if output.metadata.get("feedback_loop_state") != StoryFeedbackLoopState.AWAITING_FEEDBACK:
            continue
        raw_count = output.metadata.get("critical_gap_count")
        if raw_count is None:
            continue
        try:
            parsed_count = int(raw_count)
        except ValueError:
            continue
        if parsed_count > 0:
            count += parsed_count
    return count


def _with_synced_turn_plan_index(
    state: StorySessionStateContract, *, current_step_index: int
) -> StorySessionStateContract:
    turn_plan = state.turn_plan
    if turn_plan is None:
        return state.model_copy(update={"current_step_index": current_step_index})
    return state.model_copy(
        update={
            "current_step_index": current_step_index,
            "turn_plan": turn_plan.model_copy(update={"current_step_index": current_step_index}),
        }
    )


def _append_runtime_transition(  # noqa: PLR0913
    state: StorySessionStateContract,
    *,
    to_status: StorySessionStatus,
    action: TurnPlanAction,
    next_step_index: int,
    reason: str,
    message: str,
) -> StorySessionStateContract:
    transition = StoryTurnTransition(
        from_status=state.status,
        to_status=to_status,
        action=action,
        applied_answer_slot_ids=[],
        previous_step_index=state.current_step_index,
        next_step_index=next_step_index,
        reason=reason,
        message=message,
    )
    synced_state = _with_synced_turn_plan_index(state, current_step_index=next_step_index)
    return synced_state.model_copy(
        update={
            "status": to_status,
            "transition_history": [*synced_state.transition_history, transition],
            "last_message": message,
        }
    )


def _progress_runtime_steps(state: StorySessionStateContract) -> StorySessionStateContract:
    turn_plan = state.turn_plan
    if turn_plan is None or not turn_plan.steps:
        return state

    progressed_state = _with_synced_turn_plan_index(
        state, current_step_index=state.current_step_index
    )
    while progressed_state.current_step_index < len(turn_plan.steps):
        current_step = turn_plan.steps[progressed_state.current_step_index]
        if current_step.action in {TurnPlanAction.ASK_QUESTIONS, TurnPlanAction.WAIT_FOR_ANSWERS}:
            break
        if current_step.action == TurnPlanAction.EXECUTE_MODULES:
            progressed_state = _append_runtime_transition(
                progressed_state,
                to_status=StorySessionStatus.READY_TO_FINALIZE,
                action=TurnPlanAction.EXECUTE_MODULES,
                next_step_index=min(
                    progressed_state.current_step_index + 1, len(turn_plan.steps) - 1
                ),
                reason="execute-modules-complete",
                message="Module execution step completed; ready to finalize the story.",
            )
            continue
        if current_step.action == TurnPlanAction.FINALIZE_STORY:
            progressed_state = _append_runtime_transition(
                progressed_state,
                to_status=StorySessionStatus.COMPLETED,
                action=TurnPlanAction.FINALIZE_STORY,
                next_step_index=progressed_state.current_step_index,
                reason="story-finalized",
                message="Story finalized deterministically.",
            )
            break
        break
    return progressed_state


def initialize_story_session_state(
    result: OrchestratorResultContract,
    *,
    session_id: str,
    story_id: str | None = None,
) -> StorySessionStateContract:
    """Create a deterministic story-session state snapshot from orchestrator output."""
    turn_plan = result.response.turn_plan
    current_step_index = turn_plan.current_step_index if turn_plan is not None else 0
    return StorySessionStateContract(
        session_id=session_id,
        story_id=story_id or result.response.story_id,
        status=StorySessionStatus.INITIALIZED,
        turn_plan=turn_plan,
        current_step_index=current_step_index,
        question_items=result.response.question_items,
        answer_slots=result.response.answer_slots,
        pending_required_slot_ids=[],
        transition_history=[],
        last_message=result.message,
    )


def advance_story_session_turn(
    state: StorySessionStateContract, provided_answers: list[AnswerSlotContract] | None = None
) -> ScopeInteractionEvaluation:
    """Advance deterministic story session state by one iterative runtime turn."""
    evaluation = evaluate_scope_interaction(state, provided_answers)
    progressed_state = _progress_runtime_steps(evaluation.state)
    return evaluation.model_copy(update={"state": progressed_state})


def orchestrate_story(request: StoryGenerationRequest) -> OrchestratorResultContract:
    """Compose module outputs and append a connector bridge into one story response."""
    started_at = perf_counter()
    completed_modules: list[str] = []
    failed_modules: list[str] = []
    module_outputs: list[ModuleOutputContract] = []

    selected_modules = _selected_modules(request)
    for module_name in selected_modules:
        builder = resolve_story_module_builder(module_name)
        if builder is None:
            module_outputs.append(
                ModuleOutputContract(
                    module_name=module_name,
                    status="error",
                    summary=f"Unsupported story module '{module_name}'.",
                    warnings=[f"No builder registered for module '{module_name}'."],
                )
            )
            failed_modules.append(module_name)
            continue
        output = builder(request)
        module_outputs.append(output)
        if output.status == "error":
            failed_modules.append(module_name)
        else:
            completed_modules.append(module_name)

    connector_output = build_connector_module(request, module_outputs)
    module_outputs.append(connector_output)
    if connector_output.status == "error":
        failed_modules.append("connector")
    else:
        completed_modules.append("connector")

    follow_up_questions = connector_output.follow_up_questions
    question_items, answer_slots, module_intent_profiles = _collect_interaction_payload(
        module_outputs
    )
    answer_slots = _merge_answer_slot_values(answer_slots, request)
    turn_plan = _build_turn_plan(
        selected_modules=selected_modules,
        question_items=question_items,
        answer_slots=answer_slots,
    )
    unresolved_critical_exploration_gap_count = _critical_exploration_gap_count(module_outputs)
    if failed_modules:
        status = "error"
        message = f"Story orchestration failed for modules: {', '.join(failed_modules)}."
    elif follow_up_questions or unresolved_critical_exploration_gap_count > 0:
        status = "warning"
        if follow_up_questions and unresolved_critical_exploration_gap_count > 0:
            message = (
                "Additional context and critical exploration feedback are required "
                "before final story synthesis."
            )
        elif unresolved_critical_exploration_gap_count > 0:
            message = (
                "Critical exploration feedback is required before final story synthesis. "
                f"Unresolved critical gaps: {unresolved_critical_exploration_gap_count}."
            )
        else:
            message = "Additional context is required to complete the story."
    else:
        status = "success"
        message = None

    response = StoryGenerationResponse(
        status=status,
        title=request.prompt.strip() or "Generated Story",
        narrative=_compose_narrative(module_outputs),
        module_outputs=module_outputs,
        onboarding_guidance=_build_onboarding_guidance(request, follow_up_questions)
        if request.include_onboarding_guidance
        else None,
        follow_up_questions=follow_up_questions,
        question_items=question_items,
        answer_slots=answer_slots,
        turn_plan=turn_plan,
        module_intent_profiles=module_intent_profiles,
        message=message,
    )
    return OrchestratorResultContract(
        status=status,
        request=request,
        response=response,
        completed_modules=completed_modules,
        failed_modules=failed_modules,
        duration_ms=int((perf_counter() - started_at) * 1000),
        message=message,
    )

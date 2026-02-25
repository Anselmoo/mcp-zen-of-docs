"""Exploration module for discovery-first story planning."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import ExploreStageContract
from mcp_zen_of_docs.models import ExploreStoryStage
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryExplorationStage
from mcp_zen_of_docs.models import StoryFeedbackLoopState
from mcp_zen_of_docs.models import StoryGapSeverity
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryNextQuestionContract
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile
from mcp_zen_of_docs.modules.interaction import build_question_item


__all__ = ["build_explore_module"]

_MODULE_NAME = "explore"
_STAGE_WARNING = "Explore orchestrator requires staged follow-up before synthesis."

_STAGE_FLOW: tuple[ExploreStageContract, ...] = (
    ExploreStageContract(
        stage=ExploreStoryStage.MOTIVATION,
        title="Motivation",
        objective="Capture the reader problem and why this story matters now.",
        context_key="motivation",
        question_id="q-story-motivation",
        answer_slot_id="slot-story-motivation",
    ),
    ExploreStageContract(
        stage=ExploreStoryStage.API_STORY,
        title="API story",
        objective="Clarify the API journey, entry points, and expected interactions.",
        context_key="api_story",
        question_id="q-story-api",
        answer_slot_id="slot-story-api",
    ),
    ExploreStageContract(
        stage=ExploreStoryStage.IMPLEMENTATION_STORY,
        title="Implementation story",
        objective="Describe implementation milestones and integration sequencing.",
        context_key="implementation_story",
        question_id="q-story-implementation",
        answer_slot_id="slot-story-implementation",
    ),
    ExploreStageContract(
        stage=ExploreStoryStage.CONSTRAINTS,
        title="Constraints",
        objective="Document non-negotiables and guardrails that shape execution.",
        context_key="constraints",
        question_id="q-story-constraints",
        answer_slot_id="slot-story-constraints",
    ),
    ExploreStageContract(
        stage=ExploreStoryStage.VERIFICATION,
        title="Verification",
        objective="Define checks that prove the story outcome is complete and correct.",
        context_key="verification",
        question_id="q-story-verification",
        answer_slot_id="slot-story-verification",
    ),
)

_STAGE_QUESTIONS: dict[ExploreStoryStage, str] = {
    ExploreStoryStage.MOTIVATION: "What user problem should this story motivate first?",
    ExploreStoryStage.API_STORY: "Which API surface should this story walk through?",
    ExploreStoryStage.IMPLEMENTATION_STORY: (
        "What implementation sequence should the narrative emphasize?"
    ),
    ExploreStoryStage.CONSTRAINTS: "Which constraints should the story call out as non-negotiable?",
    ExploreStoryStage.VERIFICATION: "How will readers verify they implemented the story correctly?",
}

_STAGE_SLOT_PROMPTS: dict[ExploreStoryStage, str] = {
    ExploreStoryStage.MOTIVATION: (
        "Describe the motivation and user pain this story should resolve."
    ),
    ExploreStoryStage.API_STORY: "Summarize the API story: endpoints, contracts, or usage flow.",
    ExploreStoryStage.IMPLEMENTATION_STORY: (
        "Outline the implementation flow the final story should follow."
    ),
    ExploreStoryStage.CONSTRAINTS: "List constraints that must be reflected in the narrative.",
    ExploreStoryStage.VERIFICATION: (
        "List verification steps or checks for the final story outcome."
    ),
}

_CRITICAL_FEEDBACK_STAGES: frozenset[ExploreStoryStage] = frozenset(
    {
        ExploreStoryStage.MOTIVATION,
        ExploreStoryStage.API_STORY,
        ExploreStoryStage.IMPLEMENTATION_STORY,
    }
)

_STORY_STAGE_BY_EXPLORE_STAGE: dict[ExploreStoryStage, StoryExplorationStage] = {
    ExploreStoryStage.MOTIVATION: StoryExplorationStage.DISCOVERY,
    ExploreStoryStage.API_STORY: StoryExplorationStage.DISCOVERY,
    ExploreStoryStage.IMPLEMENTATION_STORY: StoryExplorationStage.DISCOVERY,
    ExploreStoryStage.CONSTRAINTS: StoryExplorationStage.GAP_ANALYSIS,
    ExploreStoryStage.VERIFICATION: StoryExplorationStage.FEEDBACK_LOOP,
}

_GAP_SEVERITY_BY_STAGE: dict[ExploreStoryStage, StoryGapSeverity] = {
    ExploreStoryStage.MOTIVATION: StoryGapSeverity.CRITICAL,
    ExploreStoryStage.API_STORY: StoryGapSeverity.CRITICAL,
    ExploreStoryStage.IMPLEMENTATION_STORY: StoryGapSeverity.CRITICAL,
    ExploreStoryStage.CONSTRAINTS: StoryGapSeverity.HIGH,
    ExploreStoryStage.VERIFICATION: StoryGapSeverity.MEDIUM,
}


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        normalized_value = value.strip()
        if normalized_value:
            return normalized_value
    return None


def _slot_value_lookup(answer_slots: list[AnswerSlotContract]) -> dict[str, str]:
    values: dict[str, str] = {}
    for slot in answer_slots:
        slot_value = slot.value
        normalized: str | None = None
        if isinstance(slot_value, str):
            normalized = _first_non_empty(slot_value)
        elif isinstance(slot_value, bool):
            normalized = str(slot_value).lower()
        elif isinstance(slot_value, list):
            normalized = ", ".join(item for item in slot_value if item.strip())
        if normalized:
            values[slot.slot_id] = normalized
    return values


def _resolve_stage_value(
    request: StoryGenerationRequest,
    stage: ExploreStageContract,
    resolved_slots: dict[str, str],
) -> str | None:
    legacy_constraint_slot = (
        resolved_slots.get("slot-story-constraints")
        if stage.stage == ExploreStoryStage.CONSTRAINTS
        else None
    )
    return _first_non_empty(
        request.context.get(stage.context_key),
        resolved_slots.get(stage.answer_slot_id),
        legacy_constraint_slot,
    )


def _adaptive_follow_up_stages(
    unresolved_stages: list[ExploreStageContract],
) -> list[ExploreStageContract]:
    if not unresolved_stages:
        return []
    return [unresolved_stages[0]]


def _feedback_state(
    *, unresolved_stages: list[ExploreStageContract], follow_up_stages: list[ExploreStageContract]
) -> StoryFeedbackLoopState:
    if any(stage.stage in _CRITICAL_FEEDBACK_STAGES for stage in unresolved_stages):
        return StoryFeedbackLoopState.AWAITING_FEEDBACK
    if follow_up_stages:
        return StoryFeedbackLoopState.INCORPORATING
    return StoryFeedbackLoopState.RESOLVED


def _build_next_questions(
    *,
    follow_up_stages: list[ExploreStageContract],
    feedback_state: StoryFeedbackLoopState,
) -> list[StoryNextQuestionContract]:
    return [
        StoryNextQuestionContract(
            question_id=stage.question_id,
            question=_STAGE_QUESTIONS[stage.stage],
            stage=_STORY_STAGE_BY_EXPLORE_STAGE[stage.stage],
            gap_severity=_GAP_SEVERITY_BY_STAGE[stage.stage],
            feedback_state=feedback_state,
            rationale=stage.objective,
            required=stage.required,
        )
        for stage in follow_up_stages
    ]


def build_explore_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build staged storyteller exploration prompts with adaptive follow-up behavior."""
    prompt = request.prompt.strip() or "the requested documentation outcome"
    resolved_slots = _slot_value_lookup(request.answer_slots)
    stage_values = {
        stage.stage: _resolve_stage_value(request, stage, resolved_slots) for stage in _STAGE_FLOW
    }
    unresolved_stages = [
        stage for stage in _STAGE_FLOW if stage.required and stage_values.get(stage.stage) is None
    ]
    follow_up_stages = _adaptive_follow_up_stages(unresolved_stages)
    feedback_state = _feedback_state(
        unresolved_stages=unresolved_stages,
        follow_up_stages=follow_up_stages,
    )
    next_questions = _build_next_questions(
        follow_up_stages=follow_up_stages,
        feedback_state=feedback_state,
    )
    critical_gap_count = sum(
        1 for stage in unresolved_stages if stage.stage in _CRITICAL_FEEDBACK_STAGES
    )
    follow_up_questions = [_STAGE_QUESTIONS[stage.stage] for stage in follow_up_stages]
    content = "Explore orchestrator (staged storyteller flow):\n" + "\n".join(
        f"{index}. {stage.title}: "
        f"{stage_values.get(stage.stage) or stage.objective} "
        f"[{'complete' if stage_values.get(stage.stage) else 'pending'}]"
        for index, stage in enumerate(_STAGE_FLOW, start=1)
    )
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="warning" if follow_up_questions else "success",
        content=content,
        summary=(
            "Prepared a staged exploration orchestrator with deterministic progression."
            if not follow_up_questions
            else "Prepared staged exploration and queued adaptive follow-up questions."
        ),
        metadata={
            "stage_count": str(len(_STAGE_FLOW)),
            "next_stage": (
                follow_up_stages[0].stage.value
                if follow_up_stages
                else ExploreStoryStage.VERIFICATION.value
            ),
            "feedback_loop_state": feedback_state.value,
            "critical_gap_count": str(critical_gap_count),
            "unresolved_stage_count": str(len(unresolved_stages)),
            "required_feedback_count": str(critical_gap_count),
            "next_feedback_question_id": (
                next_questions[0].question_id if next_questions else "none"
            ),
            "next_feedback_stage": (
                next_questions[0].stage.value
                if next_questions
                else StoryExplorationStage.READY_FOR_GENERATION.value
            ),
            "workflow_policy": "one-question-per-turn",
            "prompt": prompt,
        },
        warnings=(
            [
                "Critical exploration feedback is required before story synthesis can proceed."
                if critical_gap_count
                else _STAGE_WARNING
            ]
            if follow_up_questions
            else []
        ),
        follow_up_questions=follow_up_questions,
        question_items=[
            build_question_item(
                question_id=stage.question_id,
                question=_STAGE_QUESTIONS[stage.stage],
                question_type=(
                    InteractionQuestionType.CONSTRAINT
                    if stage.stage == ExploreStoryStage.CONSTRAINTS
                    else InteractionQuestionType.CLARIFICATION
                ),
                module_name=_MODULE_NAME,
                answer_slot_ids=[stage.answer_slot_id],
            )
            for stage in follow_up_stages
        ],
        answer_slots=[
            build_answer_slot(
                slot_id=stage.answer_slot_id,
                slot_type=AnswerSlotType.TEXT,
                prompt=_STAGE_SLOT_PROMPTS[stage.stage],
                module_name=_MODULE_NAME,
                value=stage_values.get(stage.stage),
            )
            for stage in _STAGE_FLOW
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary=(
                "Orchestrate motivation, API, implementation, constraints, and verification stages."
            ),
            required_context_keys=[stage.context_key for stage in _STAGE_FLOW if stage.required],
            preferred_question_ids=[stage.question_id for stage in follow_up_stages],
            consumes_answer_slot_ids=[stage.answer_slot_id for stage in _STAGE_FLOW],
        ),
    )

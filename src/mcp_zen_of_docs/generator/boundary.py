"""Generator boundary contracts and helper facades."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import DeterministicTurnPlan
from mcp_zen_of_docs.models import ModuleIntentProfile
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StorySessionStateContract
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import ToolStatus
from mcp_zen_of_docs.models import TurnPlanAction

from .orchestrator import advance_story_session_turn as _advance_story_session_turn
from .orchestrator import initialize_story_session_state as _initialize_story_session_state
from .orchestrator import orchestrate_story as _orchestrate_story


class StoryGeneratorPort(Protocol):
    """Boundary port for story generation use-cases."""

    def orchestrate_story(self, request: StoryGenerationRequest) -> OrchestratorResultContract:
        """Run deterministic module orchestration."""
        ...

    def initialize_story_session_state(
        self,
        result: OrchestratorResultContract,
        *,
        session_id: str,
        story_id: str | None = None,
    ) -> StorySessionStateContract:
        """Create deterministic session state from orchestration output."""
        ...

    def advance_story_session_turn(
        self,
        state: StorySessionStateContract,
        provided_answers: list[AnswerSlotContract] | None = None,
    ) -> StorySessionStateContract:
        """Advance one deterministic interaction turn and return updated state."""
        ...

    def initialize_story_loop(
        self,
        result: OrchestratorResultContract,
        *,
        session_id: str,
        story_id: str | None = None,
    ) -> StoryLoopProgress:
        """Initialize loop state and return channel-agnostic progress."""
        ...

    def advance_story_loop(
        self,
        state: StorySessionStateContract,
        provided_answers: list[AnswerSlotContract] | None = None,
    ) -> StoryLoopProgress:
        """Advance loop state and return channel-agnostic progress."""
        ...

    def project_story_interaction(
        self, response: StoryGenerationResponse
    ) -> StoryInteractionProjection:
        """Project orchestration output to channel-agnostic interaction payload."""
        ...


class StoryGeneratorBoundaryResult(BaseModel):
    """Typed wrapper for orchestration + session state handoff."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    result: OrchestratorResultContract = Field(
        description="Raw orchestrator result payload.",
    )
    state: StorySessionStateContract = Field(
        description="Initialized deterministic state snapshot.",
    )


class StoryLoopProgress(BaseModel):
    """Typed progress snapshot for deterministic story-loop operations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    status: ToolStatus = Field(
        description="Loop status derived from the current deterministic state.",
    )
    state: StorySessionStateContract = Field(
        description="Deterministic session state snapshot after one boundary operation.",
    )
    next_required_question_items: list[QuestionItemContract] = Field(
        default_factory=list,
        description="Required question items still unresolved after this boundary operation.",
    )
    pending_required_slot_ids: list[str] = Field(
        default_factory=list,
        description="Required answer slot identifiers without resolved values.",
    )
    applied_answer_slot_ids: list[str] = Field(
        default_factory=list,
        description="Answer slot identifiers consumed while applying this boundary operation.",
    )
    next_step_action: TurnPlanAction | None = Field(
        default=None,
        description="Next deterministic action inferred from the current turn-plan step.",
    )
    message: str | None = Field(
        default=None,
        description="Optional loop status detail for callers.",
    )


class StoryInteractionProjection(BaseModel):
    """Typed channel-agnostic interaction payload projected from story responses."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    status: ToolStatus = Field(description="Story generation status code.")
    tool: str = Field(description="Logical tool identifier for story generation.")
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Ordered follow-up questions required for completion.",
    )
    question_items: list[QuestionItemContract] = Field(
        default_factory=list,
        description="Structured interactive question contracts.",
    )
    answer_slots: list[AnswerSlotContract] = Field(
        default_factory=list,
        description="Structured answer slot contracts aggregated for this interaction payload.",
    )
    pending_required_slot_ids: list[str] = Field(
        default_factory=list,
        description="Required answer slot identifiers without resolved values.",
    )
    turn_plan: DeterministicTurnPlan | None = Field(
        default=None,
        description="Deterministic turn plan produced by orchestration when available.",
    )
    next_step_action: TurnPlanAction | None = Field(
        default=None,
        description="Next deterministic action inferred from the current turn-plan step.",
    )
    module_intent_profiles: list[ModuleIntentProfile] = Field(
        default_factory=list,
        description="Module intent profiles included for interactive orchestration clients.",
    )
    message: str | None = Field(default=None, description="Optional warning or error detail.")


def _pending_required_slot_ids(answer_slots: list[AnswerSlotContract]) -> list[str]:
    return [slot.slot_id for slot in answer_slots if slot.required and slot.value in (None, "", [])]


def _next_required_question_items(
    *,
    question_items: list[QuestionItemContract],
    pending_required_slot_ids: list[str],
) -> list[QuestionItemContract]:
    if not pending_required_slot_ids:
        return []
    pending_slot_ids = set(pending_required_slot_ids)
    return [
        question
        for question in question_items
        if question.required
        and (
            not question.answer_slot_ids
            or any(slot_id in pending_slot_ids for slot_id in question.answer_slot_ids)
        )
    ]


def _next_step_action_for_state(state: StorySessionStateContract) -> TurnPlanAction | None:
    if state.turn_plan is None or not state.turn_plan.steps:
        return None
    bounded_index = min(state.current_step_index, len(state.turn_plan.steps) - 1)
    return state.turn_plan.steps[bounded_index].action


def _loop_surface_status(
    state: StorySessionStateContract, pending_required_slot_ids: list[str]
) -> ToolStatus:
    if state.status == StorySessionStatus.ERROR:
        return "error"
    if pending_required_slot_ids:
        return "warning"
    return "success"


class StoryGeneratorBoundary:
    """Default boundary implementation delegating to orchestrator internals."""

    def orchestrate_story(self, request: StoryGenerationRequest) -> OrchestratorResultContract:
        """Run deterministic orchestration through the legacy orchestrator."""
        return _orchestrate_story(request)

    def initialize_story_session_state(
        self,
        result: OrchestratorResultContract,
        *,
        session_id: str,
        story_id: str | None = None,
    ) -> StorySessionStateContract:
        """Initialize deterministic session state."""
        return _initialize_story_session_state(result, session_id=session_id, story_id=story_id)

    def advance_story_session_turn(
        self,
        state: StorySessionStateContract,
        provided_answers: list[AnswerSlotContract] | None = None,
    ) -> StorySessionStateContract:
        """Advance deterministic state and expose only updated state at this boundary."""
        return _advance_story_session_turn(state, provided_answers).state

    def initialize_story_loop(
        self,
        result: OrchestratorResultContract,
        *,
        session_id: str,
        story_id: str | None = None,
    ) -> StoryLoopProgress:
        """Initialize deterministic loop state and return a channel-agnostic progress snapshot."""
        state = self.initialize_story_session_state(
            result,
            session_id=session_id,
            story_id=story_id,
        )
        pending_required_slot_ids = _pending_required_slot_ids(state.answer_slots)
        return StoryLoopProgress(
            status=_loop_surface_status(state, pending_required_slot_ids),
            state=state,
            next_required_question_items=_next_required_question_items(
                question_items=state.question_items,
                pending_required_slot_ids=pending_required_slot_ids,
            ),
            pending_required_slot_ids=pending_required_slot_ids,
            applied_answer_slot_ids=[],
            next_step_action=_next_step_action_for_state(state),
            message=state.last_message,
        )

    def advance_story_loop(
        self,
        state: StorySessionStateContract,
        provided_answers: list[AnswerSlotContract] | None = None,
    ) -> StoryLoopProgress:
        """Advance deterministic loop state and return a channel-agnostic progress snapshot."""
        evaluation = _advance_story_session_turn(state, provided_answers)
        progressed_state = evaluation.state
        return StoryLoopProgress(
            status=_loop_surface_status(progressed_state, evaluation.pending_required_slot_ids),
            state=progressed_state,
            next_required_question_items=list(evaluation.next_required_question_items),
            pending_required_slot_ids=list(evaluation.pending_required_slot_ids),
            applied_answer_slot_ids=list(evaluation.applied_answer_slot_ids),
            next_step_action=_next_step_action_for_state(progressed_state),
            message=progressed_state.last_message,
        )

    def project_story_interaction(
        self, response: StoryGenerationResponse
    ) -> StoryInteractionProjection:
        """Project orchestration response to a channel-agnostic interaction payload."""
        pending_required_slot_ids = _pending_required_slot_ids(response.answer_slots)
        turn_plan = response.turn_plan
        next_step_action: TurnPlanAction | None = None
        if turn_plan and turn_plan.current_step_index < len(turn_plan.steps):
            next_step_action = turn_plan.steps[turn_plan.current_step_index].action
        return StoryInteractionProjection(
            status=response.status,
            tool=response.tool,
            follow_up_questions=list(response.follow_up_questions),
            question_items=list(response.question_items),
            answer_slots=list(response.answer_slots),
            pending_required_slot_ids=pending_required_slot_ids,
            turn_plan=turn_plan,
            next_step_action=next_step_action,
            module_intent_profiles=list(response.module_intent_profiles),
            message=response.message,
        )

    def orchestrate_with_initialized_state(
        self,
        request: StoryGenerationRequest,
        *,
        session_id: str,
        story_id: str | None = None,
    ) -> StoryGeneratorBoundaryResult:
        """Compose orchestration and state initialization into one boundary operation."""
        result = self.orchestrate_story(request)
        state = self.initialize_story_session_state(
            result,
            session_id=session_id,
            story_id=story_id,
        )
        return StoryGeneratorBoundaryResult(result=result, state=state)


def get_story_generator_boundary() -> StoryGeneratorBoundary:
    """Return the default story generator boundary adapter."""
    return StoryGeneratorBoundary()


__all__ = [
    "StoryGeneratorBoundary",
    "StoryGeneratorBoundaryResult",
    "StoryGeneratorPort",
    "StoryInteractionProjection",
    "StoryLoopProgress",
    "get_story_generator_boundary",
]

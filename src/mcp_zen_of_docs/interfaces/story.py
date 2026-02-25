"""Typed interface adapters for interactive story transport surfaces."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.generator import get_story_generator_boundary
from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import DeterministicTurnPlan
from mcp_zen_of_docs.models import ModuleIntentProfile
from mcp_zen_of_docs.models import OrchestratorResultContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StorySessionStateContract
from mcp_zen_of_docs.models import ToolStatus
from mcp_zen_of_docs.models import TurnPlanAction


if TYPE_CHECKING:
    from collections.abc import Mapping
    from collections.abc import Sequence


class InterfaceChannel(StrEnum):
    """Transport channel identifiers for interface adapters."""

    CLI = "cli"
    MCP = "mcp"


class StoryLoopOperation(StrEnum):
    """Deterministic loop operation identifiers for interface adapters."""

    INITIALIZE = "initialize"
    ADVANCE = "advance"


class StoryInteractionSurface(BaseModel):
    """Channel-agnostic interaction contract for story follow-up flows."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    channel: InterfaceChannel = Field(
        description="Interface transport channel producing this payload."
    )
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
        description="Structured answer slot contracts aggregated for the interaction turn.",
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
        description="Next deterministic action inferred from the current turn plan step.",
    )
    module_intent_profiles: list[ModuleIntentProfile] = Field(
        default_factory=list,
        description="Module intent profiles included for interactive orchestration clients.",
    )
    message: str | None = Field(default=None, description="Optional warning or error detail.")


class StorySessionInitializeRequest(BaseModel):
    """Typed request adapter for deterministic story loop initialization."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    result: OrchestratorResultContract = Field(
        description=(
            "Orchestrator result payload used to initialize deterministic story session state."
        ),
    )
    session_id: str = Field(description="Stable session identifier for the interactive story loop.")
    story_id: str | None = Field(
        default=None,
        description="Optional story identifier override for the initialized session state.",
    )


class StorySessionAdvanceRequest(BaseModel):
    """Typed request adapter for deterministic story loop advancement."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    state: StorySessionStateContract = Field(
        description="Current deterministic story session state before the advancement pass.",
    )
    provided_answers: list[AnswerSlotContract] = Field(
        default_factory=list,
        description="Answer slots provided by the caller for this advancement pass.",
    )


class StoryInteractionLoopSurface(BaseModel):
    """Typed response adapter for deterministic loop initialization and advancement."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    channel: InterfaceChannel = Field(
        description="Interface transport channel producing this payload."
    )
    operation: StoryLoopOperation = Field(
        description="Deterministic loop adapter operation represented by this payload.",
    )
    status: ToolStatus = Field(
        description="Transport-stable status derived from the current loop state."
    )
    state: StorySessionStateContract = Field(
        description="Deterministic session state snapshot after applying the loop operation.",
    )
    next_required_question_items: list[QuestionItemContract] = Field(
        default_factory=list,
        description="Ordered required question items still unresolved after this loop operation.",
    )
    pending_required_slot_ids: list[str] = Field(
        default_factory=list,
        description="Required answer slot identifiers without resolved values.",
    )
    applied_answer_slot_ids: list[str] = Field(
        default_factory=list,
        description="Answer slot identifiers consumed while applying this loop operation.",
    )
    next_step_action: TurnPlanAction | None = Field(
        default=None,
        description="Next deterministic action inferred from the current turn plan step.",
    )
    message: str | None = Field(default=None, description="Optional loop status detail.")


_GENERATOR_BOUNDARY = get_story_generator_boundary()


def build_story_session_initialize_request(
    *,
    result: OrchestratorResultContract,
    session_id: str,
    story_id: str | None = None,
) -> StorySessionInitializeRequest:
    """Build a typed initialization request for deterministic story loop surfaces."""
    return StorySessionInitializeRequest(result=result, session_id=session_id, story_id=story_id)


def build_story_session_advance_request(
    *,
    state: StorySessionStateContract,
    provided_answers: Sequence[AnswerSlotContract] | None = None,
) -> StorySessionAdvanceRequest:
    """Build a typed advancement request for deterministic story loop surfaces."""
    return StorySessionAdvanceRequest(state=state, provided_answers=list(provided_answers or []))


def build_story_loop_initialize_surface(
    request: StorySessionInitializeRequest, *, channel: InterfaceChannel
) -> StoryInteractionLoopSurface:
    """Initialize deterministic session state and project transport-stable loop payload."""
    progress = _GENERATOR_BOUNDARY.initialize_story_loop(
        request.result,
        session_id=request.session_id,
        story_id=request.story_id,
    )
    return StoryInteractionLoopSurface(
        channel=channel,
        operation=StoryLoopOperation.INITIALIZE,
        status=progress.status,
        state=progress.state,
        next_required_question_items=list(progress.next_required_question_items),
        pending_required_slot_ids=list(progress.pending_required_slot_ids),
        applied_answer_slot_ids=list(progress.applied_answer_slot_ids),
        next_step_action=progress.next_step_action,
        message=progress.message,
    )


def build_story_loop_advance_surface(
    request: StorySessionAdvanceRequest, *, channel: InterfaceChannel
) -> StoryInteractionLoopSurface:
    """Advance deterministic session state and project transport-stable loop payload."""
    progress = _GENERATOR_BOUNDARY.advance_story_loop(
        request.state,
        request.provided_answers,
    )
    return StoryInteractionLoopSurface(
        channel=channel,
        operation=StoryLoopOperation.ADVANCE,
        status=progress.status,
        state=progress.state,
        next_required_question_items=list(progress.next_required_question_items),
        pending_required_slot_ids=list(progress.pending_required_slot_ids),
        applied_answer_slot_ids=list(progress.applied_answer_slot_ids),
        next_step_action=progress.next_step_action,
        message=progress.message,
    )


def build_story_request(  # noqa: PLR0913
    *,
    prompt: str,
    audience: str | None = None,
    modules: Sequence[str] | None = None,
    context: Mapping[str, str] | None = None,
    include_onboarding_guidance: bool = False,
    answer_slots: Sequence[AnswerSlotContract] | None = None,
) -> StoryGenerationRequest:
    """Build a typed story request payload from interface transport inputs."""
    return StoryGenerationRequest(
        prompt=prompt,
        audience=audience,
        modules=list(modules or []),
        context=dict(context or {}),
        include_onboarding_guidance=include_onboarding_guidance,
        answer_slots=list(answer_slots or []),
    )


def adapt_story_response_channel(
    response: StoryGenerationResponse, *, channel: InterfaceChannel
) -> StoryGenerationResponse:
    """Align onboarding channel metadata while preserving orchestration payload shape."""
    guidance = response.onboarding_guidance
    if guidance is None or guidance.channel == channel.value:
        return response
    return response.model_copy(
        update={
            "onboarding_guidance": guidance.model_copy(update={"channel": channel.value}),
        }
    )


def build_story_interaction_surface(
    response: StoryGenerationResponse, *, channel: InterfaceChannel
) -> StoryInteractionSurface:
    """Project a story response into a channel-stable interaction surface."""
    projection = _GENERATOR_BOUNDARY.project_story_interaction(response)
    return StoryInteractionSurface(
        channel=channel,
        status=projection.status,
        tool=projection.tool,
        follow_up_questions=list(projection.follow_up_questions),
        question_items=list(projection.question_items),
        answer_slots=list(projection.answer_slots),
        pending_required_slot_ids=list(projection.pending_required_slot_ids),
        turn_plan=projection.turn_plan,
        next_step_action=projection.next_step_action,
        module_intent_profiles=list(projection.module_intent_profiles),
        message=projection.message,
    )


__all__ = [
    "InterfaceChannel",
    "StoryInteractionLoopSurface",
    "StoryInteractionSurface",
    "StoryLoopOperation",
    "StorySessionAdvanceRequest",
    "StorySessionInitializeRequest",
    "adapt_story_response_channel",
    "build_story_interaction_surface",
    "build_story_loop_advance_surface",
    "build_story_loop_initialize_surface",
    "build_story_request",
    "build_story_session_advance_request",
    "build_story_session_initialize_request",
]

"""Deterministic scope interaction helpers for iterative story sessions."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import QuestionItemContract
from mcp_zen_of_docs.models import StorySessionStateContract
from mcp_zen_of_docs.models import StorySessionStatus
from mcp_zen_of_docs.models import StoryTurnTransition
from mcp_zen_of_docs.models import TurnPlanAction


__all__ = [
    "ScopeInteractionEvaluation",
    "evaluate_scope_interaction",
]


class ScopeInteractionEvaluation(BaseModel):
    """Typed evaluation result for one scope interaction resolution pass."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    state: StorySessionStateContract = Field(
        description="Updated deterministic story session state after applying provided answers.",
    )
    next_required_question_items: list[QuestionItemContract] = Field(
        default_factory=list,
        description="Ordered required questions still unresolved for the next turn.",
    )
    pending_required_slot_ids: list[str] = Field(
        default_factory=list,
        description="Required slot identifiers still missing values after answer merge.",
    )
    applied_answer_slot_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Answer slot identifiers updated from provided answers in this evaluation pass."
        ),
    )


def _is_unresolved_slot_value(value: object | None) -> bool:
    return value in (None, "", [])


def _merge_answer_slots(
    *,
    existing_slots: list[AnswerSlotContract],
    provided_answers: list[AnswerSlotContract],
) -> tuple[list[AnswerSlotContract], list[str]]:
    """Merge incoming answer slot values into current session answer slots."""
    provided_by_id = {
        slot.slot_id: slot for slot in provided_answers if not _is_unresolved_slot_value(slot.value)
    }
    merged_slots: list[AnswerSlotContract] = []
    applied_answer_slot_ids: list[str] = []
    seen_slot_ids: set[str] = set()

    for slot in existing_slots:
        seen_slot_ids.add(slot.slot_id)
        provided = provided_by_id.get(slot.slot_id)
        if provided is None:
            merged_slots.append(slot)
            continue
        merged_slots.append(slot.model_copy(update={"value": provided.value}))
        applied_answer_slot_ids.append(slot.slot_id)

    for slot in provided_answers:
        if slot.slot_id in seen_slot_ids:
            continue
        merged_slots.append(slot)
        if not _is_unresolved_slot_value(slot.value):
            applied_answer_slot_ids.append(slot.slot_id)

    return merged_slots, applied_answer_slot_ids


def _derive_pending_required_slot_ids(answer_slots: list[AnswerSlotContract]) -> list[str]:
    """Return ordered required slot identifiers that still need values."""
    return [
        slot.slot_id
        for slot in answer_slots
        if slot.required and _is_unresolved_slot_value(slot.value)
    ]


def _derive_next_required_questions(
    *,
    question_items: list[QuestionItemContract],
    pending_required_slot_ids: list[str],
) -> list[QuestionItemContract]:
    """Return required questions that map to unresolved required slots."""
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


def _resolve_next_step_index(
    state: StorySessionStateContract, *, pending_required_slot_ids: list[str]
) -> int:
    turn_plan = state.turn_plan
    if turn_plan is None or not turn_plan.steps:
        return state.current_step_index

    current_step_index = min(state.current_step_index, len(turn_plan.steps) - 1)
    if pending_required_slot_ids:
        for index in range(current_step_index, len(turn_plan.steps)):
            if turn_plan.steps[index].action == TurnPlanAction.WAIT_FOR_ANSWERS:
                return index
        return current_step_index

    for index in range(current_step_index, len(turn_plan.steps)):
        if turn_plan.steps[index].action == TurnPlanAction.EXECUTE_MODULES:
            return index
    for index in range(current_step_index, len(turn_plan.steps)):
        if turn_plan.steps[index].action == TurnPlanAction.FINALIZE_STORY:
            return index
    return current_step_index


def _resolve_next_status(
    *,
    current_status: StorySessionStatus,
    pending_required_slot_ids: list[str],
    next_step_action: TurnPlanAction | None,
) -> StorySessionStatus:
    if pending_required_slot_ids:
        return StorySessionStatus.WAITING_FOR_ANSWERS
    if next_step_action == TurnPlanAction.EXECUTE_MODULES:
        return StorySessionStatus.IN_PROGRESS
    if next_step_action == TurnPlanAction.FINALIZE_STORY:
        return StorySessionStatus.READY_TO_FINALIZE
    if current_status == StorySessionStatus.COMPLETED:
        return StorySessionStatus.COMPLETED
    return StorySessionStatus.READY_TO_FINALIZE


def evaluate_scope_interaction(
    state: StorySessionStateContract, provided_answers: list[AnswerSlotContract] | None = None
) -> ScopeInteractionEvaluation:
    """Evaluate unresolved scope interaction requirements for a story session."""
    merged_slots, applied_answer_slot_ids = _merge_answer_slots(
        existing_slots=state.answer_slots,
        provided_answers=list(provided_answers or []),
    )
    pending_required_slot_ids = _derive_pending_required_slot_ids(merged_slots)
    next_required_question_items = _derive_next_required_questions(
        question_items=state.question_items,
        pending_required_slot_ids=pending_required_slot_ids,
    )

    next_step_index = _resolve_next_step_index(
        state,
        pending_required_slot_ids=pending_required_slot_ids,
    )
    next_step_action: TurnPlanAction | None = None
    if state.turn_plan and state.turn_plan.steps:
        bounded_index = min(next_step_index, len(state.turn_plan.steps) - 1)
        next_step_action = state.turn_plan.steps[bounded_index].action

    next_status = _resolve_next_status(
        current_status=state.status,
        pending_required_slot_ids=pending_required_slot_ids,
        next_step_action=next_step_action,
    )
    reason = "required-slots-pending" if pending_required_slot_ids else "required-slots-resolved"
    transition = StoryTurnTransition(
        from_status=state.status,
        to_status=next_status,
        action=next_step_action or TurnPlanAction.WAIT_FOR_ANSWERS,
        applied_answer_slot_ids=applied_answer_slot_ids,
        previous_step_index=state.current_step_index,
        next_step_index=next_step_index,
        reason=reason,
        message=(
            "Required answer slots are still unresolved."
            if pending_required_slot_ids
            else "All required answer slots are resolved."
        ),
    )
    updated_state = state.model_copy(
        update={
            "status": next_status,
            "current_step_index": next_step_index,
            "answer_slots": merged_slots,
            "pending_required_slot_ids": pending_required_slot_ids,
            "transition_history": [*state.transition_history, transition],
            "last_message": transition.message,
        }
    )

    return ScopeInteractionEvaluation(
        state=updated_state,
        next_required_question_items=next_required_question_items,
        pending_required_slot_ids=pending_required_slot_ids,
        applied_answer_slot_ids=applied_answer_slot_ids,
    )

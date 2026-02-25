"""Shared builders for structured interaction metadata in story modules."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleIntentProfile
from mcp_zen_of_docs.models import QuestionItemContract


type StringList = list[str]
type AnswerSlotValue = str | bool | list[str] | None

__all__ = (
    "build_answer_slot",
    "build_intent_profile",
    "build_question_item",
)


def _list_or_empty(values: StringList | None) -> StringList:
    """Return input lists as-is or an empty list when absent."""
    return values or []


def build_question_item(  # noqa: PLR0913
    *,
    question_id: str,
    question: str,
    module_name: str,
    answer_slot_ids: StringList,
    question_type: InteractionQuestionType = InteractionQuestionType.CLARIFICATION,
    required: bool = True,
) -> QuestionItemContract:
    """Build a deterministic structured question payload for a module."""
    return QuestionItemContract(
        question_id=question_id,
        question=question,
        question_type=question_type,
        module_name=module_name,
        required=required,
        answer_slot_ids=answer_slot_ids,
    )


def build_answer_slot(  # noqa: PLR0913
    *,
    slot_id: str,
    slot_type: AnswerSlotType,
    prompt: str,
    module_name: str,
    required: bool = True,
    choices: StringList | None = None,
    value: AnswerSlotValue = None,
) -> AnswerSlotContract:
    """Build a deterministic answer slot payload for a module."""
    return AnswerSlotContract(
        slot_id=slot_id,
        slot_type=slot_type,
        prompt=prompt,
        module_name=module_name,
        required=required,
        choices=_list_or_empty(choices),
        value=value,
    )


def build_intent_profile(
    *,
    module_name: str,
    intent_summary: str,
    required_context_keys: StringList | None = None,
    preferred_question_ids: StringList | None = None,
    consumes_answer_slot_ids: StringList | None = None,
) -> ModuleIntentProfile:
    """Build a deterministic module intent profile for storyteller orchestration."""
    return ModuleIntentProfile(
        module_name=module_name,
        intent_summary=intent_summary,
        required_context_keys=_list_or_empty(required_context_keys),
        preferred_question_ids=_list_or_empty(preferred_question_ids),
        consumes_answer_slot_ids=_list_or_empty(consumes_answer_slot_ids),
    )

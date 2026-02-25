"""Audience module builder for storyteller context alignment."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile
from mcp_zen_of_docs.modules.interaction import build_question_item


__all__ = ["build_audience_module"]

_MODULE_NAME = "audience"
_DEFAULT_AUDIENCE = "general contributors"
_AUDIENCE_SLOT_ID = "slot-target-audience"
_AUDIENCE_QUESTION_ID = "q-target-audience"
_AUDIENCE_QUESTION = "Who is the target audience for this story?"


def build_audience_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build audience-specific writing guidance for a story request."""
    explicit_audience = (request.audience or request.context.get("audience") or "").strip()
    audience = explicit_audience or _DEFAULT_AUDIENCE
    prompt = request.prompt.strip() or "documentation update"
    warnings = (
        ["No explicit audience supplied; using default contributor profile."]
        if audience == _DEFAULT_AUDIENCE
        else []
    )
    answer_slots = [
        build_answer_slot(
            slot_id=_AUDIENCE_SLOT_ID,
            slot_type=AnswerSlotType.TEXT,
            prompt=_AUDIENCE_QUESTION,
            module_name=_MODULE_NAME,
            value=explicit_audience or None,
        )
    ]
    question_items = (
        [
            build_question_item(
                question_id=_AUDIENCE_QUESTION_ID,
                question=_AUDIENCE_QUESTION,
                question_type=InteractionQuestionType.CLARIFICATION,
                module_name=_MODULE_NAME,
                answer_slot_ids=[_AUDIENCE_SLOT_ID],
            )
        ]
        if not explicit_audience
        else []
    )
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="warning" if warnings else "success",
        content=(
            f'Target audience: {audience}. Explain "{prompt}" in practical terms, '
            "define required prior knowledge, and include one concrete outcome readers can achieve."
        ),
        summary=f"Audience alignment prepared for {audience}.",
        metadata={"audience": audience, "prompt": prompt},
        warnings=warnings,
        question_items=question_items,
        answer_slots=answer_slots,
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Define the reader persona so the story tone and depth stay grounded.",
            required_context_keys=["audience"],
            preferred_question_ids=[_AUDIENCE_QUESTION_ID] if not explicit_audience else [],
            consumes_answer_slot_ids=[_AUDIENCE_SLOT_ID],
        ),
    )

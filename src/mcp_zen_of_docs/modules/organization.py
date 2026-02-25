"""Organization module for deterministic section ordering."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile
from mcp_zen_of_docs.modules.interaction import build_question_item


__all__ = ["build_organization_module"]

_MODULE_NAME = "organization"
_SECTION_ORDER_QUESTION_ID = "q-section-order"
_SECTION_ORDER_SLOT_ID = "slot-section-order"
_REQUESTED_ORDERING_STRATEGY = "requested-order"
_DEFAULT_ORDERING_STRATEGY = "story-default"

_TITLE_OVERRIDES = {
    "audience": "Audience",
    "concepts": "Core Concepts",
    "explore": "Exploration",
    "function": "Functional Plan",
    "narrator": "Narrative Voice",
    "organization": "Document Organization",
    "structure": "Document Structure",
    "style": "Style Guide",
}
_DEFAULT_SECTIONS = ["audience", "concepts", "structure", "style"]


def _ordered_sections(modules: list[str]) -> list[str]:
    selected = modules or _DEFAULT_SECTIONS
    ordered: list[str] = []
    for module_name in selected:
        title = _TITLE_OVERRIDES.get(module_name, module_name.replace("_", " ").title())
        if title not in ordered:
            ordered.append(title)
    return ordered


def build_organization_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build recommended section ordering for the story output."""
    sections = _ordered_sections(request.modules)
    content = "Recommended section order:\n" + "\n".join(
        f"{index}. {section}" for index, section in enumerate(sections, start=1)
    )
    ordering_strategy = (
        _REQUESTED_ORDERING_STRATEGY if request.modules else _DEFAULT_ORDERING_STRATEGY
    )
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content=content,
        summary=f"Organized {len(sections)} sections for readable flow.",
        metadata={"section_count": str(len(sections)), "first_section": sections[0]},
        question_items=[
            build_question_item(
                question_id=_SECTION_ORDER_QUESTION_ID,
                question="Should section order follow requested modules or the default story arc?",
                question_type=InteractionQuestionType.CHOICE,
                module_name=_MODULE_NAME,
                required=False,
                answer_slot_ids=[_SECTION_ORDER_SLOT_ID],
            )
        ],
        answer_slots=[
            build_answer_slot(
                slot_id=_SECTION_ORDER_SLOT_ID,
                slot_type=AnswerSlotType.SINGLE_CHOICE,
                prompt="Choose the section ordering strategy.",
                module_name=_MODULE_NAME,
                required=False,
                choices=[_REQUESTED_ORDERING_STRATEGY, _DEFAULT_ORDERING_STRATEGY],
                value=ordering_strategy,
            )
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Sequence sections to support a coherent storyteller progression.",
            preferred_question_ids=[_SECTION_ORDER_QUESTION_ID],
            consumes_answer_slot_ids=[_SECTION_ORDER_SLOT_ID],
        ),
    )

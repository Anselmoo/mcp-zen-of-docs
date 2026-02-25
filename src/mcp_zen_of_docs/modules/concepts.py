"""Concept extraction module for prioritizing story ideas."""

from __future__ import annotations

import re

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import InteractionQuestionType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile
from mcp_zen_of_docs.modules.interaction import build_question_item


__all__ = ["build_concepts_module"]

_MODULE_NAME = "concepts"
_SLOT_ID = "slot-priority-concepts"
_QUESTION_ID = "q-priority-concepts"

_STOP_WORDS = {
    "about",
    "after",
    "before",
    "from",
    "into",
    "that",
    "this",
    "with",
    "your",
}
MAX_CONCEPTS = 4
MIN_CONCEPT_TOKEN_LENGTH = 4


def _extract_concepts(prompt: str) -> list[str]:
    concepts: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", prompt.lower()):
        if len(token) < MIN_CONCEPT_TOKEN_LENGTH or token in _STOP_WORDS or token in concepts:
            continue
        concepts.append(token)
        if len(concepts) == MAX_CONCEPTS:
            break
    return concepts or ["workflow", "outcome"]


def build_concepts_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build a concise key-concepts section from the story prompt."""
    concepts = _extract_concepts(request.prompt)
    concept_list = "\n".join(f"- {concept}" for concept in concepts)
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content=f"Core concepts to define:\n{concept_list}",
        summary=f"Identified {len(concepts)} core concepts to anchor the story.",
        metadata={"concept_count": str(len(concepts)), "first_concept": concepts[0]},
        question_items=[
            build_question_item(
                question_id=_QUESTION_ID,
                question="Which concepts should be emphasized first in the narrative?",
                question_type=InteractionQuestionType.CHOICE,
                module_name=_MODULE_NAME,
                required=False,
                answer_slot_ids=[_SLOT_ID],
            )
        ],
        answer_slots=[
            build_answer_slot(
                slot_id=_SLOT_ID,
                slot_type=AnswerSlotType.MULTI_CHOICE,
                prompt="Select the concepts to prioritize first in the story flow.",
                module_name=_MODULE_NAME,
                required=False,
                choices=concepts,
                value=concepts[:2],
            )
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Surface the key ideas the storyteller must define before details.",
            required_context_keys=["prompt"],
            preferred_question_ids=[_QUESTION_ID],
            consumes_answer_slot_ids=[_SLOT_ID],
        ),
    )

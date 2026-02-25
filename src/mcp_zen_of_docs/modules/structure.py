"""Structure module for markdown skeleton generation."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile


__all__ = ["build_structure_module"]

_MODULE_NAME = "structure"
_SLOT_ID = "slot-story-title"


def build_structure_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build a deterministic markdown skeleton for the story."""
    title = request.prompt.strip() or "Story"
    headings = [
        f"# {title}",
        "## Context",
        "## Approach",
        "## Verification",
        "## Next Steps",
    ]
    content = "\n".join(headings)
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content=content,
        summary="Generated a four-part structure skeleton.",
        metadata={"heading_count": str(len(headings)), "title": title},
        answer_slots=[
            build_answer_slot(
                slot_id=_SLOT_ID,
                slot_type=AnswerSlotType.TEXT,
                prompt="What title should anchor the story structure?",
                module_name=_MODULE_NAME,
                value=title,
            )
        ],
        intent_profile=build_intent_profile(
            module_name="structure",
            intent_summary=(
                "Provide a deterministic story scaffold that keeps the narrative on rails."
            ),
            required_context_keys=["prompt"],
            consumes_answer_slot_ids=[_SLOT_ID],
        ),
    )

"""Functional module for execution-focused story guidance."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile


__all__ = ["build_function_module"]

_MODULE_NAME = "function"
_SLOT_ID = "slot-functional-goal"


def build_function_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build functional guidance describing what the story should do."""
    objective = request.prompt.strip() or "deliver the requested story outcome"
    actions = [
        f"Define the input/output contract needed to execute: {objective}.",
        "Map each step to one user-visible result with clear acceptance criteria.",
        "Document fallback behavior for missing context or partial data.",
    ]
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content="Functional guidance:\n" + "\n".join(f"- {action}" for action in actions),
        summary="Captured functional execution expectations for the story.",
        metadata={"action_count": str(len(actions)), "objective": objective},
        answer_slots=[
            build_answer_slot(
                slot_id=_SLOT_ID,
                slot_type=AnswerSlotType.TEXT,
                prompt="What primary goal should the functional plan guarantee for readers?",
                module_name=_MODULE_NAME,
                value=request.context.get("goal"),
            )
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Translate narrative intent into concrete, verifiable actions.",
            required_context_keys=["goal"],
            consumes_answer_slot_ids=[_SLOT_ID],
        ),
    )

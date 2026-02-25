"""Style module for editorial guardrails in generated stories."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile


__all__ = ["build_style_module"]

_MODULE_NAME = "style"
_DEFAULT_AUDIENCE = "mixed-experience contributors"
_SLOT_ID = "slot-style-depth"
_DEPTH_CHOICES = ["concise", "balanced", "detailed"]
_DEFAULT_DEPTH = "balanced"


def build_style_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build style guardrails for writing the final story."""
    audience = (request.audience or _DEFAULT_AUDIENCE).strip()
    rules = [
        "Prefer active voice and concrete verbs.",
        "Keep sentences concise (target under 22 words).",
        f"Match depth to {audience} and define jargon on first use.",
        "Close each section with a clear action or verification step.",
    ]
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content="Style guidance:\n" + "\n".join(f"- {rule}" for rule in rules),
        summary="Prepared reusable style guardrails for consistent tone.",
        metadata={"rule_count": str(len(rules)), "audience": audience},
        answer_slots=[
            build_answer_slot(
                slot_id=_SLOT_ID,
                slot_type=AnswerSlotType.SINGLE_CHOICE,
                prompt="What level of narrative depth should style guidance target?",
                module_name=_MODULE_NAME,
                required=False,
                choices=_DEPTH_CHOICES,
                value=_DEFAULT_DEPTH,
            )
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Enforce a consistent storytelling voice and readability baseline.",
            required_context_keys=["audience"],
            consumes_answer_slot_ids=[_SLOT_ID],
        ),
    )

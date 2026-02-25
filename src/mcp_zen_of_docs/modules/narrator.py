"""Narrator module for voice and tone direction."""

from __future__ import annotations

from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import ModuleOutputContract
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.modules.interaction import build_answer_slot
from mcp_zen_of_docs.modules.interaction import build_intent_profile


__all__ = ["build_narrator_module"]

_MODULE_NAME = "narrator"
_DEFAULT_AUDIENCE = "new team members"
_VOICE = "calm-confident"
_SLOT_ID = "slot-narrator-voice"
_VOICE_CHOICES = [_VOICE, "mentor", "guide"]


def build_narrator_module(request: StoryGenerationRequest) -> ModuleOutputContract:
    """Build narrator voice guidance for the story."""
    audience = (request.audience or request.context.get("audience") or _DEFAULT_AUDIENCE).strip()
    prompt = request.prompt.strip() or "the requested documentation task"
    narrative = (
        f"Use a calm, confident narrator voice aimed at {audience}. "
        f'Introduce "{prompt}" with context first, then explain decisions with direct '
        "cause-and-effect language."
    )
    return ModuleOutputContract(
        module_name=_MODULE_NAME,
        status="success",
        content=narrative,
        summary=f"Narrator tone calibrated for {audience}.",
        metadata={"audience": audience, "voice": _VOICE},
        answer_slots=[
            build_answer_slot(
                slot_id=_SLOT_ID,
                slot_type=AnswerSlotType.SINGLE_CHOICE,
                prompt="Select the narrator voice for the story.",
                module_name=_MODULE_NAME,
                choices=_VOICE_CHOICES,
                value=_VOICE,
                required=False,
            )
        ],
        intent_profile=build_intent_profile(
            module_name=_MODULE_NAME,
            intent_summary="Maintain a consistent storyteller voice that fits reader expectations.",
            required_context_keys=["audience"],
            consumes_answer_slot_ids=[_SLOT_ID],
        ),
    )

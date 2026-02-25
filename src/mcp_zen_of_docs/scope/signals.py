"""Missing-context signal primitives for story interaction flows."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


__all__ = [
    "MissingContextKind",
    "MissingContextReport",
    "MissingContextSignal",
]


class MissingContextKind(StrEnum):
    """Typed categories for missing story context."""

    TARGET_AUDIENCE = "target-audience"
    GOAL = "goal"
    SCOPE = "scope"
    CONSTRAINTS = "constraints"
    MODULE_OUTPUT = "module-output"
    MODULE_KEY_POINT = "module-key-point"


class MissingContextSignal(BaseModel):
    """One missing-context signal with a user-facing follow-up question."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    kind: MissingContextKind = Field(
        description="Signal category describing what context is missing."
    )
    question: str = Field(
        description="Explicit follow-up question to request missing user context."
    )
    module_name: str | None = Field(
        default=None,
        description="Related module identifier when the signal is module-specific.",
    )
    context_key: str | None = Field(
        default=None,
        description="Context key that triggered the signal when applicable.",
    )


class MissingContextReport(BaseModel):
    """Aggregated missing-context signal payload for story composition flows."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    signals: list[MissingContextSignal] = Field(
        default_factory=list,
        description="Ordered missing-context signals detected for the current story scope.",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="De-duplicated follow-up questions derived from the signal set.",
    )

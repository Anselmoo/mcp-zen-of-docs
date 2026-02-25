"""Scope contracts for story composition context."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


__all__ = [
    "StoryScopeContract",
    "StoryScopeModuleOutput",
]


class StoryScopeModuleOutput(BaseModel):
    """Typed snapshot of one module output used by scope checks."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    module_name: str = Field(description="Module identifier that emitted this output.")
    summary: str | None = Field(default=None, description="Module summary content when available.")
    content: str | None = Field(default=None, description="Module body content when available.")


class StoryScopeContract(BaseModel):
    """Normalized story scope context consumed by connector checks."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    prompt: str = Field(description="Primary story generation prompt.")
    requested_modules: list[str] = Field(
        default_factory=list,
        description="Requested module identifiers in caller order.",
    )
    audience: str | None = Field(default=None, description="Explicit audience when provided.")
    goal: str | None = Field(default=None, description="Story goal context signal.")
    scope: str | None = Field(default=None, description="Story scope boundary signal.")
    constraints: str | None = Field(default=None, description="Narrative constraints signal.")
    module_outputs: list[StoryScopeModuleOutput] = Field(
        default_factory=list,
        description="Module outputs available for connector bridging.",
    )

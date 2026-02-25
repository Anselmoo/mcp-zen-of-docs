"""Telemetry helpers for FastMCP tool execution."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    from fastmcp import Context

__all__ = ["TelemetrySpan", "emit_telemetry_span"]


class TelemetrySpan(BaseModel):
    """Structured telemetry span emitted by middleware."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Telemetry span name.")
    duration_ms: float = Field(ge=0.0, description="Execution duration in milliseconds.")
    status: Literal["success", "error"] = Field(description="Final span status.")
    attributes: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="Additional telemetry attributes for the span.",
    )


def emit_telemetry_span(context: Context | None, span: TelemetrySpan) -> None:
    """Emit a telemetry span through the FastMCP context logger when available."""
    if context is None:
        return
    _ = context.debug("telemetry.span", extra={"span": span.model_dump(mode="json")})

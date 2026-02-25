"""Infrastructure boundary contracts for framework detection adapters."""

from __future__ import annotations

from os import PathLike  # noqa: TC003
from typing import Protocol

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.frameworks import detect_best_framework
from mcp_zen_of_docs.frameworks import detect_frameworks
from mcp_zen_of_docs.models import FrameworkDetectionResult  # noqa: TC001


class FrameworkDetectionPort(Protocol):
    """Boundary port for framework detection use-cases."""

    def detect_candidate(
        self, project_root: str | PathLike[str] = "."
    ) -> FrameworkDetectionResult | None:
        """Return highest-confidence framework candidate."""
        ...

    def detect_candidates(
        self, project_root: str | PathLike[str] = "."
    ) -> list[FrameworkDetectionResult]:
        """Return all framework candidates ordered by confidence."""
        ...


class FrameworkDetectionSnapshot(BaseModel):
    """Typed snapshot of framework detection outcomes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    candidate: FrameworkDetectionResult | None = Field(
        default=None,
        description="Best framework candidate for the scanned project root.",
    )
    candidates: list[FrameworkDetectionResult] = Field(
        default_factory=list,
        description="All framework candidates ordered by confidence.",
    )


class FrameworkDetectionGateway:
    """Default gateway adapter wrapping framework package integration functions."""

    def detect_candidate(
        self, project_root: str | PathLike[str] = "."
    ) -> FrameworkDetectionResult | None:
        """Return best framework candidate via framework integration functions."""
        return detect_best_framework(str(project_root))

    def detect_candidates(
        self, project_root: str | PathLike[str] = "."
    ) -> list[FrameworkDetectionResult]:
        """Return ordered framework candidates via framework integration functions."""
        return detect_frameworks(str(project_root))

    def capture_snapshot(
        self, project_root: str | PathLike[str] = "."
    ) -> FrameworkDetectionSnapshot:
        """Capture both best and full framework detection outputs."""
        candidates = self.detect_candidates(project_root)
        candidate = candidates[0] if candidates else None
        return FrameworkDetectionSnapshot(candidate=candidate, candidates=candidates)


def get_framework_detection_gateway() -> FrameworkDetectionGateway:
    """Return default infrastructure gateway for framework detection."""
    return FrameworkDetectionGateway()


__all__ = [
    "FrameworkDetectionGateway",
    "FrameworkDetectionPort",
    "FrameworkDetectionSnapshot",
    "get_framework_detection_gateway",
]

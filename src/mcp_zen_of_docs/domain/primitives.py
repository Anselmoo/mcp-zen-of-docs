"""Domain rules for authoring primitive support and framework translation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_zen_of_docs.domain.contracts import AuthoringPrimitive
from mcp_zen_of_docs.domain.contracts import FrameworkName
from mcp_zen_of_docs.domain.contracts import SupportLevel


if TYPE_CHECKING:
    from collections.abc import Callable


def list_all_primitives() -> list[AuthoringPrimitive]:
    """Return all known authoring primitives."""
    return list(AuthoringPrimitive)


def build_support_matrix(
    frameworks: list[FrameworkName],
    *,
    support_lookup: Callable[[FrameworkName, AuthoringPrimitive], SupportLevel],
) -> dict[str, dict[str, SupportLevel]]:
    """Build framework-to-primitive support mapping across all primitives."""
    primitives = list_all_primitives()
    return {
        framework.value: {
            primitive.value: support_lookup(framework, primitive) for primitive in primitives
        }
        for framework in frameworks
    }


__all__ = [
    "build_support_matrix",
    "list_all_primitives",
]

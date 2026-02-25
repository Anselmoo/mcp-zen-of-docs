"""Application layer references for mcp-zen-of-docs."""

from __future__ import annotations


APPLICATION_MODULES: tuple[str, ...] = (
    "mcp_zen_of_docs.generators",
    "mcp_zen_of_docs.generator",
    "mcp_zen_of_docs.modules",
    "mcp_zen_of_docs.validators",
)
APPLICATION_RESPONSIBILITIES: tuple[str, ...] = (
    "Coordinate story generation and validation workflows.",
    "Compose domain models into use-case level outputs for interfaces.",
)

__all__ = ["APPLICATION_MODULES", "APPLICATION_RESPONSIBILITIES"]

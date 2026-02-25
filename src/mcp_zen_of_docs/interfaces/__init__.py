"""Interface layer adapters for CLI and MCP entrypoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_zen_of_docs.cli import main as _cli_main
from mcp_zen_of_docs.server import main as _server_main

from .story import InterfaceChannel
from .story import StoryInteractionLoopSurface
from .story import StoryInteractionSurface
from .story import StoryLoopOperation
from .story import StorySessionAdvanceRequest
from .story import StorySessionInitializeRequest
from .story import adapt_story_response_channel
from .story import build_story_interaction_surface
from .story import build_story_loop_advance_surface
from .story import build_story_loop_initialize_surface
from .story import build_story_request
from .story import build_story_session_advance_request
from .story import build_story_session_initialize_request


if TYPE_CHECKING:
    from collections.abc import Sequence

INTERFACE_MODULES: tuple[str, ...] = (
    "mcp_zen_of_docs.server",
    "mcp_zen_of_docs.cli",
    "mcp_zen_of_docs.__main__",
    "mcp_zen_of_docs.interfaces.story",
)
INTERFACE_RESPONSIBILITIES: tuple[str, ...] = (
    "Expose MCP and CLI transport entrypoints.",
    "Delegate business workflows to the application layer.",
    "Project story interaction payloads into channel-stable typed contracts.",
)


def run_cli(args: Sequence[str] | None = None) -> None:
    """Run the Typer CLI entrypoint."""
    _cli_main(args)


def run_mcp_server() -> None:
    """Run the FastMCP server entrypoint."""
    _server_main()


__all__ = [
    "INTERFACE_MODULES",
    "INTERFACE_RESPONSIBILITIES",
    "InterfaceChannel",
    "StoryInteractionLoopSurface",
    "StoryInteractionSurface",
    "StoryLoopOperation",
    "StorySessionAdvanceRequest",
    "StorySessionInitializeRequest",
    "adapt_story_response_channel",
    "build_story_interaction_surface",
    "build_story_loop_advance_surface",
    "build_story_loop_initialize_surface",
    "build_story_request",
    "build_story_session_advance_request",
    "build_story_session_initialize_request",
    "run_cli",
    "run_mcp_server",
]

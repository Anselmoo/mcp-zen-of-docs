"""Transport-agnostic interface facade for application services.

This module gives CLI and MCP entrypoints a shared import surface so they no
longer depend on one another directly. The concrete implementations remain in
the existing service wrappers while the transport boundary is stabilized here.
"""

from __future__ import annotations

from mcp_zen_of_docs.server import audit_docstrings
from mcp_zen_of_docs.server import audit_frontmatter
from mcp_zen_of_docs.server import batch_scaffold_docs
from mcp_zen_of_docs.server import compose_docs_story
from mcp_zen_of_docs.server import configure_zensical_extensions
from mcp_zen_of_docs.server import create_copilot_artifact
from mcp_zen_of_docs.server import create_svg_asset
from mcp_zen_of_docs.server import detect_docs_context
from mcp_zen_of_docs.server import detect_project_readiness
from mcp_zen_of_docs.server import enrich_doc
from mcp_zen_of_docs.server import generate_agent_config
from mcp_zen_of_docs.server import generate_changelog
from mcp_zen_of_docs.server import generate_custom_theme
from mcp_zen_of_docs.server import generate_diagram
from mcp_zen_of_docs.server import generate_reference_docs
from mcp_zen_of_docs.server import generate_visual_asset
from mcp_zen_of_docs.server import get_authoring_profile
from mcp_zen_of_docs.server import init_framework_structure
from mcp_zen_of_docs.server import onboard_project
from mcp_zen_of_docs.server import optimize_docstrings
from mcp_zen_of_docs.server import plan_docs
from mcp_zen_of_docs.server import render_diagram
from mcp_zen_of_docs.server import resolve_primitive
from mcp_zen_of_docs.server import run_ephemeral_install_tool
from mcp_zen_of_docs.server import run_pipeline_phase
from mcp_zen_of_docs.server import scaffold_doc
from mcp_zen_of_docs.server import score_docs_quality
from mcp_zen_of_docs.server import sync_nav
from mcp_zen_of_docs.server import translate_primitives
from mcp_zen_of_docs.server import validate_docs
from mcp_zen_of_docs.server import write_doc


__all__ = [
    "audit_docstrings",
    "audit_frontmatter",
    "batch_scaffold_docs",
    "compose_docs_story",
    "configure_zensical_extensions",
    "create_copilot_artifact",
    "create_svg_asset",
    "detect_docs_context",
    "detect_project_readiness",
    "enrich_doc",
    "generate_agent_config",
    "generate_changelog",
    "generate_custom_theme",
    "generate_diagram",
    "generate_reference_docs",
    "generate_visual_asset",
    "get_authoring_profile",
    "init_framework_structure",
    "onboard_project",
    "optimize_docstrings",
    "plan_docs",
    "render_diagram",
    "resolve_primitive",
    "run_ephemeral_install_tool",
    "run_pipeline_phase",
    "scaffold_doc",
    "score_docs_quality",
    "sync_nav",
    "translate_primitives",
    "validate_docs",
    "write_doc",
]

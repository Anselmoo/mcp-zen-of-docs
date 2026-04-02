"""Stable public server entrypoints and tool wrappers."""

from __future__ import annotations

from .app import audit_docstrings
from .app import audit_frontmatter
from .app import batch_scaffold_docs
from .app import compose_docs_story
from .app import configure_zensical_extensions
from .app import create_copilot_artifact
from .app import create_svg_asset
from .app import detect_docs_context
from .app import detect_project_readiness
from .app import enrich_doc
from .app import generate_agent_config
from .app import generate_changelog
from .app import generate_custom_theme
from .app import generate_diagram
from .app import generate_reference_docs
from .app import generate_visual_asset
from .app import get_authoring_profile
from .app import init_framework_structure
from .app import main
from .app import mcp
from .app import onboard_project
from .app import optimize_docstrings
from .app import plan_docs
from .app import render_diagram
from .app import resolve_primitive
from .app import run_ephemeral_install_tool
from .app import run_pipeline_phase
from .app import scaffold_doc
from .app import score_docs_quality
from .app import sync_nav
from .app import translate_primitives
from .app import validate_docs
from .app import write_doc


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
    "main",
    "mcp",
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

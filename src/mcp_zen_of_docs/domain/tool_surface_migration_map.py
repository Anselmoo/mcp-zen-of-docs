"""Typed MCP tool-surface consolidation map for staged server migration."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ToolMigrationAction(StrEnum):
    """Action classification for current-to-target tool migration."""

    KEEP = "keep"
    CONSOLIDATE = "consolidate"
    ALIAS = "alias"
    REMOVE_LATER = "remove-later"


class TargetToolName(StrEnum):
    """Canonical CLI sub-app group names for the consolidated tool surface."""

    DETECT = "detect"
    PROFILE = "profile"
    SCAFFOLD = "scaffold"
    VALIDATE = "validate"
    GENERATE = "generate"
    ONBOARD = "onboard"
    THEME = "theme"
    COPILOT = "copilot"
    DOCSTRING = "docstring"
    STORY = "story"


class ToolMigrationEntry(BaseModel):
    """One source tool migration decision with execution metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    source_tool: str = Field(description="Current server tool name registered in server.py.")
    target_tool: TargetToolName = Field(description="Consolidated target tool name.")
    action: ToolMigrationAction = Field(description="Migration action for this source tool.")
    rationale: str = Field(description="Why this mapping preserves or improves the public surface.")
    migration_notes: str = Field(
        description="Practical migration notes for phased rollout and compatibility."
    )


class ToolSurfaceMigrationMap(BaseModel):
    """Machine-readable contract for MCP tool-surface consolidation planning."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    target_tools: list[TargetToolName] = Field(
        default_factory=list,
        description="Canonical target tool set in rollout order.",
    )
    entries: list[ToolMigrationEntry] = Field(
        default_factory=list,
        description="Current-to-target migration entries covering all registered server tools.",
    )
    migration_policy: str = Field(
        description="Human-readable policy string for safe, non-breaking migration sequencing."
    )


def get_tool_surface_migration_map() -> ToolSurfaceMigrationMap:
    """Return the staged mapping from the current tool surface to the target set."""
    target_tools = [
        TargetToolName.DETECT,
        TargetToolName.PROFILE,
        TargetToolName.SCAFFOLD,
        TargetToolName.VALIDATE,
        TargetToolName.GENERATE,
        TargetToolName.ONBOARD,
        TargetToolName.THEME,
        TargetToolName.COPILOT,
        TargetToolName.DOCSTRING,
        TargetToolName.STORY,
    ]
    entries = [
        ToolMigrationEntry(
            source_tool="generate_cli_docs",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale=(
                "CLI docs generation is a reference-doc subtype and aligns to a single API."
            ),
            migration_notes=(
                "Keep existing registration; introduce generate_reference_docs alias first."
            ),
        ),
        ToolMigrationEntry(
            source_tool="generate_mcp_tools_docs",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="MCP tool docs generation belongs to the same reference-doc capability.",
            migration_notes="Retain legacy wrapper and route to shared reference-doc orchestrator.",
        ),
        ToolMigrationEntry(
            source_tool="generate_material_reference_snippets",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.REMOVE_LATER,
            rationale=(
                "Snippet templates are reusable reference assets and fit one generation surface."
            ),
            migration_notes=(
                "Mark for remove-later after parity checks under generate_reference_docs."
            ),
        ),
        ToolMigrationEntry(
            source_tool="generate_onboarding_skeleton",
            target_tool=TargetToolName.ONBOARD,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Onboarding skeleton is one sub-flow within project onboarding.",
            migration_notes=(
                "Preserve as compatibility wrapper until clients migrate to onboard_project."
            ),
        ),
        ToolMigrationEntry(
            source_tool="generate_story",
            target_tool=TargetToolName.STORY,
            action=ToolMigrationAction.ALIAS,
            rationale="Story composition remains a core use-case with clearer intent naming.",
            migration_notes=(
                "Add compose_docs_story and retain generate_story as alias through transition."
            ),
        ),
        ToolMigrationEntry(
            source_tool="generate_doc_boilerplate",
            target_tool=TargetToolName.ONBOARD,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale=(
                "Boilerplate generation is a gated onboarding stage, not a separate end-state tool."
            ),
            migration_notes="Keep registration; deprecate once onboard_project exposes gated mode.",
        ),
        ToolMigrationEntry(
            source_tool="list_authoring_primitives",
            target_tool=TargetToolName.PROFILE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Primitive catalog contributes to a broader authoring-profile response.",
            migration_notes=(
                "Fold primitive list into profile payload; maintain list API for compatibility."
            ),
        ),
        ToolMigrationEntry(
            source_tool="detect_framework",
            target_tool=TargetToolName.DETECT,
            action=ToolMigrationAction.ALIAS,
            rationale=(
                "Framework detection becomes one facet of richer documentation context detection."
            ),
            migration_notes="Expose detect_docs_context then alias detect_framework in-place.",
        ),
        ToolMigrationEntry(
            source_tool="lookup_primitive_support",
            target_tool=TargetToolName.PROFILE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Support lookup is one primitive-resolution concern among several.",
            migration_notes=(
                "Route through resolve_primitive with mode=support to avoid behavior drift."
            ),
        ),
        ToolMigrationEntry(
            source_tool="render_framework_primitive",
            target_tool=TargetToolName.PROFILE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Framework snippet rendering is another primitive-resolution concern.",
            migration_notes=(
                "Route through resolve_primitive with mode=render for phased convergence."
            ),
        ),
        ToolMigrationEntry(
            source_tool="translate_primitive_syntax",
            target_tool=TargetToolName.PROFILE,
            action=ToolMigrationAction.ALIAS,
            rationale=(
                "Translation functionality remains but adopts plural naming for batch expansion."
            ),
            migration_notes=(
                "Retain translate_primitive_syntax until batch-translation semantics "
                "are stabilized."
            ),
        ),
        ToolMigrationEntry(
            source_tool="check_docs_links",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Link checking is a validator dimension under a single validation endpoint.",
            migration_notes=(
                "Expose validate_docs checks=['links']; preserve existing callable wrapper."
            ),
        ),
        ToolMigrationEntry(
            source_tool="check_orphan_docs",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Orphan detection is a validator dimension under a unified validation API.",
            migration_notes=(
                "Expose validate_docs checks=['orphan-docs']; "
                "keep legacy tool registration for now."
            ),
        ),
        ToolMigrationEntry(
            source_tool="check_language_structure",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.REMOVE_LATER,
            rationale=(
                "Language-structure checks should share configuration and reporting "
                "with validators."
            ),
            migration_notes=(
                "Expose validate_docs checks=['structure']; remove-later after adoption."
            ),
        ),
        ToolMigrationEntry(
            source_tool="score_docs_quality",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.KEEP,
            rationale="Quality scoring is already correctly scoped and named for long-term use.",
            migration_notes=(
                "Keep registration as-is; may also be callable from validate_docs aggregate mode."
            ),
        ),
        ToolMigrationEntry(
            source_tool="scaffold_doc",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale="Scaffolding is a distinct authoring operation and should remain explicit.",
            migration_notes="No rename required; retain semantics and registration unchanged.",
        ),
        ToolMigrationEntry(
            source_tool="enrich_doc",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale="Enrichment closes the generate→write gap and is a distinct authoring step.",
            migration_notes="New tool; no migration required.",
        ),
        ToolMigrationEntry(
            source_tool="get_framework_capability_matrix_v2",
            target_tool=TargetToolName.PROFILE,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale=(
                "Capability matrix data is a profile facet, not a standalone primary action."
            ),
            migration_notes=(
                "Embed matrix within get_authoring_profile; maintain read-only legacy accessor."
            ),
        ),
        ToolMigrationEntry(
            source_tool="get_runtime_onboarding_matrix",
            target_tool=TargetToolName.DETECT,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Runtime onboarding guidance aligns with readiness evaluation outputs.",
            migration_notes=(
                "Return runtime track recommendations via detect_project_readiness diagnostics."
            ),
        ),
        ToolMigrationEntry(
            source_tool="init_project",
            target_tool=TargetToolName.ONBOARD,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Initialization is a first-stage onboarding capability.",
            migration_notes=(
                "Keep init_project callable while onboard_project orchestrates full sequence."
            ),
        ),
        ToolMigrationEntry(
            source_tool="check_init_status",
            target_tool=TargetToolName.DETECT,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Init status checking is a readiness signal for project setup.",
            migration_notes=(
                "Preserve check_init_status and surface identical status "
                "in detect_project_readiness."
            ),
        ),
        ToolMigrationEntry(
            source_tool="create_instruction",
            target_tool=TargetToolName.COPILOT,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Consolidated into create_copilot_artifact with kind='instruction'.",
            migration_notes="Use create_copilot_artifact(kind='instruction', ...).",
        ),
        ToolMigrationEntry(
            source_tool="create_prompt",
            target_tool=TargetToolName.COPILOT,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Consolidated into create_copilot_artifact with kind='prompt'.",
            migration_notes="Use create_copilot_artifact(kind='prompt', ...).",
        ),
        ToolMigrationEntry(
            source_tool="create_agent",
            target_tool=TargetToolName.COPILOT,
            action=ToolMigrationAction.CONSOLIDATE,
            rationale="Consolidated into create_copilot_artifact with kind='agent'.",
            migration_notes="Use create_copilot_artifact(kind='agent', ...).",
        ),
        ToolMigrationEntry(
            source_tool="create_copilot_artifact",
            target_tool=TargetToolName.COPILOT,
            action=ToolMigrationAction.KEEP,
            rationale="Consolidated Copilot artifact creation tool (instruction/prompt/agent).",
            migration_notes="Replaces create_instruction, create_prompt, create_agent.",
        ),
        ToolMigrationEntry(
            source_tool="plan_docs",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale="New tool for structured page planning with dependencies.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="batch_scaffold_docs",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale="New tool for batch scaffold generation.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="generate_agent_config",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool for multi-agent platform configuration.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="run_pipeline_phase",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale="New tool for phase-gated docs pipeline execution.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="audit_frontmatter",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool completing the validate→fix loop for frontmatter.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="sync_nav",
            target_tool=TargetToolName.VALIDATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool for holistic nav/sidebar audit, generate, and repair.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="generate_visual_asset",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool producing real SVG markup from parametric templates.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="generate_diagram",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool providing first-class Mermaid diagram generation.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="render_diagram",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool rendering Mermaid source to SVG/PNG via mmdc.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="generate_changelog",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale="New tool parsing git conventional commits to generate changelog entries.",
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="run_ephemeral_install_tool",
            target_tool=TargetToolName.ONBOARD,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool exposing the uvx/npx tmp-and-copy pattern as a first-class MCP tool."
            ),
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="init_framework_structure",
            target_tool=TargetToolName.ONBOARD,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool running a framework's native CLI init in an isolated temp dir "
                "and copying the canonical folder scaffold to the project root."
            ),
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="write_doc",
            target_tool=TargetToolName.SCAFFOLD,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool producing a complete, ready-to-publish documentation page "
                "in a single call; distinct from scaffold_doc (stubs) and enrich_doc (fills TODOs)."
            ),
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="create_svg_asset",
            target_tool=TargetToolName.GENERATE,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool persisting arbitrary SVG markup (e.g., LLM-generated) to a file; "
                "distinct from generate_visual_asset which uses parametric templates."
            ),
            migration_notes="Direct mapping; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="audit_docstrings",
            target_tool=TargetToolName.DOCSTRING,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool auditing source files for undocumented public symbols and reporting "
                "docstring coverage across Python, TypeScript, Go, Rust, Java, and C#."
            ),
            migration_notes="New capability; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="optimize_docstrings",
            target_tool=TargetToolName.DOCSTRING,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "New tool inserting canonical docstring stubs (Google, TSDoc, GoDoc, RustDoc, "
                "JavaDoc, XML-doc) for undocumented public symbols."
            ),
            migration_notes="New capability; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="generate_custom_theme",
            target_tool=TargetToolName.THEME,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "Generates framework-specific CSS/JS theme files with brand colors "
                "for Zensical, Docusaurus, VitePress, Starlight, and generic sites."
            ),
            migration_notes="New capability; no legacy predecessor.",
        ),
        ToolMigrationEntry(
            source_tool="configure_zensical_extensions",
            target_tool=TargetToolName.THEME,
            action=ToolMigrationAction.KEEP,
            rationale=(
                "Generates TOML/YAML configuration blocks for pymdownx and standard "
                "Python-Markdown extensions used in Zensical/MkDocs Material projects. "
                "Dependency-aware: surfaces required extra_javascript CDN links."
            ),
            migration_notes="New capability; no legacy predecessor.",
        ),
    ]
    return ToolSurfaceMigrationMap(
        target_tools=target_tools,
        entries=entries,
        migration_policy=(
            "No @mcp.tool removals during initial rollout; "
            "add target aliases/consolidations first, "
            "measure parity, then deprecate legacy names with remove-later notices."
        ),
    )


def list_mapped_source_tools() -> list[str]:
    """Return all current source tool names represented in the consolidation map."""
    return [entry.source_tool for entry in get_tool_surface_migration_map().entries]


def resolve_target_tool(source_tool: str) -> TargetToolName | None:
    """Resolve the target tool for a current source tool name."""
    for entry in get_tool_surface_migration_map().entries:
        if entry.source_tool == source_tool:
            return entry.target_tool
    return None


__all__ = [
    "TargetToolName",
    "ToolMigrationAction",
    "ToolMigrationEntry",
    "ToolSurfaceMigrationMap",
    "get_tool_surface_migration_map",
    "list_mapped_source_tools",
    "resolve_target_tool",
]

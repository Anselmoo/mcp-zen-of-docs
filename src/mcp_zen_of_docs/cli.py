"""Typer CLI for the consolidated mcp-zen-of-docs tool surface."""

from __future__ import annotations

import asyncio
import json
import re

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import NoReturn

import typer

from click.exceptions import NoArgsIsHelpError
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .generators import run_ephemeral_install
from .models import AgentPlatform
from .models import AuthoringPrimitive
from .models import ChangelogEntryFormat
from .models import ComposeDocsStoryResponse
from .models import CopilotAgentMode
from .models import CopilotArtifactKind
from .models import CustomThemeTarget
from .models import DiagramType
from .models import DocsDeployProvider
from .models import DocsValidationCheck
from .models import DocstringAuditRequest
from .models import DocstringLanguage
from .models import DocstringOptimizerRequest
from .models import DocstringStyle
from .models import EphemeralInstallRequest
from .models import FrameworkName
from .models import GenerateReferenceDocsKind
from .models import OnboardProjectMode
from .models import PipelinePhase
from .models import PrimitiveResolutionMode
from .models import ScaffoldDocRequest
from .models import ShellScriptType
from .models import SourceCodeHost
from .models import StoryMigrationMode
from .models import SyncNavMode
from .models import VisualAssetKind
from .models import VisualAssetOperation
from .models import WriteDocRequest
from .models import ZensicalExtension
from .server import audit_docstrings
from .server import audit_frontmatter
from .server import batch_scaffold_docs
from .server import compose_docs_story
from .server import create_copilot_artifact
from .server import create_svg_asset
from .server import detect_docs_context
from .server import detect_project_readiness
from .server import enrich_doc
from .server import generate_agent_config
from .server import generate_changelog
from .server import generate_diagram
from .server import generate_reference_docs
from .server import generate_visual_asset
from .server import get_authoring_profile
from .server import init_framework_structure
from .server import onboard_project
from .server import optimize_docstrings
from .server import plan_docs
from .server import render_diagram
from .server import resolve_primitive
from .server import run_pipeline_phase
from .server import scaffold_doc
from .server import score_docs_quality
from .server import sync_nav
from .server import translate_primitives
from .server import validate_docs
from .server import write_doc


if TYPE_CHECKING:
    from collections.abc import Sequence

app = typer.Typer(
    add_completion=True,
    help="Consolidated CLI for mcp-zen-of-docs documentation generation and validation tasks.",
    epilog="For detailed usage of individual commands, use 'mcp-zen-of-docs <command> --help'.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

detect_app = typer.Typer(name="detect", help="Detect docs context and project readiness")
profile_app = typer.Typer(name="profile", help="Framework authoring profiles and primitives")
scaffold_app = typer.Typer(name="scaffold", help="Create and write documentation pages")
validate_app = typer.Typer(name="validate", help="Quality validation and scoring")
generate_app = typer.Typer(name="generate", help="Generate visuals, diagrams, and references")
onboard_app = typer.Typer(name="onboard", help="Set up documentation for any project")
theme_app = typer.Typer(name="theme", help="CSS/JS theme customization")
copilot_app = typer.Typer(name="copilot", help="VS Code Copilot integration")
docstring_app = typer.Typer(name="docstring", help="Source code docstring tools")

app.add_typer(detect_app, name="detect")
app.add_typer(profile_app, name="profile")
app.add_typer(scaffold_app, name="scaffold")
app.add_typer(validate_app, name="validate")
app.add_typer(generate_app, name="generate")
app.add_typer(onboard_app, name="onboard")
app.add_typer(theme_app, name="theme")
app.add_typer(copilot_app, name="copilot")
app.add_typer(docstring_app, name="docstring")


class CliErrorResponse(BaseModel):
    """Typed CLI error response contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    status: str = Field(default="error", description="CLI command status.")
    message: str = Field(description="Error detail message.")


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    return slug[:80] or "story"


def _write_story_output(response: ComposeDocsStoryResponse, output_dir: Path) -> Path:
    """Write story narrative to a markdown file in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    title = response.story.title or response.story.story_id or "story"
    filename = _slugify(title) + ".md"
    filepath = output_dir / filename

    parts: list[str] = []
    if response.story.title:
        parts.append(f"# {response.story.title}\n")
    if response.story.narrative:
        parts.append(response.story.narrative)

    filepath.write_text(
        "\n".join(parts) or "# Story\n\n_No narrative content generated._\n",
        encoding="utf-8",
    )
    return filepath


def _emit(payload: BaseModel) -> None:
    """Serialise a Pydantic model to JSON and print it to stdout."""
    typer.echo(json.dumps(payload.model_dump(mode="json"), sort_keys=True))


def _emit_error(message: str) -> NoReturn:
    """Emit a structured error response and exit with code 2."""
    _emit(CliErrorResponse(message=message))
    raise typer.Exit(code=2)


def _parse_context(context_json: str | None) -> dict[str, str]:
    """Parse an optional JSON string into a flat string-keyed dict, or return empty dict."""
    if context_json is None:
        return {}
    try:
        parsed = json.loads(context_json)
    except json.JSONDecodeError as exc:
        _emit_error(f"context-json must be valid JSON: {exc.msg}.")
    if not isinstance(parsed, dict):
        _emit_error("context-json must decode to an object.")
    return {str(key): str(value) for key, value in parsed.items()}


@detect_app.command("context")
def detect_docs_context_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
) -> None:
    """Detect docs framework context and runtime onboarding guidance."""
    _emit(detect_docs_context(project_root=str(project_root)))


@detect_app.command("readiness")
def detect_project_readiness_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
) -> None:
    """Assess project readiness and initialization gate status."""
    _emit(detect_project_readiness(project_root=str(project_root)))


@onboard_app.command("plan")
def plan_docs_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    framework: Annotated[str | None, typer.Option("--framework")] = None,
    scope: Annotated[str, typer.Option("--scope")] = "full",
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
) -> None:
    """Generate a structured documentation page plan with dependencies."""
    _emit(
        plan_docs(
            project_root=str(project_root),
            framework=framework,
            scope=scope,
            docs_root=str(docs_root),
        )
    )


@profile_app.command("show")
def get_authoring_profile_command() -> None:
    """Return primitive catalog plus framework capability matrix."""
    _emit(get_authoring_profile())


@profile_app.command("resolve")
def resolve_primitive_command(
    framework: Annotated[FrameworkName, typer.Option("--framework")],
    primitive: Annotated[AuthoringPrimitive, typer.Option("--primitive")],
    mode: Annotated[PrimitiveResolutionMode, typer.Option("--mode")] = (
        PrimitiveResolutionMode.SUPPORT
    ),
    topic: Annotated[str | None, typer.Option("--topic")] = None,
) -> None:
    """Resolve primitive support and optional rendered snippets."""
    _emit(
        resolve_primitive(
            framework=framework,
            primitive=primitive,
            mode=mode,
            topic=topic,
        )
    )


@profile_app.command("translate")
def translate_primitives_command(
    source_framework: Annotated[FrameworkName, typer.Option("--source-framework")],
    target_framework: Annotated[FrameworkName, typer.Option("--target-framework")],
    primitive: Annotated[AuthoringPrimitive, typer.Option("--primitive")],
    topic: Annotated[str | None, typer.Option("--topic")] = None,
) -> None:
    """Translate primitives between documentation frameworks."""
    _emit(
        translate_primitives(
            source_framework=source_framework,
            target_framework=target_framework,
            primitive=primitive,
            topic=topic,
        )
    )


@app.command("story")
def compose_docs_story_command(  # noqa: PLR0913
    prompt: Annotated[str, typer.Option("--prompt")],
    audience: Annotated[str | None, typer.Option("--audience")] = None,
    modules: Annotated[list[str] | None, typer.Option("--module")] = None,
    context_json: Annotated[str | None, typer.Option("--context-json")] = None,
    *,
    include_onboarding_guidance: Annotated[
        bool, typer.Option("--include-onboarding-guidance")
    ] = False,
    enable_runtime_loop: Annotated[bool | None, typer.Option("--enable-runtime-loop")] = None,
    runtime_max_turns: Annotated[int | None, typer.Option("--runtime-max-turns", min=1)] = None,
    auto_advance: Annotated[bool | None, typer.Option("--auto-advance")] = None,
    migration_mode: Annotated[StoryMigrationMode | None, typer.Option("--migration-mode")] = None,
    migration_source_framework: Annotated[
        FrameworkName | None, typer.Option("--migration-source-framework")
    ] = None,
    migration_target_framework: Annotated[
        FrameworkName | None, typer.Option("--migration-target-framework")
    ] = None,
    migration_improve_clarity: Annotated[
        bool, typer.Option("--migration-improve-clarity/--no-migration-improve-clarity")
    ] = True,
    migration_strengthen_structure: Annotated[
        bool, typer.Option("--migration-strengthen-structure/--no-migration-strengthen-structure")
    ] = True,
    migration_enrich_examples: Annotated[
        bool, typer.Option("--migration-enrich-examples/--no-migration-enrich-examples")
    ] = False,
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
) -> None:
    """Compose documentation stories via consolidated story orchestration."""
    result = compose_docs_story(
        prompt=prompt,
        audience=audience,
        modules=modules,
        context=_parse_context(context_json),
        include_onboarding_guidance=include_onboarding_guidance,
        enable_runtime_loop=enable_runtime_loop,
        runtime_max_turns=runtime_max_turns,
        auto_advance=auto_advance,
        migration_mode=migration_mode,
        migration_source_framework=migration_source_framework,
        migration_target_framework=migration_target_framework,
        migration_improve_clarity=migration_improve_clarity,
        migration_strengthen_structure=migration_strengthen_structure,
        migration_enrich_examples=migration_enrich_examples,
    )

    if output_dir is not None:
        written_path = _write_story_output(result, output_dir)
        typer.echo(f"Written to: {written_path}")

    _emit(result)


@scaffold_app.command("doc")
def scaffold_doc_command(  # noqa: PLR0913
    doc_path: Annotated[Path, typer.Option("--doc-path")],
    title: Annotated[str, typer.Option("--title")],
    *,
    add_to_nav: Annotated[bool, typer.Option("--add-to-nav/--no-add-to-nav")] = True,
    mkdocs_file: Annotated[Path, typer.Option("--mkdocs-file")] = Path("mkdocs.yml"),
    description: Annotated[str, typer.Option("--description")] = "",
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
) -> None:
    """Create docs scaffold files with optional MkDocs navigation updates."""
    _emit(
        scaffold_doc(
            doc_path=str(doc_path),
            title=title,
            add_to_nav=add_to_nav,
            mkdocs_file=str(mkdocs_file),
            description=description,
            overwrite=overwrite,
            framework=framework,
        )
    )


@scaffold_app.command("batch")
def batch_scaffold_docs_command(
    pages_json: Annotated[Path | None, typer.Option("--pages-json")] = None,
    plan_response_json: Annotated[Path | None, typer.Option("--plan-response-json")] = None,
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
) -> None:
    """Batch-create multiple doc scaffolds from JSON input."""
    if pages_json and plan_response_json:
        _emit_error("Provide --pages-json or --plan-response-json, not both.")
    if not pages_json and not plan_response_json:
        _emit_error("Provide --pages-json or --plan-response-json.")
    if plan_response_json:
        raw = json.loads(plan_response_json.read_text(encoding="utf-8"))
        pages_data = [
            {"doc_path": p["path"], "title": p["title"], "description": p.get("description", "")}
            for p in raw.get("pages", [])
        ]
    else:
        pages_data = json.loads(pages_json.read_text(encoding="utf-8"))  # type: ignore[union-attr]
    _emit(
        batch_scaffold_docs(
            pages=[ScaffoldDocRequest.model_validate(p) for p in pages_data],
            docs_root=str(docs_root),
            framework=framework.value if framework else None,
        )
    )


@scaffold_app.command("enrich")
def enrich_doc_command(
    doc_path: Annotated[Path, typer.Option("--doc-path")],
    content: Annotated[str, typer.Option("--content")] = "",
    *,
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
    sections_to_enrich: Annotated[list[str] | None, typer.Option("--section")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Enrich a scaffold stub by replacing TODO placeholders with provided content."""
    _emit(
        enrich_doc(
            doc_path=str(doc_path),
            content=content,
            framework=framework,
            sections_to_enrich=sections_to_enrich,
            overwrite=overwrite,
        )
    )


@validate_app.command("all")
def validate_docs_command(  # noqa: PLR0913
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    mkdocs_file: Annotated[Path, typer.Option("--mkdocs-file")] = Path("mkdocs.yml"),
    external_mode: Annotated[str, typer.Option("--external-mode")] = "report",
    required_headers: Annotated[list[str] | None, typer.Option("--required-header")] = None,
    required_frontmatter: Annotated[
        list[str] | None, typer.Option("--required-frontmatter")
    ] = None,
    checks: Annotated[list[DocsValidationCheck] | None, typer.Option("--check")] = None,
) -> None:
    """Run consolidated docs validation checks."""
    _emit(
        validate_docs(
            docs_root=str(docs_root),
            mkdocs_file=str(mkdocs_file),
            external_mode=external_mode,
            required_headers=required_headers,
            required_frontmatter=required_frontmatter,
            checks=checks,
        )
    )


@validate_app.command("score")
def score_docs_quality_command(
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
) -> None:
    """Score documentation quality for a docs root."""
    _emit(score_docs_quality(docs_root=str(docs_root)))


@onboard_app.command("full")
def onboard_project_command(  # noqa: PLR0913
    project_name: Annotated[str, typer.Option("--project-name")] = "Project",
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    output_file: Annotated[Path | None, typer.Option("--output-file")] = None,
    mode: Annotated[OnboardProjectMode, typer.Option("--mode")] = OnboardProjectMode.SKELETON,
    *,
    include_checklist: Annotated[
        bool, typer.Option("--include-checklist/--no-include-checklist")
    ] = True,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    include_shell_scripts: Annotated[bool, typer.Option("--include-shell-scripts")] = True,
    deploy_provider: Annotated[DocsDeployProvider, typer.Option("--deploy-provider")] = (
        DocsDeployProvider.GITHUB_PAGES
    ),
    gate_confirmed: Annotated[bool, typer.Option("--gate-confirmed")] = False,
    shell_targets: Annotated[list[ShellScriptType] | None, typer.Option("--shell-target")] = None,
) -> None:
    """Run consolidated onboarding workflows."""
    _emit(
        asyncio.run(
            onboard_project(
                project_root=str(project_root),
                project_name=project_name,
                output_file=str(output_file) if output_file is not None else None,
                mode=mode,
                include_checklist=include_checklist,
                overwrite=overwrite,
                include_shell_scripts=include_shell_scripts,
                deploy_provider=deploy_provider,
                gate_confirmed=gate_confirmed,
                shell_targets=shell_targets,
            )
        )
    )


@generate_app.command("reference")
def generate_reference_docs_command(  # noqa: PLR0913
    kind: Annotated[GenerateReferenceDocsKind, typer.Option("--kind")] = (
        GenerateReferenceDocsKind.MCP_TOOLS
    ),
    cli_command: Annotated[str | None, typer.Option("--cli-command")] = None,
    target: Annotated[Path | None, typer.Option("--target")] = None,
    output_file: Annotated[Path | None, typer.Option("--output-file")] = None,
    timeout_seconds: Annotated[int, typer.Option("--timeout-seconds", min=1)] = 10,
    topic: Annotated[str | None, typer.Option("--topic")] = None,
    source_host: Annotated[SourceCodeHost | None, typer.Option("--source-host")] = None,
    repository_url: Annotated[str | None, typer.Option("--repository-url")] = None,
    source_file: Annotated[str | None, typer.Option("--source-file")] = None,
    line_start: Annotated[int | None, typer.Option("--line-start", min=1)] = None,
    line_end: Annotated[int | None, typer.Option("--line-end", min=1)] = None,
    asset_kind: Annotated[VisualAssetKind | None, typer.Option("--asset-kind")] = None,
    asset_prompt: Annotated[str | None, typer.Option("--asset-prompt")] = None,
    style_notes: Annotated[str | None, typer.Option("--style-notes")] = None,
    target_size_hint: Annotated[str | None, typer.Option("--target-size-hint")] = None,
    source_svg: Annotated[str | None, typer.Option("--source-svg")] = None,
) -> None:
    """Generate consolidated reference documentation artifacts."""
    _emit(
        generate_reference_docs(
            kind=kind,
            cli_command=cli_command,
            target=str(target) if target is not None else None,
            output_file=str(output_file) if output_file is not None else None,
            timeout_seconds=timeout_seconds,
            topic=topic,
            source_host=source_host,
            repository_url=repository_url,
            source_file=source_file,
            line_start=line_start,
            line_end=line_end,
            asset_kind=asset_kind,
            asset_prompt=asset_prompt,
            style_notes=style_notes,
            target_size_hint=target_size_hint,
            source_svg=source_svg,
        )
    )


@copilot_app.command("artifact")
def create_artifact_command(  # noqa: PLR0913
    kind: Annotated[
        CopilotArtifactKind,
        typer.Argument(help="Artifact kind: instruction, prompt, or agent."),
    ],
    file_stem: Annotated[str, typer.Argument(help="Stem name for the output file.")],
    content: Annotated[str, typer.Argument(help="Markdown body content.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    description: Annotated[str | None, typer.Option("--description")] = None,
    apply_to: Annotated[str, typer.Option("--apply-to")] = "**",
    agent: Annotated[CopilotAgentMode, typer.Option("--agent")] = CopilotAgentMode.AGENT,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    *,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Create a Copilot artifact (.instructions.md, .prompt.md, or .agent.md)."""
    _emit(
        create_copilot_artifact(
            kind=kind,
            file_stem=file_stem,
            content=content,
            title=title,
            description=description,
            apply_to=apply_to,
            agent=agent,
            project_root=str(project_root),
            overwrite=overwrite,
        )
    )


@copilot_app.command("config")
def generate_agent_config_command(
    platform: Annotated[AgentPlatform, typer.Option("--platform")] = AgentPlatform.COPILOT,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    *,
    include_tools: Annotated[bool, typer.Option("--include-tools/--no-tools")] = True,
) -> None:
    """Generate AI agent configuration for docs workflow integration."""
    _emit(
        generate_agent_config(
            platform=platform,
            project_root=str(project_root),
            include_tools=include_tools,
        )
    )


@onboard_app.command("phase")
def run_pipeline_phase_command(
    phase: Annotated[PipelinePhase, typer.Option("--phase")] = PipelinePhase.CONSTITUTION,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    artifacts_dir: Annotated[str, typer.Option("--artifacts-dir")] = ".zen-of-docs",
    *,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Execute a docs pipeline phase (constitution → specify → plan → tasks → implement)."""
    _emit(
        run_pipeline_phase(
            phase=phase,
            project_root=str(project_root),
            artifacts_dir=artifacts_dir,
            force=force,
        )
    )


@validate_app.command("frontmatter")
def audit_frontmatter_command(
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    required_keys: Annotated[list[str] | None, typer.Option("--required-key")] = None,
    *,
    fix: Annotated[bool, typer.Option("--fix")] = False,
) -> None:
    """Bulk-audit frontmatter across a docs directory; optionally fix missing keys."""
    _emit(audit_frontmatter(docs_root=str(docs_root), required_keys=required_keys, fix=fix))


@validate_app.command("nav")
def sync_nav_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    framework: Annotated[str | None, typer.Option("--framework")] = None,
    mode: Annotated[SyncNavMode, typer.Option("--mode")] = SyncNavMode.AUDIT,
) -> None:
    """Audit, generate, or repair docs navigation config."""
    _emit(sync_nav(project_root=str(project_root), framework=framework, mode=mode))


@generate_app.command("visual")
def generate_visual_asset_command(  # noqa: PLR0913
    kind: Annotated[VisualAssetKind, typer.Option("--kind")] = VisualAssetKind.HEADER,
    operation: Annotated[
        VisualAssetOperation, typer.Option("--operation")
    ] = VisualAssetOperation.RENDER,
    title: Annotated[str | None, typer.Option("--title")] = None,
    subtitle: Annotated[str | None, typer.Option("--subtitle")] = None,
    primary_color: Annotated[str, typer.Option("--primary-color")] = "#5C6BC0",
    background_color: Annotated[str, typer.Option("--background-color")] = "#F8F9FA",
    output_path: Annotated[Path | None, typer.Option("--output-path")] = None,
    asset_prompt: Annotated[str | None, typer.Option("--asset-prompt")] = None,
    style_notes: Annotated[str | None, typer.Option("--style-notes")] = None,
    target_size_hint: Annotated[str | None, typer.Option("--target-size-hint")] = None,
    source_svg: Annotated[str | None, typer.Option("--source-svg")] = None,
    source_file: Annotated[str | None, typer.Option("--source-file")] = None,
) -> None:
    """Generate parametric SVG markup or perform a visual asset operation."""
    _emit(
        generate_visual_asset(
            kind=kind,
            operation=operation,
            title=title,
            subtitle=subtitle,
            primary_color=primary_color,
            background_color=background_color,
            output_path=str(output_path) if output_path else None,
            asset_prompt=asset_prompt,
            style_notes=style_notes,
            target_size_hint=target_size_hint,
            source_svg=source_svg,
            source_file=str(source_file) if source_file else None,
        )
    )


@generate_app.command("diagram")
def generate_diagram_command(
    description: Annotated[str, typer.Option("--description")] = "System overview",
    diagram_type: Annotated[DiagramType, typer.Option("--diagram-type")] = DiagramType.FLOWCHART,
    framework: Annotated[str | None, typer.Option("--framework")] = None,
    title: Annotated[str | None, typer.Option("--title")] = None,
) -> None:
    """Generate Mermaid diagram source from a template."""
    _emit(
        generate_diagram(
            description=description,
            diagram_type=diagram_type,
            framework=framework,
            title=title,
        )
    )


@generate_app.command("render")
def render_diagram_command(
    mermaid_source: Annotated[str, typer.Argument()],
    output_format: Annotated[str, typer.Option("--output-format")] = "svg",
    output_path: Annotated[Path | None, typer.Option("--output-path")] = None,
) -> None:
    """Render Mermaid source to SVG/PNG via mmdc."""
    _emit(
        render_diagram(
            mermaid_source=mermaid_source,
            output_format=output_format,
            output_path=str(output_path) if output_path else None,
        )
    )


@generate_app.command("changelog")
def generate_changelog_command(
    version: Annotated[str, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    since_tag: Annotated[str | None, typer.Option("--since-tag")] = None,
    fmt: Annotated[
        ChangelogEntryFormat, typer.Option("--format")
    ] = ChangelogEntryFormat.KEEP_A_CHANGELOG,
) -> None:
    """Parse git conventional commits and generate a structured changelog entry."""
    _emit(
        generate_changelog(
            version=version,
            project_root=str(project_root),
            since_tag=since_tag,
            fmt=fmt,
        )
    )


@onboard_app.command("install")
def run_ephemeral_install_tool_command(  # noqa: PLR0913
    installer: Annotated[str, typer.Argument(help="Installer: 'uvx' or 'npx'")],
    package: Annotated[str, typer.Argument(help="Package to install/run")],
    command: Annotated[str, typer.Argument(help="Command to run (for uvx)")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    args: Annotated[str | None, typer.Option("--args")] = None,
    source_subdir: Annotated[str | None, typer.Option("--source-subdir")] = None,
    stdin_input: Annotated[str | None, typer.Option("--stdin-input")] = None,
) -> None:
    """Run a package installer (uvx/npx) in a temp dir and copy artifacts to project root."""
    req = EphemeralInstallRequest(
        installer=installer,
        package=package,
        command=command,
        project_root=project_root,
        args=args.split() if args else [],
        source_subdir=source_subdir,
        stdin_input=stdin_input,
    )
    _emit(run_ephemeral_install(req))


@onboard_app.command("init")
def init_framework_structure_command(
    framework: Annotated[
        FrameworkName, typer.Argument(help="Documentation framework to initialise")
    ],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
) -> None:
    """Initialise a framework's canonical folder structure using its native CLI init command."""
    _emit(init_framework_structure(framework=framework, project_root=str(project_root)))


def main(args: Sequence[str] | None = None) -> int:
    """Run the Typer CLI app."""
    try:
        app(
            prog_name="mcp-zen-of-docs",
            args=list(args) if args is not None else None,
            standalone_mode=False,
        )
    except NoArgsIsHelpError:
        return 0
    return 0


@scaffold_app.command("write")
def write_doc_command(  # noqa: PLR0913
    topic: Annotated[str, typer.Option("--topic")],
    output_path: Annotated[Path, typer.Option("--output-path")],
    *,
    framework: Annotated[FrameworkName, typer.Option("--framework")] = FrameworkName.ZENSICAL,
    audience: Annotated[str | None, typer.Option("--audience")] = None,
    content_hints: Annotated[str | None, typer.Option("--content-hints")] = None,
    sections: Annotated[list[str] | None, typer.Option("--section")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Write a complete, ready-to-publish documentation page for a given topic."""
    _emit(
        write_doc(
            WriteDocRequest(
                topic=topic,
                framework=framework,
                output_path=output_path,
                audience=audience,
                content_hints=content_hints,
                sections=sections or [],
                overwrite=overwrite,
            )
        )
    )


@generate_app.command("svg")
def create_svg_asset_command(  # noqa: PLR0913
    output_path: Annotated[Path, typer.Option("--output-path")],
    *,
    svg_markup: Annotated[str | None, typer.Option("--svg-markup")] = None,
    svg_file: Annotated[Path | None, typer.Option("--svg-file")] = None,
    asset_kind: Annotated[VisualAssetKind, typer.Option("--asset-kind")] = VisualAssetKind.ICONS,
    convert_to_png: Annotated[bool, typer.Option("--convert-to-png/--no-convert-to-png")] = False,
    png_output_path: Annotated[Path | None, typer.Option("--png-output-path")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Persist arbitrary SVG markup to a file and optionally convert to PNG."""
    if svg_file is not None:
        markup = svg_file.read_text(encoding="utf-8")
    elif svg_markup is not None:
        markup = svg_markup
    else:
        typer.echo("Error: provide --svg-markup or --svg-file", err=True)
        raise typer.Exit(1)
    from .models import CreateSvgAssetRequest  # noqa: PLC0415

    _emit(
        create_svg_asset(
            CreateSvgAssetRequest(
                svg_markup=markup,
                output_path=output_path,
                asset_kind=asset_kind,
                convert_to_png=convert_to_png,
                png_output_path=png_output_path,
                overwrite=overwrite,
            )
        )
    )


@docstring_app.command("audit")
def audit_docstrings_command(
    path: Annotated[Path, typer.Argument(help="Source file or directory to audit")],
    *,
    language: Annotated[DocstringLanguage | None, typer.Option("--language")] = None,
    include_private: Annotated[
        bool, typer.Option("--include-private/--no-include-private")
    ] = False,
) -> None:
    """Scan source files for undocumented public symbols and report coverage."""
    _emit(
        audit_docstrings(
            DocstringAuditRequest(
                source_path=path,
                language=language,
                include_private=include_private,
            )
        )
    )


@docstring_app.command("optimize")
def optimize_docstrings_command(
    path: Annotated[Path, typer.Argument(help="Source file to add docstring stubs to")],
    *,
    language: Annotated[DocstringLanguage | None, typer.Option("--language")] = None,
    style: Annotated[DocstringStyle | None, typer.Option("--style")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
    include_private: Annotated[
        bool, typer.Option("--include-private/--no-include-private")
    ] = False,
) -> None:
    """Insert canonical docstring stubs for undocumented public symbols."""
    _emit(
        optimize_docstrings(
            DocstringOptimizerRequest(
                source_path=path,
                language=language,
                style=style,
                overwrite=overwrite,
                include_private=include_private,
            )
        )
    )


@theme_app.command("css")
def generate_custom_theme_command(  # noqa: PLR0913
    framework: Annotated[FrameworkName, typer.Argument(help="Target docs framework")],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    *,
    theme_name: Annotated[str, typer.Option("--theme-name")] = "custom",
    primary_color: Annotated[str, typer.Option("--primary-color")] = "#1de9b6",
    accent_color: Annotated[str, typer.Option("--accent-color")] = "#7c4dff",
    target: Annotated[CustomThemeTarget, typer.Option("--target")] = CustomThemeTarget.CSS_AND_JS,
    dark_mode: Annotated[bool, typer.Option("--dark-mode/--no-dark-mode")] = True,
    font_body: Annotated[str | None, typer.Option("--font-body")] = None,
    font_code: Annotated[str | None, typer.Option("--font-code")] = None,
) -> None:
    """Generate framework-specific CSS/JS theme files with brand colors."""
    from .generators import generate_custom_theme_impl  # noqa: PLC0415
    from .models import GenerateCustomThemeRequest  # noqa: PLC0415

    _emit(
        generate_custom_theme_impl(
            GenerateCustomThemeRequest(
                framework=framework,
                output_dir=output_dir,
                theme_name=theme_name,
                primary_color=primary_color,
                accent_color=accent_color,
                target=target,
                dark_mode=dark_mode,
                font_body=font_body,
                font_code=font_code,
            )
        )
    )


@theme_app.command("extensions")
def configure_zensical_extensions_command(
    extensions: Annotated[
        list[ZensicalExtension],
        typer.Argument(help="Extension names to configure (e.g. pymdownx.arithmatex)"),
    ],
    *,
    output_format: Annotated[str, typer.Option("--output-format")] = "toml",
    include_examples: Annotated[
        bool, typer.Option("--include-examples/--no-include-examples")
    ] = True,
) -> None:
    """Generate zensical.toml / mkdocs.yml config blocks for pymdownx extensions."""
    from typing import Literal  # noqa: PLC0415

    from .generators import configure_zensical_extensions_impl  # noqa: PLC0415
    from .models import ConfigureZensicalExtensionsRequest  # noqa: PLC0415

    fmt: Literal["toml", "yaml", "both"] = (
        "toml" if output_format == "toml" else ("yaml" if output_format == "yaml" else "both")
    )
    _emit(
        configure_zensical_extensions_impl(
            ConfigureZensicalExtensionsRequest(
                extensions=extensions,
                output_format=fmt,
                include_authoring_examples=include_examples,
            )
        )
    )


__all__ = ["app", "main"]

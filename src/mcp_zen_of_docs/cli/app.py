"""Typer CLI for the consolidated mcp-zen-of-docs tool surface."""

from __future__ import annotations

import asyncio
import json
import re
import sys

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Literal
from typing import NoReturn
from typing import cast

import typer

from click import Context as ClickContext
from click import get_current_context
from click.exceptions import ClickException
from click.exceptions import NoArgsIsHelpError
from click.exceptions import NoSuchOption
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.generator import get_story_generator_boundary
from mcp_zen_of_docs.generators import run_ephemeral_install
from mcp_zen_of_docs.interfaces.story import InterfaceChannel
from mcp_zen_of_docs.interfaces.story import adapt_story_response_channel
from mcp_zen_of_docs.interfaces.story import build_story_loop_advance_surface
from mcp_zen_of_docs.interfaces.story import build_story_loop_initialize_surface
from mcp_zen_of_docs.interfaces.story import build_story_request
from mcp_zen_of_docs.interfaces.story import build_story_session_advance_request
from mcp_zen_of_docs.interfaces.story import build_story_session_initialize_request
from mcp_zen_of_docs.models import AgentPlatform
from mcp_zen_of_docs.models import AnswerSlotContract
from mcp_zen_of_docs.models import AnswerSlotType
from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import ChangelogEntryFormat
from mcp_zen_of_docs.models import ComposeDocsStoryResponse
from mcp_zen_of_docs.models import CopilotAgentMode
from mcp_zen_of_docs.models import CopilotArtifactKind
from mcp_zen_of_docs.models import CustomThemeTarget
from mcp_zen_of_docs.models import DiagramType
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import DocsValidationCheck
from mcp_zen_of_docs.models import DocstringAuditRequest
from mcp_zen_of_docs.models import DocstringLanguage
from mcp_zen_of_docs.models import DocstringOptimizerRequest
from mcp_zen_of_docs.models import DocstringStyle
from mcp_zen_of_docs.models import EphemeralInstallRequest
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GenerateReferenceDocsKind
from mcp_zen_of_docs.models import OnboardProjectMode
from mcp_zen_of_docs.models import PipelinePhase
from mcp_zen_of_docs.models import PrimitiveResolutionMode
from mcp_zen_of_docs.models import ScaffoldDocRequest
from mcp_zen_of_docs.models import ShellScriptType
from mcp_zen_of_docs.models import SourceCodeHost
from mcp_zen_of_docs.models import StoryGenerationRequest
from mcp_zen_of_docs.models import StoryGenerationResponse
from mcp_zen_of_docs.models import StoryMigrationMode
from mcp_zen_of_docs.models import SyncNavMode
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import VisualAssetOperation
from mcp_zen_of_docs.models import WriteDocRequest
from mcp_zen_of_docs.models import ZensicalExtension
from mcp_zen_of_docs.server.app import audit_docstrings
from mcp_zen_of_docs.server.app import audit_frontmatter
from mcp_zen_of_docs.server.app import batch_scaffold_docs
from mcp_zen_of_docs.server.app import compose_docs_story
from mcp_zen_of_docs.server.app import create_copilot_artifact
from mcp_zen_of_docs.server.app import create_svg_asset
from mcp_zen_of_docs.server.app import detect_docs_context
from mcp_zen_of_docs.server.app import detect_project_readiness
from mcp_zen_of_docs.server.app import enrich_doc
from mcp_zen_of_docs.server.app import generate_agent_config
from mcp_zen_of_docs.server.app import generate_changelog
from mcp_zen_of_docs.server.app import generate_diagram
from mcp_zen_of_docs.server.app import generate_reference_docs
from mcp_zen_of_docs.server.app import generate_visual_asset
from mcp_zen_of_docs.server.app import get_authoring_profile
from mcp_zen_of_docs.server.app import init_framework_structure
from mcp_zen_of_docs.server.app import onboard_project
from mcp_zen_of_docs.server.app import optimize_docstrings
from mcp_zen_of_docs.server.app import plan_docs
from mcp_zen_of_docs.server.app import render_diagram
from mcp_zen_of_docs.server.app import resolve_primitive
from mcp_zen_of_docs.server.app import run_pipeline_phase
from mcp_zen_of_docs.server.app import scaffold_doc
from mcp_zen_of_docs.server.app import score_docs_quality
from mcp_zen_of_docs.server.app import sync_nav
from mcp_zen_of_docs.server.app import translate_primitives
from mcp_zen_of_docs.server.app import validate_docs
from mcp_zen_of_docs.server.app import write_doc
from mcp_zen_of_docs.cli.presenters import format_human_payload


if TYPE_CHECKING:
    from collections.abc import Sequence

app = typer.Typer(
    add_completion=True,
    help="Human-first CLI for mcp-zen-of-docs documentation workflows.",
    epilog=(
        "Use --json for raw automation contracts. "
        "Legacy command names remain available as hidden compatibility aliases."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)

detect_app = typer.Typer(name="detect", help="Detect docs context and project readiness")
profile_app = typer.Typer(name="profile", help="Framework authoring profiles and primitives")
scaffold_app = typer.Typer(name="scaffold", help="Create and write documentation pages")
validate_app = typer.Typer(
    name="validate",
    help=(
        "Audit docs quality. Running `validate` without a subcommand performs the standard checks."
    ),
)
generate_app = typer.Typer(name="generate", help="Generate visuals, diagrams, and references")
setup_app = typer.Typer(
    name="setup",
    help=(
        "Bootstrap docs work for a project. Running `setup` prints a setup "
        "guide; use `setup init` for framework-native structure."
    ),
)
syntax_app = typer.Typer(
    name="syntax",
    help="Check a framework primitive or convert syntax between frameworks.",
)
page_app = typer.Typer(
    name="page",
    help=(
        "Create docs pages. Use `page new` for a scaffold, `page fill` to "
        "enrich, or `page write` for a full draft."
    ),
)
diagram_app = typer.Typer(
    name="diagram",
    help="Create Mermaid from plain English or render Mermaid to SVG/PNG.",
)
asset_app = typer.Typer(
    name="asset",
    help="Generate badges, headers, and icons, or write raw SVG assets.",
)
integrations_app = typer.Typer(
    name="integrations",
    help="Generate AI/editor integration templates such as Copilot instructions and config files.",
)
code_doc_app = typer.Typer(
    name="code-doc",
    help="Audit docstring coverage or generate docstring stubs.",
)
onboard_app = typer.Typer(
    name="onboard",
    help="Bootstrap docs setup artifacts, starter pages, and contributor guidance.",
)
theme_app = typer.Typer(name="theme", help="CSS/JS theme customization")
copilot_app = typer.Typer(name="copilot", help="VS Code Copilot integration")
docstring_app = typer.Typer(name="docstring", help="Source code docstring tools")

app.add_typer(detect_app, name="detect", hidden=True)
app.add_typer(profile_app, name="profile", hidden=True)
app.add_typer(scaffold_app, name="scaffold", hidden=True)
app.add_typer(validate_app, name="validate")
app.add_typer(generate_app, name="generate", hidden=True)
app.add_typer(onboard_app, name="onboard", hidden=True)
app.add_typer(setup_app, name="setup")
app.add_typer(syntax_app, name="syntax")
app.add_typer(page_app, name="page")
app.add_typer(diagram_app, name="diagram")
app.add_typer(asset_app, name="asset")
app.add_typer(integrations_app, name="integrations")
app.add_typer(code_doc_app, name="code-doc")
app.add_typer(theme_app, name="theme", hidden=True)
app.add_typer(copilot_app, name="copilot", hidden=True)
app.add_typer(docstring_app, name="docstring", hidden=True)

OutputMode = Literal["auto", "human", "json"]
type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
BLOCK_TEXT_THRESHOLD = 120
COMMAND_FAMILY_SUBCOMMANDS: dict[str, set[str]] = {
    "page": {"new", "batch-new", "fill", "write"},
    "syntax": {"check", "convert"},
    "diagram": {"create", "render"},
    "asset": {"create", "write-svg"},
    "integrations": {"init", "artifact"},
    "code-doc": {"coverage", "stubs"},
}


class CliState(BaseModel):
    """Mutable CLI runtime state for a single process invocation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    output_mode: OutputMode = "auto"


FALLBACK_CLI_STATE = CliState()


class CliErrorResponse(BaseModel):
    """Typed CLI error response contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    status: str = Field(default="error", description="CLI command status.")
    message: str = Field(description="Error detail message.")


class StatusCommandResponse(BaseModel):
    """Human-facing project status summary for the CLI taxonomy layer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    status: str = Field(description="CLI command status.")
    tool: str = Field(default="status", description="CLI wrapper identifier.")
    project_root: Path = Field(description="Project root path inspected.")
    framework: FrameworkName | None = Field(
        default=None,
        description="Detected documentation framework when available.",
    )
    initialized: bool = Field(description="Whether docs initialization artifacts are present.")
    readiness_level: str | None = Field(
        default=None,
        description="Summary readiness level for the docs workflow.",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Suggested next CLI actions for a human operator.",
    )
    message: str | None = Field(default=None, description="Error or warning detail when present.")


@app.callback()
def configure_output_mode(
    ctx: typer.Context,
    *,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit JSON output for scripts and automation.",
        ),
    ] = False,
    human_output: Annotated[
        bool,
        typer.Option(
            "--human",
            help="Emit human-readable output even when stdout is not a TTY.",
        ),
    ] = False,
) -> None:
    """Configure CLI output rendering."""
    if json_output and human_output:
        msg = "Choose either --json or --human, not both."
        raise typer.BadParameter(msg)

    state = _get_cli_state(ctx)
    if json_output:
        state.output_mode = "json"
    elif human_output:
        state.output_mode = "human"
    else:
        state.output_mode = "auto"


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


def _humanize_label(value: str) -> str:
    """Convert internal identifiers into human-readable labels."""
    return value.replace("-", " ").replace("_", " ").strip().capitalize()


def _get_cli_state(ctx: ClickContext | None = None) -> CliState:
    """Return the per-invocation CLI state stored on the active Click context."""
    active_ctx = ctx or get_current_context(silent=True)
    if active_ctx is None:
        return FALLBACK_CLI_STATE
    if isinstance(active_ctx.obj, CliState):
        return active_ctx.obj
    state = FALLBACK_CLI_STATE.model_copy()
    active_ctx.obj = state
    return state


def _format_scalar(value: JsonScalar) -> str:
    """Return a human-readable scalar string."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _looks_like_block_text(key: str, value: str) -> bool:
    """Return True when a field should be rendered as an indented text block."""
    return (
        "\n" in value
        or len(value) > BLOCK_TEXT_THRESHOLD
        or key
        in {
            "markdown",
            "mermaid_source",
            "svg_content",
            "svg_markup",
            "narrative",
            "content",
        }
    )


def _render_block(label: str, value: str, *, indent: int = 0) -> list[str]:
    """Render multiline text as an indented block."""
    prefix = " " * indent
    lines = [f"{prefix}{label}:"]
    lines.extend(f"{prefix}  {line}" for line in value.splitlines())
    return lines


def _format_confidence(value: JsonValue) -> str | None:
    """Format model confidence values for human-readable output."""
    if isinstance(value, (int, float)):
        return f"{value:.0%}" if 0 <= value <= 1 else str(value)
    if isinstance(value, str):
        return value
    return None


def _render_bullets(
    label: str, items: list[JsonValue], *, indent: int = 0, limit: int | None = None
) -> list[str]:
    """Render a list of values as nested bullets."""
    prefix = " " * indent
    lines = [f"{prefix}{label}"]
    displayed = items if limit is None else items[:limit]
    for item in displayed:
        if isinstance(item, (str, int, float, bool)) or item is None:
            lines.append(f"{prefix}  - {_format_scalar(item)}")
            continue
        if isinstance(item, dict):
            summary = _summarize_mapping(item)
            if summary is not None:
                lines.append(f"{prefix}  - {summary}")
                continue
            nested = _render_mapping(None, item, indent=indent + 4)
            if nested:
                first, *rest = nested
                lines.append(f"{prefix}  - {first.strip()}")
                lines.extend(rest)
            continue
        if isinstance(item, list):
            lines.append(f"{prefix}  -")
            lines.extend(f"{prefix}    - {_format_scalar(nested_item)}" for nested_item in item)
    if limit is not None and len(items) > limit:
        lines.append(f"{prefix}  - …and {len(items) - limit} more")
    return lines


def _summarize_mapping(value: dict[str, JsonValue]) -> str | None:
    """Return a compact one-line summary for well-known mapping shapes."""
    runtime = value.get("runtime")
    if isinstance(runtime, str):
        parts = [runtime]
        notes = value.get("notes")
        if isinstance(notes, list) and notes and isinstance(notes[0], str):
            parts.append(notes[0])
        return " — ".join(parts)

    framework = value.get("framework")
    confidence = _format_confidence(value.get("confidence"))
    support_level = value.get("support_level")
    if isinstance(framework, str) and confidence is not None:
        summary = f"{framework} ({confidence} confidence)"
        if isinstance(support_level, str):
            summary += f", {support_level} support"
        return summary

    file_path = value.get("file_path")
    if isinstance(file_path, str):
        return file_path
    return None


def _render_mapping(
    label: str | None, value: dict[str, JsonValue], *, indent: int = 0
) -> list[str]:
    """Render a mapping using prose-first CLI formatting."""
    if label == "Framework match" or "best_match" in value:
        return _render_framework_detection(value, indent=indent)
    if label == "Runtime guidance":
        return _render_runtime_onboarding(value, indent=indent)

    prefix = " " * indent
    lines: list[str] = []
    if label is not None:
        lines.append(f"{prefix}{label}")
    for key, item in value.items():
        rendered = _render_value(_humanize_label(key), item, indent=indent + (2 if label else 0))
        lines.extend(rendered)
    return lines


def _render_framework_detection(value: dict[str, JsonValue], *, indent: int = 0) -> list[str]:
    """Render framework detection results as a concise summary."""
    prefix = " " * indent
    lines: list[str] = [f"{prefix}Framework match"]
    best_match = value.get("best_match")
    if not isinstance(best_match, dict):
        return lines

    framework = best_match.get("framework")
    confidence = _format_confidence(best_match.get("confidence"))
    support_level = best_match.get("support_level")
    if isinstance(framework, str):
        lines.append(f"{prefix}  Framework: {framework}")
    if confidence is not None:
        lines.append(f"{prefix}  Confidence: {confidence}")
    if isinstance(support_level, str):
        lines.append(f"{prefix}  Support level: {support_level}")

    matched_signals = best_match.get("matched_signals")
    if isinstance(matched_signals, list) and matched_signals:
        signal_text = ", ".join(str(signal) for signal in matched_signals)
        lines.append(f"{prefix}  Matched signals: {signal_text}")

    candidates = value.get("candidates")
    if isinstance(candidates, list):
        candidate_items = cast("list[JsonValue]", candidates)
        alternatives = [
            candidate
            for candidate in candidate_items
            if isinstance(candidate, dict) and candidate.get("framework") != framework
        ]
        if alternatives:
            lines.extend(
                _render_bullets(
                    "Alternative frameworks",
                    cast("list[JsonValue]", alternatives),
                    indent=indent + 2,
                    limit=3,
                )
            )
    return lines


def _render_runtime_onboarding(value: dict[str, JsonValue], *, indent: int = 0) -> list[str]:
    """Render runtime onboarding guidance for humans."""
    prefix = " " * indent
    lines: list[str] = [f"{prefix}Runtime guidance"]
    python_tracks = value.get("python_tracks")
    if isinstance(python_tracks, list) and python_tracks:
        lines.extend(
            _render_bullets(
                "Recommended Python runtimes",
                cast("list[JsonValue]", python_tracks),
                indent=indent + 2,
            )
        )

    js_tracks = value.get("js_tracks")
    if isinstance(js_tracks, list) and js_tracks:
        lines.extend(
            _render_bullets(
                "Recommended JS runtimes",
                cast("list[JsonValue]", js_tracks),
                indent=indent + 2,
            )
        )

    follow_up_questions = value.get("follow_up_questions")
    if isinstance(follow_up_questions, list) and follow_up_questions:
        lines.extend(
            _render_bullets(
                "Follow-up questions",
                cast("list[JsonValue]", follow_up_questions),
                indent=indent + 2,
            )
        )
    return lines


def _render_value(label: str, value: JsonValue, *, indent: int = 0) -> list[str]:
    """Render an arbitrary JSON-like value as user-facing text."""
    prefix = " " * indent
    if isinstance(value, dict):
        return _render_mapping(label, value, indent=indent)
    if isinstance(value, list):
        return _render_bullets(label, value, indent=indent)
    if isinstance(value, str) and _looks_like_block_text(label.lower().replace(" ", "_"), value):
        return _render_block(label, value, indent=indent)
    return [f"{prefix}{label}: {_format_scalar(value)}"]


def _pop_detected_framework(data: dict[str, JsonValue]) -> str | None:
    """Return the detected framework name when present in the payload."""
    framework_detection = data.get("framework_detection")
    if not isinstance(framework_detection, dict):
        return None
    best_match = framework_detection.get("best_match")
    if not isinstance(best_match, dict):
        return None
    framework = best_match.get("framework")
    return framework if isinstance(framework, str) else None


def _collect_summary_lines(data: dict[str, JsonValue]) -> list[str]:
    """Collect top-level scalar summaries for human-readable output."""
    summary_fields = (
        "project_name",
        "project_root",
        "docs_root",
        "framework",
        "kind",
        "operation",
        "mode",
        "output_path",
        "output_file",
        "canvas_width",
        "canvas_height",
        "count",
    )
    lines: list[str] = []
    for field in summary_fields:
        value = data.pop(field, None)
        if _is_empty_value(value):
            continue
        lines.extend(_render_value(_humanize_label(field), value))
    return lines


def _collect_section_lines(data: dict[str, JsonValue]) -> list[str]:
    """Collect detailed sections for remaining payload fields."""
    section_labels = {
        "framework_detection": "Framework match",
        "runtime_onboarding": "Runtime guidance",
        "pipeline_context": "Pipeline context",
    }
    lines: list[str] = []
    for field in ("framework_detection", "runtime_onboarding", "pipeline_context"):
        value = data.pop(field, None)
        if _is_empty_value(value):
            continue
        lines.extend(_render_value(section_labels[field], value))

    for key, value in data.items():
        lines.extend(_render_value(_humanize_label(key), value))
    return lines


def _status_prefix(status: str | None) -> str:
    """Return a concise status prefix for human-readable output."""
    prefixes = {
        "success": "Success",
        "warning": "Warning",
        "error": "Error",
    }
    if status is None:
        return "Result"
    return prefixes.get(status.lower(), _humanize_label(status))


def _is_empty_value(value: JsonValue) -> bool:
    """Return True when a dumped JSON value should be omitted from human output."""
    return value in (None, "", [], {})


def _strip_empty_values(value: JsonValue) -> JsonValue:
    """Recursively remove empty values from payloads before human rendering."""
    if isinstance(value, dict):
        cleaned = {
            key: _strip_empty_values(item)
            for key, item in value.items()
            if not _is_empty_value(item)
        }
        return {key: item for key, item in cleaned.items() if not _is_empty_value(item)}
    if isinstance(value, list):
        cleaned_list = [_strip_empty_values(item) for item in value]
        return [item for item in cleaned_list if not _is_empty_value(item)]
    return value


def _format_human_payload(payload: BaseModel) -> str:
    """Render a Pydantic payload as human-readable CLI output."""
    return format_human_payload(payload)


def _resolve_output_mode() -> Literal["human", "json"]:
    """Resolve the effective CLI output mode for the current invocation."""
    cli_state = _get_cli_state()
    if cli_state.output_mode == "json":
        return "json"
    if cli_state.output_mode == "human":
        return "human"
    return "human" if sys.stdout.isatty() else "json"


def _payload_exit_code(payload: BaseModel) -> int | None:
    """Return the process exit code implied by a response payload."""
    status = getattr(payload, "status", None)
    if not isinstance(status, str) or status.lower() != "error":
        return None

    exit_code = getattr(payload, "exit_code", None)
    if isinstance(exit_code, int) and exit_code != 0:
        return exit_code
    return 1


def _emit(payload: BaseModel, *, err: bool = False, exit_on_error: bool = True) -> None:
    """Emit a typed payload to the configured CLI output stream."""
    if _resolve_output_mode() == "json":
        typer.echo(
            json.dumps(payload.model_dump(mode="json"), sort_keys=True),
            err=err,
        )
    else:
        typer.echo(_format_human_payload(payload), err=err)

    if exit_on_error:
        exit_code = _payload_exit_code(payload)
        if exit_code is not None:
            raise typer.Exit(code=exit_code)


def _emit_error(message: str) -> NoReturn:
    """Emit a structured error response and exit with code 2."""
    _emit(CliErrorResponse(message=message), err=True, exit_on_error=False)
    raise typer.Exit(code=2)


def _first_command_token(args: Sequence[str]) -> str | None:
    """Return the first non-global command token from the original argv list."""
    global_flags = {"--json", "--human"}
    for token in args:
        if token in global_flags:
            continue
        if token.startswith("-"):
            return None
        return token
    return None


def _format_click_exception(args: Sequence[str], exc: ClickException) -> str:
    """Convert Click/Typer parse exceptions into human-oriented CLI guidance."""
    if isinstance(exc, NoSuchOption):
        command = _first_command_token(args)
        option_name = exc.option_name.lstrip("-")
        if (
            command is not None
            and command in COMMAND_FAMILY_SUBCOMMANDS
            and option_name in COMMAND_FAMILY_SUBCOMMANDS[command]
        ):
            return (
                f"Use `mcp-zen-of-docs {command} {option_name}` instead of "
                f"`mcp-zen-of-docs {command} --{option_name}`."
            )
    return exc.format_message()


def _merge_statuses(*statuses: str | None) -> str:
    """Return one consolidated status from multiple payload status strings."""
    normalized = {status.lower() for status in statuses if isinstance(status, str)}
    if "error" in normalized:
        return "error"
    if "warning" in normalized:
        return "warning"
    return "success"


def _run_validate_all(  # noqa: PLR0913
    *,
    docs_root: Path,
    mkdocs_file: Path | None,
    external_mode: str,
    required_headers: list[str] | None,
    required_frontmatter: list[str] | None,
    checks: list[DocsValidationCheck] | None,
) -> None:
    """Execute the consolidated validate-all flow shared by visible and legacy surfaces."""
    _emit(
        validate_docs(
            docs_root=str(docs_root),
            mkdocs_file=str(mkdocs_file) if mkdocs_file is not None else None,
            external_mode=external_mode,
            required_headers=required_headers,
            required_frontmatter=required_frontmatter,
            checks=checks,
        )
    )


def _run_setup_full(  # noqa: PLR0913
    *,
    project_name: str,
    project_root: Path,
    output_file: Path | None,
    mode: OnboardProjectMode,
    include_checklist: bool,
    overwrite: bool,
    include_shell_scripts: bool,
    deploy_provider: DocsDeployProvider,
    gate_confirmed: bool,
    shell_targets: list[ShellScriptType] | None,
) -> None:
    """Execute the consolidated setup/bootstrap flow shared by new and legacy surfaces."""
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


def _build_status_response(project_root: Path) -> StatusCommandResponse:
    """Combine detect/readiness payloads into one human-facing project status summary."""
    context_payload = detect_docs_context(project_root=str(project_root))
    readiness_payload = detect_project_readiness(project_root=str(project_root))
    best_match = context_payload.framework_detection.best_match
    framework = best_match.framework if best_match is not None else None
    readiness_level = {
        "none": "Not initialized",
        "partial": "Partially ready",
        "full": "Ready",
    }.get(str(readiness_payload.readiness_level), str(readiness_payload.readiness_level))
    next_steps = (
        [
            "Run `mcp-zen-of-docs setup --mode skeleton` for a safe first-run guide.",
            "Run `mcp-zen-of-docs setup` to bootstrap docs artifacts.",
        ]
        if not readiness_payload.initialized
        else [
            "Run `mcp-zen-of-docs validate` to audit docs quality.",
            "Use `mcp-zen-of-docs page write` to draft a new page.",
        ]
    )
    message = next(
        (
            detail
            for detail in (context_payload.message, readiness_payload.message)
            if detail is not None
        ),
        None,
    )
    return StatusCommandResponse(
        status=_merge_statuses(context_payload.status, readiness_payload.status),
        project_root=project_root,
        framework=framework,
        initialized=readiness_payload.initialized,
        readiness_level=readiness_level,
        next_steps=next_steps,
        message=message,
    )


def _parse_context(
    context_json: str | None,
    context_items: Sequence[str] | None = None,
) -> dict[str, str]:
    """Parse JSON and key=value context inputs into one flat string-keyed dict."""
    parsed_items: dict[str, str] = {}
    for item in context_items or []:
        if "=" not in item:
            _emit_error("context values must use key=value format.")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            _emit_error("context values must use a non-empty key=value format.")
        parsed_items[key] = value

    if context_json is None:
        return parsed_items
    try:
        parsed = json.loads(context_json)
    except json.JSONDecodeError as exc:
        _emit_error(f"context-json must be valid JSON: {exc.msg}.")
    if not isinstance(parsed, dict):
        _emit_error("context-json must decode to an object.")
    parsed_json = {str(key): str(value) for key, value in parsed.items()}
    return {**parsed_json, **parsed_items}


_STORY_SLOT_CONTEXT_KEY_ALIASES = {
    "slot-target-audience": "audience",
    "slot-audience": "audience",
    "slot-goal": "goal",
    "slot-functional-goal": "goal",
    "slot-scope": "scope",
    "slot-constraints": "constraints",
    "slot-story-motivation": "motivation",
    "slot-story-api": "api_story",
    "slot-story-implementation": "implementation_story",
    "slot-story-constraints": "constraints",
    "slot-story-verification": "verification",
}


def _compose_story_payload(response: StoryGenerationResponse) -> ComposeDocsStoryResponse:
    """Wrap a story response in the CLI-facing payload contract."""
    adapted_story = adapt_story_response_channel(response, channel=InterfaceChannel.CLI)
    return ComposeDocsStoryResponse(
        status=adapted_story.status,
        story=adapted_story,
        message=adapted_story.message,
    )


def _story_human_interactive_mode_enabled() -> bool:
    """Return True when the story command can safely collect interactive answers."""
    return _resolve_output_mode() == "human" and sys.stdin.isatty() and sys.stdout.isatty()


def _resolved_story_context(answer_slots: Sequence[AnswerSlotContract]) -> dict[str, str]:
    """Project resolved answer slots into canonical story context keys."""
    context: dict[str, str] = {}
    for slot in answer_slots:
        value = slot.value
        if value in (None, "", []):
            continue
        key = _STORY_SLOT_CONTEXT_KEY_ALIASES.get(slot.slot_id)
        if key is None:
            key = slot.slot_id.removeprefix("slot-").replace("-", "_") or slot.slot_id
        if isinstance(value, bool):
            context[key] = str(value).lower()
        elif isinstance(value, list):
            cleaned = [item.strip() for item in value if item.strip()]
            if cleaned:
                context[key] = ", ".join(cleaned)
        elif isinstance(value, str):
            normalized = value.strip()
            if normalized:
                context[key] = normalized
    return context


def _story_request_with_answers(
    base_request: StoryGenerationRequest,
    answer_slots: Sequence[AnswerSlotContract],
) -> StoryGenerationRequest:
    """Merge resolved interactive answers back into a story request."""
    resolved_context = _resolved_story_context(answer_slots)
    merged_context = {**base_request.context, **resolved_context}
    audience = (
        base_request.audience or resolved_context.get("audience") or merged_context.get("audience")
    )
    return build_story_request(
        prompt=base_request.prompt,
        audience=audience,
        modules=base_request.modules,
        context=merged_context,
        include_onboarding_guidance=base_request.include_onboarding_guidance,
        answer_slots=answer_slots,
    )


def _prompt_story_answer(question: str, slot: AnswerSlotContract) -> str | bool | list[str]:
    """Collect one interactive answer using the slot contract as the prompt schema."""
    if slot.slot_type == AnswerSlotType.BOOLEAN:
        default = slot.value if isinstance(slot.value, bool) else False
        return typer.confirm(question, default=default)
    if slot.slot_type == AnswerSlotType.SINGLE_CHOICE:
        choices = ", ".join(slot.choices)
        default = slot.value if isinstance(slot.value, str) and slot.value in slot.choices else None
        while True:
            value = typer.prompt(f"{question} [{choices}]", default=default).strip()
            if value in slot.choices:
                return value
            typer.echo(f"Choose one of: {choices}", err=True)
    if slot.slot_type == AnswerSlotType.MULTI_CHOICE:
        choices = ", ".join(slot.choices)
        default = (
            ", ".join(slot.value)
            if isinstance(slot.value, list) and all(isinstance(item, str) for item in slot.value)
            else None
        )
        while True:
            raw = typer.prompt(
                f"{question} [{choices}] (comma-separated)",
                default=default,
            ).strip()
            selected = [item.strip() for item in raw.split(",") if item.strip()]
            if all(item in slot.choices for item in selected):
                return selected
            typer.echo(f"Choose only from: {choices}", err=True)
    default_text = slot.value if isinstance(slot.value, str) and slot.value.strip() else None
    return typer.prompt(question, default=default_text).strip()


def _collect_story_interactive_answers(
    *,
    pending_required_slot_ids: Sequence[str],
    answer_slots: Sequence[AnswerSlotContract],
    question_items: Sequence[BaseModel],
) -> list[AnswerSlotContract]:
    """Collect a deduplicated batch of interactive answers for unresolved required slots."""
    pending_slot_ids = set(pending_required_slot_ids)
    slot_by_id = {slot.slot_id: slot for slot in answer_slots}
    grouped_prompts: list[tuple[str, list[AnswerSlotContract]]] = []
    prompt_index: dict[str, int] = {}
    covered_slot_ids: set[str] = set()

    for question in question_items:
        slot_group = [
            slot_by_id[slot_id]
            for slot_id in getattr(question, "answer_slot_ids", [])
            if slot_id in pending_slot_ids and slot_id in slot_by_id
        ]
        if not slot_group:
            continue
        prompt = getattr(question, "question", None) or slot_group[0].prompt
        if prompt in prompt_index:
            grouped_prompts[prompt_index[prompt]][1].extend(slot_group)
        else:
            prompt_index[prompt] = len(grouped_prompts)
            grouped_prompts.append((prompt, list(slot_group)))
        covered_slot_ids.update(slot.slot_id for slot in slot_group)

    for slot_id in pending_required_slot_ids:
        if slot_id in covered_slot_ids or slot_id not in slot_by_id:
            continue
        slot = slot_by_id[slot_id]
        grouped_prompts.append((slot.prompt, [slot]))

    provided_answers: list[AnswerSlotContract] = []
    for prompt, slots in grouped_prompts:
        value = _prompt_story_answer(prompt, slots[0])
        provided_answers.extend(slot.model_copy(update={"value": value}) for slot in slots)
    return provided_answers


def _run_story_human_flow(  # noqa: PLR0913
    *,
    prompt: str,
    audience: str | None,
    modules: list[str] | None,
    context: dict[str, str],
    include_onboarding_guidance: bool,
    enable_runtime_loop: bool | None,
    runtime_max_turns: int | None,
) -> ComposeDocsStoryResponse:
    """Drive the human story CLI flow through the deterministic loop surfaces."""
    boundary = get_story_generator_boundary()
    base_request = build_story_request(
        prompt=prompt,
        audience=audience,
        modules=modules,
        context=context,
        include_onboarding_guidance=include_onboarding_guidance,
    )
    initial_result = boundary.orchestrate_story(base_request)
    payload = _compose_story_payload(initial_result.response)
    if (
        payload.status != "warning"
        or enable_runtime_loop is False
        or not _story_human_interactive_mode_enabled()
    ):
        return payload

    max_turns = runtime_max_turns or 6
    surface = build_story_loop_initialize_surface(
        build_story_session_initialize_request(
            result=initial_result,
            session_id=f"cli-story-{_slugify(prompt)}",
            story_id=initial_result.response.story_id,
        ),
        channel=InterfaceChannel.CLI,
    )
    turn_count = 0

    while surface.pending_required_slot_ids and turn_count < max_turns:
        typer.echo("Need a bit more context to finish this story:")
        for question in surface.next_required_question_items:
            typer.echo(f"- {question.question}")
        typer.echo("")
        provided_answers = _collect_story_interactive_answers(
            pending_required_slot_ids=surface.pending_required_slot_ids,
            answer_slots=surface.state.answer_slots,
            question_items=surface.next_required_question_items,
        )
        surface = build_story_loop_advance_surface(
            build_story_session_advance_request(
                state=surface.state,
                provided_answers=provided_answers,
            ),
            channel=InterfaceChannel.CLI,
        )
        turn_count += 1

    refreshed_request = _story_request_with_answers(base_request, surface.state.answer_slots)
    refreshed_result = boundary.orchestrate_story(refreshed_request)
    return _compose_story_payload(refreshed_result.response)


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


@app.command("status")
def status_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
) -> None:
    """Summarize detected docs framework and readiness in one human-facing command."""
    _emit(_build_status_response(project_root))


@setup_app.callback(invoke_without_command=True)
def setup_command(  # noqa: PLR0913
    ctx: typer.Context,
    project_name: Annotated[str, typer.Option("--project-name")] = "Project",
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    output_file: Annotated[Path | None, typer.Option("--output-file")] = None,
    mode: Annotated[OnboardProjectMode, typer.Option("--mode")] = OnboardProjectMode.FULL,
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
    """Set up docs artifacts and contributor guidance for this project."""
    if ctx.invoked_subcommand is not None:
        return
    _run_setup_full(
        project_name=project_name,
        project_root=project_root,
        output_file=output_file,
        mode=mode,
        include_checklist=include_checklist,
        overwrite=overwrite,
        include_shell_scripts=include_shell_scripts,
        deploy_provider=deploy_provider,
        gate_confirmed=gate_confirmed,
        shell_targets=shell_targets,
    )


@setup_app.command("init")
def setup_init_command(
    framework: Annotated[
        FrameworkName,
        typer.Argument(help="Documentation framework to initialise."),
    ],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
) -> None:
    """Initialise a framework's native docs structure."""
    _emit(init_framework_structure(framework=framework, project_root=str(project_root)))


@setup_app.command("full", hidden=True)
def setup_full_command(  # noqa: PLR0913
    project_name: Annotated[str, typer.Option("--project-name")] = "Project",
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    output_file: Annotated[Path | None, typer.Option("--output-file")] = None,
    mode: Annotated[OnboardProjectMode, typer.Option("--mode")] = OnboardProjectMode.FULL,
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
    """Compatibility alias for the previous `setup full` surface."""
    _run_setup_full(
        project_name=project_name,
        project_root=project_root,
        output_file=output_file,
        mode=mode,
        include_checklist=include_checklist,
        overwrite=overwrite,
        include_shell_scripts=include_shell_scripts,
        deploy_provider=deploy_provider,
        gate_confirmed=gate_confirmed,
        shell_targets=shell_targets,
    )


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


@syntax_app.command("check")
def syntax_check_command(
    primitive: Annotated[AuthoringPrimitive, typer.Argument(help="Primitive to inspect.")],
    framework: Annotated[FrameworkName, typer.Option("--framework")],
    *,
    render: Annotated[bool, typer.Option("--render/--support-only")] = False,
    topic: Annotated[str | None, typer.Option("--topic")] = None,
) -> None:
    """Check whether a framework supports a docs syntax feature and optionally render it."""
    _emit(
        resolve_primitive(
            framework=framework,
            primitive=primitive,
            mode=PrimitiveResolutionMode.RENDER if render else PrimitiveResolutionMode.SUPPORT,
            topic=topic,
        )
    )


@syntax_app.command("convert")
def syntax_convert_command(
    primitive: Annotated[AuthoringPrimitive, typer.Argument(help="Primitive to translate.")],
    source_framework: Annotated[FrameworkName, typer.Option("--from", "--source-framework")],
    target_framework: Annotated[FrameworkName, typer.Option("--to", "--target-framework")],
    topic: Annotated[str | None, typer.Option("--topic")] = None,
) -> None:
    """Convert a docs syntax feature from one framework to another."""
    _emit(
        translate_primitives(
            source_framework=source_framework,
            target_framework=target_framework,
            primitive=primitive,
            topic=topic,
        )
    )


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


@app.command("story", hidden=True)
def compose_docs_story_command(  # noqa: PLR0913
    prompt: Annotated[str, typer.Option("--prompt")],
    audience: Annotated[str | None, typer.Option("--audience")] = None,
    modules: Annotated[list[str] | None, typer.Option("--module")] = None,
    context_items: Annotated[
        list[str] | None,
        typer.Option(
            "--context",
            help="Provide extra story context as key=value. Repeat as needed.",
        ),
    ] = None,
    context_json: Annotated[str | None, typer.Option("--context-json")] = None,
    *,
    interactive: Annotated[
        bool | None,
        typer.Option(
            "--interactive/--no-interactive",
            help="Prompt for missing required story context in human mode.",
        ),
    ] = None,
    include_onboarding_guidance: Annotated[
        bool, typer.Option("--include-onboarding-guidance")
    ] = False,
    enable_runtime_loop: Annotated[
        bool | None,
        typer.Option("--enable-runtime-loop", hidden=True),
    ] = None,
    runtime_max_turns: Annotated[
        int | None,
        typer.Option("--runtime-max-turns", min=1, hidden=True),
    ] = None,
    auto_advance: Annotated[
        bool | None,
        typer.Option("--auto-advance", hidden=True),
    ] = None,
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
    context = _parse_context(context_json, context_items)
    interactive_mode = interactive if interactive is not None else enable_runtime_loop
    if _resolve_output_mode() == "human" and migration_mode is None:
        result = _run_story_human_flow(
            prompt=prompt,
            audience=audience,
            modules=modules,
            context=context,
            include_onboarding_guidance=include_onboarding_guidance,
            enable_runtime_loop=interactive_mode,
            runtime_max_turns=runtime_max_turns,
        )
    else:
        result = compose_docs_story(
            prompt=prompt,
            audience=audience,
            modules=modules,
            context=context,
            include_onboarding_guidance=include_onboarding_guidance,
            enable_runtime_loop=interactive_mode,
            runtime_max_turns=runtime_max_turns,
            auto_advance=auto_advance,
            migration_mode=migration_mode,
            migration_source_framework=migration_source_framework,
            migration_target_framework=migration_target_framework,
            migration_improve_clarity=migration_improve_clarity,
            migration_strengthen_structure=migration_strengthen_structure,
            migration_enrich_examples=migration_enrich_examples,
        )

    if output_dir is not None and result.status == "success":
        written_path = _write_story_output(result, output_dir)
        typer.echo(f"Written to: {written_path}", err=True)
    elif output_dir is not None and result.status != "success":
        typer.echo("Story is incomplete; nothing was written.", err=True)

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


@page_app.command("new")
def page_new_command(  # noqa: PLR0913
    output_path: Annotated[Path, typer.Argument(help="Path to the page to create.")],
    title: Annotated[str, typer.Option("--title")],
    *,
    add_to_nav: Annotated[bool, typer.Option("--add-to-nav/--no-add-to-nav")] = True,
    mkdocs_file: Annotated[Path, typer.Option("--mkdocs-file")] = Path("mkdocs.yml"),
    description: Annotated[str, typer.Option("--description")] = "",
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
) -> None:
    """Create a new documentation page scaffold."""
    _emit(
        scaffold_doc(
            doc_path=str(output_path),
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


@page_app.command("batch-new")
def page_batch_new_command(
    pages_json: Annotated[Path | None, typer.Option("--pages-json")] = None,
    plan_response_json: Annotated[Path | None, typer.Option("--plan-response-json")] = None,
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
) -> None:
    """Create multiple page scaffolds from JSON input."""
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


@page_app.command("fill")
def page_fill_command(
    doc_path: Annotated[Path, typer.Argument(help="Path to the page to enrich.")],
    content: Annotated[str, typer.Option("--content")] = "",
    *,
    framework: Annotated[FrameworkName | None, typer.Option("--framework")] = None,
    sections_to_enrich: Annotated[list[str] | None, typer.Option("--section")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Fill TODO placeholders in an existing page scaffold."""
    _emit(
        enrich_doc(
            doc_path=str(doc_path),
            content=content,
            framework=framework,
            sections_to_enrich=sections_to_enrich,
            overwrite=overwrite,
        )
    )


@validate_app.callback(invoke_without_command=True)
def validate_command(  # noqa: PLR0913
    ctx: typer.Context,
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    mkdocs_file: Annotated[Path | None, typer.Option("--mkdocs-file")] = None,
    external_mode: Annotated[str, typer.Option("--external-mode")] = "report",
    required_headers: Annotated[list[str] | None, typer.Option("--required-header")] = None,
    required_frontmatter: Annotated[
        list[str] | None, typer.Option("--required-frontmatter")
    ] = None,
    checks: Annotated[list[DocsValidationCheck] | None, typer.Option("--check")] = None,
) -> None:
    """Run read-only docs validation checks."""
    if ctx.invoked_subcommand is not None:
        return
    _run_validate_all(
        docs_root=docs_root,
        mkdocs_file=mkdocs_file,
        external_mode=external_mode,
        required_headers=required_headers,
        required_frontmatter=required_frontmatter,
        checks=checks,
    )


@validate_app.command("all", hidden=True)
def validate_docs_command(  # noqa: PLR0913
    docs_root: Annotated[Path, typer.Option("--docs-root")] = Path("docs"),
    mkdocs_file: Annotated[Path | None, typer.Option("--mkdocs-file")] = None,
    external_mode: Annotated[str, typer.Option("--external-mode")] = "report",
    required_headers: Annotated[list[str] | None, typer.Option("--required-header")] = None,
    required_frontmatter: Annotated[
        list[str] | None, typer.Option("--required-frontmatter")
    ] = None,
    checks: Annotated[list[DocsValidationCheck] | None, typer.Option("--check")] = None,
) -> None:
    """Run consolidated docs validation checks."""
    _run_validate_all(
        docs_root=docs_root,
        mkdocs_file=mkdocs_file,
        external_mode=external_mode,
        required_headers=required_headers,
        required_frontmatter=required_frontmatter,
        checks=checks,
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
    mode: Annotated[OnboardProjectMode, typer.Option("--mode")] = OnboardProjectMode.FULL,
    dev_url: Annotated[str | None, typer.Option("--dev-url")] = None,
    staging_url: Annotated[str | None, typer.Option("--staging-url")] = None,
    production_url: Annotated[str | None, typer.Option("--production-url")] = None,
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
    """Bootstrap docs setup artifacts, starter docs, and contributor guidance."""
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
                dev_url=dev_url,
                staging_url=staging_url,
                production_url=production_url,
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


@integrations_app.command("artifact")
def integrations_artifact_command(  # noqa: PLR0913
    kind: Annotated[
        CopilotArtifactKind,
        typer.Argument(help="Artifact kind: instruction, prompt, or agent."),
    ],
    file_stem: Annotated[str, typer.Argument(help="Stem name for the output file.")],
    *,
    content: Annotated[str | None, typer.Option("--content")] = None,
    from_file: Annotated[Path | None, typer.Option("--from-file")] = None,
    title: Annotated[str | None, typer.Option("--title")] = None,
    description: Annotated[str | None, typer.Option("--description")] = None,
    apply_to: Annotated[str, typer.Option("--apply-to")] = "**",
    agent: Annotated[CopilotAgentMode, typer.Option("--agent")] = CopilotAgentMode.AGENT,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Create an AI/editor integration artifact for this repository."""
    if (content is None) == (from_file is None):
        _emit_error("Provide exactly one of --content or --from-file.")
    if content is not None:
        artifact_content = content
    else:
        if from_file is None:
            _emit_error("Provide exactly one of --content or --from-file.")
        artifact_content = from_file.read_text(encoding="utf-8")
    _emit(
        create_copilot_artifact(
            kind=kind,
            file_stem=file_stem,
            content=artifact_content,
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


@integrations_app.command("init")
def integrations_init_command(
    platform: Annotated[AgentPlatform, typer.Option("--platform")] = AgentPlatform.COPILOT,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    *,
    include_tools: Annotated[bool, typer.Option("--include-tools/--no-tools")] = True,
) -> None:
    """Generate AI/editor integration config files for this project."""
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


@asset_app.command("create")
def asset_create_command(  # noqa: PLR0913
    kind: Annotated[VisualAssetKind, typer.Argument(help="Asset kind to generate.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    subtitle: Annotated[str | None, typer.Option("--subtitle")] = None,
    primary_color: Annotated[str, typer.Option("--primary-color")] = "#5C6BC0",
    background_color: Annotated[str, typer.Option("--background-color")] = "#F8F9FA",
    output_path: Annotated[Path | None, typer.Option("--output-path")] = None,
) -> None:
    """Create a visual documentation asset such as a header, badge, or icon set."""
    _emit(
        generate_visual_asset(
            kind=kind,
            operation=VisualAssetOperation.RENDER,
            title=title,
            subtitle=subtitle,
            primary_color=primary_color,
            background_color=background_color,
            output_path=str(output_path) if output_path else None,
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


@diagram_app.command("create")
def diagram_create_command(
    description: Annotated[str, typer.Argument(help="Plain-language diagram description.")],
    diagram_type: Annotated[DiagramType, typer.Option("--type")] = DiagramType.FLOWCHART,
    framework: Annotated[str | None, typer.Option("--framework")] = None,
    title: Annotated[str | None, typer.Option("--title")] = None,
) -> None:
    """Create Mermaid diagram source from a plain-language description."""
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


@diagram_app.command("render")
def diagram_render_command(
    mermaid_source: Annotated[str, typer.Argument(help="Mermaid source to render.")],
    output_format: Annotated[str, typer.Option("--output-format")] = "svg",
    output_path: Annotated[Path | None, typer.Option("--output-path")] = None,
) -> None:
    """Render Mermaid source to SVG or PNG output."""
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


@app.command("changelog")
def changelog_command(
    version: Annotated[str, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path(),
    since_tag: Annotated[str | None, typer.Option("--since-tag")] = None,
    fmt: Annotated[
        ChangelogEntryFormat, typer.Option("--format")
    ] = ChangelogEntryFormat.KEEP_A_CHANGELOG,
) -> None:
    """Generate a structured changelog entry from git history."""
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
    argv = list(args) if args is not None else sys.argv[1:]
    cli_state = _get_cli_state()
    if "--json" in argv:
        cli_state.output_mode = "json"
    elif "--human" in argv:
        cli_state.output_mode = "human"
    else:
        cli_state.output_mode = "auto"
    try:
        result = app(
            prog_name="mcp-zen-of-docs",
            args=argv if args is not None else None,
            standalone_mode=False,
        )
    except NoArgsIsHelpError:
        return 0
    except ClickException as exc:
        _emit(
            CliErrorResponse(message=_format_click_exception(argv, exc)),
            err=True,
            exit_on_error=False,
        )
        return exc.exit_code
    return result if isinstance(result, int) else 0


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


@page_app.command("write")
def page_write_command(  # noqa: PLR0913
    output_path: Annotated[Path, typer.Argument(help="Path where the page should be written.")],
    topic: Annotated[str, typer.Option("--topic")],
    *,
    framework: Annotated[FrameworkName, typer.Option("--framework")] = FrameworkName.ZENSICAL,
    audience: Annotated[str | None, typer.Option("--audience")] = None,
    content_hints: Annotated[str | None, typer.Option("--content-hints")] = None,
    sections: Annotated[list[str] | None, typer.Option("--section")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Write a structured documentation page draft for a topic."""
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
    from mcp_zen_of_docs.models import CreateSvgAssetRequest  # noqa: PLC0415

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


@asset_app.command("write-svg")
def asset_write_svg_command(  # noqa: PLR0913
    output_path: Annotated[Path, typer.Argument(help="Path where the SVG should be written.")],
    *,
    svg_markup: Annotated[str | None, typer.Option("--svg-markup")] = None,
    svg_file: Annotated[Path | None, typer.Option("--svg-file")] = None,
    asset_kind: Annotated[VisualAssetKind, typer.Option("--asset-kind")] = VisualAssetKind.ICONS,
    convert_to_png: Annotated[bool, typer.Option("--convert-to-png/--no-convert-to-png")] = False,
    png_output_path: Annotated[Path | None, typer.Option("--png-output-path")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
) -> None:
    """Write raw SVG markup to disk and optionally convert it to PNG."""
    if svg_file is not None:
        markup = svg_file.read_text(encoding="utf-8")
    elif svg_markup is not None:
        markup = svg_markup
    else:
        _emit_error("Provide --svg-markup or --svg-file.")
    from mcp_zen_of_docs.models import CreateSvgAssetRequest  # noqa: PLC0415

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


@code_doc_app.command("coverage")
def code_doc_coverage_command(
    path: Annotated[Path, typer.Argument(help="Source file or directory to audit.")],
    *,
    language: Annotated[DocstringLanguage | None, typer.Option("--language")] = None,
    include_private: Annotated[
        bool, typer.Option("--include-private/--no-include-private")
    ] = False,
    min_coverage: Annotated[float, typer.Option("--min-coverage", min=0.0, max=1.0)] = 0.8,
) -> None:
    """Audit source-code documentation coverage."""
    _emit(
        audit_docstrings(
            DocstringAuditRequest(
                source_path=path,
                language=language,
                include_private=include_private,
                min_coverage=min_coverage,
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


@code_doc_app.command("stubs")
def code_doc_stubs_command(  # noqa: PLR0913
    path: Annotated[Path, typer.Argument(help="Source file or directory to enrich.")],
    *,
    language: Annotated[DocstringLanguage | None, typer.Option("--language")] = None,
    style: Annotated[DocstringStyle | None, typer.Option("--style")] = None,
    context_hint: Annotated[str | None, typer.Option("--context-hint")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite/--no-overwrite")] = False,
    include_private: Annotated[
        bool, typer.Option("--include-private/--no-include-private")
    ] = False,
) -> None:
    """Generate canonical docstring stubs for undocumented symbols."""
    _emit(
        optimize_docstrings(
            DocstringOptimizerRequest(
                source_path=path,
                language=language,
                style=style,
                overwrite=overwrite,
                include_private=include_private,
                context_hint=context_hint,
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
    from mcp_zen_of_docs.generators import generate_custom_theme_impl  # noqa: PLC0415
    from mcp_zen_of_docs.models import GenerateCustomThemeRequest  # noqa: PLC0415

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
    from mcp_zen_of_docs.generators import configure_zensical_extensions_impl  # noqa: PLC0415
    from mcp_zen_of_docs.models import ConfigureZensicalExtensionsRequest  # noqa: PLC0415

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

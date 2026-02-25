"""Documentation generator tool implementations."""

from __future__ import annotations

import ast
import datetime
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import tempfile

from collections.abc import Callable
from pathlib import Path
from typing import Literal
from typing import TypedDict

from .asset_conversion import convert_visual_asset
from .asset_conversion import generate_svg_png_conversion_scripts
from .frameworks.material_profile import DEFAULT_SECTIONS
from .frameworks.material_profile import MATERIAL_SNIPPETS
from .generator import orchestrate_story
from .infrastructure import capture_framework_detection_snapshot
from .infrastructure.filesystem_adapter import discover_copilot_assets
from .infrastructure.filesystem_adapter import discover_docs_deploy_pipelines
from .infrastructure.filesystem_adapter import discover_shell_scripts
from .infrastructure.filesystem_adapter import persist_init_state
from .infrastructure.filesystem_adapter import required_init_artifacts
from .infrastructure.filesystem_adapter import resolve_project_root
from .infrastructure.filesystem_adapter import write_copilot_assets
from .infrastructure.filesystem_adapter import write_docs_deploy_pipeline
from .infrastructure.filesystem_adapter import write_shell_script
from .infrastructure.filesystem_adapter import write_text_file
from .infrastructure.shell_adapter import default_shell_for_platform
from .infrastructure.shell_adapter import execute_default_init_script
from .migration import orchestrate_story_migration
from .models import AgentConfigRequest
from .models import AgentConfigResponse
from .models import AgentPlatform
from .models import AuthoringPrimitive
from .models import BoilerplateGenerationErrorCode
from .models import CapabilityMatrixItem
from .models import CapabilityMatrixV2Response
from .models import CapabilityStrategy
from .models import CapabilitySupportDetail
from .models import ChangelogCategoryEntry
from .models import ChangelogEntryFormat
from .models import CheckInitStatusResponse
from .models import ConfigureZensicalExtensionsRequest
from .models import ConfigureZensicalExtensionsResponse
from .models import CopilotArtifactKind
from .models import CopilotInitArtifactMetadata
from .models import CreateAgentRequest
from .models import CreateAgentResponse
from .models import CreateCopilotArtifactRequest
from .models import CreateCopilotArtifactResponse
from .models import CreateInstructionRequest
from .models import CreateInstructionResponse
from .models import CreatePromptRequest
from .models import CreatePromptResponse
from .models import CustomThemeTarget
from .models import DetectFrameworkRequest
from .models import DetectFrameworkResponse
from .models import DiagramType
from .models import DocsDeployPipelineArtifactMetadata
from .models import DocsDeployProvider
from .models import EnrichDocRequest
from .models import EnrichDocResponse
from .models import EphemeralInstallRequest
from .models import EphemeralInstallResponse
from .models import FrameworkInitSpec  # noqa: F401  (re-exported for server convenience)
from .models import FrameworkName
from .models import GatedBoilerplateGenerationRequest
from .models import GatedBoilerplateGenerationResponse
from .models import GenerateChangelogRequest
from .models import GenerateChangelogResponse
from .models import GenerateCliDocsRequest
from .models import GenerateCliDocsResponse
from .models import GenerateCustomThemeFile
from .models import GenerateCustomThemeRequest
from .models import GenerateCustomThemeResponse
from .models import GenerateDiagramRequest
from .models import GenerateDiagramResponse
from .models import GenerateMcpToolsDocsRequest
from .models import GenerateMcpToolsDocsResponse
from .models import GenerateProjectManifestDocsResponse
from .models import GenerateReferenceDocsKind
from .models import GenerateVisualAssetRequest
from .models import GenerateVisualAssetResponse
from .models import InitFrameworkStructureRequest
from .models import InitFrameworkStructureResponse
from .models import InitProjectRequest
from .models import InitProjectResponse
from .models import ManifestType
from .models import MarkupDialect
from .models import MaterialSnippetRequest
from .models import MaterialSnippetResponse
from .models import MigrationModeContract
from .models import MigrationQualityEnhancementToggles
from .models import OnboardingGuidanceContract
from .models import OnboardingSkeletonRequest
from .models import OnboardingSkeletonResponse
from .models import PhaseArtifact
from .models import PipelineContext
from .models import PipelinePhase
from .models import PipelinePhaseRequest
from .models import PipelinePhaseResponse
from .models import PipelinePhaseStatus
from .models import PlanDocsRequest
from .models import PlanDocsResponse
from .models import PlannedPage
from .models import PrimitiveCatalogResponse
from .models import PrimitiveSupportLookupRequest
from .models import PrimitiveSupportLookupResponse
from .models import ReadinessLevel
from .models import ReferenceAuthoringPackResponse
from .models import RenderDiagramRequest
from .models import RenderDiagramResponse
from .models import RenderPrimitiveSnippetRequest
from .models import RenderPrimitiveSnippetResponse
from .models import RuntimeOnboardingMatrixResponse
from .models import RuntimeTrack
from .models import ShellScriptArtifactMetadata
from .models import ShellScriptType
from .models import SourceCodeHost
from .models import SourceLineLink
from .models import StoryGenerationRequest
from .models import StoryGenerationResponse
from .models import StoryMigrationMode
from .models import SvgPngScriptsResponse
from .models import SvgPromptRequest
from .models import SvgPromptToolkitResponse
from .models import ToolSignature
from .models import TranslatePrimitiveSyntaxRequest
from .models import TranslatePrimitiveSyntaxResponse
from .models import VisualAssetConversionRequest
from .models import VisualAssetConversionResponse
from .models import VisualAssetFormat
from .models import VisualAssetKind
from .models import VisualAssetOperation
from .models import WriteDocRequest
from .models import WriteDocResponse
from .models import ZensicalExtension
from .models import ZensicalExtensionConfig
from .primitives_engine import build_framework_support_matrix
from .primitives_engine import list_all_primitives
from .primitives_engine import list_supported_frameworks
from .primitives_engine import lookup_support_level
from .primitives_engine import render_primitive_for_framework
from .primitives_engine import translate_primitive_between_frameworks
from .templates import FRAMEWORK_INIT_SPECS
from .templates import iter_doc_boilerplate_templates
from .visual_assets import generate_svg_prompt_toolkit


__all__ = [
    "check_init_status",
    "convert_svg_to_png_reference",
    "create_agent_impl",
    "create_copilot_artifact_impl",
    "create_instruction_impl",
    "create_prompt_impl",
    "default_reference_output_file",
    "detect_framework",
    "enrich_doc",
    "generate_agent_config",
    "generate_changelog_impl",
    "generate_cli_docs",
    "generate_diagram_impl",
    "generate_doc_boilerplate",
    "generate_material_reference_snippets",
    "generate_mcp_tools_docs",
    "generate_onboarding_skeleton",
    "generate_reference_authoring_pack",
    "generate_story",
    "generate_svg_png_scripts_reference",
    "generate_svg_prompt_toolkit_reference",
    "generate_visual_asset_impl",
    "get_framework_capability_matrix_v2",
    "get_runtime_onboarding_matrix",
    "init_framework_structure_impl",
    "init_project",
    "list_authoring_primitives",
    "lookup_primitive_support",
    "plan_docs",
    "render_diagram_impl",
    "render_framework_primitive",
    "run_ephemeral_install",
    "run_pipeline_phase",
    "translate_primitive_syntax",
    "write_doc_impl",
]


def _coerce_path(value: Path | str | None) -> Path | None:
    return Path(value) if isinstance(value, str) else value


def _coerce_framework_name(value: FrameworkName | str) -> FrameworkName:
    return value if isinstance(value, FrameworkName) else FrameworkName(value)


def _coerce_primitive(value: AuthoringPrimitive | str) -> AuthoringPrimitive:
    return value if isinstance(value, AuthoringPrimitive) else AuthoringPrimitive(value)


def _resolve_mcp_target_path(target: Path | None) -> Path:
    return Path(target or "src/mcp_zen_of_docs/server.py")


def _resolve_project_root(project_root: Path | str) -> Path:
    return resolve_project_root(project_root)


def _write_shell_script(
    project_root: Path,
    *,
    shell: ShellScriptType,
    overwrite: bool,
) -> tuple[ShellScriptArtifactMetadata, Path | None]:
    return write_shell_script(project_root, shell=shell, overwrite=overwrite)


def _default_shell_for_platform() -> ShellScriptType:
    return default_shell_for_platform()


def _execute_default_script(
    *,
    project_root: Path,
    shell_scripts: list[ShellScriptArtifactMetadata],
) -> str | None:
    return execute_default_init_script(project_root=project_root, shell_scripts=shell_scripts)


def _write_init_state(
    project_root: Path,
    *,
    shell_scripts: list[ShellScriptArtifactMetadata],
    copilot_assets: list[CopilotInitArtifactMetadata] | None = None,
    deploy_pipelines: list[DocsDeployPipelineArtifactMetadata] | None = None,
) -> Path:
    return persist_init_state(
        project_root,
        shell_scripts=shell_scripts,
        copilot_assets=copilot_assets,
        deploy_pipelines=deploy_pipelines,
    )


def _required_init_artifacts(
    project_root: Path,
    *,
    deploy_provider: DocsDeployProvider,
) -> list[Path]:
    return required_init_artifacts(project_root, deploy_provider=deploy_provider)


def _discover_shell_scripts(project_root: Path) -> list[ShellScriptArtifactMetadata]:
    return discover_shell_scripts(project_root)


def _write_copilot_assets(
    project_root: Path,
    *,
    overwrite: bool,
) -> tuple[list[CopilotInitArtifactMetadata], list[Path]]:
    return write_copilot_assets(project_root, overwrite=overwrite)


def _discover_copilot_assets(project_root: Path) -> list[CopilotInitArtifactMetadata]:
    return discover_copilot_assets(project_root)


def _write_docs_deploy_pipeline(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
    overwrite: bool,
) -> tuple[DocsDeployPipelineArtifactMetadata, Path | None]:
    return write_docs_deploy_pipeline(
        project_root,
        provider=provider,
        overwrite=overwrite,
    )


def _discover_docs_deploy_pipelines(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
) -> list[DocsDeployPipelineArtifactMetadata]:
    return discover_docs_deploy_pipelines(project_root, provider=provider)


def _decorator_tool_name(node_name: str, decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
        return node_name
    if not (
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "tool"
    ):
        return None
    custom_name = next(
        (
            str(keyword.value.value)
            for keyword in decorator.keywords
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant)
        ),
        None,
    )
    return custom_name or node_name


def _extract_tool_signatures(module_tree: ast.Module) -> list[ToolSignature]:
    tools: list[ToolSignature] = []
    for node in module_tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        tool_name = next(
            (
                name
                for decorator in node.decorator_list
                if (name := _decorator_tool_name(node.name, decorator)) is not None
            ),
            None,
        )
        if tool_name is None:
            continue
        tools.append(ToolSignature(name=tool_name, params=[arg.arg for arg in node.args.args]))
    return tools


def generate_cli_docs(
    cli_command: str, output_file: Path | str | None = None, timeout_seconds: int = 10
) -> GenerateCliDocsResponse:
    """Generate Markdown docs from a CLI help output.

    Runs the given command with ``--help`` appended (if not already present),
    captures stdout/stderr, and wraps the output in a fenced Markdown block.

    Args:
        cli_command: Shell command string to run (e.g. ``"myapp"`` or
            ``"myapp --help"``).
        output_file: Optional path to write the generated Markdown file.
            Parent directories are created automatically.
        timeout_seconds: Maximum seconds to wait for the subprocess to exit.
            Defaults to ``10``.

    Returns:
        Response with status, exit code, generated Markdown, and optional
        output file path.
    """
    request = GenerateCliDocsRequest(
        cli_command=cli_command,
        output_file=_coerce_path(output_file),
        timeout_seconds=timeout_seconds,
    )
    if not request.cli_command.strip():
        return GenerateCliDocsResponse(
            status="error",
            message="cli_command must not be empty.",
        )

    command_parts = shlex.split(request.cli_command)
    if "--help" not in command_parts and "-h" not in command_parts:
        command_parts.append("--help")

    try:
        completed = subprocess.run(  # noqa: S603
            command_parts,
            capture_output=True,
            text=True,
            check=False,
            timeout=request.timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return GenerateCliDocsResponse(
            status="error",
            command=" ".join(command_parts),
            message=str(exc),
        )

    output = (completed.stdout or "").strip() or (completed.stderr or "").strip()
    markdown = (
        f"# CLI Reference: `{command_parts[0]}`\n\n"
        "## Command\n\n"
        f"`{' '.join(command_parts)}`\n\n"
        "## Help Output\n\n"
        "```text\n"
        f"{output}\n"
        "```\n"
    )
    if request.output_file:
        request.output_file.parent.mkdir(parents=True, exist_ok=True)
        request.output_file.write_text(markdown, encoding="utf-8")

    return GenerateCliDocsResponse(
        status="success" if completed.returncode == 0 else "warning",
        command=" ".join(command_parts),
        exit_code=completed.returncode,
        output_file=request.output_file,
        markdown=markdown,
    )


def generate_mcp_tools_docs(
    target: Path | str | None = None, output_file: Path | str | None = None
) -> GenerateMcpToolsDocsResponse:
    """Generate Markdown docs for MCP tools found in a Python module.

    Parses the target Python file with the AST, extracts ``@mcp.tool``
    decorated function signatures, and renders a Markdown table of tool names
    and their parameters.

    Args:
        target: Path to a Python module file. Defaults to the server module
            entry point resolved from the installed package.
        output_file: Optional path to write the generated Markdown file.
            Parent directories are created automatically.

    Returns:
        Response with status, tool count, extracted signatures, generated
        Markdown, and optional output file path.
    """
    request = GenerateMcpToolsDocsRequest(
        target=_coerce_path(target),
        output_file=_coerce_path(output_file),
    )
    target_path = _resolve_mcp_target_path(request.target)
    if not target_path.exists():
        return GenerateMcpToolsDocsResponse(
            status="error",
            target=target_path,
            message="Target file does not exist.",
        )

    tree = ast.parse(target_path.read_text(encoding="utf-8"))
    tools = _extract_tool_signatures(tree)

    header = "# MCP Tool Reference\n\n| Tool | Parameters |\n| --- | --- |\n"
    rows = "".join(f"| `{tool.name}` | `{', '.join(tool.params)}` |\n" for tool in tools)
    markdown = header + rows
    if request.output_file:
        request.output_file.parent.mkdir(parents=True, exist_ok=True)
        request.output_file.write_text(markdown, encoding="utf-8")

    return GenerateMcpToolsDocsResponse(
        status="success",
        target=target_path,
        count=len(tools),
        tools=tools,
        output_file=request.output_file,
        markdown=markdown,
    )


def _dedup_blank_lines(lines: list[str]) -> str:
    """Join lines, collapsing consecutive blank lines into one."""
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        if line == "" and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = line == ""
    return "\n".join(cleaned).rstrip() + "\n"


def _generate_pyproject_markdown(toml_path: Path) -> tuple[str, str, str]:
    """Parse pyproject.toml and return (markdown, name, version)."""
    import tomllib  # noqa: PLC0415

    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)

    project = data.get("project", {})
    name = project.get("name", "")
    version = project.get("version", "")
    description = project.get("description", "")
    readme = project.get("readme", "")
    requires_python = project.get("requires-python", "")
    scripts = project.get("scripts", {})
    deps: list[str] = project.get("dependencies", [])
    dep_groups: dict[str, list[str]] = data.get("dependency-groups", {})
    build_system: dict[str, object] = data.get("build-system", {})
    tool: dict[str, object] = data.get("tool", {})

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Project Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        f"| **Python** | `{requires_python}` |",
        *([f"| **Readme** | `{readme}` |"] if readme else []),
        "",
    ]
    if scripts:
        lines += [
            "## Entry-Point Scripts",
            "",
            "| Script | Entry Point |",
            "| ------ | ----------- |",
            *[f"| `{k}` | `{v}` |" for k, v in scripts.items()],
            "",
        ]
    if deps:
        lines += [
            "## Runtime Dependencies",
            "",
            "| Package |",
            "| ------- |",
            *[f"| `{d}` |" for d in deps],
            "",
        ]
    for group_name, group_deps in dep_groups.items():
        title = group_name.replace("-", " ").title()
        lines += [
            f"## {title} Dependencies (`{group_name}` group)",
            "",
            "| Package |",
            "| ------- |",
            *[f"| `{d}` |" for d in group_deps],
            "",
        ]
    if build_system:
        backend = build_system.get("build-backend", "")
        requires_build = build_system.get("requires", [])
        lines += [
            "## Build System",
            "",
            f"- **Backend:** `{backend}`",
            *(f"- **Requires:** `{r}`" for r in requires_build),
            "",
        ]
    for tool_key, tool_title in [
        ("pytest", "pytest"),
        ("ruff", "ruff"),
        ("ty", "ty (type checker)"),
        ("poe", "Poe the Poet tasks"),
    ]:
        tool_data = tool.get(tool_key)
        if not tool_data:
            continue
        lines += [f"## `[tool.{tool_key}]` — {tool_title}", ""]
        if isinstance(tool_data, dict):
            if tool_key == "poe" and "tasks" in tool_data:
                lines += ["| Task | Command |", "| ---- | ------- |"]
                for task_name, task_val in tool_data["tasks"].items():
                    cmd = task_val if isinstance(task_val, str) else str(task_val)
                    lines.append(f"| `poe {task_name}` | `{cmd}` |")
                lines.append("")
            else:
                lines += ["```toml", *[f"{k} = {v!r}" for k, v in tool_data.items()], "```", ""]
        lines.append("")
    return _dedup_blank_lines(lines), name, version


def _generate_nodejs_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse package.json and return (markdown, name, version)."""
    import json  # noqa: PLC0415

    data: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = str(data.get("name", ""))
    version = str(data.get("version", ""))
    description = str(data.get("description", ""))
    main = str(data.get("main", ""))
    license_ = str(data.get("license", ""))
    engines: dict[str, str] = data.get("engines", {})
    scripts: dict[str, str] = data.get("scripts", {})
    deps: dict[str, str] = data.get("dependencies", {})
    dev_deps: dict[str, str] = data.get("devDependencies", {})
    peer_deps: dict[str, str] = data.get("peerDependencies", {})

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Package Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        *([f"| **License** | `{license_}` |"] if license_ else []),
        *([f"| **Main** | `{main}` |"] if main else []),
        *(
            [f"| **Engines** | {', '.join(f'`{k}: {v}`' for k, v in engines.items())} |"]
            if engines
            else []
        ),
        "",
    ]
    if scripts:
        lines += [
            "## Scripts",
            "",
            "| Script | Command |",
            "| ------ | ------- |",
            *[f"| `npm run {k}` | `{v}` |" for k, v in scripts.items()],
            "",
        ]
    if deps:
        lines += [
            "## Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in deps.items()],
            "",
        ]
    if dev_deps:
        lines += [
            "## Dev Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in dev_deps.items()],
            "",
        ]
    if peer_deps:
        lines += [
            "## Peer Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in peer_deps.items()],
            "",
        ]
    return _dedup_blank_lines(lines), name, version


def _as_str_object_dict(value: object) -> dict[str, object]:
    """Normalize loose mapping-like input into a string-keyed dict."""
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _as_str_list_dict(value: object) -> dict[str, list[str]]:
    """Normalize loose mapping-like input into string lists keyed by strings."""
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, item in value.items():
        if isinstance(item, list):
            normalized[str(key)] = [str(entry) for entry in item]
    return normalized


def _as_str_list(value: object) -> list[str]:
    """Normalize loose sequence input into a list of strings."""
    if not isinstance(value, list):
        return []
    return [str(entry) for entry in value]


class _ZensicalExtensionRegistryEntry(TypedDict):
    """Typed shape of a Zensical extension registry entry."""

    description: str
    toml_snippet: str
    yaml_snippet: str
    authoring_guides: list[str]
    extra_js: list[str]
    requires: list[ZensicalExtension]


def _generate_cargo_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse Cargo.toml and return (markdown, name, version)."""
    import tomllib  # noqa: PLC0415

    with manifest_path.open("rb") as fh:
        data = tomllib.load(fh)

    pkg = _as_str_object_dict(data.get("package"))
    name = str(pkg.get("name", ""))
    version = str(pkg.get("version", ""))
    edition = str(pkg.get("edition", ""))
    description = str(pkg.get("description", ""))
    license_ = str(pkg.get("license", ""))
    rust_version = str(pkg.get("rust-version", ""))
    deps = _as_str_object_dict(data.get("dependencies"))
    dev_deps = _as_str_object_dict(data.get("dev-dependencies"))
    features = _as_str_list_dict(data.get("features"))

    def _dep_version(v: object) -> str:
        if isinstance(v, str):
            return v
        dep_config = _as_str_object_dict(v)
        if dep_config:
            version_value = dep_config.get("version", "workspace")
            return str(version_value)
        return str(v)

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Crate Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        *([f"| **Edition** | `{edition}` |"] if edition else []),
        *([f"| **MSRV** | `{rust_version}` |"] if rust_version else []),
        *([f"| **License** | `{license_}` |"] if license_ else []),
        "",
    ]
    if deps:
        lines += [
            "## Dependencies",
            "",
            "| Crate | Version |",
            "| ----- | ------- |",
            *[f"| `{k}` | `{_dep_version(v)}` |" for k, v in deps.items()],
            "",
        ]
    if dev_deps:
        lines += [
            "## Dev Dependencies",
            "",
            "| Crate | Version |",
            "| ----- | ------- |",
            *[f"| `{k}` | `{_dep_version(v)}` |" for k, v in dev_deps.items()],
            "",
        ]
    if features:
        lines += ["## Feature Flags", ""]
        for feat_name, feat_deps in features.items():
            enables = ", ".join(f"`{d}`" for d in feat_deps) if feat_deps else "*(no extras)*"
            lines.append(f"- **`{feat_name}`** — enables: {enables}")
        lines.append("")
    return _dedup_blank_lines(lines), name, version


def _generate_gomod_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse go.mod and return (markdown, module_path, go_version)."""
    content = manifest_path.read_text(encoding="utf-8")
    import re  # noqa: PLC0415

    module_match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
    go_match = re.search(r"^go\s+(\S+)", content, re.MULTILINE)
    module = module_match.group(1) if module_match else ""
    go_version = go_match.group(1) if go_match else ""
    name = module.split("/")[-1]

    requires = re.findall(r"^\s+(\S+)\s+(\S+)", content, re.MULTILINE)
    direct = [(m, v) for m, v in requires if not v.endswith("// indirect")]

    lines: list[str] = [
        f"# {name}" if name else "# Go Module",
        "",
        "---",
        "",
        "## Module Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Module** | `{module}` |",
        f"| **Go Version** | `{go_version}` |",
        "",
    ]
    if direct:
        lines += [
            "## Direct Dependencies",
            "",
            "| Module | Version |",
            "| ------ | ------- |",
            *[f"| `{m}` | `{v}` |" for m, v in direct],
            "",
        ]
    return _dedup_blank_lines(lines), module, go_version


def _generate_gemfile_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse Gemfile/gemspec and return (markdown, name, version)."""
    import re  # noqa: PLC0415

    content = manifest_path.read_text(encoding="utf-8")
    name = ""
    version = ""
    if manifest_path.suffix == ".gemspec":
        nm = re.search(r'\.name\s*=\s*["\']([^"\']+)["\']', content)
        vm = re.search(r'\.version\s*=\s*["\']([^"\']+)["\']', content)
        name = nm.group(1) if nm else ""
        version = vm.group(1) if vm else ""

    gems = re.findall(r"""gem\s+['"]([\w\-]+)['"](?:,\s*['"~>=<^! ]*([^'"\n]+))?""", content)
    ruby_match = re.search(r"^ruby\s+['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    ruby_version = ruby_match.group(1) if ruby_match else ""

    display_name = name or manifest_path.stem
    lines: list[str] = [
        f"# {display_name}",
        "",
        "---",
        "",
        "## Gemfile Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **File** | `{manifest_path.name}` |",
        *([f"| **Ruby** | `{ruby_version}` |"] if ruby_version else []),
        *([f"| **Version** | `{version}` |"] if version else []),
        "",
    ]
    if gems:
        lines += [
            "## Gems",
            "",
            "| Gem | Version Constraint |",
            "| --- | ----------------- |",
            *[
                f"| `{g}` | `{v.strip()}` |" if v.strip() else f"| `{g}` | *(any)* |"
                for g, v in gems
            ],
            "",
        ]
    return _dedup_blank_lines(lines), display_name, version


# Ordered list of (filename, manifest_type, parser)
type ManifestParser = Callable[[Path], tuple[str, str, str]]


_MANIFEST_CANDIDATES: list[tuple[str, ManifestType, ManifestParser]] = [
    ("pyproject.toml", ManifestType.PYTHON, _generate_pyproject_markdown),
    ("package.json", ManifestType.NODEJS, _generate_nodejs_markdown),
    ("Cargo.toml", ManifestType.RUST, _generate_cargo_markdown),
    ("go.mod", ManifestType.GO, _generate_gomod_markdown),
    ("Gemfile", ManifestType.RUBY, _generate_gemfile_markdown),
]


def generate_project_manifest_docs(  # noqa: C901, PLR0912
    target: Path | str | None = None,
    output_file: Path | str | None = None,
) -> GenerateProjectManifestDocsResponse:
    """Generate a comprehensive Markdown reference page from a project manifest.

    Auto-detects the project type by scanning for standard manifest files in
    priority order: ``pyproject.toml`` (Python), ``package.json`` (Node.js/JS/TS),
    ``Cargo.toml`` (Rust), ``go.mod`` (Go), ``Gemfile``/``*.gemspec`` (Ruby).

    A direct path to a manifest file may also be supplied via *target* to bypass
    auto-detection.

    Args:
        target: Path to a manifest file **or** a project directory to scan.
            Defaults to the current working directory.
        output_file: Optional path to write the generated Markdown file.

    Returns:
        GenerateProjectManifestDocsResponse with markdown, detected manifest
        type, project name, and version.
    """
    target_path = _coerce_path(target) or Path.cwd()

    # Direct file path supplied — infer type from name
    if target_path.is_file():
        for filename, mtype, parser in _MANIFEST_CANDIDATES:
            if target_path.name == filename or target_path.name.endswith(".gemspec"):
                manifest_path = target_path
                manifest_type = mtype
                _parser: Callable[[Path], tuple[str, str, str]] = parser
                break
        else:
            return GenerateProjectManifestDocsResponse(
                status="error",
                manifest_type=ManifestType.UNKNOWN,
                manifest_file=target_path.name,
                message=f"Unrecognised manifest file: {target_path.name}",
            )
    else:
        # Directory — scan for known manifests in priority order
        manifest_path = None
        manifest_type = ManifestType.UNKNOWN
        _parser: ManifestParser | None = None
        for filename, mtype, parser in _MANIFEST_CANDIDATES:
            candidate = target_path / filename
            if candidate.exists():
                manifest_path = candidate
                manifest_type = mtype
                _parser = parser
                break
        # Also check for *.gemspec files when Gemfile not found
        if manifest_path is None:
            gemspecs = list(target_path.glob("*.gemspec"))
            if gemspecs:
                manifest_path = gemspecs[0]
                manifest_type = ManifestType.RUBY
                _parser = _generate_gemfile_markdown

        if manifest_path is None:
            return GenerateProjectManifestDocsResponse(
                status="error",
                manifest_type=ManifestType.UNKNOWN,
                message=(
                    f"No recognised project manifest found in {target_path}. "
                    "Looked for: pyproject.toml, package.json, Cargo.toml, go.mod, Gemfile, *.gemspec"  # noqa: E501
                ),
            )

    if _parser is None:
        return GenerateProjectManifestDocsResponse(
            status="error",
            manifest_type=manifest_type,
            manifest_file=manifest_path.name,
            message=f"Unable to resolve a parser for {manifest_path.name}.",
        )

    try:
        markdown, name, version = _parser(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return GenerateProjectManifestDocsResponse(
            status="error",
            manifest_type=manifest_type,
            manifest_file=manifest_path.name,
            message=f"Failed to parse {manifest_path.name}: {exc}",
        )

    out_path = _coerce_path(output_file)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")

    return GenerateProjectManifestDocsResponse(
        status="success",
        manifest_type=manifest_type,
        manifest_file=manifest_path.name,
        project_name=name or None,
        project_version=version or None,
        output_file=out_path,
        markdown=markdown,
    )


def generate_material_reference_snippets(topic: str | None = None) -> MaterialSnippetResponse:
    """Return Material reference snippets for quick reuse.

    Looks up pre-authored Material for MkDocs snippets optionally filtered by
    topic keyword. Returns all available snippets when *topic* is ``None``.

    Args:
        topic: Optional keyword used to filter returned snippets by relevance.
            When ``None`` all available snippets are returned.

    Returns:
        Response containing a list of matched Material snippet strings and
        optional topic context.
    """
    request = MaterialSnippetRequest(topic=topic)
    if request.topic:
        snippet = MATERIAL_SNIPPETS.get(request.topic)
        if snippet is None:
            return MaterialSnippetResponse(
                status="error",
                topic=request.topic,
                available_topics=sorted(MATERIAL_SNIPPETS),
                message="Unknown snippet topic.",
            )
        return MaterialSnippetResponse(
            status="success",
            topic=request.topic,
            snippet=snippet,
        )

    return MaterialSnippetResponse(
        status="success",
        available_topics=sorted(MATERIAL_SNIPPETS),
        snippets=MATERIAL_SNIPPETS,
        recommended_sections=list(DEFAULT_SECTIONS),
    )


def _normalize_line_range(line_start: int | None, line_end: int | None) -> tuple[int, int]:
    start = line_start or 1
    end = line_end or start
    return (start, end) if start <= end else (end, start)


def _render_source_link(
    *,
    host: SourceCodeHost,
    repository_url: str,
    source_file: str,
    line_start: int,
    line_end: int,
) -> SourceLineLink:
    base_url = repository_url.rstrip("/")
    clean_file = source_file.lstrip("/")
    match host:
        case SourceCodeHost.GITLAB:
            # GitLab: /-/blob/main/file#L10-20
            anchor = f"#L{line_start}-{line_end}" if line_start != line_end else f"#L{line_start}"
            url = f"{base_url}/-/blob/main/{clean_file}{anchor}"
        case SourceCodeHost.BITBUCKET:
            # Bitbucket: /src/HEAD/file#lines-10:20
            anchor = (
                f"#lines-{line_start}:{line_end}"
                if line_start != line_end
                else f"#lines-{line_start}"
            )
            url = f"{base_url}/src/HEAD/{clean_file}{anchor}"
        case SourceCodeHost.AZURE_DEVOPS:
            # Azure DevOps: query-string line ranges
            qs = (
                f"?path=/{clean_file}&version=GBmain"
                f"&line={line_start}&lineEnd={line_end}"
                f"&lineStartColumn=1&lineEndColumn=999&lineStyle=plain"
            )
            url = f"{base_url}{qs}"
        case SourceCodeHost.GITEA | SourceCodeHost.CODEBERG:
            # Gitea / Codeberg / Forgejo: /src/branch/main/file#L10-L20
            anchor = f"#L{line_start}-L{line_end}" if line_start != line_end else f"#L{line_start}"
            url = f"{base_url}/src/branch/main/{clean_file}{anchor}"
        case _:
            # GitHub, self-hosted, unknown: GitHub-style anchors
            anchor = f"#L{line_start}-L{line_end}" if line_start != line_end else f"#L{line_start}"
            url = f"{base_url}/blob/main/{clean_file}{anchor}"
    return SourceLineLink(
        host=host,
        repository_url=base_url,
        file_path=clean_file,
        line_start=line_start,
        line_end=line_end,
        url=url,
    )


def generate_reference_authoring_pack(
    *,
    source_host: SourceCodeHost | None = None,
    repository_url: str | None = None,
    source_file: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
) -> ReferenceAuthoringPackResponse:
    """Generate standardized code-block and linking guidance for docs authoring."""
    start_line, end_line = _normalize_line_range(line_start, line_end)
    effective_repository = (repository_url or "https://github.com/example/repo").strip()
    effective_source_file = (source_file or "src/mcp_zen_of_docs/generator/orchestrator.py").strip()
    hosts = (
        [source_host]
        if source_host is not None
        else [
            SourceCodeHost.GITHUB,
            SourceCodeHost.GITLAB,
            SourceCodeHost.BITBUCKET,
            SourceCodeHost.AZURE_DEVOPS,
            SourceCodeHost.GITEA,
            SourceCodeHost.CODEBERG,
        ]
    )
    source_line_links = [
        _render_source_link(
            host=host,
            repository_url=effective_repository,
            source_file=effective_source_file,
            line_start=start_line,
            line_end=end_line,
        )
        for host in hosts
    ]

    zensical_mkdocstrings_setup = (
        "plugins:\n"
        "  - search\n"
        "  - mkdocstrings:\n"
        "      handlers:\n"
        "        python:\n"
        "          options:\n"
        "            show_source: false\n"
        "            show_root_heading: true\n"
        "\n"
        "::: mcp_zen_of_docs.generator.orchestrator.orchestrate_story\n"
        "    options:\n"
        "      show_source: true\n"
    )
    shell_code_blocks = {
        "bash": "```bash\nuv run --group docs zensical build\n```",
        "zsh": "```zsh\nuv run --group docs zensical build\n```",
        "powershell": "```powershell\nuv run --group docs zensical build\n```",
    }
    api_code_blocks = {
        "http": (
            "```http\nGET /tools/compose_docs_story HTTP/1.1\nHost: localhost\n"
            "Accept: application/json\n```"
        ),
        "json-payload": (
            '```json\n{\n  "prompt": "Document detect-profile-act loop",\n'
            '  "modules": ["audience", "concepts", "structure", "style"],\n'
            '  "context": {\n    "goal": "stable docs automation",\n'
            '    "scope": "core tools",\n'
            '    "constraints": "typed outputs only"\n  }\n}\n```'
        ),
    }
    storyteller_mode_blocks = {
        "single-pass": (
            '```json\n{\n  "enable_runtime_loop": false,\n'
            '  "auto_advance": true,\n'
            '  "runtime_max_turns": 1\n}\n```'
        ),
        "interactive-loop": (
            '```json\n{\n  "enable_runtime_loop": true,\n'
            '  "auto_advance": false,\n'
            '  "runtime_max_turns": 6\n}\n```'
        ),
    }
    markup_examples = {
        MarkupDialect.MARKDOWN: (
            "```markdown\n# API walkthrough\n\n"
            "See [orchestrator source](SOURCE_LINK) for implementation details.\n```"
        ),
        MarkupDialect.MDX: (
            "```mdx\nimport Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n\n"
            '<Tabs>\n  <TabItem value="bash" label="bash">\n\n'
            "```bash\nuv run --group docs zensical build\n```\n\n"
            "  </TabItem>\n</Tabs>\n```"
        ),
        MarkupDialect.MARKDOC: (
            '```markdoc\n{% callout type="note" title="Reference" %}\n'
            "Use source links with line anchors such as {{ source_link }}.\n"
            "{% /callout %}\n```"
        ),
    }
    return ReferenceAuthoringPackResponse(
        status="success",
        zensical_mkdocstrings_setup=zensical_mkdocstrings_setup,
        shell_code_blocks=shell_code_blocks,
        api_code_blocks=api_code_blocks,
        storyteller_mode_blocks=storyteller_mode_blocks,
        markup_examples=markup_examples,
        source_line_links=source_line_links,
        message=(
            "Generated authoring pack with standardized code blocks, mkdocstrings setup, and "
            "host-specific line links."
        ),
    )


def default_reference_output_file(kind: GenerateReferenceDocsKind) -> Path | None:
    """Resolve optional default output path from MCP_ZEN_OF_DOCS_REFERENCE_DIR."""
    output_dir = os.getenv("MCP_ZEN_OF_DOCS_REFERENCE_DIR")
    if output_dir is None or not output_dir.strip():
        return None
    names = {
        GenerateReferenceDocsKind.CLI: "cli-reference.md",
        GenerateReferenceDocsKind.MCP_TOOLS: "mcp-tools.md",
        GenerateReferenceDocsKind.MATERIAL_SNIPPETS: "material-snippets.md",
        GenerateReferenceDocsKind.AUTHORING_PACK: "authoring-pack.md",
        GenerateReferenceDocsKind.DOCSTRING_PACK: "docstring-coverage.md",
        GenerateReferenceDocsKind.PROJECT_MANIFEST: "project-manifest.md",
    }
    return Path(output_dir) / names.get(kind, "reference.md")


def _build_onboarding_guidance(
    project_name: str,
    *,
    channel: Literal["cli", "mcp"],
) -> OnboardingGuidanceContract:
    python_tracks, js_tracks, follow_up_questions = _runtime_onboarding_tracks()
    setup_steps = [
        "uv sync --group dev --group docs",
        "uv run --group dev pytest",
        "uv run --group dev ruff check .",
        "uv run --group docs zensical serve",
    ]
    return OnboardingGuidanceContract(
        channel=channel,
        project_name=project_name,
        summary=f"Use this checklist to onboard contributors to {project_name}.",
        setup_steps=setup_steps,
        verification_commands=[
            "uv run --group dev pytest",
            "uv run --group dev ruff check .",
            "uv run --group docs zensical build",
        ],
        next_actions=[
            (
                "Run `uvx --from mcp-zen-of-docs mcp-zen-of-docs-server` when you need a "
                "zero-install MCP runtime."
            ),
            "Review docs/index.md and pick one documentation improvement task.",
        ],
        metadata={
            "python_env_notes": (
                "For poetry/.venv workflows, run equivalent commands via `poetry run` or "
                "activate `.venv` before executing tools."
            ),
            "js_docs_framework_notes": (
                "For Docusaurus, VitePress, or Starlight docs, use npm/pnpm/yarn docs scripts "
                "in place of zensical commands."
            ),
            "python_runtime_tracks": ", ".join(track.runtime for track in python_tracks),
            "js_runtime_tracks": ", ".join(track.runtime for track in js_tracks),
        },
        follow_up_questions=follow_up_questions,
    )


def generate_onboarding_skeleton(
    project_name: str,
    output_file: Path | str | None = None,
    *,
    include_checklist: bool = True,
    channel: Literal["cli", "mcp"] = "mcp",
) -> OnboardingSkeletonResponse:
    """Generate an onboarding document skeleton for a project.

    Produces a structured Markdown document with a purpose statement, numbered
    local setup steps, and an optional first-contribution checklist. Setup
    commands are derived from the project name and the selected channel.

    Args:
        project_name: Human-readable project name used in headings and
            setup command templates.
        output_file: Optional path to write the generated Markdown file.
        include_checklist: When ``True``, appends a first-contributions
            checklist section to the document. Defaults to ``True``.
        channel: Delivery channel that determines setup command templates.
            Either ``"mcp"`` (default) or ``"cli"``.

    Returns:
        Response containing the generated Markdown, project name, onboarding
        guidance metadata, and optional output file path.
    """
    request = OnboardingSkeletonRequest(
        project_name=project_name,
        output_file=_coerce_path(output_file),
        include_checklist=include_checklist,
        channel=channel,
    )
    guidance = _build_onboarding_guidance(request.project_name, channel=request.channel)
    setup_markdown = "\n".join(
        f"{index}. `{command}`" for index, command in enumerate(guidance.setup_steps, start=1)
    )
    checklist = (
        "\n## First contributions checklist\n\n"
        "- [ ] Run local checks.\n"
        "- [ ] Add one example page.\n"
        "- [ ] Validate links and nav consistency.\n"
        if request.include_checklist
        else ""
    )
    markdown = (
        f"# Onboarding: {request.project_name}\n\n"
        "## Purpose\n\n"
        f"`{request.project_name}` provides a documentation automation MCP server.\n\n"
        "## Local setup\n\n"
        f"{setup_markdown}\n"
        f"{checklist}"
    )
    if request.output_file:
        request.output_file.write_text(markdown, encoding="utf-8")

    return OnboardingSkeletonResponse(
        status="success",
        project_name=request.project_name,
        output_file=request.output_file,
        markdown=markdown,
        guidance=guidance,
    )


def init_project(
    project_root: Path | str = Path(),
    *,
    overwrite: bool = False,
    include_shell_scripts: bool = True,
    deploy_provider: DocsDeployProvider = DocsDeployProvider.GITHUB_PAGES,
) -> InitProjectResponse:
    """Initialize deterministic local artifacts, including shell bootstrap scripts.

    Creates shell bootstrap scripts for all supported shells, GitHub Copilot
    artifacts, and a docs deploy pipeline CI configuration. Persists an init
    state file and executes the default bootstrap script for the current platform.

    Args:
        project_root: Root directory of the project to initialize. Defaults to
            the current working directory.
        overwrite: When ``True``, existing artifacts are overwritten. Defaults
            to ``False``.
        include_shell_scripts: When ``False``, initialization is skipped
            because shell scripts are required for deterministic artifacts.
            Defaults to ``True``.
        deploy_provider: CI/CD deploy provider for which to generate the
            pipeline configuration. Defaults to ``DocsDeployProvider.GITHUB_PAGES``.

    Returns:
        Response with status, initialized flag, paths of created files,
        shell script metadata, Copilot asset metadata, and deploy pipeline
        metadata.
    """
    request = InitProjectRequest(
        project_root=Path(project_root),
        overwrite=overwrite,
        include_shell_scripts=include_shell_scripts,
        deploy_provider=deploy_provider,
    )
    resolved_root = _resolve_project_root(request.project_root)
    if not resolved_root.exists() or not resolved_root.is_dir():
        return InitProjectResponse(
            status="error",
            project_root=resolved_root,
            initialized=False,
            message="project_root must exist and be a directory.",
        )

    if not request.include_shell_scripts:
        return InitProjectResponse(
            status="warning",
            project_root=resolved_root,
            initialized=False,
            message=(
                "Initialization requires include_shell_scripts=True for deterministic artifacts."
            ),
        )

    shell_scripts: list[ShellScriptArtifactMetadata] = []
    created_files: list[Path] = []
    for shell in ShellScriptType:
        artifact, created_file = _write_shell_script(
            resolved_root,
            shell=shell,
            overwrite=request.overwrite,
        )
        shell_scripts.append(artifact)
        if created_file is not None:
            created_files.append(created_file)

    copilot_assets, copilot_created_files = _write_copilot_assets(
        resolved_root,
        overwrite=request.overwrite,
    )
    created_files.extend(copilot_created_files)
    deploy_pipeline, deploy_pipeline_created = _write_docs_deploy_pipeline(
        resolved_root,
        provider=request.deploy_provider,
        overwrite=request.overwrite,
    )
    deploy_pipelines = [deploy_pipeline]
    if deploy_pipeline_created is not None:
        created_files.append(deploy_pipeline_created)
    state_file = _write_init_state(
        resolved_root,
        shell_scripts=shell_scripts,
        copilot_assets=copilot_assets,
        deploy_pipelines=deploy_pipelines,
    )
    if request.overwrite or state_file not in created_files:
        created_files.append(state_file)

    execution_error = _execute_default_script(
        project_root=resolved_root,
        shell_scripts=shell_scripts,
    )
    if execution_error is not None:
        return InitProjectResponse(
            status="warning",
            project_root=resolved_root,
            initialized=False,
            created_files=created_files,
            shell_scripts=shell_scripts,
            copilot_assets=copilot_assets,
            deploy_pipelines=deploy_pipelines,
            message=execution_error,
        )

    return InitProjectResponse(
        status="success",
        project_root=resolved_root,
        initialized=True,
        created_files=created_files,
        shell_scripts=shell_scripts,
        copilot_assets=copilot_assets,
        deploy_pipelines=deploy_pipelines,
    )


_COPILOT_FILE_PATTERNS: tuple[str, ...] = (
    "*.instructions.md",
    "*.prompt.md",
    "*.agent.md",
)


def _discover_existing_copilot_files(project_root: Path) -> list[Path]:
    """Discover pre-existing Copilot artifact files in the .github directory tree."""
    github_dir = project_root / ".github"
    if not github_dir.is_dir():
        return []
    found: list[Path] = []
    for pattern in _COPILOT_FILE_PATTERNS:
        found.extend(sorted(github_dir.rglob(pattern)))
    return sorted(set(found))


def _compute_readiness_level(
    *,
    missing_artifacts: list[Path],
    existing_copilot_files: list[Path],
) -> ReadinessLevel:
    """Compute project readiness level from artifact presence."""
    if not missing_artifacts:
        return ReadinessLevel.FULL
    if existing_copilot_files:
        return ReadinessLevel.PARTIAL
    return ReadinessLevel.NONE


def check_init_status(
    project_root: Path | str = Path(),
    *,
    deploy_provider: DocsDeployProvider = DocsDeployProvider.GITHUB_PAGES,
) -> CheckInitStatusResponse:
    """Check deterministic initialization artifacts without relying on process-level globals.

    Inspects the project root for the presence of required init artifacts
    (shell scripts, Copilot assets, deploy pipelines) and computes an overall
    readiness level based on what is found.

    Args:
        project_root: Root directory of the project to inspect. Defaults to
            the current working directory.
        deploy_provider: Deploy provider used to determine which pipeline
            artifact to expect. Defaults to ``DocsDeployProvider.GITHUB_PAGES``.

    Returns:
        Response with initialization status, readiness level, lists of
        discovered and missing artifacts, and categorized artifact metadata.
    """
    resolved_root = _resolve_project_root(project_root)
    if not resolved_root.exists() or not resolved_root.is_dir():
        return CheckInitStatusResponse(
            status="error",
            project_root=resolved_root,
            initialized=False,
            message="project_root must exist and be a directory.",
        )
    required_artifacts = _required_init_artifacts(
        resolved_root,
        deploy_provider=deploy_provider,
    )
    missing_artifacts = [artifact for artifact in required_artifacts if not artifact.exists()]
    shell_scripts = _discover_shell_scripts(resolved_root)
    copilot_assets = _discover_copilot_assets(resolved_root)
    deploy_pipelines = _discover_docs_deploy_pipelines(
        resolved_root,
        provider=deploy_provider,
    )
    existing_copilot_files = _discover_existing_copilot_files(resolved_root)
    readiness_level = _compute_readiness_level(
        missing_artifacts=missing_artifacts,
        existing_copilot_files=existing_copilot_files,
    )
    initialized = readiness_level is not ReadinessLevel.NONE
    return CheckInitStatusResponse(
        status="success" if not missing_artifacts else "warning",
        project_root=resolved_root,
        initialized=initialized,
        readiness_level=readiness_level,
        existing_copilot_files=existing_copilot_files,
        missing_artifacts=missing_artifacts,
        shell_scripts=shell_scripts,
        copilot_assets=copilot_assets,
        deploy_pipelines=deploy_pipelines,
    )


def _resolve_shell_script_metadata(
    *,
    project_root: Path,
    shell_targets: list[ShellScriptType],
) -> list[ShellScriptArtifactMetadata]:
    discovered_scripts = _discover_shell_scripts(project_root)
    selected_shells = set(shell_targets)
    return [script for script in discovered_scripts if script.shell in selected_shells]


def generate_doc_boilerplate(
    project_root: Path | str = Path(),
    *,
    gate_confirmed: bool = False,
    overwrite: bool = False,
    shell_targets: list[ShellScriptType] | None = None,
) -> GatedBoilerplateGenerationResponse:
    """Generate deterministic documentation boilerplate after hard init gate validation.

    Verifies that the project has been initialized (via ``init_project``) before
    writing any boilerplate content. The *gate_confirmed* flag must be ``True``
    to proceed, acting as an explicit user confirmation.

    Args:
        project_root: Root directory of the initialized project. Defaults to
            the current working directory.
        gate_confirmed: Must be ``True`` to pass the init gate check and allow
            boilerplate generation. Defaults to ``False``.
        overwrite: When ``True``, existing boilerplate files are overwritten.
            Defaults to ``False``.
        shell_targets: Specific shell script types to include in boilerplate
            generation. When ``None``, all available scripts are used.

    Returns:
        Response with status, error code on gate failure, generated file paths,
        and shell script artifact metadata.
    """
    request = GatedBoilerplateGenerationRequest(
        project_root=Path(project_root),
        gate_confirmed=gate_confirmed,
        overwrite=overwrite,
        shell_targets=shell_targets
        or [
            ShellScriptType.BASH,
            ShellScriptType.ZSH,
            ShellScriptType.POWERSHELL,
        ],
    )
    resolved_root = _resolve_project_root(request.project_root)
    if not resolved_root.exists() or not resolved_root.is_dir():
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=resolved_root,
            gate_confirmed=request.gate_confirmed,
            boilerplate_generated=False,
            error_code=BoilerplateGenerationErrorCode.PROJECT_ROOT_INVALID,
            message="project_root must exist and be a directory.",
        )

    shell_scripts = _resolve_shell_script_metadata(
        project_root=resolved_root,
        shell_targets=request.shell_targets,
    )
    if not request.gate_confirmed:
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=resolved_root,
            gate_confirmed=False,
            boilerplate_generated=False,
            shell_scripts=shell_scripts,
            error_code=BoilerplateGenerationErrorCode.GATE_NOT_CONFIRMED,
            message=(
                "Boilerplate generation gate not confirmed. "
                "Set gate_confirmed=True after init checks."
            ),
        )

    init_status = check_init_status(project_root=resolved_root)
    if not init_status.initialized:
        return GatedBoilerplateGenerationResponse(
            status="error",
            project_root=resolved_root,
            gate_confirmed=True,
            boilerplate_generated=False,
            shell_scripts=shell_scripts,
            missing_init_artifacts=init_status.missing_artifacts,
            error_code=BoilerplateGenerationErrorCode.INIT_NOT_COMPLETE,
            message=(
                "Initialization gate failed. Run init_project and confirm "
                "check_init_status.initialized "
                "before generating doc boilerplate."
            ),
        )

    generated_files: list[Path] = []
    for template in sorted(
        iter_doc_boilerplate_templates(),
        key=lambda item: item.relative_path.as_posix(),
    ):
        file_path = resolved_root / template.relative_path
        if file_path.exists() and not request.overwrite:
            continue
        generated_files.append(write_text_file(file_path, content=template.content))

    return GatedBoilerplateGenerationResponse(
        status="success",
        project_root=resolved_root,
        gate_confirmed=True,
        boilerplate_generated=True,
        generated_files=generated_files,
        shell_scripts=shell_scripts,
    )


def _build_migration_contract(  # noqa: PLR0913
    *,
    mode: StoryMigrationMode,
    source_framework: FrameworkName | None,
    target_framework: FrameworkName | None,
    improve_clarity: bool,
    strengthen_structure: bool,
    enrich_examples: bool,
) -> tuple[MigrationModeContract | None, str | None]:
    if mode is StoryMigrationMode.SAME_TARGET:
        resolved_framework = source_framework or target_framework
        if resolved_framework is None:
            return (
                None,
                (
                    "migration_source_framework or migration_target_framework must be provided "
                    "for same-target migration mode."
                ),
            )
        return (
            MigrationModeContract(
                mode=mode,
                source_framework=resolved_framework,
                target_framework=resolved_framework,
                quality_enhancements=MigrationQualityEnhancementToggles(
                    improve_clarity=improve_clarity,
                    strengthen_structure=strengthen_structure,
                    enrich_examples=enrich_examples,
                ),
            ),
            None,
        )
    if source_framework is None or target_framework is None:
        return (
            None,
            (
                "migration_source_framework and migration_target_framework must both be provided "
                "for cross-target migration mode."
            ),
        )
    return (
        MigrationModeContract(
            mode=mode,
            source_framework=source_framework,
            target_framework=target_framework,
            quality_enhancements=MigrationQualityEnhancementToggles(
                improve_clarity=improve_clarity,
                strengthen_structure=strengthen_structure,
                enrich_examples=enrich_examples,
            ),
        ),
        None,
    )


def generate_story(  # noqa: PLR0913
    prompt: str,
    audience: str | None = None,
    modules: list[str] | None = None,
    context: dict[str, str] | None = None,
    *,
    include_onboarding_guidance: bool = False,
    enable_runtime_loop: bool | None = None,
    runtime_max_turns: int | None = None,
    auto_advance: bool | None = None,
    migration_mode: StoryMigrationMode | None = None,
    migration_source_framework: FrameworkName | None = None,
    migration_target_framework: FrameworkName | None = None,
    migration_improve_clarity: bool = True,
    migration_strengthen_structure: bool = True,
    migration_enrich_examples: bool = False,
) -> StoryGenerationResponse:
    """Generate a story by orchestrating selected module outputs and connector follow-ups.

    Routes the request through the standard story orchestrator or the migration
    orchestrator depending on whether *migration_mode* is set.

    Args:
        prompt: Primary story prompt describing the documentation objective.
        audience: Target audience description used to tune output tone. When
            ``None``, no audience-specific tailoring is applied.
        modules: List of module identifiers to activate for the story. When
            ``None`` or empty, the orchestrator selects default modules.
        context: Arbitrary key-value context pairs forwarded to active modules.
        include_onboarding_guidance: When ``True``, appends runtime onboarding
            guidance to the generated story. Defaults to ``False``.
        enable_runtime_loop: Override for the interactive runtime loop setting.
            ``None`` defers to the orchestrator default.
        runtime_max_turns: Maximum number of interactive turns allowed when the
            runtime loop is active. ``None`` defers to the orchestrator default.
        auto_advance: When ``True``, the runtime loop advances without user
            confirmation. ``None`` defers to the orchestrator default.
        migration_mode: Migration strategy contract to use when adapting story
            content between frameworks. When ``None``, standard story generation
            is used.
        migration_source_framework: Source framework for migration. Required
            when *migration_mode* is set.
        migration_target_framework: Target framework for migration. Required
            when *migration_mode* is set.
        migration_improve_clarity: When ``True``, applies clarity improvements
            during migration. Defaults to ``True``.
        migration_strengthen_structure: When ``True``, applies structural
            strengthening during migration. Defaults to ``True``.
        migration_enrich_examples: When ``True``, enriches examples during
            migration. Defaults to ``False``.

    Returns:
        Story generation response containing the generated content, status,
        and optional pipeline context for downstream tool chaining.
    """
    request = StoryGenerationRequest(
        prompt=prompt,
        audience=audience,
        modules=modules or [],
        context=context or {},
        include_onboarding_guidance=include_onboarding_guidance,
        enable_runtime_loop=enable_runtime_loop,
        runtime_max_turns=runtime_max_turns,
        auto_advance=auto_advance,
    )
    if migration_mode is None:
        result = orchestrate_story(request)
        return result.response

    migration_contract, migration_error = _build_migration_contract(
        mode=migration_mode,
        source_framework=migration_source_framework,
        target_framework=migration_target_framework,
        improve_clarity=migration_improve_clarity,
        strengthen_structure=migration_strengthen_structure,
        enrich_examples=migration_enrich_examples,
    )
    if migration_contract is None:
        return StoryGenerationResponse(
            status="error",
            message=migration_error,
        )
    result = orchestrate_story_migration(request, migration_contract)
    if result.message is None or result.response.message is not None:
        return result.response
    return result.response.model_copy(update={"message": result.message})


def generate_svg_prompt_toolkit_reference(
    *,
    asset_kind: VisualAssetKind,
    asset_prompt: str,
    style_notes: str | None = None,
    target_size_hint: str | None = None,
) -> SvgPromptToolkitResponse:
    """Generate deterministic SVG prompt and spec output for reference-doc surfaces."""
    request = SvgPromptRequest(
        asset_kind=asset_kind,
        prompt=asset_prompt,
        style_notes=style_notes,
        target_size_hint=target_size_hint,
    )
    return generate_svg_prompt_toolkit(request)


def generate_svg_png_scripts_reference() -> SvgPngScriptsResponse:
    """Generate deterministic SVG-to-PNG wrapper scripts for all supported shells."""
    scripts_raw = generate_svg_png_conversion_scripts()
    scripts = {ShellScriptType(shell): body for shell, body in scripts_raw.items()}
    return SvgPngScriptsResponse(status="success", scripts=scripts)


def convert_svg_to_png_reference(
    *,
    asset_kind: VisualAssetKind,
    source_svg: str,
    output_file: Path,
) -> VisualAssetConversionResponse:
    """Convert SVG content to PNG and return typed conversion metadata."""
    request = VisualAssetConversionRequest(
        asset_kind=asset_kind,
        source_svg=source_svg,
        output_format=VisualAssetFormat.PNG,
        output_path=output_file,
    )
    return convert_visual_asset(request)


def get_framework_capability_matrix_v2() -> CapabilityMatrixV2Response:
    """Return capability matrix v2 with plugin/fallback strategy semantics."""
    items = [
        CapabilityMatrixItem(
            capability="rich-inline-formatting",
            description=(
                "Highlights, sub/superscript, keyboard keys, and critic-markup migration paths."
            ),
            details=[
                CapabilitySupportDetail(
                    framework=FrameworkName.VITEPRESS,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="markdown-it-mark, markdown-it-sub, markdown-it-sup, markdown-it-kbd",
                    notes=(
                        "Best plugin path for rich inline syntax; critic markup remains"
                        " unsupported."
                    ),
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.DOCUSAURUS,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="remark-sub-super (+ optional custom remark plugins)",
                    notes=(
                        "Use remark plugins where available; fallback to HTML for "
                        "underline/keyboard variants."
                    ),
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.STARLIGHT,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="starlight-kbd (+ remark/rehype additions)",
                    notes=(
                        "Keyboard has dedicated plugin; additional inline formatting requires"
                        " remark/rehype or HTML."
                    ),
                ),
            ],
            migration_hint=(
                "Treat critic markup as unsupported and convert to explicit <ins>/<del> HTML"
                " fallback."
            ),
        ),
        CapabilityMatrixItem(
            capability="definition-lists",
            description="Term/definition blocks in Markdown docs.",
            details=[
                CapabilitySupportDetail(
                    framework=FrameworkName.VITEPRESS,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="markdown-it-deflist",
                    notes="Drop-in support via markdown-it config.",
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.DOCUSAURUS,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="remark-deflist",
                    notes="Attach plugin to docs remarkPlugins in docusaurus config.",
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.STARLIGHT,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="remark-deflist",
                    notes="Configure through Astro markdown remarkPlugins.",
                ),
            ],
            migration_hint=(
                "Enable plugin before migration and add one golden sample page per framework."
            ),
        ),
        CapabilityMatrixItem(
            capability="abbreviations",
            description="Abbreviation declarations and inline expansion behavior.",
            details=[
                CapabilitySupportDetail(
                    framework=FrameworkName.VITEPRESS,
                    strategy=CapabilityStrategy.PLUGIN,
                    plugin="markdown-it-abbr",
                    notes="Closest parity to Zensical auto-expansion.",
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.DOCUSAURUS,
                    strategy=CapabilityStrategy.FALLBACK,
                    plugin=None,
                    notes=(
                        "Prefer <abbr> HTML or custom remark plugin for broader expansion behavior."
                    ),
                ),
                CapabilitySupportDetail(
                    framework=FrameworkName.STARLIGHT,
                    strategy=CapabilityStrategy.FALLBACK,
                    plugin=None,
                    notes="Use <abbr> HTML or custom rehype/remark extension.",
                ),
            ],
            migration_hint=(
                "When auto-expansion is required, keep a custom plugin layer for"
                " non-VitePress stacks."
            ),
        ),
    ]
    return CapabilityMatrixV2Response(
        status="success",
        items=items,
        follow_up_questions=[
            "Do you allow project-level plugin dependencies for docs rendering?",
            "Should critic markup be preserved literally or converted to HTML in migrations?",
        ],
    )


def _runtime_onboarding_tracks() -> tuple[list[RuntimeTrack], list[RuntimeTrack], list[str]]:
    python_tracks = [
        RuntimeTrack(
            runtime="python-uv",
            setup_steps=[
                "uv sync --group dev --group docs",
                "uv run --group dev pytest",
                "uv run --group dev ruff check .",
                "uv run --group docs zensical serve",
            ],
            verification_commands=[
                "uv run --group dev pytest",
                "uv run --group docs zensical build",
            ],
            notes=["Primary recommended workflow for this repository."],
        ),
        RuntimeTrack(
            runtime="python-uvx",
            setup_steps=["uvx --from mcp-zen-of-docs mcp-zen-of-docs-server"],
            verification_commands=["uvx --from mcp-zen-of-docs mcp-zen-of-docs --help"],
            notes=["Best zero-install path for running the packaged MCP command."],
        ),
        RuntimeTrack(
            runtime="python-poetry",
            setup_steps=[
                "poetry install",
                "poetry run pytest",
                "poetry run ruff check .",
            ],
            verification_commands=["poetry run pytest"],
            notes=["Use when team policy requires Poetry-managed environments."],
        ),
        RuntimeTrack(
            runtime="python-dot-venv",
            setup_steps=[
                "source .venv/bin/activate",
                "python -m pip install -e .",
                "pytest",
            ],
            verification_commands=["pytest"],
            notes=[
                "Use only when the repository is already wired for a pre-activated virtual"
                " environment."
            ],
        ),
    ]
    js_tracks = [
        RuntimeTrack(
            runtime="docusaurus",
            setup_steps=["npm install", "npm run start"],
            verification_commands=["npm run build"],
            notes=["Replace zensical commands with Docusaurus scripts."],
        ),
        RuntimeTrack(
            runtime="vitepress",
            setup_steps=["pnpm install", "pnpm docs:dev"],
            verification_commands=["pnpm docs:build"],
            notes=["Use markdown-it plugins for richer primitive coverage."],
        ),
        RuntimeTrack(
            runtime="starlight",
            setup_steps=["pnpm install", "pnpm astro dev"],
            verification_commands=["pnpm astro check", "pnpm astro build"],
            notes=["Use Astro markdown pipeline for remark/rehype customization."],
        ),
    ]
    follow_up_questions = [
        "Do you need uv-managed commands, poetry commands, or a pre-activated .venv path?",
        (
            "Which JS/TS docs framework should replace zensical commands (Docusaurus,"
            " VitePress, or Starlight)?"
        ),
        "Where will you define canonical-source docs ownership and review expectations?",
        "Which audience and prerequisites should be mandatory in your docs templates?",
    ]
    return python_tracks, js_tracks, follow_up_questions


def get_runtime_onboarding_matrix() -> RuntimeOnboardingMatrixResponse:
    """Return runtime onboarding matrix for Python and JS/TS documentation ecosystems."""
    python_tracks, js_tracks, follow_up_questions = _runtime_onboarding_tracks()
    return RuntimeOnboardingMatrixResponse(
        status="success",
        python_tracks=python_tracks,
        js_tracks=js_tracks,
        follow_up_questions=follow_up_questions,
    )


def list_authoring_primitives() -> PrimitiveCatalogResponse:
    """List all primitives and support coverage across registered frameworks.

    Returns:
        Response containing the full list of authoring primitives, registered
        framework names, and a support matrix mapping each primitive to its
        support level per framework.
    """
    frameworks = list_supported_frameworks()
    return PrimitiveCatalogResponse(
        status="success",
        primitives=list_all_primitives(),
        frameworks=frameworks,
        support_matrix=build_framework_support_matrix(frameworks),
    )


def detect_framework(project_root: Path | str = ".") -> DetectFrameworkResponse:
    """Detect framework candidates from project configuration signals.

    Scans the project root for configuration files (``mkdocs.yml``,
    ``zensical.toml``, ``docusaurus.config.*``, etc.) and ranks detected
    frameworks by confidence score.

    Args:
        project_root: Path to the project root directory to inspect.
            Defaults to the current working directory (``"."``).

    Returns:
        Response with the best-match framework detection result, all ranked
        candidates, and an error message when the root does not exist.
    """
    request = DetectFrameworkRequest(project_root=Path(project_root))
    root = request.project_root
    if not root.exists():
        return DetectFrameworkResponse(
            status="error",
            project_root=request.project_root,
            message="project_root does not exist.",
        )

    snapshot = capture_framework_detection_snapshot(root)
    return DetectFrameworkResponse(
        status="success",
        project_root=request.project_root,
        best_match=snapshot.candidate,
        candidates=snapshot.candidates,
    )


def lookup_primitive_support(
    framework: FrameworkName | str,
    primitive: AuthoringPrimitive | str,
) -> PrimitiveSupportLookupResponse:
    """Lookup support level for a primitive in a given framework.

    Args:
        framework: Target framework identifier (``FrameworkName`` or its
            string value).
        primitive: Authoring primitive to query (``AuthoringPrimitive`` or
            its string value).

    Returns:
        Response containing the resolved framework, primitive, and their
        support level classification.
    """
    request = PrimitiveSupportLookupRequest(
        framework=_coerce_framework_name(framework),
        primitive=_coerce_primitive(primitive),
    )
    return PrimitiveSupportLookupResponse(
        status="success",
        framework=request.framework,
        primitive=request.primitive,
        support_level=lookup_support_level(request.framework, request.primitive),
    )


def render_framework_primitive(
    framework: FrameworkName | str,
    primitive: AuthoringPrimitive | str,
    topic: str | None = None,
) -> RenderPrimitiveSnippetResponse:
    """Render framework-specific snippet for a primitive.

    Args:
        framework: Target framework identifier (``FrameworkName`` or its
            string value).
        primitive: Authoring primitive to render (``AuthoringPrimitive`` or
            its string value).
        topic: Optional topic context used to customise the rendered snippet.
            Defaults to ``None``.

    Returns:
        Response containing the rendered snippet string, support level, and a
        warning message when no snippet is available for the primitive.
    """
    request = RenderPrimitiveSnippetRequest(
        framework=_coerce_framework_name(framework),
        primitive=_coerce_primitive(primitive),
        topic=topic,
    )
    snippet = render_primitive_for_framework(
        request.framework, request.primitive, topic=request.topic
    )
    support = lookup_support_level(request.framework, request.primitive)
    status = "success" if snippet is not None else "warning"
    message = None if snippet is not None else "No snippet available for the requested primitive."
    return RenderPrimitiveSnippetResponse(
        status=status,
        framework=request.framework,
        primitive=request.primitive,
        support_level=support,
        snippet=snippet,
        message=message,
    )


def translate_primitive_syntax(
    source_framework: FrameworkName | str,
    target_framework: FrameworkName | str,
    primitive: AuthoringPrimitive | str,
    topic: str | None = None,
) -> TranslatePrimitiveSyntaxResponse:
    """Provide primitive syntax migration guidance between two frameworks.

    Compares the primitive's rendering in both frameworks and derives
    actionable migration hints using domain translation rules.

    Args:
        source_framework: Framework to migrate from (``FrameworkName`` or
            its string value).
        target_framework: Framework to migrate to (``FrameworkName`` or its
            string value).
        primitive: Authoring primitive to translate (``AuthoringPrimitive``
            or its string value).
        topic: Optional topic context for snippet rendering. Defaults to
            ``None``.

    Returns:
        Response containing source and target support levels, rendered
        snippets for both frameworks, and ordered migration hints.
    """
    request = TranslatePrimitiveSyntaxRequest(
        source_framework=_coerce_framework_name(source_framework),
        target_framework=_coerce_framework_name(target_framework),
        primitive=_coerce_primitive(primitive),
        topic=topic,
    )
    guidance = translate_primitive_between_frameworks(
        request.primitive,
        source_framework=request.source_framework,
        target_framework=request.target_framework,
        topic=request.topic,
    )
    return TranslatePrimitiveSyntaxResponse(
        status="success",
        source_framework=request.source_framework,
        target_framework=request.target_framework,
        primitive=request.primitive,
        source_support_level=guidance.source_support_level,
        target_support_level=guidance.target_support_level,
        source_snippet=guidance.source_snippet,
        target_snippet=guidance.target_snippet,
        hints=guidance.hints,
    )


# ---------------------------------------------------------------------------
# Create Instruction / Prompt / Agent implementations
# ---------------------------------------------------------------------------


def _write_yaml_frontmatter(fields: dict[str, object]) -> str:
    """Render a YAML frontmatter block from a dict of fields."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            # Use flow-style sequence with quoted strings to avoid YAML alias conflicts.
            items = ", ".join(f'"{item}"' for item in value)
            lines.append(f"{key}: [{items}]")
        else:
            lines.append(f"{key}: {value!r}" if isinstance(value, str) else f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def create_instruction_impl(
    request: CreateInstructionRequest,
) -> CreateInstructionResponse:
    """Create a ``*.instructions.md`` file with proper YAML frontmatter."""
    root = resolve_project_root(str(request.project_root))
    target_dir = Path(root) / ".github" / "instructions"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{request.file_stem}.instructions.md"
    target_path = target_dir / filename

    if target_path.exists() and not request.overwrite:
        return CreateInstructionResponse(
            status="warning",
            file_path=target_path,
            file_stem=request.file_stem,
            apply_to=request.apply_to,
            message=f"File already exists: {target_path}. Set overwrite=True to replace.",
        )

    frontmatter = _write_yaml_frontmatter({"applyTo": request.apply_to})
    body = f"{frontmatter}\n\n# {request.title}\n\n{request.content}\n"
    target_path.write_text(body, encoding="utf-8")

    return CreateInstructionResponse(
        status="success",
        file_path=target_path,
        file_stem=request.file_stem,
        apply_to=request.apply_to,
        message=f"Created {target_path}",
    )


def create_prompt_impl(
    request: CreatePromptRequest,
) -> CreatePromptResponse:
    """Create a ``*.prompt.md`` file with proper YAML frontmatter."""
    root = resolve_project_root(str(request.project_root))
    target_dir = Path(root) / ".github" / "prompts"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{request.file_stem}.prompt.md"
    target_path = target_dir / filename

    if target_path.exists() and not request.overwrite:
        return CreatePromptResponse(
            status="warning",
            file_path=target_path,
            file_stem=request.file_stem,
            agent=request.agent,
            message=f"File already exists: {target_path}. Set overwrite=True to replace.",
        )

    frontmatter = _write_yaml_frontmatter(
        {
            "mode": str(request.agent),
            "tools": request.tools,
            "description": request.description,
        }
    )
    body = f"{frontmatter}\n\n{request.content}\n"
    target_path.write_text(body, encoding="utf-8")

    return CreatePromptResponse(
        status="success",
        file_path=target_path,
        file_stem=request.file_stem,
        agent=request.agent,
        message=f"Created {target_path}",
    )


def create_agent_impl(
    request: CreateAgentRequest,
) -> CreateAgentResponse:
    """Create a ``*.agent.md`` file with proper YAML frontmatter."""
    root = resolve_project_root(str(request.project_root))
    target_dir = Path(root) / ".github" / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{request.agent_name}.agent.md"
    target_path = target_dir / filename

    if target_path.exists() and not request.overwrite:
        return CreateAgentResponse(
            status="warning",
            file_path=target_path,
            agent_name=request.agent_name,
            message=f"File already exists: {target_path}. Set overwrite=True to replace.",
        )

    fm_fields: dict[str, object] = {
        "agents": request.agents,
        "name": request.agent_name,
        "description": request.description,
        "tools": request.tools,
    }

    frontmatter = _write_yaml_frontmatter(fm_fields)
    body = f"{frontmatter}\n\n{request.content}\n"
    target_path.write_text(body, encoding="utf-8")

    return CreateAgentResponse(
        status="success",
        file_path=target_path,
        agent_name=request.agent_name,
        message=f"Created {target_path}",
    )


def create_copilot_artifact_impl(
    request: CreateCopilotArtifactRequest,
) -> CreateCopilotArtifactResponse:
    """Consolidated dispatcher: create an instruction, prompt, or agent artifact."""
    if request.kind == CopilotArtifactKind.INSTRUCTION:
        sub = CreateInstructionRequest(
            file_stem=request.file_stem,
            title=request.title or request.file_stem,
            content=request.content,
            apply_to=request.apply_to,
            project_root=request.project_root,
            overwrite=request.overwrite,
        )
        result = create_instruction_impl(sub)
        return CreateCopilotArtifactResponse(
            status=result.status,
            kind=request.kind,
            file_path=result.file_path,
            file_stem=request.file_stem,
            message=result.message,
        )
    if request.kind == CopilotArtifactKind.PROMPT:
        sub_prompt = CreatePromptRequest(
            file_stem=request.file_stem,
            description=request.description or "",
            content=request.content,
            agent=request.agent,
            tools=request.tools,
            project_root=request.project_root,
            overwrite=request.overwrite,
        )
        result_prompt = create_prompt_impl(sub_prompt)
        return CreateCopilotArtifactResponse(
            status=result_prompt.status,
            kind=request.kind,
            file_path=result_prompt.file_path,
            file_stem=request.file_stem,
            message=result_prompt.message,
        )
    # CopilotArtifactKind.AGENT
    sub_agent = CreateAgentRequest(
        agent_name=request.file_stem,
        description=request.description or "",
        agents=request.agents,
        content=request.content,
        tools=request.tools,
        project_root=request.project_root,
        overwrite=request.overwrite,
    )
    result_agent = create_agent_impl(sub_agent)
    return CreateCopilotArtifactResponse(
        status=result_agent.status,
        kind=request.kind,
        file_path=result_agent.file_path,
        file_stem=request.file_stem,
        message=result_agent.message,
    )


# ---------------------------------------------------------------------------
# Ephemeral uvx/npx install-in-tmp-and-copy
# ---------------------------------------------------------------------------


def _build_ephemeral_cmd(request: EphemeralInstallRequest, _tmp_dir: Path) -> list[str]:
    """Build the shell command for an ephemeral install run."""
    if request.installer == "uvx":
        # uvx runs CLI tools in isolated envs: uvx <command> <args>
        return ["uvx", request.command, *request.args]
    return ["npx", "--yes", request.package, *request.args]


def _copy_ephemeral_artifacts(
    tmp_dir: Path,
    resolved_root: Path,
    patterns: list[str],
) -> list[Path]:
    """Copy matching artifacts from *tmp_dir* back to *resolved_root*."""
    copied: list[Path] = []
    for pattern in patterns:
        src_path = tmp_dir / pattern
        if src_path.is_dir():
            dest_path = resolved_root / pattern
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            copied.append(dest_path)
        elif src_path.is_file():
            dest_path = resolved_root / pattern
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            copied.append(dest_path)
        else:
            for match_path in tmp_dir.glob(pattern):
                rel = match_path.relative_to(tmp_dir)
                dest = resolved_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if match_path.is_dir():
                    shutil.copytree(match_path, dest)
                else:
                    shutil.copy2(match_path, dest)
                copied.append(dest)
    return copied


def run_ephemeral_install(
    request: EphemeralInstallRequest,
) -> EphemeralInstallResponse:
    """Install a package in a temporary directory, run it, and copy artifacts back.

    This implements the "npx / uvx tmp-and-copy" pattern:

    1. Create a temporary directory.
    2. ``uvx install <package>`` (or ``npx --yes <package>``) into that directory.
    3. Run the command with the supplied args (cwd = tmp dir).
    4. Copy ``copy_artifacts`` globs back to ``project_root``.
    5. Clean up the temporary directory on success.
    """
    resolved_root = resolve_project_root(request.project_root)
    if not resolved_root.exists() or not resolved_root.is_dir():
        return EphemeralInstallResponse(
            status="error",
            installer=request.installer,
            package=request.package,
            message="project_root must exist and be a directory.",
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="zen-docs-ephemeral-"))
    try:
        install_cmd = _build_ephemeral_cmd(request, tmp_dir)
        result = subprocess.run(  # noqa: S603
            install_cmd,
            cwd=str(tmp_dir),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            input=request.stdin_input,
        )
        if result.returncode != 0:
            return EphemeralInstallResponse(
                status="error",
                installer=request.installer,
                package=request.package,
                tmp_dir=tmp_dir,
                message=(
                    f"Ephemeral install failed (exit {result.returncode}):\n{result.stderr.strip()}"
                ),
            )

        # Resolve the source directory — strip source_subdir prefix if set
        src_base = tmp_dir / request.source_subdir if request.source_subdir else tmp_dir
        copied = _copy_ephemeral_artifacts(src_base, resolved_root, request.copy_artifacts)
        return EphemeralInstallResponse(
            status="success",
            installer=request.installer,
            package=request.package,
            copied_artifacts=copied,
            message=(
                f"Ephemeral {request.installer} run completed. "
                f"Copied {len(copied)} artifact(s) to {resolved_root}."
            ),
        )
    except subprocess.TimeoutExpired:
        return EphemeralInstallResponse(
            status="error",
            installer=request.installer,
            package=request.package,
            tmp_dir=tmp_dir,
            message="Ephemeral install timed out after 120 seconds.",
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def init_framework_structure_impl(
    request: InitFrameworkStructureRequest,
) -> InitFrameworkStructureResponse:
    """Initialise a framework's canonical folder structure using its native CLI.

    Looks up ``FRAMEWORK_INIT_SPECS[request.framework]``, runs the official
    init command in an isolated temp directory via the
    ``run_ephemeral_install`` tmp-and-copy pattern, and copies the resulting
    scaffold back to ``project_root``.

    Args:
        request: Framework, project root, and overwrite flag.

    Returns:
        ``InitFrameworkStructureResponse`` with status, docs_root, and
        the list of copied artifacts.
    """
    spec = FRAMEWORK_INIT_SPECS.get(request.framework)
    if spec is None:
        return InitFrameworkStructureResponse(
            status="error",
            framework=request.framework,
            docs_root=Path("docs"),
            cli_command="",
            message=(
                f"No init spec registered for framework '{request.framework}'. "
                f"Supported: {[f.value for f in FRAMEWORK_INIT_SPECS]}"
            ),
        )

    cli_command = " ".join([spec.installer, spec.command, *spec.init_args])

    ephemeral_req = EphemeralInstallRequest(
        installer=spec.installer,
        package=spec.package,
        command=spec.command,
        args=spec.init_args,
        copy_artifacts=spec.copy_artifacts,
        project_root=request.project_root,
        source_subdir=spec.source_subdir,
        stdin_input=spec.stdin_input,
    )

    result = run_ephemeral_install(ephemeral_req)

    if result.status != "success":
        return InitFrameworkStructureResponse(
            status="error",
            framework=request.framework,
            docs_root=spec.docs_root,
            cli_command=cli_command,
            copied_artifacts=[],
            message=result.message,
        )

    return InitFrameworkStructureResponse(
        status="success",
        framework=request.framework,
        docs_root=spec.docs_root,
        cli_command=cli_command,
        copied_artifacts=result.copied_artifacts,
        message=(
            f"Initialised {request.framework} structure. "
            f"Docs root: {spec.docs_root}. "
            f"Copied {len(result.copied_artifacts)} artifact(s)."
        ),
    )


_TODO_PATTERNS = (
    re.compile(r"<!--\s*TODO.*?-->", re.IGNORECASE),
    re.compile(r"TODO:\s*add content\.?", re.IGNORECASE),
    re.compile(r"_TODO:.*", re.IGNORECASE),
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


def _replace_section_body(
    result_lines: list[str],
    section_body_start: int,
    new_content: str,
) -> None:
    """Replace lines from *section_body_start* onward with *new_content*."""
    del result_lines[section_body_start:]
    text = new_content if new_content.endswith("\n") else new_content + "\n"
    result_lines.append("\n")
    result_lines.append(text)
    result_lines.append("\n")


def _process_section(  # noqa: PLR0913
    *,
    heading_text: str,
    result_lines: list[str],
    section_body_start: int,
    section_body: list[str],
    content: str,
    overwrite: bool,
    enriched: list[str],
    skipped: list[str],
) -> None:
    """Decide whether to enrich or skip a single section."""
    body_text = "".join(section_body)
    has_todo = any(p.search(body_text) for p in _TODO_PATTERNS)

    if (has_todo and content) or (not has_todo and overwrite and content):
        _replace_section_body(result_lines, section_body_start, content)
        enriched.append(heading_text)
    else:
        skipped.append(heading_text)


def enrich_doc(
    doc_path: Path | str,
    *,
    content: str = "",
    framework: FrameworkName | None = None,
    sections_to_enrich: list[str] | None = None,
    overwrite: bool = False,
) -> EnrichDocResponse:
    """Replace TODO placeholder sections in a scaffold document with provided content.

    Args:
        doc_path: Path to the existing document to enrich.
        content: Additional content to incorporate into TODO sections.
        framework: Target framework. Auto-detected when omitted.
        sections_to_enrich: Specific section headings to enrich.
            Enriches all TODO sections when empty.
        overwrite: Whether to overwrite existing non-TODO content.

    Returns:
        EnrichDocResponse with enrichment statistics.
    """
    request = EnrichDocRequest(
        doc_path=Path(doc_path),
        content=content,
        framework=framework,
        sections_to_enrich=sections_to_enrich or [],
        overwrite=overwrite,
    )
    target = request.doc_path
    if not target.exists():
        return EnrichDocResponse(
            status="error",
            doc_path=str(target),
            message=f"Document not found: {target}",
        )

    original_text = target.read_text(encoding="utf-8")
    lines = original_text.splitlines(keepends=True)
    target_sections = {s.strip().lower() for s in request.sections_to_enrich}
    enriched: list[str] = []
    skipped: list[str] = []

    i = 0
    result_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        heading_match = _HEADING_RE.match(line.rstrip("\n\r"))
        if heading_match:
            heading_text = heading_match.group(2).strip()
            # Check if this section should be enriched
            if target_sections and heading_text.lower() not in target_sections:
                result_lines.append(line)
                i += 1
                continue

            # Collect the section body (lines until next heading or EOF)
            result_lines.append(line)
            i += 1
            section_body_start = len(result_lines)
            while i < len(lines):
                next_heading = _HEADING_RE.match(lines[i].rstrip("\n\r"))
                if next_heading:
                    break
                result_lines.append(lines[i])
                i += 1
            section_body = result_lines[section_body_start:]

            # Determine if section contains TODO placeholders
            _process_section(
                heading_text=heading_text,
                result_lines=result_lines,
                section_body_start=section_body_start,
                section_body=section_body,
                content=request.content,
                overwrite=request.overwrite,
                enriched=enriched,
                skipped=skipped,
            )
        else:
            result_lines.append(line)
            i += 1

    new_text = "".join(result_lines)
    content_added = new_text != original_text
    if content_added:
        target.write_text(new_text, encoding="utf-8")

    return EnrichDocResponse(
        status="success",
        doc_path=str(target),
        sections_enriched=enriched,
        sections_skipped=skipped,
        content_added=content_added,
        message=f"Enriched {len(enriched)} section(s)." if enriched else "No sections enriched.",
    )


# ---------------------------------------------------------------------------
# plan_docs — structured page plan with dependencies
# ---------------------------------------------------------------------------

_FULL_SECTIONS: list[dict[str, object]] = [
    {
        "slug": "index",
        "title": "Home",
        "description": "Project overview, value proposition, and navigation entry point.",
        "primitives": [
            AuthoringPrimitive.FRONTMATTER,
            AuthoringPrimitive.HEADING_H1,
            AuthoringPrimitive.BADGE,
        ],
        "dependencies": [],
        "priority": "high",
    },
    {
        "slug": "quickstart",
        "title": "Quickstart",
        "description": "Step-by-step guide for first-time users to get started quickly.",
        "primitives": [
            AuthoringPrimitive.STEP_LIST,
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.ADMONITION,
        ],
        "dependencies": ["index"],
        "priority": "high",
    },
    {
        "slug": "architecture",
        "title": "Architecture",
        "description": "High-level system design, component relationships, and data flow.",
        "primitives": [
            AuthoringPrimitive.DIAGRAM,
            AuthoringPrimitive.HEADING_H1,
            AuthoringPrimitive.IMAGE,
        ],
        "dependencies": ["index"],
        "priority": "medium",
    },
    {
        "slug": "api",
        "title": "API Reference",
        "description": "Comprehensive API endpoint documentation with request/response examples.",
        "primitives": [
            AuthoringPrimitive.API_ENDPOINT,
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.TABLE,
        ],
        "dependencies": ["quickstart"],
        "priority": "medium",
    },
    {
        "slug": "contributing",
        "title": "Contributing",
        "description": "Contribution guidelines, development workflow, and code standards.",
        "primitives": [
            AuthoringPrimitive.STEP_LIST,
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.TASK_LIST,
        ],
        "dependencies": ["index"],
        "priority": "medium",
    },
    {
        "slug": "deployment",
        "title": "Deployment",
        "description": (
            "Deployment procedures, environment configuration, and infrastructure setup."
        ),
        "primitives": [
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.ADMONITION,
            AuthoringPrimitive.TABS,
        ],
        "dependencies": ["quickstart"],
        "priority": "medium",
    },
    {
        "slug": "troubleshooting",
        "title": "Troubleshooting",
        "description": "Common issues, error messages, and diagnostic procedures.",
        "primitives": [
            AuthoringPrimitive.ADMONITION,
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.TABLE,
        ],
        "dependencies": ["quickstart"],
        "priority": "low",
    },
    {
        "slug": "changelog",
        "title": "Changelog",
        "description": "Version history, breaking changes, and migration notes.",
        "primitives": [
            AuthoringPrimitive.HEADING_H1,
            AuthoringPrimitive.LINK,
            AuthoringPrimitive.BADGE,
        ],
        "dependencies": ["index"],
        "priority": "low",
    },
    {
        "slug": "standards",
        "title": "Standards",
        "description": "Coding standards, documentation conventions, and style guides.",
        "primitives": [
            AuthoringPrimitive.CODE_FENCE,
            AuthoringPrimitive.TABLE,
            AuthoringPrimitive.ADMONITION,
        ],
        "dependencies": ["contributing"],
        "priority": "low",
    },
]

_SCOPE_SECTIONS: dict[str, list[str]] = {
    "full": [str(s["slug"]) for s in _FULL_SECTIONS],
    "api-only": ["index", "api"],
    "quickstart": ["index", "quickstart"],
}

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


_TOOL_LIST = """\
- detect_docs_context — Detect framework and project structure
- detect_project_readiness — Assess project readiness for docs
- get_authoring_profile — List primitives and framework capabilities
- resolve_primitive — Resolve primitive support for a framework
- translate_primitives — Translate primitives between frameworks
- compose_docs_story — Compose documentation stories
- scaffold_doc — Scaffold a new documentation page
- batch_scaffold_docs — Scaffold multiple pages at once
- enrich_doc — Enrich documentation with metadata
- validate_docs — Validate links, structure, orphans
- score_docs_quality — Score documentation quality
- onboard_project — Full onboarding workflow
- plan_docs — Generate structured page plan
- run_pipeline_phase — Execute a pipeline phase
- generate_agent_config — Generate AI agent configuration
"""


def _copilot_config_content(*, include_tools: bool) -> str:
    """Generate .github/copilot-instructions.md content."""
    tools_section = f"\n## Available MCP Tools\n\n{_TOOL_LIST}" if include_tools else ""
    return (
        "# Copilot Instructions — Documentation Workflow\n\n"
        "This project uses **mcp-zen-of-docs** for documentation.\n\n"
        "## Pipeline Phases\n\n"
        "1. **Detect** — Identify framework and project structure\n"
        "2. **Plan** — Generate structured page plan\n"
        "3. **Scaffold** — Create documentation pages\n"
        "4. **Compose** — Write documentation stories\n"
        "5. **Enrich** — Add metadata and cross-references\n"
        "6. **Validate** — Check links, structure, quality\n"
        "7. **Score** — Measure documentation quality\n"
        f"{tools_section}"
    )


def _cursor_config_content(*, include_tools: bool) -> str:
    """Generate .cursor/rules/zen-docs.mdc content."""
    tools_section = f"\n## MCP Tools\n\n{_TOOL_LIST}" if include_tools else ""
    return (
        "---\n"
        "description: Documentation workflow rules for mcp-zen-of-docs\n"
        "globs: docs/**/*.md\n"
        "---\n\n"
        "# Zen of Docs — Cursor Rules\n\n"
        "Use the mcp-zen-of-docs MCP server for documentation tasks.\n\n"
        "## Workflow\n\n"
        "1. Detect → 2. Plan → 3. Scaffold → 4. Compose → "
        "5. Enrich → 6. Validate → 7. Score\n"
        f"{tools_section}"
    )


def _windsurf_config_content(*, include_tools: bool) -> str:
    """Generate .windsurfrules content."""
    tools_section = f"\n## MCP Tools\n\n{_TOOL_LIST}" if include_tools else ""
    return (
        "# Windsurf Rules — Documentation Workflow\n\n"
        "This project uses **mcp-zen-of-docs** for documentation.\n\n"
        "## Pipeline\n\n"
        "Detect → Plan → Scaffold → Compose → Enrich → Validate → Score\n"
        f"{tools_section}"
    )


def _claude_code_config_content(*, include_tools: bool) -> str:
    """Generate CLAUDE.md content."""
    tools_section = f"\n## MCP Tools\n\n{_TOOL_LIST}" if include_tools else ""
    return (
        "# CLAUDE.md — Documentation Workflow\n\n"
        "This project uses **mcp-zen-of-docs** for documentation.\n\n"
        "## Pipeline Phases\n\n"
        "Detect → Plan → Scaffold → Compose → Enrich → Validate → Score\n"
        f"{tools_section}"
    )


def _generic_config_content(*, include_tools: bool) -> str:
    """Generate platform-agnostic markdown guide."""
    tools_section = f"\n## Available MCP Tools\n\n{_TOOL_LIST}" if include_tools else ""
    return (
        "# Documentation Workflow Guide\n\n"
        "This project uses **mcp-zen-of-docs** MCP server.\n\n"
        "## Pipeline Phases\n\n"
        "1. Detect — Identify framework and project structure\n"
        "2. Plan — Generate structured page plan\n"
        "3. Scaffold — Create documentation pages\n"
        "4. Compose — Write documentation stories\n"
        "5. Enrich — Add metadata and cross-references\n"
        "6. Validate — Check links, structure, quality\n"
        "7. Score — Measure documentation quality\n"
        f"{tools_section}"
    )


_PLATFORM_GENERATORS: dict[AgentPlatform, tuple[str, object]] = {
    AgentPlatform.COPILOT: (".github/copilot-instructions.md", _copilot_config_content),
    AgentPlatform.CURSOR: (".cursor/rules/zen-docs.mdc", _cursor_config_content),
    AgentPlatform.WINDSURF: (".windsurfrules", _windsurf_config_content),
    AgentPlatform.CLAUDE_CODE: ("CLAUDE.md", _claude_code_config_content),
    AgentPlatform.GENERIC: ("zen-docs-guide.md", _generic_config_content),
}


def generate_agent_config(request: AgentConfigRequest) -> AgentConfigResponse:
    """Generate AI agent configuration for docs workflow integration.

    Args:
        request: Agent config request with platform and options.

    Returns:
        AgentConfigResponse with generated config file contents.
    """
    root = Path(request.project_root).expanduser().resolve()
    if not root.exists():
        return AgentConfigResponse(
            status="error",
            platform=request.platform,
            message="project_root does not exist.",
        )

    entry = _PLATFORM_GENERATORS.get(request.platform)
    if entry is None:
        return AgentConfigResponse(
            status="error",
            platform=request.platform,
            message=f"Unsupported platform: {request.platform}",
        )

    file_path, generator_fn = entry
    content = generator_fn(include_tools=request.include_tools)  # type: ignore[operator]

    return AgentConfigResponse(
        status="success",
        platform=request.platform,
        config_files=[{"path": file_path, "content": content}],
        message=f"Generated config for {request.platform}.",
    )


def plan_docs(
    project_root: Path | str = ".",
    framework: FrameworkName | None = None,
    scope: str = "full",
    docs_root: Path | str = Path("docs"),
) -> PlanDocsResponse:
    """Generate a structured documentation page plan with dependencies.

    Takes detect output and produces an ordered list of planned pages,
    each with suggested authoring primitives and dependency information.
    """
    request = PlanDocsRequest(
        project_root=Path(project_root),
        framework=framework,
        scope=scope,
        docs_root=Path(docs_root),
    )

    root = request.project_root.resolve()
    if not root.exists():
        return PlanDocsResponse(
            status="error",
            message="project_root does not exist.",
        )

    resolved_docs_root = root / request.docs_root

    # Auto-detect framework when not specified.
    detected_framework = request.framework
    if detected_framework is None:
        snapshot = capture_framework_detection_snapshot(root)
        if snapshot.candidate is not None:
            detected_framework = snapshot.candidate.framework

    # Determine which sections to include based on scope.
    allowed_slugs = _SCOPE_SECTIONS.get(request.scope, _SCOPE_SECTIONS["full"])
    sections = [s for s in _FULL_SECTIONS if s["slug"] in allowed_slugs]

    # Scan for existing .md files.
    existing_files: set[str] = set()
    if resolved_docs_root.exists():
        for md_file in resolved_docs_root.rglob("*.md"):
            existing_files.add(str(md_file.relative_to(root)))

    pages: list[PlannedPage] = []
    for section in sections:
        slug: str = section["slug"]  # type: ignore[assignment]
        rel_path = str(request.docs_root / f"{slug}.md")
        dep_paths = [
            str(request.docs_root / f"{d}.md")
            for d in section["dependencies"]  # type: ignore[union-attr]
            if d in allowed_slugs
        ]
        pages.append(
            PlannedPage(
                path=rel_path,
                title=section["title"],  # type: ignore[arg-type]
                description=section["description"],  # type: ignore[arg-type]
                suggested_primitives=list(section["primitives"]),  # type: ignore[arg-type]
                dependencies=dep_paths,
                priority=section["priority"],  # type: ignore[arg-type]
                exists=rel_path in existing_files,
            )
        )

    # Sort by priority then dependency order.
    pages.sort(key=lambda p: (_PRIORITY_ORDER.get(p.priority, 1), len(p.dependencies)))

    existing_count = sum(1 for p in pages if p.exists)
    return PlanDocsResponse(
        status="success",
        framework=detected_framework,
        pages=pages,
        total_pages=len(pages),
        existing_pages=existing_count,
        new_pages=len(pages) - existing_count,
        message=f"Planned {len(pages)} page(s) for scope '{request.scope}'.",
    )


# ---------------------------------------------------------------------------
# Pipeline phase execution
# ---------------------------------------------------------------------------

_PHASE_ORDER: list[PipelinePhase] = [
    PipelinePhase.CONSTITUTION,
    PipelinePhase.SPECIFY,
    PipelinePhase.PLAN,
    PipelinePhase.TASKS,
    PipelinePhase.IMPLEMENT,
]

_PHASE_ARTIFACTS: dict[PipelinePhase, str] = {
    PipelinePhase.CONSTITUTION: "constitution.md",
    PipelinePhase.SPECIFY: "spec.md",
    PipelinePhase.PLAN: "plan.md",
    PipelinePhase.TASKS: "tasks.md",
    PipelinePhase.IMPLEMENT: "implement-log.md",
}


def _sha256(content: str) -> str:
    """Return hex SHA-256 digest for *content*."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _previous_phase(phase: PipelinePhase) -> PipelinePhase | None:
    """Return the phase that must precede *phase*, or ``None`` for constitution."""
    idx = _PHASE_ORDER.index(phase)
    return _PHASE_ORDER[idx - 1] if idx > 0 else None


def _next_phase(phase: PipelinePhase) -> PipelinePhase | None:
    """Return the phase that follows *phase*, or ``None`` for implement."""
    idx = _PHASE_ORDER.index(phase)
    return _PHASE_ORDER[idx + 1] if idx < len(_PHASE_ORDER) - 1 else None


def _write_artifact(artifacts_dir: Path, filename: str, content: str) -> PhaseArtifact:
    """Write *content* to *artifacts_dir/filename* and return a ``PhaseArtifact``."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    target = artifacts_dir / filename
    target.write_text(content, encoding="utf-8")
    phase_key = next(p for p, f in _PHASE_ARTIFACTS.items() if f == filename)
    return PhaseArtifact(
        phase=phase_key,
        path=str(target),
        content_hash=_sha256(content),
    )


def _run_constitution(root: Path, artifacts_dir: Path) -> PipelinePhaseResponse:
    """Generate constitution.md with project docs quality standards."""
    snapshot = capture_framework_detection_snapshot(root)
    framework = snapshot.candidate.framework if snapshot.candidate else "unknown"
    docs_root = root / "docs"
    existing_pages = list(docs_root.rglob("*.md")) if docs_root.exists() else []
    content = (
        "# Documentation Constitution\n\n"
        f"**Framework**: {framework}\n"
        f"**Project root**: {root}\n"
        f"**Existing docs**: {len(existing_pages)} page(s)\n\n"
        "## Quality Standards\n\n"
        "1. Every page has a clear purpose and audience.\n"
        "2. Use framework-native authoring primitives.\n"
        "3. Keep navigation flat and scannable.\n"
        "4. Validate links and structure before committing.\n"
        "5. Code examples must be runnable.\n"
        "6. One topic per page with clear heading hierarchy.\n"
    )
    artifact = _write_artifact(artifacts_dir, "constitution.md", content)
    return PipelinePhaseResponse(
        status="success",
        phase=PipelinePhase.CONSTITUTION,
        phase_status=PipelinePhaseStatus.DONE,
        artifacts=[artifact],
        next_phase=_next_phase(PipelinePhase.CONSTITUTION),
        message="Constitution created with project docs quality standards.",
        pipeline_context=PipelineContext(
            framework=snapshot.candidate.framework if snapshot.candidate else None,
            project_root=root,
            docs_root=docs_root,
            last_tool="run_pipeline_phase",
        ),
    )


def _run_specify(root: Path, artifacts_dir: Path) -> PipelinePhaseResponse:
    """Generate spec.md based on constitution and existing docs."""
    constitution_path = artifacts_dir / "constitution.md"
    constitution = constitution_path.read_text(encoding="utf-8")
    docs_root = root / "docs"
    existing = (
        sorted(str(p.relative_to(root)) for p in docs_root.rglob("*.md"))
        if docs_root.exists()
        else []
    )
    content = (
        "# Documentation Specification\n\n"
        "## Source\n\n"
        f"Based on constitution at `{constitution_path}`.\n\n"
        "## Existing Pages\n\n"
        + ("\n".join(f"- `{p}`" for p in existing) if existing else "- _None found._\n")
        + "\n\n## Gaps\n\n"
        "- Review constitution standards against existing pages.\n"
        "- Identify missing sections and outdated content.\n"
    )
    _ = constitution  # read to confirm dependency
    artifact = _write_artifact(artifacts_dir, "spec.md", content)
    return PipelinePhaseResponse(
        status="success",
        phase=PipelinePhase.SPECIFY,
        phase_status=PipelinePhaseStatus.DONE,
        artifacts=[artifact],
        next_phase=_next_phase(PipelinePhase.SPECIFY),
        message="Specification created from constitution and docs scan.",
    )


def _run_plan(root: Path, artifacts_dir: Path) -> PipelinePhaseResponse:
    """Generate plan.md using existing plan_docs logic."""
    plan_result = plan_docs(project_root=root)
    lines = ["# Documentation Plan\n"]
    for page in plan_result.pages:
        status = "✅ exists" if page.exists else "🆕 new"
        lines.append(f"- **{page.title}** (`{page.path}`) — {status}")
    lines.append(
        f"\n**Total**: {plan_result.total_pages} pages "
        f"({plan_result.existing_pages} existing, {plan_result.new_pages} new)\n"
    )
    content = "\n".join(lines)
    artifact = _write_artifact(artifacts_dir, "plan.md", content)
    return PipelinePhaseResponse(
        status="success",
        phase=PipelinePhase.PLAN,
        phase_status=PipelinePhaseStatus.DONE,
        artifacts=[artifact],
        next_phase=_next_phase(PipelinePhase.PLAN),
        message=f"Plan created with {plan_result.total_pages} page(s).",
    )


def _run_tasks(root: Path, artifacts_dir: Path) -> PipelinePhaseResponse:
    """Generate tasks.md from the plan with actionable items."""
    plan_path = artifacts_dir / "plan.md"
    plan_content = plan_path.read_text(encoding="utf-8")
    plan_result = plan_docs(project_root=root)
    lines = ["# Documentation Tasks\n"]
    for idx, page in enumerate(plan_result.pages, 1):
        if page.exists:
            lines.append(f"- [ ] Task {idx}: Enrich `{page.path}` — {page.title}")
        else:
            lines.append(f"- [ ] Task {idx}: Scaffold `{page.path}` — {page.title}")
    lines.append("")
    _ = plan_content  # read to confirm dependency
    content = "\n".join(lines)
    artifact = _write_artifact(artifacts_dir, "tasks.md", content)
    return PipelinePhaseResponse(
        status="success",
        phase=PipelinePhase.TASKS,
        phase_status=PipelinePhaseStatus.DONE,
        artifacts=[artifact],
        next_phase=_next_phase(PipelinePhase.TASKS),
        message=f"Task list created with {len(plan_result.pages)} task(s).",
    )


def _run_implement(root: Path, artifacts_dir: Path) -> PipelinePhaseResponse:
    """Execute scaffold/enrich for tasks and log results."""
    tasks_path = artifacts_dir / "tasks.md"
    _ = tasks_path.read_text(encoding="utf-8")
    plan_result = plan_docs(project_root=root)
    log_lines = ["# Implementation Log\n"]
    for page in plan_result.pages:
        if page.exists:
            log_lines.append(f"- ✅ `{page.path}` — already exists, enrich pending.")
        else:
            log_lines.append(f"- 🆕 `{page.path}` — scaffold pending.")
    log_lines.append("")
    content = "\n".join(log_lines)
    artifact = _write_artifact(artifacts_dir, "implement-log.md", content)
    return PipelinePhaseResponse(
        status="success",
        phase=PipelinePhase.IMPLEMENT,
        phase_status=PipelinePhaseStatus.DONE,
        artifacts=[artifact],
        next_phase=None,
        message="Implementation log created. Pipeline complete.",
    )


def run_pipeline_phase(request: PipelinePhaseRequest) -> PipelinePhaseResponse:
    """Execute a single pipeline phase with artifact gating.

    Args:
        request: Pipeline phase request with phase, project root, and options.

    Returns:
        PipelinePhaseResponse with artifacts, status, and next phase.
    """
    root = Path(request.project_root).expanduser().resolve()
    artifacts_dir = root / request.artifacts_dir

    # Check prerequisite artifact exists (unless constitution or force).
    prev = _previous_phase(request.phase)
    if prev is not None and not request.force:
        prev_artifact = artifacts_dir / _PHASE_ARTIFACTS[prev]
        if not prev_artifact.exists():
            return PipelinePhaseResponse(
                status="error",
                phase=request.phase,
                phase_status=PipelinePhaseStatus.BLOCKED,
                message=(
                    f"Phase '{request.phase}' blocked: "
                    f"missing prerequisite '{prev_artifact.name}' from '{prev}' phase."
                ),
            )

    # Skip if artifact already exists and not forced.
    current_artifact = artifacts_dir / _PHASE_ARTIFACTS[request.phase]
    if current_artifact.exists() and not request.force:
        existing_content = current_artifact.read_text(encoding="utf-8")
        return PipelinePhaseResponse(
            status="success",
            phase=request.phase,
            phase_status=PipelinePhaseStatus.DONE,
            artifacts=[
                PhaseArtifact(
                    phase=request.phase,
                    path=str(current_artifact),
                    content_hash=_sha256(existing_content),
                )
            ],
            next_phase=_next_phase(request.phase),
            message=f"Phase '{request.phase}' already complete. Use force=True to re-run.",
        )

    phase_runners = {
        PipelinePhase.CONSTITUTION: _run_constitution,
        PipelinePhase.SPECIFY: _run_specify,
        PipelinePhase.PLAN: _run_plan,
        PipelinePhase.TASKS: _run_tasks,
        PipelinePhase.IMPLEMENT: _run_implement,
    }
    runner = phase_runners[request.phase]
    return runner(root, artifacts_dir)


# ---------------------------------------------------------------------------
# generate_visual_asset — parametric SVG templates
# ---------------------------------------------------------------------------

_SVG_CANVAS: dict[str, tuple[int, int]] = {
    "header": (1440, 560),
    "social-card": (1200, 630),
    "icon": (64, 64),
    "icons": (64, 64),  # alias for VisualAssetKind.ICONS = "icons"
    "favicon": (32, 32),
    "badge": (80, 20),
    "toc": (800, 480),
}

_SVG_HEADER_TMPL = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{primary};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{bg};stop-opacity:1"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-family="system-ui, sans-serif" font-size="{fs}" font-weight="700"
        fill="white" opacity="0.95">{title}</text>
  {subtitle_elem}
</svg>"""

_SVG_ICON_TMPL = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" rx="{rx}" fill="{primary}"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-family="system-ui, sans-serif" font-size="{fs}" fill="white">{glyph}</text>
</svg>"""

_SVG_TOC_TMPL = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" fill="{bg}"/>
  <text x="40" y="48" font-family="system-ui, sans-serif" font-size="22"
        font-weight="700" fill="{primary}">{title}</text>
  <line x1="40" y1="64" x2="{lx}" y2="64" stroke="{primary}" stroke-width="2"/>
  <rect x="40" y="88" width="12" height="12" rx="3" fill="{primary}"/>
  <rect x="60" y="90" width="200" height="8" rx="4" fill="{primary}" opacity="0.4"/>
  <rect x="40" y="118" width="12" height="12" rx="3" fill="{primary}" opacity="0.7"/>
  <rect x="60" y="120" width="160" height="8" rx="4" fill="{primary}" opacity="0.3"/>
  <rect x="64" y="148" width="12" height="12" rx="3" fill="{primary}" opacity="0.5"/>
  <rect x="84" y="150" width="140" height="8" rx="4" fill="{primary}" opacity="0.2"/>
  <rect x="40" y="178" width="12" height="12" rx="3" fill="{primary}" opacity="0.7"/>
  <rect x="60" y="180" width="180" height="8" rx="4" fill="{primary}" opacity="0.3"/>
  <rect x="64" y="208" width="12" height="12" rx="3" fill="{primary}" opacity="0.5"/>
  <rect x="84" y="210" width="120" height="8" rx="4" fill="{primary}" opacity="0.2"/>
  <rect x="40" y="238" width="12" height="12" rx="3" fill="{primary}" opacity="0.7"/>
  <rect x="60" y="240" width="150" height="8" rx="4" fill="{primary}" opacity="0.3"/>
</svg>"""


def _make_svg(request: GenerateVisualAssetRequest) -> tuple[str, int, int]:
    kind_val = str(request.kind).lower()
    w, h = _SVG_CANVAS.get(kind_val, (800, 400))
    cx, cy = w // 2, h // 2
    title = request.title or "Documentation"
    subtitle = request.subtitle or ""
    primary = request.primary_color
    bg = request.background_color

    subtitle_elem = ""
    if subtitle:
        subtitle_elem = (
            f'<text x="{cx}" y="{cy + 48}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="system-ui, sans-serif" font-size="28" fill="white" opacity="0.75">'
            f"{subtitle}</text>"
        )

    if kind_val in ("icon", "icons", "favicon", "badge"):
        glyph = title[0].upper() if title else "D"
        fs = max(10, w // 3)
        rx = w // 8
        svg = _SVG_ICON_TMPL.format(
            w=w, h=h, rx=rx, cx=cx, cy=cy, fs=fs, primary=primary, glyph=glyph
        )
    elif kind_val == "toc":
        svg = _SVG_TOC_TMPL.format(w=w, h=h, title=title, primary=primary, bg=bg, lx=w - 40)
    else:
        fs = 72 if kind_val == "header" else 56
        svg = _SVG_HEADER_TMPL.format(
            w=w,
            h=h,
            cx=cx,
            cy=cy,
            fs=fs,
            primary=primary,
            bg=bg,
            title=title,
            subtitle_elem=subtitle_elem,
        )
    return svg, w, h


def generate_visual_asset_impl(  # noqa: PLR0911
    request: GenerateVisualAssetRequest,
) -> GenerateVisualAssetResponse:
    """Generate parametric SVG markup or perform a visual asset operation."""
    if request.operation == VisualAssetOperation.PROMPT_SPEC:
        if request.asset_prompt is None:
            return GenerateVisualAssetResponse(
                status="error",
                kind=request.kind,
                operation=request.operation,
                message="asset_prompt is required when operation='prompt_spec'.",
            )
        toolkit = generate_svg_prompt_toolkit_reference(
            asset_kind=request.kind,
            asset_prompt=request.asset_prompt,
            style_notes=request.style_notes,
            target_size_hint=request.target_size_hint,
        )
        return GenerateVisualAssetResponse(
            status=toolkit.status,
            kind=request.kind,
            operation=request.operation,
            svg_prompt_toolkit=toolkit,
            message=toolkit.message,
        )

    if request.operation == VisualAssetOperation.GENERATE_SCRIPTS:
        script_bundle = generate_svg_png_scripts_reference()
        return GenerateVisualAssetResponse(
            status=script_bundle.status,
            kind=request.kind,
            operation=request.operation,
            svg_png_scripts=script_bundle,
            message=script_bundle.message,
        )

    if request.operation == VisualAssetOperation.CONVERT_TO_PNG:
        source_svg_text = request.source_svg
        if source_svg_text is None:
            if request.source_file is None:
                return GenerateVisualAssetResponse(
                    status="error",
                    kind=request.kind,
                    operation=request.operation,
                    message=(
                        "source_svg or source_file is required when operation='convert_to_png'."
                    ),
                )
            source_path = request.source_file.expanduser()
            if not source_path.exists():
                return GenerateVisualAssetResponse(
                    status="error",
                    kind=request.kind,
                    operation=request.operation,
                    message=f"source_file does not exist: {source_path}",
                )
            source_svg_text = source_path.read_text(encoding="utf-8")
        if request.output_path is None:
            return GenerateVisualAssetResponse(
                status="error",
                kind=request.kind,
                operation=request.operation,
                message="output_path is required when operation='convert_to_png'.",
            )
        conversion = convert_svg_to_png_reference(
            asset_kind=request.kind,
            source_svg=source_svg_text,
            output_file=request.output_path,
        )
        return GenerateVisualAssetResponse(
            status=conversion.status,
            kind=request.kind,
            operation=request.operation,
            svg_to_png=conversion,
            message=conversion.message,
        )

    # Default: RENDER operation
    svg_content, w, h = _make_svg(request)
    out_path: str | None = None
    if request.output_path is not None:
        p = request.output_path.expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(svg_content, encoding="utf-8")
        out_path = str(p)
    return GenerateVisualAssetResponse(
        status="success",
        kind=request.kind,
        operation=request.operation,
        svg_content=svg_content,
        canvas_width=w,
        canvas_height=h,
        output_path=out_path,
    )


# ---------------------------------------------------------------------------
# generate_diagram — Mermaid template engine
# ---------------------------------------------------------------------------

_DIAGRAM_TEMPLATES: dict[DiagramType, str] = {
    DiagramType.FLOWCHART: (
        "flowchart TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Action]\n    B -->|No| D[End]"
    ),
    DiagramType.SEQUENCE: (
        "sequenceDiagram\n"
        "    participant Client\n"
        "    participant Server\n"
        "    Client->>Server: Request\n"
        "    Server-->>Client: Response"
    ),
    DiagramType.CLASS: (
        "classDiagram\n"
        "    class Animal {\n"
        "        +String name\n"
        "        +speak() void\n"
        "    }\n"
        "    class Dog {\n"
        "        +fetch() void\n"
        "    }\n"
        "    Animal <|-- Dog"
    ),
    DiagramType.ER: (
        "erDiagram\n    USER ||--o{ ORDER : places\n    ORDER ||--|{ LINE-ITEM : contains"
    ),
    DiagramType.C4_CONTEXT: (
        "C4Context\n"
        "    title System Context\n"
        '    Person(user, "User", "A user of the system")\n'
        '    System(sys, "System", "The system")\n'
        '    Rel(user, sys, "Uses")'
    ),
    DiagramType.GANTT: (
        "gantt\n"
        "    title Project Timeline\n"
        "    dateFormat YYYY-MM-DD\n"
        "    section Phase 1\n"
        "    Task A: 2024-01-01, 7d\n"
        "    Task B: after Task A, 5d"
    ),
    DiagramType.MINDMAP: (
        "mindmap\n  root((Topic))\n    Branch A\n      Leaf 1\n      Leaf 2\n    Branch B"
    ),
    DiagramType.STATE: (
        "stateDiagram-v2\n"
        "    [*] --> Idle\n"
        "    Idle --> Running : start\n"
        "    Running --> Idle : stop\n"
        "    Running --> [*] : finish"
    ),
}

_FRAMEWORK_FENCE_OPEN: dict[str, str] = {
    "zensical": "```mermaid",
    "mkdocs-material": "```mermaid",
    "docusaurus": "```mermaid",
    "vitepress": "```mermaid",
    "starlight": "```mermaid",
}


def generate_diagram_impl(request: GenerateDiagramRequest) -> GenerateDiagramResponse:
    """Generate Mermaid diagram source from a template, optionally wrapped per framework."""
    source = _DIAGRAM_TEMPLATES.get(request.diagram_type, _DIAGRAM_TEMPLATES[DiagramType.FLOWCHART])
    if request.title:
        # Prepend a title comment in Mermaid style
        source = f"---\ntitle: {request.title}\n---\n" + source

    fence_open = "```mermaid"
    snippet = f"{fence_open}\n{source}\n```"

    return GenerateDiagramResponse(
        status="success",
        diagram_type=request.diagram_type,
        mermaid_source=source,
        framework_snippet=snippet,
        framework=request.framework,
    )


# ---------------------------------------------------------------------------
# render_diagram — mmdc-backed rendering
# ---------------------------------------------------------------------------


def render_diagram_impl(request: RenderDiagramRequest) -> RenderDiagramResponse:
    """Render Mermaid source to SVG/PNG via mmdc, or return source with install hint."""
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        return RenderDiagramResponse(
            status="warning",
            output_format=request.output_format,
            backend_available=False,
            install_hint=(
                "Install mermaid-cli to enable rendering: "
                "`npm install -g @mermaid-js/mermaid-cli` or `npx mmdc ...`"
            ),
        )

    with tempfile.NamedTemporaryFile(
        suffix=".mmd", mode="w", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(request.mermaid_source)
        tmp_path = tmp.name

    try:
        out_path_str: str
        if request.output_path is not None:
            out_path_str = str(request.output_path.expanduser())
            Path(out_path_str).parent.mkdir(parents=True, exist_ok=True)
        else:
            suffix = f".{request.output_format}"
            out_path_str = tmp_path + suffix

        result = subprocess.run(  # noqa: S603
            [mmdc, "-i", tmp_path, "-o", out_path_str],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return RenderDiagramResponse(
                status="error",
                output_format=request.output_format,
                backend_available=True,
                backend_used=mmdc,
                install_hint=result.stderr.strip() or None,
            )

        svg_content: str | None = None
        if request.output_format == "svg" and request.output_path is None:
            svg_content = Path(out_path_str).read_text(encoding="utf-8")

        return RenderDiagramResponse(
            status="success",
            output_format=request.output_format,
            output_path=out_path_str if request.output_path else None,
            svg_content=svg_content,
            backend_available=True,
            backend_used=mmdc,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# generate_changelog — conventional commit parser
# ---------------------------------------------------------------------------

_CONVENTIONAL_CATEGORIES: dict[str, str] = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Documentation",
    "style": "Changed",
    "test": "Changed",
    "chore": "Chores",
    "build": "Chores",
    "ci": "Chores",
    "revert": "Fixed",
    "breaking": "Breaking Changes",
}

_CONV_COMMIT_RE = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<desc>.+)$")


def _parse_git_log(project_root: Path, since_tag: str | None) -> list[str]:
    """Return commit oneline messages; empty list on git error."""
    cmd = ["git", "log", "--oneline", "--no-merges"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    try:
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, cwd=str(project_root), timeout=15, check=False
        )
        if result.returncode == 0:
            return [line.split(" ", 1)[1] for line in result.stdout.splitlines() if " " in line]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def generate_changelog_impl(request: GenerateChangelogRequest) -> GenerateChangelogResponse:
    """Generate a structured changelog entry from git conventional commits."""
    root = request.project_root.expanduser().resolve()
    commits = _parse_git_log(root, request.since_tag)

    bucket: dict[str, list[str]] = {}
    for msg in commits:
        m = _CONV_COMMIT_RE.match(msg)
        if m:
            ctype = m.group("type").lower()
            breaking = bool(m.group("breaking"))
            cat = "Breaking Changes" if breaking else _CONVENTIONAL_CATEGORIES.get(ctype, "Changed")
            desc = m.group("desc").strip()
        else:
            cat = "Changed"
            desc = msg.strip()
        bucket.setdefault(cat, []).append(desc)

    # Canonical category order for Keep a Changelog
    _order = ["Breaking Changes", "Added", "Fixed", "Changed", "Documentation", "Chores"]
    categories = [
        ChangelogCategoryEntry(category=cat, items=bucket[cat]) for cat in _order if cat in bucket
    ]
    # Append any unrecognised categories
    for cat, items in bucket.items():
        if cat not in _order:
            categories.append(ChangelogCategoryEntry(category=cat, items=items))

    today = datetime.datetime.now(tz=datetime.UTC).date().isoformat()

    if request.format == ChangelogEntryFormat.KEEP_A_CHANGELOG:
        lines = [f"## [{request.version}] — {today}", ""]
        for entry in categories:
            lines.append(f"### {entry.category}")
            lines.extend(f"- {item}" for item in entry.items)
            lines.append("")
        changelog_text = "\n".join(lines).rstrip()
    else:  # GITHUB_RELEASE
        lines = [f"# {request.version}", ""]
        for entry in categories:
            lines.append(f"## {entry.category}")
            lines.extend(f"- {item}" for item in entry.items)
            lines.append("")
        changelog_text = "\n".join(lines).rstrip()

    return GenerateChangelogResponse(
        status="success",
        version=request.version,
        format=request.format,
        changelog_text=changelog_text,
        categories=categories,
        commits_parsed=len(commits),
    )


# ---------------------------------------------------------------------------
# write_doc — single-pass complete documentation page writer
# ---------------------------------------------------------------------------

_DEFAULT_WRITE_DOC_SECTIONS: list[str] = ["Overview", "Usage", "References"]

_FRAMEWORK_FRONTMATTER: dict[str, str] = {
    "zensical": "---\ntitle: {title}\ndescription: {description}\n---\n\n",
    "docusaurus": (
        "---\ntitle: {title}\ndescription: {description}\nsidebar_label: {title}\n---\n\n"
    ),
    "vitepress": "---\ntitle: {title}\ndescription: {description}\n---\n\n",
    "starlight": "---\ntitle: {title}\ndescription: {description}\n---\n\n",
}


def write_doc_impl(request: WriteDocRequest) -> WriteDocResponse:
    """Write a complete, ready-to-publish documentation page for a given topic.

    Args:
        request: WriteDocRequest with topic, framework, output_path, and optional hints.

    Returns:
        WriteDocResponse with status, word_count, and section_count.
    """
    if not request.overwrite and request.output_path.exists():
        return WriteDocResponse(
            status="error",
            output_path=request.output_path,
            framework=request.framework,
            message=f"File already exists: {request.output_path}. Set overwrite=True to replace.",
        )

    sections = list(request.sections) if request.sections else list(_DEFAULT_WRITE_DOC_SECTIONS)
    framework_key = str(request.framework).lower()
    frontmatter_tmpl = _FRAMEWORK_FRONTMATTER.get(framework_key, _FRAMEWORK_FRONTMATTER["zensical"])
    description = request.audience or request.content_hints or f"Documentation for {request.topic}."
    frontmatter = frontmatter_tmpl.format(title=request.topic, description=description[:200])

    section_lines: list[str] = []
    hint_text = request.content_hints or ""
    for section in sections:
        section_lines.append(f"## {section}\n")
        if hint_text:
            section_lines.append(f"{hint_text}\n\n")
        else:
            section_lines.append("TODO: Document this section.\n\n")

    body = f"# {request.topic}\n\n" + "".join(section_lines)
    full_content = frontmatter + body

    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(full_content, encoding="utf-8")

    return WriteDocResponse(
        status="success",
        output_path=request.output_path,
        framework=request.framework,
        word_count=len(full_content.split()),
        section_count=len(sections),
    )


# ---------------------------------------------------------------------------
# Custom theme generation
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a #RRGGBB hex string to an (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _darken(hex_color: str, factor: float = 0.8) -> str:
    """Return a darkened hex color by multiplying RGB by *factor*."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


def _lighten(hex_color: str, factor: float = 0.85) -> str:
    """Return a lightened hex color by blending toward white."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"#{int(r + (255 - r) * (1 - factor)):02x}{int(g + (255 - g) * (1 - factor)):02x}{int(b + (255 - b) * (1 - factor)):02x}"  # noqa: E501


def _generate_zensical_theme(req: GenerateCustomThemeRequest) -> GenerateCustomThemeResponse:
    """Generate Zensical / MkDocs Material custom theme files."""
    from .models import FrameworkName  # noqa: PLC0415

    primary = req.primary_color
    accent = req.accent_color
    primary_dark = _darken(primary, 0.82)
    accent_dark = _darken(accent, 0.82)  # noqa: F841
    name = req.theme_name
    font_body = req.font_body or "Inter"
    font_code = req.font_code or "JetBrains Mono"

    css_light = f"""\
/* {name} theme — Zensical / MkDocs Material light scheme */
[data-md-color-scheme="{name}"] {{
  --md-primary-fg-color:        {primary};
  --md-primary-fg-color--light: {_lighten(primary, 0.7)};
  --md-primary-fg-color--dark:  {primary_dark};
  --md-accent-fg-color:         {accent};
  --md-typeset-a-color:         {primary_dark};
  color-scheme: light;
}}
"""
    css_dark = f"""\
/* {name}-dark theme — Zensical / MkDocs Material dark scheme */
[data-md-color-scheme="{name}-dark"] {{
  --md-primary-fg-color:        {primary};
  --md-primary-fg-color--light: {_lighten(primary, 0.5)};
  --md-primary-fg-color--dark:  {primary_dark};
  --md-accent-fg-color:         {accent};
  --md-typeset-a-color:         {primary};
  --md-default-bg-color:        #0d1117;
  --md-default-fg-color:        #e6edf3;
  color-scheme: dark;
}}
"""
    js_content = f"""\
/* {name} — palette persistence */
(function () {{
  var stored = localStorage.getItem("data-md-color-scheme");
  if (stored) document.body.setAttribute("data-md-color-scheme", stored);
  document.querySelectorAll("[data-md-color-scheme]").forEach(function (el) {{
    el.addEventListener("click", function () {{
      localStorage.setItem("data-md-color-scheme", el.getAttribute("data-md-color-scheme"));
    }});
  }});
}})();
"""

    config_snippet = f"""\
# zensical.toml — paste inside [project.theme] section
[[project.theme.palette]]
scheme  = "{name}"
primary = "custom"
accent  = "custom"
toggle  = {{ icon = "material/weather-night", name = "Switch to dark mode" }}

[[project.theme.palette]]
scheme  = "{name}-dark"
primary = "custom"
accent  = "custom"
toggle  = {{ icon = "material/weather-sunny", name = "Switch to light mode" }}

[project]
extra_css        = ["stylesheets/{name}.css"]
extra_javascript = ["javascripts/{name}.js"]

# Optional: custom font
[project.theme]
font = {{ text = "{font_body}", code = "{font_code}" }}
"""

    css_combined = css_light + ("\n" + css_dark if req.dark_mode else "")
    files: list[GenerateCustomThemeFile] = [
        GenerateCustomThemeFile(
            path=req.output_dir / f"{name}.css",
            content=css_combined,
            description=f"CSS variables for the '{name}' and '{name}-dark' color schemes.",
        ),
    ]
    if req.target in (CustomThemeTarget.CSS_AND_JS, CustomThemeTarget.FULL):
        js_dir = req.output_dir.parent / "javascripts"
        files.append(
            GenerateCustomThemeFile(
                path=js_dir / f"{name}.js",
                content=js_content,
                description="JavaScript for palette persistence across page loads.",
            )
        )

    _write_theme_files(files)
    return GenerateCustomThemeResponse(
        status="success",
        framework=FrameworkName.ZENSICAL,
        theme_name=name,
        files=files,
        config_snippet=config_snippet,
        message=f"Generated {len(files)} file(s) for theme '{name}'.",
    )


def _generate_docusaurus_theme(req: GenerateCustomThemeRequest) -> GenerateCustomThemeResponse:
    """Generate Docusaurus custom theme files (Infima CSS variables)."""
    from .models import FrameworkName  # noqa: PLC0415

    primary = req.primary_color
    accent = req.accent_color  # noqa: F841
    r, g, b = _hex_to_rgb(primary)
    name = req.theme_name
    font_body = req.font_body or "Inter, system-ui, sans-serif"
    font_code = req.font_code or "JetBrains Mono, Consolas, monospace"

    css_light = f"""\
/* {name} Docusaurus theme — light */
:root {{
  --ifm-color-primary:         {primary};
  --ifm-color-primary-dark:    {_darken(primary, 0.88)};
  --ifm-color-primary-darker:  {_darken(primary, 0.82)};
  --ifm-color-primary-darkest: {_darken(primary, 0.70)};
  --ifm-color-primary-light:   {_lighten(primary, 0.75)};
  --ifm-color-primary-lighter: {_lighten(primary, 0.65)};
  --ifm-color-primary-lightest:{_lighten(primary, 0.55)};
  --ifm-link-color:            {primary};
  --ifm-font-family-base:      {font_body};
  --ifm-font-family-monospace: {font_code};
  --ifm-code-font-size:        90%;
  --docusaurus-highlighted-code-line-bg: rgba({r}, {g}, {b}, 0.12);
}}
"""
    css_dark = f"""\
/* {name} Docusaurus theme — dark */
[data-theme="dark"] {{
  --ifm-color-primary:         {_lighten(primary, 0.7)};
  --ifm-color-primary-dark:    {primary};
  --ifm-link-color:            {_lighten(primary, 0.7)};
  --ifm-background-color:      #0d1117;
  --ifm-background-surface-color: #161b22;
  --docusaurus-highlighted-code-line-bg: rgba({r}, {g}, {b}, 0.2);
}}
"""

    config_snippet = f"""\
// docusaurus.config.js — add to themeConfig
themeConfig: {{
  colorMode: {{
    defaultMode: 'light',
    respectPrefersColorScheme: true,
  }},
}},
// Add to module.exports customCss field:
customCss: ['./src/css/{name}.css'],
"""

    css_combined = css_light + ("\n" + css_dark if req.dark_mode else "")
    files: list[GenerateCustomThemeFile] = [
        GenerateCustomThemeFile(
            path=req.output_dir / f"{name}.css",
            content=css_combined,
            description="Infima CSS variable overrides for light and dark Docusaurus themes.",
        )
    ]
    _write_theme_files(files)
    return GenerateCustomThemeResponse(
        status="success",
        framework=FrameworkName.DOCUSAURUS,
        theme_name=name,
        files=files,
        config_snippet=config_snippet,
        message=f"Generated {len(files)} file(s) for theme '{name}'.",
    )


def _generate_vitepress_theme(req: GenerateCustomThemeRequest) -> GenerateCustomThemeResponse:
    """Generate VitePress custom theme files."""
    from .models import FrameworkName  # noqa: PLC0415

    primary = req.primary_color
    accent = req.accent_color
    name = req.theme_name
    font_body = req.font_body or "Inter, system-ui, sans-serif"
    font_code = req.font_code or "JetBrains Mono, Consolas, monospace"

    css_content = f"""\
/* {name} VitePress theme */
:root {{
  --vp-c-brand-1: {primary};
  --vp-c-brand-2: {_darken(primary, 0.88)};
  --vp-c-brand-3: {_lighten(primary, 0.7)};
  --vp-c-brand-soft: {_lighten(primary, 0.9)}20;
  --vp-c-accent: {accent};
  --vp-font-family-base: "{font_body}";
  --vp-font-family-mono: "{font_code}";
}}
"""
    css_dark = f"""\
.dark {{
  --vp-c-brand-1: {_lighten(primary, 0.75)};
  --vp-c-brand-2: {primary};
  --vp-c-brand-3: {_darken(primary, 0.85)};
  --vp-c-bg: #0d1117;
  --vp-c-bg-soft: #161b22;
  --vp-c-bg-mute: #21262d;
}}
"""
    index_ts = f"""\
// .vitepress/theme/index.ts
import DefaultTheme from 'vitepress/theme'
import './{name}.css'

export default DefaultTheme
"""
    css_combined = css_content + ("\n" + css_dark if req.dark_mode else "")

    config_snippet = f"""\
// .vitepress/config.ts — no extra config needed; theme/index.ts auto-imports.
// Create .vitepress/theme/index.ts with:
// import DefaultTheme from 'vitepress/theme'
// import './{name}.css'
// export default DefaultTheme
"""
    files: list[GenerateCustomThemeFile] = [
        GenerateCustomThemeFile(
            path=req.output_dir / f"{name}.css",
            content=css_combined,
            description=f"VitePress --vp-c-brand-* CSS variable overrides for '{name}' theme.",
        ),
    ]
    if req.target in (CustomThemeTarget.CSS_AND_JS, CustomThemeTarget.FULL):
        files.append(
            GenerateCustomThemeFile(
                path=req.output_dir / "index.ts",
                content=index_ts,
                description="VitePress theme entry point that imports the custom CSS.",
            )
        )
    _write_theme_files(files)
    return GenerateCustomThemeResponse(
        status="success",
        framework=FrameworkName.VITEPRESS,
        theme_name=name,
        files=files,
        config_snippet=config_snippet,
        message=f"Generated {len(files)} file(s) for theme '{name}'.",
    )


def _generate_starlight_theme(req: GenerateCustomThemeRequest) -> GenerateCustomThemeResponse:
    """Generate Starlight (Astro) custom theme files."""
    from .models import FrameworkName  # noqa: PLC0415

    primary = req.primary_color
    accent = req.accent_color  # noqa: F841
    name = req.theme_name
    font_body = req.font_body or "Inter, system-ui, sans-serif"

    css_content = f"""\
/* {name} Starlight theme */
:root,
::backdrop {{
  --sl-color-accent-low:   {_lighten(primary, 0.85)};
  --sl-color-accent:       {primary};
  --sl-color-accent-high:  {_darken(primary, 0.8)};
  --sl-color-white:        #ffffff;
  --sl-color-gray-1:       #e6edf3;
  --sl-font: "{font_body}";
}}
"""
    css_dark = f"""\
:root[data-theme='dark'],
[data-theme='dark'] ::backdrop {{
  --sl-color-accent-low:  {_darken(primary, 0.7)};
  --sl-color-accent:      {_lighten(primary, 0.7)};
  --sl-color-accent-high: {_lighten(primary, 0.85)};
  --sl-color-bg:          #0d1117;
  --sl-color-bg-nav:      #0d1117;
  --sl-color-bg-sidebar:  #0d1117;
}}
"""
    config_snippet = f"""\
// astro.config.mjs — inside starlight({{ ... }})
customCss: ['./src/styles/{name}.css'],
"""
    css_combined = css_content + ("\n" + css_dark if req.dark_mode else "")
    files: list[GenerateCustomThemeFile] = [
        GenerateCustomThemeFile(
            path=req.output_dir / f"{name}.css",
            content=css_combined,
            description=f"Starlight --sl-color-accent-* CSS variable overrides for '{name}'.",
        )
    ]
    _write_theme_files(files)
    return GenerateCustomThemeResponse(
        status="success",
        framework=FrameworkName.STARLIGHT,
        theme_name=name,
        files=files,
        config_snippet=config_snippet,
        message=f"Generated {len(files)} file(s) for theme '{name}'.",
    )


def _generate_generic_css_theme(req: GenerateCustomThemeRequest) -> GenerateCustomThemeResponse:
    """Fallback: generate generic CSS custom properties theme."""
    primary = req.primary_color
    accent = req.accent_color
    name = req.theme_name

    css_content = f"""\
/* {name} generic theme */
:root {{
  --color-primary:       {primary};
  --color-primary-dark:  {_darken(primary, 0.85)};
  --color-primary-light: {_lighten(primary, 0.75)};
  --color-accent:        {accent};
  --color-accent-dark:   {_darken(accent, 0.85)};
}}
"""
    config_snippet = """\
<!-- Add to your HTML <head> -->
<link rel="stylesheet" href="custom.css">
"""
    files: list[GenerateCustomThemeFile] = [
        GenerateCustomThemeFile(
            path=req.output_dir / f"{name}.css",
            content=css_content,
            description="Generic CSS custom properties theme.",
        )
    ]
    _write_theme_files(files)
    return GenerateCustomThemeResponse(
        status="success",
        framework=req.framework,
        theme_name=name,
        files=files,
        config_snippet=config_snippet,
        message=f"Generated {len(files)} file(s) for theme '{name}' (generic fallback).",
    )


def _write_theme_files(files: list[GenerateCustomThemeFile]) -> None:
    """Write each theme file to disk, creating parent directories as needed."""
    for f in files:
        f.path.parent.mkdir(parents=True, exist_ok=True)
        f.path.write_text(f.content, encoding="utf-8")


def generate_custom_theme_impl(
    request: GenerateCustomThemeRequest,
) -> GenerateCustomThemeResponse:
    """Generate framework-specific CSS/JS theme customization files.

    Args:
        request: GenerateCustomThemeRequest specifying framework, colors, and output options.

    Returns:
        GenerateCustomThemeResponse with generated file contents and a config snippet.
    """
    from .models import FrameworkName  # noqa: PLC0415

    match request.framework:
        case FrameworkName.ZENSICAL | FrameworkName.MKDOCS_MATERIAL:
            return _generate_zensical_theme(request)
        case FrameworkName.DOCUSAURUS:
            return _generate_docusaurus_theme(request)
        case FrameworkName.VITEPRESS:
            return _generate_vitepress_theme(request)
        case FrameworkName.STARLIGHT:
            return _generate_starlight_theme(request)
        case _:
            return _generate_generic_css_theme(request)


# ---------------------------------------------------------------------------
# Zensical extension configuration generator
# ---------------------------------------------------------------------------

# Complete knowledge base for all supported Zensical/pymdownx extensions.
_ZENSICAL_EXTENSION_REGISTRY: dict[ZensicalExtension, _ZensicalExtensionRegistryEntry] = {
    ZensicalExtension.ARITHMATEX: {
        "description": (
            "Renders LaTeX math expressions via MathJax or KaTeX. "
            "Inline: $E=mc^2$, block: $$\\int_0^\\infty x dx$$."
        ),
        "toml_snippet": ("[project.markdown_extensions.pymdownx.arithmatex]\ngeneric = true\n"),
        "yaml_snippet": ("markdown_extensions:\n  - pymdownx.arithmatex:\n      generic: true\n"),
        "authoring_guides": [
            "Inline math: $E=mc^2$",
            "Block math:\n  $$\n  \\int_0^\\infty f(x)\\,dx\n  $$",
            "Requires extra_javascript entries for MathJax CDN (see extra_js field).",
        ],
        "extra_js": [
            "javascripts/mathjax.js",
            "https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js",
        ],
        "requires": [],
    },
    ZensicalExtension.HIGHLIGHT: {
        "description": (
            "Syntax highlighting for code blocks. Works with SuperFences. "
            "Supports anchor line numbers, auto-titles, and line spans."
        ),
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.highlight]\n"
            "anchor_linenums = true\n"
            'line_spans = "__span"\n'
            "pygments_lang_class = true\n"
        ),
        "yaml_snippet": (
            "markdown_extensions:\n"
            "  - pymdownx.highlight:\n"
            "      anchor_linenums: true\n"
            "      line_spans: __span\n"
            "      pygments_lang_class: true\n"
        ),
        "authoring_guides": [
            "Add line numbers to all blocks: linenums = true",
            "Add a title: ``` py title='example.py'",
            "Highlight lines: ``` py hl_lines='1 3'",
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.SUPERFENCES],
    },
    ZensicalExtension.SUPERFENCES: {
        "description": (
            "Allows nesting of code, admonitions, tabs, and other blocks. "
            "Enables Mermaid diagram rendering via custom fences."
        ),
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.superfences]\n"
            "custom_fences = [\n"
            '  { name = "mermaid", class = "mermaid", '
            'format = "pymdownx.superfences.fence_code_format" }\n'
            "]\n"
        ),
        "yaml_snippet": (
            "markdown_extensions:\n"
            "  - pymdownx.superfences:\n"
            "      custom_fences:\n"
            "        - name: mermaid\n"
            "          class: mermaid\n"
            "          format: !!python/name:pymdownx.superfences.fence_code_format\n"
        ),
        "authoring_guides": [
            "Nest admonitions inside tabs, or code blocks inside admonitions.",
            "Mermaid diagrams: use ``` mermaid fenced blocks.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.INLINEHILITE: {
        "description": "Inline code syntax highlighting. Requires Highlight extension.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.inlinehilite]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.inlinehilite\n",
        "authoring_guides": ["`#!python print('hello')`  — highlighted inline code"],
        "extra_js": [],
        "requires": [ZensicalExtension.HIGHLIGHT],
    },
    ZensicalExtension.TABBED: {
        "description": (
            "Content tabs for grouping related content. "
            'Syntax: === "Tab Name" with indented content.'
        ),
        "toml_snippet": ("[project.markdown_extensions.pymdownx.tabbed]\nalternate_style = true\n"),
        "yaml_snippet": (
            "markdown_extensions:\n  - pymdownx.tabbed:\n      alternate_style: true\n"
        ),
        "authoring_guides": [
            '=== "Python"\n    ```python\n    print("hello")\n    ```\n\n'
            '=== "JavaScript"\n    ```js\n    console.log("hello")\n    ```',
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.SUPERFENCES],
    },
    ZensicalExtension.TASKLIST: {
        "description": (
            "GitHub-style task lists with custom checkboxes. "
            "Use custom_checkbox = true for styled checkboxes."
        ),
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.tasklist]\ncustom_checkbox = true\n"
        ),
        "yaml_snippet": (
            "markdown_extensions:\n  - pymdownx.tasklist:\n      custom_checkbox: true\n"
        ),
        "authoring_guides": [
            "- [x] Completed task",
            "- [ ] Pending task",
            "- [x] Subtask",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.DETAILS: {
        "description": (
            "Collapsible admonition-style blocks. "
            "??? type 'title' for collapsed, !!!+ type for open."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.details]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.details\n",
        "authoring_guides": [
            "??? note\n    Collapsed by default.",
            "???+ tip 'Custom title'\n    Expanded by default.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.EMOJI: {
        "description": (
            "Emoji and icon support via Twemoji and Material icons. "
            "Uses Zensical-patched emoji namespace."
        ),
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.emoji]\n"
            'emoji_index = "material.extensions.emoji.twemoji"\n'
            'emoji_generator = "material.extensions.emoji.to_svg"\n'
            "[project.markdown_extensions.pymdownx.emoji.options]\n"
            'custom_icons = ["overrides/.icons"]\n'
        ),
        "yaml_snippet": (
            "markdown_extensions:\n"
            "  - pymdownx.emoji:\n"
            "      emoji_index: !!python/name:material.extensions.emoji.twemoji\n"
            "      emoji_generator: !!python/name:material.extensions.emoji.to_svg\n"
            "      options:\n"
            "        custom_icons:\n"
            "          - overrides/.icons\n"
        ),
        "authoring_guides": [
            ":smile: :heart: :rocket: — shortcode emoji",
            ":material-check: :octicons-alert-16: — Material/Octicons icons",
            "Custom icons in overrides/.icons/ — :custom-icon:",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.CARET: {
        "description": "Caret (^) markup for superscript and insert. H^2^O, ^^inserted text^^.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.caret]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.caret\n",
        "authoring_guides": ["H^2^O — superscript", "^^inserted text^^ — underline/insert"],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.MARK: {
        "description": "Mark (==) syntax for highlighting text. ==highlighted text==.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.mark]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.mark\n",
        "authoring_guides": ["==highlighted== — background highlight"],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.TILDE: {
        "description": "Tilde (~~) markup for subscript and strikethrough. H~2~O, ~~deleted~~.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.tilde]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.tilde\n",
        "authoring_guides": ["H~2~O — subscript", "~~deleted~~ — strikethrough"],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.KEYS: {
        "description": "Keyboard key rendering. ++ctrl+alt+del++.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.keys]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.keys\n",
        "authoring_guides": ["++ctrl+c++ — copy", "++meta+shift+r++ — hard refresh"],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.SMARTSYMBOLS: {
        "description": "Smart symbol conversion: (c) → ©, (tm) → ™, 1/2 → ½.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.smartsymbols]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.smartsymbols\n",
        "authoring_guides": ["(c) copyright, (r) registered, (tm) trademark, 1/2 fraction"],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.SNIPPETS: {
        "description": "Embed content from external files using --8<-- syntax.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.snippets]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.snippets\n",
        "authoring_guides": [
            "--8<-- 'docs/includes/abbreviations.md'  — embed file content",
            "--8<-- 'src/module.py:10:25'  — embed line range from source file",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.MAGICLINK: {
        "description": "Auto-link bare URLs and @mention syntax to GitHub/GitLab.",
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.magiclink]\n"
            "normalize_issue_symbols = true\n"
            "repo_url_shortener = true\n"
            "repo_url_shorthand = true\n"
            'user = "org"\n'
            'repo = "project"\n'
        ),
        "yaml_snippet": (
            "markdown_extensions:\n"
            "  - pymdownx.magiclink:\n"
            "      normalize_issue_symbols: true\n"
            "      repo_url_shortener: true\n"
            "      repo_url_shorthand: true\n"
            "      user: org\n"
            "      repo: project\n"
        ),
        "authoring_guides": [
            "https://example.com — auto-linked",
            "@mention — links to GitHub user",
            "#42 — links to issue/PR",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.BLOCKS_CAPTION: {
        "description": "Adds caption support to images, code blocks, and other block elements.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks.caption]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks.caption\n",
        "authoring_guides": ["/// caption\n    Figure 1: Chart showing growth.\n///"],
        "extra_js": [],
        "requires": [],
    },
    # Standard Python-Markdown extensions
    ZensicalExtension.ADMONITION: {
        "description": "Standard admonition blocks (note, tip, warning, etc.).",
        "toml_snippet": "[project.markdown_extensions.admonition]\n",
        "yaml_snippet": "markdown_extensions:\n  - admonition\n",
        "authoring_guides": [
            "!!! note 'Title'\n    Content of the note.",
            "!!! warning\n    This is a warning.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.ATTR_LIST: {
        "description": "Add HTML attributes to elements. Required for grids, buttons, and icons.",
        "toml_snippet": "[project.markdown_extensions.attr_list]\n",
        "yaml_snippet": "markdown_extensions:\n  - attr_list\n",
        "authoring_guides": [
            "# Heading { #custom-id }",
            "[Link](url){ .md-button }",
            "![Image](img.png){ align=left }",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.DEF_LIST: {
        "description": "Definition lists for glossaries and key-value pairs.",
        "toml_snippet": "[project.markdown_extensions.def_list]\n",
        "yaml_snippet": "markdown_extensions:\n  - def_list\n",
        "authoring_guides": [
            "Term\n:   Definition text\n\nAnother term\n:   Another definition",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.FOOTNOTES: {
        "description": "Footnote support. [^1] inline, [^1]: definition below.",
        "toml_snippet": "[project.markdown_extensions.footnotes]\n",
        "yaml_snippet": "markdown_extensions:\n  - footnotes\n",
        "authoring_guides": [
            "Text with footnote.[^1]\n\n[^1]: The footnote content.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.MD_IN_HTML: {
        "description": "Parse Markdown inside HTML blocks. Needed for grid cards.",
        "toml_snippet": "[project.markdown_extensions.md_in_html]\n",
        "yaml_snippet": "markdown_extensions:\n  - md_in_html\n",
        "authoring_guides": [
            '<div class="grid cards" markdown>',
            "  - Content rendered as Markdown",
            "</div>",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.TOC: {
        "description": "Table of contents generation with permalink support.",
        "toml_snippet": ("[project.markdown_extensions.toc]\npermalink = true\n"),
        "yaml_snippet": ("markdown_extensions:\n  - toc:\n      permalink: true\n"),
        "authoring_guides": [
            "Adds ¶ permalink anchor to each heading.",
            "Customize slug with slugify option.",
        ],
        "extra_js": [],
        "requires": [],
    },
    # --- Beta Blocks system (generic block containers) ---
    ZensicalExtension.BLOCKS: {
        "description": (
            "Generic block container system. Base for blocks.admonition, blocks.details, "
            "blocks.html, and blocks.tab."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks\n",
        "authoring_guides": [
            "/// html | div.my-class\nContent rendered inside a div.\n///",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.BLOCKS_ADMONITION: {
        "description": "Block-style admonitions via the Blocks system (`/// note`).",
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks.admonition]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks.admonition\n",
        "authoring_guides": [
            "/// note | Optional title\nAdmonition body rendered as Markdown.\n///",
            "/// warning\nNo title — defaults to type name.\n///",
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.BLOCKS],
    },
    ZensicalExtension.BLOCKS_DETAILS: {
        "description": "Block-style collapsible details (`/// details`) via the Blocks system.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks.details]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks.details\n",
        "authoring_guides": [
            "/// details | Click to expand\n    open: false\nHidden content here.\n///",
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.BLOCKS],
    },
    ZensicalExtension.BLOCKS_HTML: {
        "description": "Arbitrary HTML block containers with Markdown content inside.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks.html]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks.html\n",
        "authoring_guides": [
            "/// html | div.grid.cards\n- Card A\n- Card B\n///",
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.BLOCKS],
    },
    ZensicalExtension.BLOCKS_TAB: {
        "description": "Block-style tabbed sections (`/// tab`) via the Blocks system.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.blocks.tab]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.blocks.tab\n",
        "authoring_guides": [
            "/// tab | Python\n```python\nprint('Hello')\n```\n///\n"
            "/// tab | JavaScript\n```js\nconsole.log('Hello')\n```\n///",
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.BLOCKS],
    },
    # --- Track changes ---
    ZensicalExtension.CRITIC: {
        "description": (
            "CriticMarkup track-changes syntax: insertions, deletions, substitutions, "
            "highlights, and comments."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.critic]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.critic\n",
        "authoring_guides": [
            "{++inserted text++}",
            "{--deleted text--}",
            "{~~old text~>new text~~}",
            "{==highlighted==}",
            "{>>comment<<}",
        ],
        "extra_js": [],
        "requires": [],
    },
    # --- Emphasis ---
    ZensicalExtension.BETTEREM: {
        "description": (
            "Smarter handling of bold/italic boundary cases — avoids mid-word emphasis surprises."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.betterem]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.betterem\n",
        "authoring_guides": [
            "mid_word_bold=false means **word**s does not make 'words' bold.",
        ],
        "extra_js": [],
        "requires": [],
    },
    # --- Lists ---
    ZensicalExtension.FANCYLISTS: {
        "description": (
            "Extended ordered list syntax: start value, reversed lists, "
            "and arbitrary enumerators (a. A. i. I.)."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.fancylists]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.fancylists\n",
        "authoring_guides": [
            "1. First item\n2. Second item\n\na. Alpha item\nb. Bravo item",
            "Reversed: `reversed` attribute on `<ol>` tag.",
        ],
        "extra_js": [],
        "requires": [],
    },
    # --- Misc ---
    ZensicalExtension.ESCAPEALL: {
        "description": "Escape any character with a backslash, including spaces and newlines.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.escapeall]\nhardbreak = true\n",
        "yaml_snippet": ("markdown_extensions:\n  - pymdownx.escapeall:\n      hardbreak: true\n"),
        "authoring_guides": [
            "End a line with \\ to insert a hard line break.",
            "\\space escapes a literal space.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.SANEHEADERS: {
        "description": (
            "Require a space between `#` and heading text. "
            "Prevents `#hashtag` from becoming a heading."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.saneheaders]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.saneheaders\n",
        "authoring_guides": [
            "# Valid heading (space required)",
            "#NoSpace — NOT a heading with saneheaders enabled.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.PROGRESSBAR: {
        "description": "Render visual progress bar elements from inline syntax.",
        "toml_snippet": "[project.markdown_extensions.pymdownx.progressbar]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.progressbar\n",
        "authoring_guides": [
            '[= 75% "75%"]',
            '[= 100% "Complete"]{: .success}',
        ],
        "extra_js": [],
        "requires": [ZensicalExtension.ATTR_LIST],
    },
    ZensicalExtension.STRIPHTML: {
        "description": (
            "Strip or escape raw HTML from the Markdown source. Useful for untrusted user content."
        ),
        "toml_snippet": "[project.markdown_extensions.pymdownx.striphtml]\n",
        "yaml_snippet": "markdown_extensions:\n  - pymdownx.striphtml\n",
        "authoring_guides": [
            "Strips <script>, <style>, and on* event handlers.",
            "Configure strip_comments and strip_attributes options.",
        ],
        "extra_js": [],
        "requires": [],
    },
    ZensicalExtension.PATHCONVERTER: {
        "description": (
            "Convert relative paths in links and images to absolute or root-relative URLs. "
            "Useful when serving docs from a sub-path."
        ),
        "toml_snippet": (
            "[project.markdown_extensions.pymdownx.pathconverter]\n"
            'base_path = "."\nrelative_path = ""\n'
        ),
        "yaml_snippet": (
            "markdown_extensions:\n"
            "  - pymdownx.pathconverter:\n"
            "      base_path: '.'\n"
            "      relative_path: ''\n"
        ),
        "authoring_guides": [
            "Converts ./assets/img.png → /docs/assets/img.png based on base_path.",
        ],
        "extra_js": [],
        "requires": [],
    },
}


def configure_zensical_extensions_impl(  # noqa: C901
    request: ConfigureZensicalExtensionsRequest,
) -> ConfigureZensicalExtensionsResponse:
    """Generate zensical.toml and mkdocs.yml configuration blocks for requested extensions.

    Builds a comprehensive TOML/YAML configuration for any subset of the pymdownx and
    standard Python-Markdown extensions supported by Zensical. Also surfaces the extra
    JavaScript assets required (e.g., MathJax CDN for arithmatex).

    Args:
        request: Extension selection, format preference, and authoring example flag.

    Returns:
        Per-extension config details plus combined TOML/YAML blocks ready to paste.
    """
    # Expand to include any required dependencies
    all_requested: list[ZensicalExtension] = list(request.extensions)
    for ext in request.extensions:
        data = _ZENSICAL_EXTENSION_REGISTRY.get(ext)
        if data is not None:
            for dep in data["requires"]:
                if dep not in all_requested:
                    all_requested.append(dep)

    ext_configs: list[ZensicalExtensionConfig] = []
    combined_toml_parts: list[str] = []
    combined_yaml_parts: list[str] = []
    all_extra_js: list[str] = []

    for ext in all_requested:
        data = _ZENSICAL_EXTENSION_REGISTRY.get(ext)
        if data is None:
            continue
        toml_snip = data["toml_snippet"]
        yaml_snip = data["yaml_snippet"]
        extra_js = data["extra_js"]
        guides: list[str] = []
        if request.include_authoring_examples:
            guides = data["authoring_guides"]
        requires = data["requires"]
        ext_configs.append(
            ZensicalExtensionConfig(
                extension=ext,
                description=data["description"],
                toml_snippet=toml_snip,
                yaml_snippet=yaml_snip,
                authoring_guides=list(guides),
                requires=list(requires),
                extra_js=list(extra_js),
            )
        )
        combined_toml_parts.append(toml_snip)
        combined_yaml_parts.append(yaml_snip)
        for js in extra_js:
            if js not in all_extra_js:
                all_extra_js.append(js)

    combined_toml = "\n".join(combined_toml_parts)
    combined_yaml = "\n".join(combined_yaml_parts)

    # Add extra_javascript hint to TOML output if needed
    if all_extra_js:
        extra_js_toml = "extra_javascript = [\n"
        extra_js_toml += "".join(f'  "{js}",\n' for js in all_extra_js)
        extra_js_toml += "]\n"
        combined_toml = combined_toml + "\n" + extra_js_toml

    message = (
        f"Configured {len(ext_configs)} extension(s). "
        "Copy the combined_toml block into your [project] section of zensical.toml."
    )
    return ConfigureZensicalExtensionsResponse(
        status="success",
        extensions=ext_configs,
        combined_toml=combined_toml,
        combined_yaml=combined_yaml,
        extra_js=all_extra_js,
        message=message,
    )

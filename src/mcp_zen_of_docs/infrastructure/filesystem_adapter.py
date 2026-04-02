"""Infrastructure adapter for filesystem-backed init artifacts."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactContract
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactSpecContract
from mcp_zen_of_docs.domain.copilot_artifact_spec import get_copilot_artifact_spec
from mcp_zen_of_docs.domain.copilot_artifact_spec import iter_copilot_assets
from mcp_zen_of_docs.models import CopilotInitArtifactMetadata
from mcp_zen_of_docs.models import DocsDeployPipelineArtifactMetadata
from mcp_zen_of_docs.models import DocsDeployProvider
from mcp_zen_of_docs.models import FileWriteRecord
from mcp_zen_of_docs.models import ShellScriptArtifactMetadata
from mcp_zen_of_docs.models import ShellScriptType
from mcp_zen_of_docs.templates.copilot_assets import render_copilot_asset_content
from mcp_zen_of_docs.templates.docs_deploy_workflows import render_docs_deploy_workflow


_INIT_ARTIFACT_DIR = Path(".mcp-zen-of-docs") / "init"
_INIT_STATE_FILE_NAME = "state.json"
_DOCS_DEPLOY_WORKFLOW_PATH = Path(".github") / "workflows" / "docs-deploy.yml"
_UNIX_SHELLS: frozenset[ShellScriptType] = frozenset({ShellScriptType.BASH, ShellScriptType.ZSH})
_SCRIPT_FILE_BY_SHELL: dict[ShellScriptType, str] = {
    ShellScriptType.BASH: "init.bash.sh",
    ShellScriptType.ZSH: "init.zsh.sh",
    ShellScriptType.POWERSHELL: "init.powershell.ps1",
}


class InitOperationRecord(BaseModel):
    """Deterministic operation record for init artifact generation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    operation_id: str = Field(description="Stable operation identifier for one init action.")
    responsibility: str = Field(description="Clear responsibility assigned to this init action.")
    workflow_step: str = Field(description="Intuitive workflow step associated with this action.")
    tool_family: str = Field(description="Tool family that produced the artifact.")
    touched_files: list[Path] = Field(
        default_factory=list,
        description="Files touched by this operation.",
    )


class InitStatePayload(BaseModel):
    """Serialized init state payload persisted to disk."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    initialized: bool = Field(description="Whether initialization completed successfully.")
    shell_scripts: list[ShellScriptArtifactMetadata] = Field(
        default_factory=list,
        description="Generated shell script metadata captured for initialization.",
    )
    copilot_assets: list[CopilotInitArtifactMetadata] = Field(
        default_factory=list,
        description="Generated Copilot init artifact metadata captured for initialization.",
    )
    deploy_pipelines: list[DocsDeployPipelineArtifactMetadata] = Field(
        default_factory=list,
        description="Generated docs deploy pipeline metadata captured for initialization.",
    )
    responsibility_pillar: str = Field(
        default="clear-responsibility",
        description="Responsibility pillar used to structure init artifacts and ownership.",
    )
    workflow_pillar: str = Field(
        default="intuitive-workflows",
        description="Workflow pillar used to keep onboarding and init steps predictable.",
    )
    instruction_root: Path = Field(
        default=Path(".github/instructions"),
        description="Canonical instructions root for initialized instruction artifacts.",
    )
    operation_log: list[InitOperationRecord] = Field(
        default_factory=list,
        description="Deterministic operation records for generated init artifacts.",
    )


def resolve_project_root(project_root: Path | str) -> Path:
    """Resolve and normalize the project root path."""
    return Path(project_root).expanduser().resolve()


def init_artifact_dir(project_root: Path) -> Path:
    """Return the absolute init artifact directory for a project root."""
    return project_root / _INIT_ARTIFACT_DIR


def init_state_file(project_root: Path) -> Path:
    """Return the init state file path for a project root."""
    return init_artifact_dir(project_root) / _INIT_STATE_FILE_NAME


def shell_script_path(project_root: Path, shell: ShellScriptType) -> Path:
    """Return script path for a given shell target."""
    return init_artifact_dir(project_root) / _SCRIPT_FILE_BY_SHELL[shell]


def shell_script_body(shell: ShellScriptType) -> str:
    """Return deterministic bootstrap script body for a shell target."""
    if shell is ShellScriptType.BASH:
        return (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"\n'
            'state_file="${script_dir}/state.json"\n'
            'if [[ ! -f "${state_file}" ]]; then\n'
            "  printf 'mcp-zen-of-docs init (bash) failed: missing state file at %s\\n'"
            ' "${state_file}" >&2\n'
            "  exit 1\n"
            "fi\n"
            "printf 'mcp-zen-of-docs init (bash) completed: %s\\n' \"${state_file}\"\n"
        )
    if shell is ShellScriptType.ZSH:
        return (
            "#!/usr/bin/env zsh\n"
            "emulate -L zsh\n"
            "set -euo pipefail\n"
            'script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"\n'
            'state_file="${script_dir}/state.json"\n'
            'if [[ ! -f "${state_file}" ]]; then\n'
            "  printf 'mcp-zen-of-docs init (zsh) failed: missing state file at %s\\n'"
            ' "${state_file}" >&2\n'
            "  exit 1\n"
            "fi\n"
            "printf 'mcp-zen-of-docs init (zsh) completed: %s\\n' \"${state_file}\"\n"
        )
    return (
        "Set-StrictMode -Version Latest\n"
        "$ErrorActionPreference = 'Stop'\n"
        "$ScriptDir = Split-Path -Parent $PSCommandPath\n"
        "$StateFile = Join-Path $ScriptDir 'state.json'\n"
        "if (-not (Test-Path -LiteralPath $StateFile)) {\n"
        '    throw "mcp-zen-of-docs init (powershell) failed: missing state file at $StateFile"\n'
        "}\n"
        'Write-Output "mcp-zen-of-docs init (powershell) completed: $StateFile"\n'
    )


def script_is_executable(shell: ShellScriptType) -> bool:
    """Return whether executable permissions should be applied for a shell."""
    return shell in _UNIX_SHELLS


def docs_deploy_workflow_path(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
) -> Path:
    """Return deterministic docs deploy workflow path for a provider."""
    _ = provider
    return project_root / _DOCS_DEPLOY_WORKFLOW_PATH


def docs_deploy_workflow_content(provider: DocsDeployProvider) -> str:
    """Return deterministic docs deploy workflow content for a provider."""
    return render_docs_deploy_workflow(provider)


def write_docs_deploy_pipeline(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
    overwrite: bool,
) -> tuple[DocsDeployPipelineArtifactMetadata, FileWriteRecord | None]:
    """Write deterministic docs deploy workflow artifact for a provider."""
    workflow_path = docs_deploy_workflow_path(project_root, provider=provider)
    write_record: FileWriteRecord | None = None
    if workflow_path.exists() and not overwrite:
        return (
            DocsDeployPipelineArtifactMetadata(
                provider=provider,
                workflow_path=workflow_path,
                required=True,
                generated=False,
            ),
            write_record,
        )

    was_preexisting = workflow_path.exists()
    original_content = workflow_path.read_text(encoding="utf-8") if was_preexisting else None
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(docs_deploy_workflow_content(provider), encoding="utf-8")
    write_record = FileWriteRecord(
        path=workflow_path,
        was_preexisting=was_preexisting,
        original_content=original_content,
    )
    return (
        DocsDeployPipelineArtifactMetadata(
            provider=provider,
            workflow_path=workflow_path,
            required=True,
            generated=True,
        ),
        write_record,
    )


def discover_docs_deploy_pipelines(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
) -> list[DocsDeployPipelineArtifactMetadata]:
    """Discover docs deploy pipeline artifact metadata for a provider."""
    workflow_path = docs_deploy_workflow_path(project_root, provider=provider)
    return [
        DocsDeployPipelineArtifactMetadata(
            provider=provider,
            workflow_path=workflow_path,
            required=True,
            generated=workflow_path.exists(),
        )
    ]


def required_docs_deploy_artifacts(
    project_root: Path,
    *,
    provider: DocsDeployProvider,
) -> list[Path]:
    """Return required docs deploy workflow paths for init-status enforcement."""
    return [docs_deploy_workflow_path(project_root, provider=provider)]


def _copilot_asset_content(asset: CopilotArtifactContract) -> str:
    """Return deterministic markdown content for one Copilot artifact contract."""
    return render_copilot_asset_content(asset)


def write_shell_script(
    project_root: Path,
    *,
    shell: ShellScriptType,
    overwrite: bool,
) -> tuple[ShellScriptArtifactMetadata, FileWriteRecord | None]:
    """Write one deterministic shell script artifact to the init directory."""
    script_path = shell_script_path(project_root, shell)
    write_record: FileWriteRecord | None = None
    if script_path.exists() and not overwrite:
        return (
            ShellScriptArtifactMetadata(
                shell=shell,
                script_path=script_path,
                executable=script_is_executable(shell),
                generated=False,
            ),
            write_record,
        )

    was_preexisting = script_path.exists()
    original_content = script_path.read_text(encoding="utf-8") if was_preexisting else None
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(shell_script_body(shell), encoding="utf-8")
    if script_is_executable(shell):
        script_path.chmod(0o755)
    write_record = FileWriteRecord(
        path=script_path,
        was_preexisting=was_preexisting,
        original_content=original_content,
    )
    return (
        ShellScriptArtifactMetadata(
            shell=shell,
            script_path=script_path,
            executable=script_is_executable(shell),
            generated=True,
        ),
        write_record,
    )


def discover_shell_scripts(project_root: Path) -> list[ShellScriptArtifactMetadata]:
    """Discover expected shell script artifacts and annotate generation status."""
    metadata: list[ShellScriptArtifactMetadata] = []
    for shell in ShellScriptType:
        script_path = shell_script_path(project_root, shell)
        metadata.append(
            ShellScriptArtifactMetadata(
                shell=shell,
                script_path=script_path,
                executable=script_is_executable(shell),
                generated=script_path.exists(),
            )
        )
    return metadata


def write_copilot_artifact(
    project_root: Path,
    *,
    asset: CopilotArtifactContract,
    overwrite: bool,
) -> tuple[CopilotInitArtifactMetadata, FileWriteRecord | None]:
    """Write one deterministic Copilot artifact derived from the domain contract."""
    file_path = project_root / asset.relative_path
    write_record: FileWriteRecord | None = None
    if file_path.exists() and not overwrite:
        return (
            CopilotInitArtifactMetadata(
                artifact_id=asset.artifact_id,
                family=asset.family,
                pack=asset.pack,
                file_path=file_path,
                required=asset.required,
                hook_target=asset.hook_target,
                generated=False,
            ),
            write_record,
        )
    was_preexisting = file_path.exists()
    original_content = file_path.read_text(encoding="utf-8") if was_preexisting else None
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(_copilot_asset_content(asset), encoding="utf-8")
    write_record = FileWriteRecord(
        path=file_path,
        was_preexisting=was_preexisting,
        original_content=original_content,
    )
    return (
        CopilotInitArtifactMetadata(
            artifact_id=asset.artifact_id,
            family=asset.family,
            pack=asset.pack,
            file_path=file_path,
            required=asset.required,
            hook_target=asset.hook_target,
            generated=True,
        ),
        write_record,
    )


def write_copilot_assets(
    project_root: Path,
    *,
    overwrite: bool,
    spec: CopilotArtifactSpecContract | None = None,
) -> tuple[list[CopilotInitArtifactMetadata], list[FileWriteRecord]]:
    """Write deterministic Copilot assets from the domain spec."""
    active_spec = spec or get_copilot_artifact_spec()
    metadata: list[CopilotInitArtifactMetadata] = []
    write_records: list[FileWriteRecord] = []
    for asset in iter_copilot_assets(active_spec):
        artifact, write_record = write_copilot_artifact(
            project_root,
            asset=asset,
            overwrite=overwrite,
        )
        metadata.append(artifact)
        if write_record is not None:
            write_records.append(write_record)
    return metadata, write_records


def discover_copilot_assets(
    project_root: Path,
    *,
    spec: CopilotArtifactSpecContract | None = None,
) -> list[CopilotInitArtifactMetadata]:
    """Discover Copilot assets defined in the active domain spec."""
    active_spec = spec or get_copilot_artifact_spec()
    discovered: list[CopilotInitArtifactMetadata] = []
    for asset in iter_copilot_assets(active_spec):
        file_path = project_root / asset.relative_path
        discovered.append(
            CopilotInitArtifactMetadata(
                artifact_id=asset.artifact_id,
                family=asset.family,
                pack=asset.pack,
                file_path=file_path,
                required=asset.required,
                hook_target=asset.hook_target,
                generated=file_path.exists(),
            )
        )
    return discovered


def required_copilot_artifacts(
    project_root: Path,
    *,
    spec: CopilotArtifactSpecContract | None = None,
) -> list[Path]:
    """Return required Copilot artifact paths for init-status enforcement."""
    active_spec = spec or get_copilot_artifact_spec()
    return [
        project_root / asset.relative_path
        for asset in iter_copilot_assets(active_spec)
        if asset.required
    ]


def required_init_artifacts(
    project_root: Path,
    *,
    deploy_provider: DocsDeployProvider = DocsDeployProvider.GITHUB_PAGES,
    shell_targets: list[ShellScriptType] | None = None,
) -> list[Path]:
    """Return required shell scripts and state file paths for init completion."""
    selected_shells = shell_targets or list(ShellScriptType)
    scripts = [shell_script_path(project_root, shell) for shell in selected_shells]
    return [
        *scripts,
        *required_copilot_artifacts(project_root),
        *required_docs_deploy_artifacts(project_root, provider=deploy_provider),
        init_state_file(project_root),
    ]


def persist_init_state(
    project_root: Path,
    *,
    shell_scripts: list[ShellScriptArtifactMetadata],
    copilot_assets: list[CopilotInitArtifactMetadata] | None = None,
    deploy_pipelines: list[DocsDeployPipelineArtifactMetadata] | None = None,
) -> Path:
    """Persist immutable init state metadata to disk as formatted JSON."""
    state_file = init_state_file(project_root)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    operation_log: list[InitOperationRecord] = [
        InitOperationRecord(
            operation_id=f"shell-script:{artifact.shell.value}",
            responsibility="generate-shell-bootstrap",
            workflow_step="init-shell-bootstrap",
            tool_family="shell",
            touched_files=[artifact.script_path],
        )
        for artifact in shell_scripts
    ]
    operation_log.extend(
        InitOperationRecord(
            operation_id=f"instruction-artifact:{artifact.artifact_id}",
            responsibility="generate-instructions-artifact",
            workflow_step="init-instructions-artifacts",
            tool_family="instructions",
            touched_files=[artifact.file_path],
        )
        for artifact in (copilot_assets or [])
    )
    operation_log.extend(
        InitOperationRecord(
            operation_id=f"deploy-pipeline:{artifact.provider.value}",
            responsibility="generate-docs-deploy-pipeline",
            workflow_step="init-docs-deploy-pipeline",
            tool_family="docs-deploy",
            touched_files=[artifact.workflow_path],
        )
        for artifact in (deploy_pipelines or [])
    )
    operation_log = sorted(operation_log, key=lambda item: item.operation_id)
    payload = InitStatePayload(
        initialized=True,
        shell_scripts=sorted(shell_scripts, key=lambda item: item.shell.value),
        copilot_assets=sorted(
            copilot_assets or [],
            key=lambda item: (item.pack, item.family, item.artifact_id),
        ),
        deploy_pipelines=sorted(deploy_pipelines or [], key=lambda item: item.provider.value),
        operation_log=operation_log,
    )
    state_file.write_text(
        payload.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )
    return state_file


def write_text_file(file_path: Path, *, content: str) -> Path:
    """Write UTF-8 text file and create parent directories when needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


__all__ = [
    "CopilotInitArtifactMetadata",
    "DocsDeployPipelineArtifactMetadata",
    "DocsDeployProvider",
    "FileWriteRecord",
    "InitOperationRecord",
    "InitStatePayload",
    "discover_copilot_assets",
    "discover_docs_deploy_pipelines",
    "discover_shell_scripts",
    "docs_deploy_workflow_content",
    "docs_deploy_workflow_path",
    "init_artifact_dir",
    "init_state_file",
    "persist_init_state",
    "required_copilot_artifacts",
    "required_docs_deploy_artifacts",
    "required_init_artifacts",
    "resolve_project_root",
    "script_is_executable",
    "shell_script_body",
    "shell_script_path",
    "write_copilot_artifact",
    "write_copilot_assets",
    "write_docs_deploy_pipeline",
    "write_shell_script",
    "write_text_file",
]

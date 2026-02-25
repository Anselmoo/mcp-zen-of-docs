"""Infrastructure layer references for framework-specific integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .boundary import FrameworkDetectionGateway
from .boundary import FrameworkDetectionPort
from .boundary import FrameworkDetectionSnapshot
from .boundary import get_framework_detection_gateway
from .filesystem_adapter import CopilotInitArtifactMetadata
from .filesystem_adapter import DocsDeployPipelineArtifactMetadata
from .filesystem_adapter import DocsDeployProvider
from .filesystem_adapter import InitStatePayload
from .filesystem_adapter import discover_copilot_assets
from .filesystem_adapter import discover_docs_deploy_pipelines
from .filesystem_adapter import discover_shell_scripts
from .filesystem_adapter import docs_deploy_workflow_content
from .filesystem_adapter import docs_deploy_workflow_path
from .filesystem_adapter import init_artifact_dir
from .filesystem_adapter import init_state_file
from .filesystem_adapter import persist_init_state
from .filesystem_adapter import required_copilot_artifacts
from .filesystem_adapter import required_docs_deploy_artifacts
from .filesystem_adapter import required_init_artifacts
from .filesystem_adapter import resolve_project_root
from .filesystem_adapter import script_is_executable
from .filesystem_adapter import shell_script_body
from .filesystem_adapter import shell_script_path
from .filesystem_adapter import write_copilot_artifact
from .filesystem_adapter import write_copilot_assets
from .filesystem_adapter import write_docs_deploy_pipeline
from .filesystem_adapter import write_shell_script
from .filesystem_adapter import write_text_file
from .process_adapter import ProcessExecutionResult
from .process_adapter import run_process
from .shell_adapter import default_shell_for_platform
from .shell_adapter import execute_default_init_script


if TYPE_CHECKING:
    from pathlib import Path

    from mcp_zen_of_docs.models import FrameworkDetectionResult

INFRASTRUCTURE_MODULES: tuple[str, ...] = (
    "mcp_zen_of_docs.infrastructure.boundary",
    "mcp_zen_of_docs.infrastructure.filesystem_adapter",
    "mcp_zen_of_docs.infrastructure.process_adapter",
    "mcp_zen_of_docs.infrastructure.shell_adapter",
    "mcp_zen_of_docs.frameworks",
    "mcp_zen_of_docs.frameworks.base",
)
INFRASTRUCTURE_RESPONSIBILITIES: tuple[str, ...] = (
    "Provide framework profile adapters and detection integrations.",
    "Provide runtime adapters for process execution and shell invocation.",
    "Provide filesystem adapters for deterministic init and boilerplate artifacts.",
    "Contain implementation details tied to specific documentation ecosystems.",
    "Offer typed infrastructure gateways consumed by application/interface layers.",
)


def detect_framework_candidate(project_root: Path | str = ".") -> FrameworkDetectionResult | None:
    """Return the highest-confidence framework detection candidate."""
    gateway = get_framework_detection_gateway()
    return gateway.detect_candidate(project_root)


def detect_framework_candidates(project_root: Path | str = ".") -> list[FrameworkDetectionResult]:
    """Return all framework detection candidates sorted by confidence."""
    gateway = get_framework_detection_gateway()
    return gateway.detect_candidates(project_root)


def capture_framework_detection_snapshot(
    project_root: Path | str = ".",
) -> FrameworkDetectionSnapshot:
    """Return both best-candidate and full candidate list for one scan."""
    gateway = get_framework_detection_gateway()
    return gateway.capture_snapshot(project_root)


__all__ = [
    "INFRASTRUCTURE_MODULES",
    "INFRASTRUCTURE_RESPONSIBILITIES",
    "CopilotInitArtifactMetadata",
    "DocsDeployPipelineArtifactMetadata",
    "DocsDeployProvider",
    "FrameworkDetectionGateway",
    "FrameworkDetectionPort",
    "FrameworkDetectionSnapshot",
    "InitStatePayload",
    "ProcessExecutionResult",
    "capture_framework_detection_snapshot",
    "default_shell_for_platform",
    "detect_framework_candidate",
    "detect_framework_candidates",
    "discover_copilot_assets",
    "discover_docs_deploy_pipelines",
    "discover_shell_scripts",
    "docs_deploy_workflow_content",
    "docs_deploy_workflow_path",
    "execute_default_init_script",
    "get_framework_detection_gateway",
    "init_artifact_dir",
    "init_state_file",
    "persist_init_state",
    "required_copilot_artifacts",
    "required_docs_deploy_artifacts",
    "required_init_artifacts",
    "resolve_project_root",
    "run_process",
    "script_is_executable",
    "shell_script_body",
    "shell_script_path",
    "write_copilot_artifact",
    "write_copilot_assets",
    "write_docs_deploy_pipeline",
    "write_shell_script",
    "write_text_file",
]

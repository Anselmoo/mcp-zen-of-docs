"""Infrastructure adapter for shell/platform execution behavior."""

from __future__ import annotations

import os
import shutil
import subprocess

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.models import ShellScriptArtifactMetadata
from mcp_zen_of_docs.models import ShellScriptType

from .process_adapter import run_process


if TYPE_CHECKING:
    from pathlib import Path

_SHELL_EXECUTABLES_BY_TYPE: dict[ShellScriptType, tuple[str, ...]] = {
    ShellScriptType.BASH: ("bash",),
    ShellScriptType.ZSH: ("zsh",),
    ShellScriptType.POWERSHELL: ("powershell", "pwsh"),
}


class ShellExecutionPlan(BaseModel):
    """Resolved shell execution details for deterministic process invocation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    shell: ShellScriptType = Field(description="Shell selected for script execution.")
    executable: str = Field(description="Resolved shell executable name available on host.")
    command_prefix: tuple[str, ...] = Field(
        description="Command prefix tokens that should run before script path."
    )


def _resolve_shell_execution_plan(shell: ShellScriptType) -> ShellExecutionPlan | None:
    """Resolve available shell executable and command prefix for process invocation."""
    candidates = _SHELL_EXECUTABLES_BY_TYPE[shell]
    executable = next((candidate for candidate in candidates if shutil.which(candidate)), None)
    if executable is None:
        return None
    if shell is ShellScriptType.POWERSHELL:
        return ShellExecutionPlan(
            shell=shell,
            executable=executable,
            command_prefix=(executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"),
        )
    return ShellExecutionPlan(
        shell=shell,
        executable=executable,
        command_prefix=(executable,),
    )


def default_shell_for_platform() -> ShellScriptType:
    """Return default shell target for the current platform/environment."""
    if os.name == "nt":
        return ShellScriptType.POWERSHELL
    current_shell = os.environ.get("SHELL", "").strip().lower()
    if current_shell.endswith(("/zsh", "\\zsh.exe")):
        return ShellScriptType.ZSH
    return ShellScriptType.BASH


def execute_default_init_script(
    *,
    project_root: Path,
    shell_scripts: list[ShellScriptArtifactMetadata],
    shell: ShellScriptType | None = None,
) -> str | None:
    """Execute the default shell init script and return optional error details."""
    target_shell = shell or default_shell_for_platform()
    script_by_shell = {metadata.shell: metadata for metadata in shell_scripts}
    script_metadata = script_by_shell.get(target_shell)
    if script_metadata is None:
        return f"Default shell script '{target_shell.value}' was not generated."

    execution_plan = _resolve_shell_execution_plan(target_shell)
    if execution_plan is None:
        attempted = ", ".join(_SHELL_EXECUTABLES_BY_TYPE[target_shell])
        return (
            "Default init script execution failed for "
            f"{target_shell.value}: shell executable not found (attempted: {attempted})."
        )

    command = [*execution_plan.command_prefix, str(script_metadata.script_path)]
    try:
        result = run_process(command, cwd=project_root, timeout_seconds=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return (
            "Default init script execution failed for "
            f"{target_shell.value} via {execution_plan.executable}: {exc}"
        )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        return (
            "Default init script execution failed for "
            f"{target_shell.value} via {execution_plan.executable} "
            f"(exit {result.returncode}): {detail}"
        )
    return None


__all__ = [
    "ShellExecutionPlan",
    "default_shell_for_platform",
    "execute_default_init_script",
]

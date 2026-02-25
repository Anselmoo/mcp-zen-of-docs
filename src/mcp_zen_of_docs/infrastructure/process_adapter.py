"""Infrastructure adapter for subprocess execution."""

from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    from pathlib import Path


class ProcessExecutionResult(BaseModel):
    """Typed result for subprocess command execution."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    command: tuple[str, ...] = Field(description="Command tokens executed by subprocess.")
    returncode: int = Field(description="Process return code from command execution.")
    stdout: str = Field(description="Captured standard output from the process.")
    stderr: str = Field(description="Captured standard error from the process.")


def run_process(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> ProcessExecutionResult:
    """Run a subprocess command and return a typed immutable execution result."""
    completed = subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        check=False,
        cwd=cwd,
        text=True,
        timeout=timeout_seconds,
    )
    return ProcessExecutionResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=getattr(completed, "stdout", "") or "",
        stderr=getattr(completed, "stderr", "") or "",
    )


__all__ = ["ProcessExecutionResult", "run_process", "subprocess"]

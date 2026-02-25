"""Deterministic, offline-safe SVG-to-PNG conversion utilities."""

from __future__ import annotations

import importlib
import shutil
import subprocess

from importlib import metadata
from importlib import util
from pathlib import Path
from textwrap import dedent
from typing import Literal

from mcp_zen_of_docs.models import VisualAssetBackend
from mcp_zen_of_docs.models import VisualAssetBackendMetadata
from mcp_zen_of_docs.models import VisualAssetConversionRequest
from mcp_zen_of_docs.models import VisualAssetConversionResponse
from mcp_zen_of_docs.models import VisualAssetFormat
from mcp_zen_of_docs.models import VisualAssetKind


type _RunnerName = Literal["cairosvg", "imagemagick"]
type _ShellName = Literal["bash", "zsh", "powershell"]

_MAGICK_TIMEOUT_SECONDS = 20

_BASH_SCRIPT = dedent(
    """\
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ "$#" -ne 2 ]]; then
      echo 'Usage: convert-svg-png <source.svg> <output.png>' >&2
      exit 1
    fi
    SOURCE_SVG="$1"
    OUTPUT_PNG="$2"
    python - "${SOURCE_SVG}" "${OUTPUT_PNG}" <<'PY'
    from pathlib import Path
    import sys

    from mcp_zen_of_docs.asset_conversion import convert_svg_file

    response = convert_svg_file(
        source_path=Path(sys.argv[1]),
        output_path=Path(sys.argv[2]),
    )
    if response.status != 'success':
        raise SystemExit(response.message or 'SVG->PNG conversion failed.')
    print(response.output_path)
    PY
    """
)

_ZSH_SCRIPT = dedent(
    """\
    #!/usr/bin/env zsh
    emulate -L zsh
    set -euo pipefail
    if [[ "$#" -ne 2 ]]; then
      echo 'Usage: convert-svg-png <source.svg> <output.png>' >&2
      exit 1
    fi
    SOURCE_SVG="$1"
    OUTPUT_PNG="$2"
    python - "${SOURCE_SVG}" "${OUTPUT_PNG}" <<'PY'
    from pathlib import Path
    import sys

    from mcp_zen_of_docs.asset_conversion import convert_svg_file

    response = convert_svg_file(
        source_path=Path(sys.argv[1]),
        output_path=Path(sys.argv[2]),
    )
    if response.status != 'success':
        raise SystemExit(response.message or 'SVG->PNG conversion failed.')
    print(response.output_path)
    PY
    """
)

_POWERSHELL_SCRIPT = dedent(
    """\
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    param(
        [Parameter(Mandatory=$true)][string]$SourceSvg,
        [Parameter(Mandatory=$true)][string]$OutputPng
    )
    $Code = @'
    from pathlib import Path
    import sys

    from mcp_zen_of_docs.asset_conversion import convert_svg_file

    response = convert_svg_file(
        source_path=Path(sys.argv[1]),
        output_path=Path(sys.argv[2]),
    )
    if response.status != "success":
        raise SystemExit(response.message or "SVG->PNG conversion failed.")
    print(response.output_path)
    '@
    python -c $Code -- $SourceSvg $OutputPng
    """
)


__all__ = [
    "convert_svg_file",
    "convert_visual_asset",
    "generate_svg_png_conversion_script",
    "generate_svg_png_conversion_scripts",
    "select_conversion_backend",
]


def _detect_cairosvg_backend() -> VisualAssetBackendMetadata | None:
    """Return CairoSVG backend metadata when available."""
    if util.find_spec("cairosvg") is None:
        return None

    backend_version: str | None
    try:
        backend_version = metadata.version("cairosvg")
    except metadata.PackageNotFoundError:
        backend_version = None

    return VisualAssetBackendMetadata(
        backend=VisualAssetBackend.CAIROSVG,
        backend_version=backend_version,
        notes="CairoSVG backend detected and selected.",
    )


def _imagemagick_executable() -> str | None:
    """Return ImageMagick executable path when available."""
    return shutil.which("magick") or shutil.which("convert")


def _resolve_imagemagick_version(executable: str) -> str | None:
    """Resolve ImageMagick version string from the local executable."""
    try:
        result = subprocess.run(  # noqa: S603
            [executable, "-version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    version_line = (result.stdout or "").splitlines()
    if not version_line:
        return None
    return version_line[0].strip() or None


def _detect_imagemagick_backend() -> tuple[VisualAssetBackendMetadata, str] | None:
    """Return ImageMagick backend metadata and executable when available."""
    executable = _imagemagick_executable()
    if executable is None:
        return None

    return (
        VisualAssetBackendMetadata(
            backend=VisualAssetBackend.IMAGEMAGICK,
            backend_version=_resolve_imagemagick_version(executable),
            notes=f"ImageMagick backend detected via '{executable}'.",
        ),
        executable,
    )


def select_conversion_backend() -> tuple[VisualAssetBackendMetadata, _RunnerName | None]:
    """Select a deterministic local backend with CairoSVG preference and local fallback."""
    cairosvg_backend = _detect_cairosvg_backend()
    if cairosvg_backend is not None:
        return cairosvg_backend, "cairosvg"

    imagemagick_backend = _detect_imagemagick_backend()
    if imagemagick_backend is not None:
        metadata_payload, _ = imagemagick_backend
        return metadata_payload, "imagemagick"

    if util.find_spec("PIL") is not None:
        return (
            VisualAssetBackendMetadata(
                backend=VisualAssetBackend.PILLOW,
                backend_version=None,
                notes=(
                    "Pillow detected, but deterministic SVG rasterization is unavailable "
                    "without additional render plugins."
                ),
            ),
            None,
        )

    return (
        VisualAssetBackendMetadata(
            backend=VisualAssetBackend.CAIROSVG,
            backend_version=None,
            notes=(
                "No usable SVG->PNG backend detected. Install cairosvg or ensure "
                "ImageMagick is available in PATH."
            ),
        ),
        None,
    )


def _convert_with_cairosvg(*, source_svg: str, output_path: Path) -> str | None:
    """Convert SVG to PNG with CairoSVG and return an error message when it fails."""
    try:
        cairosvg = importlib.import_module("cairosvg")
        cairosvg.svg2png(bytestring=source_svg.encode("utf-8"), write_to=str(output_path))
    except (ImportError, OSError, ValueError) as exc:
        return str(exc)
    return None


def _convert_with_imagemagick(*, source_svg: str, output_path: Path, executable: str) -> str | None:
    """Convert SVG to PNG with ImageMagick and return an error message when it fails."""
    command = [executable, "svg:-", f"png32:{output_path}"]
    if Path(executable).name == "magick":
        command = [executable, "convert", "svg:-", f"png32:{output_path}"]

    try:
        result = subprocess.run(  # noqa: S603
            command,
            input=source_svg.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=_MAGICK_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return str(exc)

    if result.returncode == 0:
        return None

    stderr = result.stderr.decode("utf-8", errors="replace").strip()
    stdout = result.stdout.decode("utf-8", errors="replace").strip()
    return stderr or stdout or f"ImageMagick exited with code {result.returncode}."


def convert_visual_asset(request: VisualAssetConversionRequest) -> VisualAssetConversionResponse:
    """Convert a visual asset request into a deterministic PNG file on disk."""
    backend_metadata, runner = select_conversion_backend()

    if request.output_format is not VisualAssetFormat.PNG:
        return VisualAssetConversionResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_format=request.output_format,
            backend_metadata=backend_metadata,
            output_path=request.output_path,
            message="Deterministic offline conversion currently supports only PNG output.",
        )

    if request.output_path is None:
        return VisualAssetConversionResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_format=request.output_format,
            backend_metadata=backend_metadata,
            output_path=None,
            message="Output path is required for deterministic file conversion.",
        )

    if runner is None:
        return VisualAssetConversionResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_format=request.output_format,
            backend_metadata=backend_metadata,
            output_path=request.output_path,
            message=backend_metadata.notes or "No usable conversion backend available.",
        )

    output_path = request.output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    error_message: str | None
    if runner == "cairosvg":
        error_message = _convert_with_cairosvg(
            source_svg=request.source_svg,
            output_path=output_path,
        )
    else:
        imagemagick_backend = _detect_imagemagick_backend()
        if imagemagick_backend is None:
            error_message = "ImageMagick backend unavailable when conversion started."
        else:
            _, executable = imagemagick_backend
            error_message = _convert_with_imagemagick(
                source_svg=request.source_svg,
                output_path=output_path,
                executable=executable,
            )

    if error_message is not None:
        return VisualAssetConversionResponse(
            status="error",
            asset_kind=request.asset_kind,
            output_format=request.output_format,
            backend_metadata=backend_metadata,
            output_path=output_path,
            message=error_message,
        )

    return VisualAssetConversionResponse(
        status="success",
        asset_kind=request.asset_kind,
        output_format=request.output_format,
        backend_metadata=backend_metadata,
        output_path=output_path,
    )


def convert_svg_file(
    *,
    source_path: Path,
    output_path: Path,
    asset_kind: VisualAssetKind = VisualAssetKind.ICONS,
) -> VisualAssetConversionResponse:
    """Convert an SVG file on disk to PNG via deterministic backend selection."""
    request = VisualAssetConversionRequest(
        asset_kind=asset_kind,
        source_svg=source_path.read_text(encoding="utf-8"),
        output_format=VisualAssetFormat.PNG,
        output_path=output_path,
    )
    return convert_visual_asset(request)


def _unsupported_shell_error(shell: str) -> ValueError:
    """Build a deterministic unsupported-shell error."""
    message = f"Unsupported shell: {shell}"
    return ValueError(message)


def generate_svg_png_conversion_script(shell: _ShellName) -> str:
    """Return deterministic shell script content for SVG->PNG conversion wrappers."""
    match shell:
        case "bash":
            return _BASH_SCRIPT
        case "zsh":
            return _ZSH_SCRIPT
        case "powershell":
            return _POWERSHELL_SCRIPT
        case _:
            raise _unsupported_shell_error(shell)


def generate_svg_png_conversion_scripts() -> dict[_ShellName, str]:
    """Return deterministic script content for all supported wrapper shells."""
    return {
        "bash": _BASH_SCRIPT,
        "zsh": _ZSH_SCRIPT,
        "powershell": _POWERSHELL_SCRIPT,
    }

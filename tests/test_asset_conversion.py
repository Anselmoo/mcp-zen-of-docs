from __future__ import annotations

import pytest

from mcp_zen_of_docs.asset_conversion import convert_visual_asset
from mcp_zen_of_docs.asset_conversion import generate_svg_png_conversion_script
from mcp_zen_of_docs.asset_conversion import generate_svg_png_conversion_scripts
from mcp_zen_of_docs.asset_conversion import select_conversion_backend
from mcp_zen_of_docs.models import VisualAssetBackend
from mcp_zen_of_docs.models import VisualAssetBackendMetadata
from mcp_zen_of_docs.models import VisualAssetConversionRequest
from mcp_zen_of_docs.models import VisualAssetFormat
from mcp_zen_of_docs.models import VisualAssetKind


def test_backend_selection_prefers_cairosvg(monkeypatch) -> None:
    cairosvg_metadata = VisualAssetBackendMetadata(
        backend=VisualAssetBackend.CAIROSVG,
        backend_version="2.7.1",
        notes="CairoSVG backend detected and selected.",
    )

    monkeypatch.setattr(
        "mcp_zen_of_docs.asset_conversion._detect_cairosvg_backend",
        lambda: cairosvg_metadata,
    )
    monkeypatch.setattr(
        "mcp_zen_of_docs.asset_conversion._detect_imagemagick_backend",
        lambda: (
            VisualAssetBackendMetadata(
                backend=VisualAssetBackend.IMAGEMAGICK,
                backend_version="ImageMagick 7.1.1",
                notes="fallback",
            ),
            "magick",
        ),
    )

    metadata_payload, runner = select_conversion_backend()

    assert runner == "cairosvg"
    assert metadata_payload.backend is VisualAssetBackend.CAIROSVG


def test_backend_selection_falls_back_to_imagemagick(monkeypatch) -> None:
    monkeypatch.setattr(
        "mcp_zen_of_docs.asset_conversion._detect_cairosvg_backend",
        lambda: None,
    )
    monkeypatch.setattr(
        "mcp_zen_of_docs.asset_conversion._detect_imagemagick_backend",
        lambda: (
            VisualAssetBackendMetadata(
                backend=VisualAssetBackend.IMAGEMAGICK,
                backend_version="ImageMagick 7.1.1",
                notes="ImageMagick backend detected.",
            ),
            "magick",
        ),
    )

    metadata_payload, runner = select_conversion_backend()

    assert runner == "imagemagick"
    assert metadata_payload.backend is VisualAssetBackend.IMAGEMAGICK


def test_convert_visual_asset_returns_error_when_no_backend(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "mcp_zen_of_docs.asset_conversion.select_conversion_backend",
        lambda: (
            VisualAssetBackendMetadata(
                backend=VisualAssetBackend.CAIROSVG,
                backend_version=None,
                notes="No usable SVG->PNG backend detected.",
            ),
            None,
        ),
    )

    request = VisualAssetConversionRequest(
        asset_kind=VisualAssetKind.ICONS,
        source_svg="<svg viewBox='0 0 64 64'></svg>",
        output_format=VisualAssetFormat.PNG,
        output_path=tmp_path / "icon.png",
    )

    payload = convert_visual_asset(request)

    assert payload.status == "error"
    assert payload.backend_metadata.notes is not None
    assert "No usable" in payload.backend_metadata.notes


def test_script_generation_is_deterministic_for_all_shells() -> None:
    first = generate_svg_png_conversion_scripts()
    second = generate_svg_png_conversion_scripts()

    assert first == second
    assert "set -euo pipefail" in first["bash"]
    assert "emulate -L zsh" in first["zsh"]
    assert "Set-StrictMode -Version Latest" in first["powershell"]
    assert "convert_svg_file" in first["bash"]


def test_script_generation_rejects_unknown_shell() -> None:
    with pytest.raises(ValueError, match="Unsupported shell"):
        generate_svg_png_conversion_script("fish")

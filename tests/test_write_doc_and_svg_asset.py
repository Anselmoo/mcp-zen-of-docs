"""Tests for write_doc_impl and create_svg_asset_impl."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mcp_zen_of_docs.generators import write_doc_impl
from mcp_zen_of_docs.models import CreateSvgAssetRequest
from mcp_zen_of_docs.models import CreateSvgAssetResponse
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import VisualAssetKind
from mcp_zen_of_docs.models import WriteDocRequest
from mcp_zen_of_docs.models import WriteDocResponse
from mcp_zen_of_docs.visual_assets import create_svg_asset_impl


if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "test_create_svg_asset_all_kinds_succeed",
    "test_create_svg_asset_asset_kind_is_returned",
    "test_create_svg_asset_overwrite_true_replaces",
    "test_create_svg_asset_rejects_invalid_markup",
    "test_create_svg_asset_rejects_overwrite_false",
    "test_create_svg_asset_returns_typed_response",
    "test_create_svg_asset_writes_file",
    "test_write_doc_creates_file",
    "test_write_doc_custom_sections",
    "test_write_doc_default_sections",
    "test_write_doc_docusaurus_framework",
    "test_write_doc_overwrite_false_rejects_existing",
    "test_write_doc_overwrite_true_replaces_file",
    "test_write_doc_returns_typed_response",
]

# ---------------------------------------------------------------------------
# write_doc_impl tests
# ---------------------------------------------------------------------------

_SIMPLE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    '<rect width="100" height="100"/></svg>'
)


def test_write_doc_returns_typed_response(tmp_path: Path) -> None:
    """write_doc_impl returns a WriteDocResponse Pydantic model."""
    out = tmp_path / "test.md"
    req = WriteDocRequest(topic="Test Topic", output_path=out)
    result = write_doc_impl(req)
    assert isinstance(result, WriteDocResponse)


def test_write_doc_creates_file(tmp_path: Path) -> None:
    """write_doc_impl writes a file at output_path."""
    out = tmp_path / "guide.md"
    req = WriteDocRequest(topic="Getting Started", output_path=out)
    result = write_doc_impl(req)
    assert result.status == "success"
    assert out.exists()


def test_write_doc_default_sections(tmp_path: Path) -> None:
    """write_doc_impl uses default sections when none are specified."""
    out = tmp_path / "doc.md"
    req = WriteDocRequest(topic="API Reference", output_path=out)
    result = write_doc_impl(req)
    assert result.section_count == 3  # Overview, Usage, References
    content = out.read_text()
    assert "## Overview" in content
    assert "## Usage" in content
    assert "## References" in content


def test_write_doc_custom_sections(tmp_path: Path) -> None:
    """write_doc_impl uses provided sections list."""
    out = tmp_path / "custom.md"
    req = WriteDocRequest(topic="Custom", output_path=out, sections=["Introduction", "Examples"])
    result = write_doc_impl(req)
    assert result.section_count == 2
    content = out.read_text()
    assert "## Introduction" in content
    assert "## Examples" in content


def test_write_doc_overwrite_false_rejects_existing(tmp_path: Path) -> None:
    """write_doc_impl returns error when file exists and overwrite=False."""
    out = tmp_path / "existing.md"
    out.write_text("old content")
    req = WriteDocRequest(topic="Topic", output_path=out, overwrite=False)
    result = write_doc_impl(req)
    assert result.status == "error"
    assert out.read_text() == "old content"  # file unchanged


def test_write_doc_overwrite_true_replaces_file(tmp_path: Path) -> None:
    """write_doc_impl replaces file when overwrite=True."""
    out = tmp_path / "replace.md"
    out.write_text("old content")
    req = WriteDocRequest(topic="New Topic", output_path=out, overwrite=True)
    result = write_doc_impl(req)
    assert result.status == "success"
    assert "# New Topic" in out.read_text()


def test_write_doc_docusaurus_framework(tmp_path: Path) -> None:
    """write_doc_impl uses Docusaurus frontmatter when framework=docusaurus."""
    out = tmp_path / "doc.md"
    req = WriteDocRequest(topic="Components", output_path=out, framework=FrameworkName.DOCUSAURUS)
    result = write_doc_impl(req)
    assert result.status == "success"
    assert result.framework == FrameworkName.DOCUSAURUS


def test_write_doc_word_count_positive(tmp_path: Path) -> None:
    """write_doc_impl reports positive word_count for non-empty content."""
    out = tmp_path / "wordy.md"
    req = WriteDocRequest(
        topic="Words",
        output_path=out,
        content_hints="This section explains words and their usage.",
    )
    result = write_doc_impl(req)
    assert result.word_count > 0


# ---------------------------------------------------------------------------
# create_svg_asset_impl tests
# ---------------------------------------------------------------------------


def test_create_svg_asset_returns_typed_response(tmp_path: Path) -> None:
    """create_svg_asset_impl returns a CreateSvgAssetResponse Pydantic model."""
    out = tmp_path / "icon.svg"
    req = CreateSvgAssetRequest(svg_markup=_SIMPLE_SVG, output_path=out)
    result = create_svg_asset_impl(req)
    assert isinstance(result, CreateSvgAssetResponse)


def test_create_svg_asset_writes_file(tmp_path: Path) -> None:
    """create_svg_asset_impl writes SVG file to output_path."""
    out = tmp_path / "icon.svg"
    req = CreateSvgAssetRequest(svg_markup=_SIMPLE_SVG, output_path=out)
    result = create_svg_asset_impl(req)
    assert result.status == "success"
    assert out.exists()
    assert result.file_size_bytes > 0


def test_create_svg_asset_rejects_invalid_markup(tmp_path: Path) -> None:
    """create_svg_asset_impl returns error for non-SVG markup."""
    out = tmp_path / "bad.svg"
    req = CreateSvgAssetRequest(svg_markup="<div>not svg</div>", output_path=out)
    result = create_svg_asset_impl(req)
    assert result.status == "error"
    assert not out.exists()


def test_create_svg_asset_rejects_overwrite_false(tmp_path: Path) -> None:
    """create_svg_asset_impl returns error when file exists and overwrite=False."""
    out = tmp_path / "existing.svg"
    out.write_text(_SIMPLE_SVG)
    req = CreateSvgAssetRequest(svg_markup=_SIMPLE_SVG, output_path=out, overwrite=False)
    result = create_svg_asset_impl(req)
    assert result.status == "error"


def test_create_svg_asset_overwrite_true_replaces(tmp_path: Path) -> None:
    """create_svg_asset_impl replaces file when overwrite=True."""
    out = tmp_path / "replace.svg"
    out.write_text("<svg></svg>")
    req = CreateSvgAssetRequest(svg_markup=_SIMPLE_SVG, output_path=out, overwrite=True)
    result = create_svg_asset_impl(req)
    assert result.status == "success"
    assert out.read_text() == _SIMPLE_SVG


def test_create_svg_asset_asset_kind_is_returned(tmp_path: Path) -> None:
    """create_svg_asset_impl echoes asset_kind in response."""
    out = tmp_path / "header.svg"
    req = CreateSvgAssetRequest(
        svg_markup=_SIMPLE_SVG,
        output_path=out,
        asset_kind=VisualAssetKind.HEADER,
    )
    result = create_svg_asset_impl(req)
    assert result.asset_kind == VisualAssetKind.HEADER


@pytest.mark.parametrize("kind", list(VisualAssetKind))
def test_create_svg_asset_all_kinds_succeed(tmp_path: Path, kind: VisualAssetKind) -> None:
    """create_svg_asset_impl succeeds for every VisualAssetKind."""
    out = tmp_path / f"{kind.value}.svg"
    req = CreateSvgAssetRequest(svg_markup=_SIMPLE_SVG, output_path=out, asset_kind=kind)
    result = create_svg_asset_impl(req)
    assert result.status == "success"

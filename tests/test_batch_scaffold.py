"""Tests for batch_scaffold_docs tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_zen_of_docs.models import BatchScaffoldRequest
from mcp_zen_of_docs.models import BatchScaffoldResponse
from mcp_zen_of_docs.models import ScaffoldDocRequest
from mcp_zen_of_docs.server.app import batch_scaffold_docs as server_batch
from mcp_zen_of_docs.validators import batch_scaffold_docs


@pytest.fixture
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change to tmp directory and return it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _make_request(
    pages: list[ScaffoldDocRequest],
    framework: str | None = None,
) -> BatchScaffoldRequest:
    return BatchScaffoldRequest(
        pages=pages,
        docs_root=Path("docs"),
        framework=framework,
    )


def test_batch_creates_multiple_files(work_dir: Path) -> None:
    """Batch scaffold creates multiple files."""
    pages = [
        ScaffoldDocRequest(doc_path=Path("guide.md"), title="Guide"),
        ScaffoldDocRequest(doc_path=Path("reference.md"), title="Reference"),
    ]
    result = batch_scaffold_docs(_make_request(pages))
    assert isinstance(result, BatchScaffoldResponse)
    assert result.status == "success"
    assert result.total == 2
    assert len(result.created) == 2
    assert len(result.skipped) == 0
    assert (work_dir / "docs" / "guide.md").exists()
    assert (work_dir / "docs" / "reference.md").exists()


def test_batch_skips_existing_files(work_dir: Path) -> None:
    """Batch scaffold skips files that already exist."""
    docs = work_dir / "docs"
    docs.mkdir()
    (docs / "existing.md").write_text("# Existing", encoding="utf-8")

    pages = [
        ScaffoldDocRequest(doc_path=Path("existing.md"), title="Existing"),
        ScaffoldDocRequest(doc_path=Path("new-page.md"), title="New Page"),
    ]
    result = batch_scaffold_docs(_make_request(pages))
    assert result.status == "warning"
    assert len(result.created) == 1
    assert len(result.skipped) == 1
    assert "existing.md" in result.skipped[0]


def test_batch_with_framework_override(work_dir: Path) -> None:
    """Batch scaffold applies framework override."""
    pages = [
        ScaffoldDocRequest(doc_path=Path("framed.md"), title="Framed"),
    ]
    result = batch_scaffold_docs(
        _make_request(pages, framework="mkdocs-material"),
    )
    assert result.status == "success"
    assert len(result.created) == 1
    assert result.created[0].framework is not None


def test_batch_empty_input(work_dir: Path) -> None:
    """Batch scaffold with empty input returns success."""
    result = batch_scaffold_docs(_make_request([]))
    assert result.status == "success"
    assert result.total == 0
    assert len(result.created) == 0
    assert len(result.skipped) == 0


def test_batch_all_skipped(work_dir: Path) -> None:
    """Batch scaffold returns error when all pages skipped."""
    docs = work_dir / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A", encoding="utf-8")
    (docs / "b.md").write_text("# B", encoding="utf-8")

    pages = [
        ScaffoldDocRequest(doc_path=Path("a.md"), title="A"),
        ScaffoldDocRequest(doc_path=Path("b.md"), title="B"),
    ]
    result = batch_scaffold_docs(_make_request(pages))
    assert result.status == "error"
    assert len(result.skipped) == 2
    assert len(result.created) == 0


def test_batch_server_tool_returns_pipeline_context(
    work_dir: Path,
) -> None:
    """Server-level batch_scaffold_docs populates pipeline_context."""
    result = server_batch(
        pages=[
            {"doc_path": "ctx.md", "title": "Ctx"},
        ],
    )
    assert isinstance(result, BatchScaffoldResponse)
    assert result.pipeline_context is not None
    assert result.pipeline_context.last_tool == "batch_scaffold_docs"

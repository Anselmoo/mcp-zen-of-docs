"""Tests for pipeline context chaining across tool responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pydantic import BaseModel
from pydantic import ValidationError

from mcp_zen_of_docs.models import ComposeDocsStoryResponse
from mcp_zen_of_docs.models import DetectDocsContextResponse
from mcp_zen_of_docs.models import EnrichDocResponse
from mcp_zen_of_docs.models import PipelineContext
from mcp_zen_of_docs.models import PlanDocsResponse
from mcp_zen_of_docs.models import ScaffoldDocResponse
from mcp_zen_of_docs.models import ScoreDocsQualityResponse
from mcp_zen_of_docs.models import ValidateDocsResponse
from mcp_zen_of_docs.server import detect_docs_context
from mcp_zen_of_docs.server import scaffold_doc
from mcp_zen_of_docs.server import validate_docs


if TYPE_CHECKING:
    from pathlib import Path


class TestPipelineContextModel:
    """PipelineContext Pydantic model validation."""

    def test_pipeline_context_defaults(self) -> None:
        ctx = PipelineContext()
        assert ctx.framework is None
        assert ctx.project_root is None
        assert ctx.docs_root is None
        assert ctx.doc_paths == []
        assert ctx.last_tool is None

    def test_pipeline_context_with_values(self, tmp_path: Path) -> None:
        proj = tmp_path / "proj"
        ctx = PipelineContext(
            framework="mkdocs-material",
            project_root=proj,
            docs_root=proj / "docs",
            doc_paths=["docs/index.md", "docs/api.md"],
            last_tool="detect_docs_context",
        )
        assert ctx.framework == "mkdocs-material"
        assert ctx.last_tool == "detect_docs_context"
        assert len(ctx.doc_paths) == 2

    def test_pipeline_context_is_frozen(self) -> None:
        ctx = PipelineContext(last_tool="test")
        with pytest.raises(ValidationError):
            ctx.last_tool = "modified"


class TestPipelineContextOnResponses:
    """Verify pipeline_context field exists on all pipeline response models."""

    @pytest.mark.parametrize(
        "model_cls",
        [
            DetectDocsContextResponse,
            PlanDocsResponse,
            ScaffoldDocResponse,
            ComposeDocsStoryResponse,
            EnrichDocResponse,
            ValidateDocsResponse,
            ScoreDocsQualityResponse,
        ],
    )
    def test_pipeline_response_has_pipeline_context_field(
        self,
        model_cls: type[BaseModel],
    ) -> None:
        """Every pipeline response model has an optional pipeline_context field."""
        fields = model_cls.model_fields
        assert "pipeline_context" in fields
        field_info = fields["pipeline_context"]
        assert field_info.default is None


class TestDetectDocsContextPipelineContext:
    """detect_docs_context populates pipeline_context."""

    def test_detect_populates_pipeline_context(self, tmp_path: Path) -> None:
        result = detect_docs_context(project_root=str(tmp_path))
        assert isinstance(result, DetectDocsContextResponse)
        assert result.pipeline_context is not None
        assert result.pipeline_context.last_tool == "detect_docs_context"
        assert result.pipeline_context.project_root == tmp_path


class TestScaffoldDocPipelineContext:
    """scaffold_doc populates pipeline_context."""

    def test_scaffold_populates_pipeline_context(self, tmp_path: Path) -> None:
        doc_path = tmp_path / "docs" / "test.md"
        result = scaffold_doc(doc_path=str(doc_path), title="Test Page")
        assert isinstance(result, ScaffoldDocResponse)
        assert result.pipeline_context is not None
        assert result.pipeline_context.last_tool == "scaffold_doc"
        assert str(doc_path) in result.pipeline_context.doc_paths


class TestValidateDocsPipelineContext:
    """validate_docs populates pipeline_context."""

    def test_validate_populates_pipeline_context(self, tmp_path: Path) -> None:
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        result = validate_docs(docs_root=str(docs_root))
        assert isinstance(result, ValidateDocsResponse)
        assert result.pipeline_context is not None
        assert result.pipeline_context.last_tool == "validate_docs"
        assert result.pipeline_context.docs_root == docs_root

"""Tests for framework-native init.

Covers FrameworkInitSpec, EphemeralInstallRequest extensions,
init_framework_structure_impl, and scaffold_doc framework-aware docs_root resolution.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from mcp_zen_of_docs.domain.contracts import FrameworkName
from mcp_zen_of_docs.models import EphemeralInstallRequest
from mcp_zen_of_docs.models import FrameworkInitSpec
from mcp_zen_of_docs.models import InitFrameworkStructureRequest
from mcp_zen_of_docs.models import InitFrameworkStructureResponse
from mcp_zen_of_docs.templates.init_specs import FRAMEWORK_INIT_SPECS


class TestFrameworkInitSpecs:
    """Validate FRAMEWORK_INIT_SPECS dict is complete and correct."""

    def test_all_four_frameworks_present(self) -> None:
        assert FrameworkName.ZENSICAL in FRAMEWORK_INIT_SPECS
        assert FrameworkName.DOCUSAURUS in FRAMEWORK_INIT_SPECS
        assert FrameworkName.VITEPRESS in FRAMEWORK_INIT_SPECS
        assert FrameworkName.STARLIGHT in FRAMEWORK_INIT_SPECS

    def test_zensical_spec(self) -> None:
        spec = FRAMEWORK_INIT_SPECS[FrameworkName.ZENSICAL]
        assert spec.installer == "uvx"
        assert spec.command == "zensical"
        assert spec.init_args == ["new", "."]
        assert spec.source_subdir is None
        assert spec.docs_root == Path("docs")
        assert spec.stdin_input is None
        assert "docs/" in spec.copy_artifacts

    def test_docusaurus_spec(self) -> None:
        spec = FRAMEWORK_INIT_SPECS[FrameworkName.DOCUSAURUS]
        assert spec.installer == "npx"
        assert spec.source_subdir == "site"
        assert spec.docs_root == Path("docs")
        assert "docs/" in spec.copy_artifacts
        assert "docusaurus.config.ts" in spec.copy_artifacts

    def test_vitepress_spec(self) -> None:
        spec = FRAMEWORK_INIT_SPECS[FrameworkName.VITEPRESS]
        assert spec.installer == "npx"
        assert spec.source_subdir is None
        assert spec.docs_root == Path("docs")
        assert spec.stdin_input is not None  # piped newlines for non-interactive mode
        assert "docs/" in spec.copy_artifacts

    def test_starlight_spec(self) -> None:
        spec = FRAMEWORK_INIT_SPECS[FrameworkName.STARLIGHT]
        assert spec.installer == "npx"
        assert spec.source_subdir == "site"
        assert spec.docs_root == Path("src/content/docs")  # unique — not "docs/"
        assert "src/content/docs/" in spec.copy_artifacts
        assert "astro.config.mjs" in spec.copy_artifacts

    def test_spec_is_immutable_pydantic_model(self) -> None:
        spec = FRAMEWORK_INIT_SPECS[FrameworkName.ZENSICAL]
        assert isinstance(spec, FrameworkInitSpec)
        with pytest.raises(Exception):  # noqa: B017  frozen model raises on setattr
            spec.installer = "pip"


class TestEphemeralInstallRequestExtensions:
    """Verify the source_subdir and stdin_input fields added to EphemeralInstallRequest."""

    def test_source_subdir_defaults_to_none(self) -> None:
        req = EphemeralInstallRequest(installer="uvx", package="zensical", command="zensical")
        assert req.source_subdir is None

    def test_source_subdir_can_be_set(self) -> None:
        req = EphemeralInstallRequest(
            installer="npx",
            package="create-docusaurus@latest",
            command="create-docusaurus@latest",
            source_subdir="site",
        )
        assert req.source_subdir == "site"

    def test_stdin_input_defaults_to_none(self) -> None:
        req = EphemeralInstallRequest(installer="uvx", package="zensical", command="zensical")
        assert req.stdin_input is None

    def test_stdin_input_can_be_set(self) -> None:
        req = EphemeralInstallRequest(
            installer="npx",
            package="vitepress@latest",
            command="vitepress@latest",
            stdin_input="\n\n\n\n",
        )
        assert req.stdin_input == "\n\n\n\n"


class TestInitFrameworkStructureImpl:
    """Unit tests for init_framework_structure_impl using mocked subprocess."""

    def test_unknown_framework_returns_error(self) -> None:
        from mcp_zen_of_docs.generators import init_framework_structure_impl

        req = InitFrameworkStructureRequest(
            framework=FrameworkName.GENERIC_MARKDOWN,  # not in FRAMEWORK_INIT_SPECS
            project_root=Path(),
        )
        result = init_framework_structure_impl(req)
        assert result.status == "error"
        assert "No init spec registered" in (result.message or "")

    def test_successful_init_returns_success(self, tmp_path: Path) -> None:
        from mcp_zen_of_docs.generators import init_framework_structure_impl

        # Separate directories: ephemeral tmp (source) and project root (destination)
        ephemeral_tmp = tmp_path / "ephemeral"
        project_root = tmp_path / "project"
        ephemeral_tmp.mkdir()
        project_root.mkdir()

        # Simulate what zensical new . would create in the ephemeral dir
        (ephemeral_tmp / "docs").mkdir()
        (ephemeral_tmp / "docs" / "index.md").write_text("# Hello", encoding="utf-8")
        (ephemeral_tmp / "zensical.toml").write_text("[site]\ntitle = 'Test'", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with (
            patch("mcp_zen_of_docs.generators.subprocess.run", return_value=mock_result),
            patch(
                "mcp_zen_of_docs.generators.tempfile.mkdtemp",
                return_value=str(ephemeral_tmp),
            ),
            patch("mcp_zen_of_docs.generators.shutil.rmtree"),
        ):
            req = InitFrameworkStructureRequest(
                framework=FrameworkName.ZENSICAL,
                project_root=project_root,
            )
            result = init_framework_structure_impl(req)

        assert isinstance(result, InitFrameworkStructureResponse)
        assert result.framework == FrameworkName.ZENSICAL
        assert result.docs_root == Path("docs")
        assert "zensical" in result.cli_command
        assert result.status == "success"

    def test_failed_subprocess_propagates_error(self, tmp_path: Path) -> None:
        from mcp_zen_of_docs.generators import init_framework_structure_impl

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "command not found: zensical"

        with (
            patch("mcp_zen_of_docs.generators.subprocess.run", return_value=mock_result),
            patch("mcp_zen_of_docs.generators.tempfile.mkdtemp", return_value=str(tmp_path)),
            patch("mcp_zen_of_docs.generators.shutil.rmtree"),
        ):
            req = InitFrameworkStructureRequest(
                framework=FrameworkName.ZENSICAL,
                project_root=tmp_path,
            )
            result = init_framework_structure_impl(req)

        assert result.status == "error"
        assert "command not found" in (result.message or "")


class TestScaffoldDocFrameworkAwareness:
    """Verify scaffold_doc uses framework-native docs_root from FRAMEWORK_INIT_SPECS."""

    def test_starlight_uses_src_content_docs_root(self) -> None:
        from mcp_zen_of_docs.validators import scaffold_doc

        result = scaffold_doc(
            "guides/quickstart.md",
            "Quick Start",
            framework=FrameworkName.STARLIGHT,
            add_to_nav=False,
        )
        # Starlight docs_root is src/content/docs — path must start there
        assert result.doc_path.parts[0] == "src"
        assert "content" in result.doc_path.parts
        assert "docs" in result.doc_path.parts

    def test_zensical_uses_docs_root(self) -> None:
        from mcp_zen_of_docs.validators import scaffold_doc

        result = scaffold_doc(
            "guides/intro.md",
            "Introduction",
            framework=FrameworkName.ZENSICAL,
            add_to_nav=False,
        )
        assert result.doc_path.parts[0] == "docs"

    def test_docusaurus_uses_docs_root(self) -> None:
        from mcp_zen_of_docs.validators import scaffold_doc

        result = scaffold_doc(
            "tutorial/start.md",
            "Tutorial",
            framework=FrameworkName.DOCUSAURUS,
            add_to_nav=False,
        )
        assert result.doc_path.parts[0] == "docs"

    def test_no_framework_falls_back_to_docs(self) -> None:
        from mcp_zen_of_docs.validators import scaffold_doc

        result = scaffold_doc(
            "readme.md",
            "Readme",
            framework=None,
            add_to_nav=False,
        )
        assert result.doc_path.parts[0] == "docs"

    def test_already_prefixed_path_not_doubled(self) -> None:
        from mcp_zen_of_docs.validators import scaffold_doc

        result = scaffold_doc(
            "docs/already-prefixed.md",
            "Prefixed",
            framework=FrameworkName.ZENSICAL,
            add_to_nav=False,
        )
        # Should not produce docs/docs/...
        path_str = str(result.doc_path)
        assert "docs/docs" not in path_str

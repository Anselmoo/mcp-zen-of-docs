from pathlib import Path

import mcp_zen_of_docs.validators as validators_module

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import CheckDocsLinksResponse
from mcp_zen_of_docs.models import CheckLanguageStructureResponse
from mcp_zen_of_docs.models import CheckOrphanDocsResponse
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import ScaffoldDocResponse
from mcp_zen_of_docs.models import ScoreDocsQualityResponse
from mcp_zen_of_docs.validators import check_docs_links
from mcp_zen_of_docs.validators import check_language_structure
from mcp_zen_of_docs.validators import check_orphan_docs
from mcp_zen_of_docs.validators import scaffold_doc
from mcp_zen_of_docs.validators import score_docs_quality


def test_check_docs_links_reports_missing_internal(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\n[Broken](missing.md)\n", encoding="utf-8")
    result = check_docs_links(docs_root=str(docs))
    payload = CheckDocsLinksResponse.model_validate(result)
    assert payload.status == "warning"
    assert payload.tool == "check_docs_links"
    assert payload.missing_internal_count == 1


def test_check_orphan_docs_detects_unlinked_file(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home", encoding="utf-8")
    (docs / "orphan.md").write_text("# Orphan", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("nav:\n  - Home: index.md\n", encoding="utf-8")
    result = check_orphan_docs(docs_root=str(docs), mkdocs_file=str(mkdocs))
    payload = CheckOrphanDocsResponse.model_validate(result)
    assert payload.status == "warning"
    assert payload.tool == "check_orphan_docs"
    assert "orphan.md" in payload.orphans


def test_check_language_structure_reports_frontmatter_and_headers(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text("# Page\n\n``` \nno language\n```\n", encoding="utf-8")
    result = check_language_structure(docs_root=str(docs), required_headers=["## Usage"])
    payload = CheckLanguageStructureResponse.model_validate(result)
    assert payload.status == "warning"
    assert payload.tool == "check_language_structure"
    assert payload.issues


def test_scaffold_doc_creates_page_and_updates_nav(tmp_path: Path) -> None:
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: demo\nnav:\n  - Home: index.md\n", encoding="utf-8")
    result = scaffold_doc(
        doc_path=str(tmp_path / "docs" / "new.md"),
        title="New page",
        mkdocs_file=str(mkdocs),
    )
    payload = ScaffoldDocResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.tool == "scaffold_doc"
    assert (tmp_path / "docs" / "new.md").exists()


def test_score_docs_quality_returns_structured_score_for_well_formed_docs(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "---\n"
        "title: Home\n"
        "description: Landing page.\n"
        "---\n\n"
        "# Home\n\n"
        "## Usage\n\n"
        "Use [guide](guide.md).\n\n"
        "```bash\n"
        "echo hello\n"
        "```\n\n"
        "| Key | Value |\n"
        "| --- | --- |\n"
        "| demo | true |\n",
        encoding="utf-8",
    )
    (docs / "guide.md").write_text(
        "---\n"
        "title: Guide\n"
        "description: Guide page.\n"
        "---\n\n"
        "# Guide\n\n"
        "Use this guide for setup.\n",
        encoding="utf-8",
    )
    result = score_docs_quality(docs_root=str(docs))
    payload = ScoreDocsQualityResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.quality_score is not None
    assert payload.quality_score.overall >= 70
    assert "structure" in payload.component_scores
    assert payload.detected_primitives


def test_score_docs_quality_handles_missing_docs_root(tmp_path: Path) -> None:
    result = score_docs_quality(docs_root=str(tmp_path / "missing"))
    payload = ScoreDocsQualityResponse.model_validate(result)
    assert payload.status == "error"
    assert payload.message is not None


def test_score_docs_quality_handles_docs_root_without_markdown(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "notes.txt").write_text("placeholder", encoding="utf-8")
    payload = ScoreDocsQualityResponse.model_validate(score_docs_quality(docs_root=str(docs)))
    assert payload.status == "error"
    assert payload.message == "No markdown files found under docs_root."


def test_score_docs_quality_detects_extended_primitive_patterns(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "---\n"
        "title: Advanced\n"
        "description: Covers rich primitives.\n"
        "---\n\n"
        "# Advanced\n\n"
        "!!! note\n"
        "    Callout\n\n"
        '=== "Python"\n'
        "    ```python\n"
        "    print('ok')\n"
        "    ```\n\n"
        "- [x] Checklist item\n\n"
        "![Badge](https://img.shields.io/badge/docs-ready-green)\n\n"
        "![Diagram](assets/flow.png)\n\n"
        "GET /api/docs\n\n"
        "1. Step one\n\n"
        "| K | V |\n"
        "| --- | --- |\n"
        "| a | b |\n\n"
        "[Guide](guide.md)\n\n"
        "```mermaid\n"
        "graph TD\n"
        "A-->B\n"
        "```\n",
        encoding="utf-8",
    )
    (docs / "guide.md").write_text(
        "---\ntitle: Guide\ndescription: Linked page.\n---\n\n# Guide\n\nDetails.\n",
        encoding="utf-8",
    )
    payload = ScoreDocsQualityResponse.model_validate(score_docs_quality(docs_root=str(docs)))
    detected = set(payload.detected_primitives)
    assert payload.status in {"success", "warning"}
    assert AuthoringPrimitive.BADGE in detected
    assert AuthoringPrimitive.DIAGRAM in detected
    assert AuthoringPrimitive.API_ENDPOINT in detected
    assert AuthoringPrimitive.STEP_LIST in detected
    assert AuthoringPrimitive.TABS in detected
    assert AuthoringPrimitive.TASK_LIST in detected


def test_score_docs_quality_flags_untyped_code_fence(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "---\ntitle: Home\ndescription: Home page.\n---\n\n# Home\n\n```\necho hello\n```\n",
        encoding="utf-8",
    )
    payload = ScoreDocsQualityResponse.model_validate(score_docs_quality(docs_root=str(docs)))
    assert payload.status == "warning"
    assert any(
        issue.category == "code-hygiene" and "missing language identifiers" in issue.detail
        for issue in payload.issues
    )


def test_check_docs_links_returns_error_for_missing_docs_root(tmp_path: Path) -> None:
    payload = CheckDocsLinksResponse.model_validate(
        check_docs_links(docs_root=str(tmp_path / "missing"))
    )
    assert payload.status == "error"
    assert payload.message == "docs_root does not exist."


def test_check_docs_links_ignores_external_links_when_mode_is_ignore(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "# Home\n\n"
        "[Anchor](#top)\n"
        "[Mail](mailto:team@example.com)\n"
        "[External](https://example.com)\n",
        encoding="utf-8",
    )

    payload = CheckDocsLinksResponse.model_validate(
        check_docs_links(docs_root=str(docs), external_mode="ignore")
    )

    assert payload.status == "success"
    assert payload.issues == []
    assert payload.missing_internal_count == 0


def test_check_orphan_docs_returns_error_when_paths_are_missing(tmp_path: Path) -> None:
    payload = CheckOrphanDocsResponse.model_validate(
        check_orphan_docs(
            docs_root=str(tmp_path / "missing-docs"),
            mkdocs_file=str(tmp_path / "missing-mkdocs.yml"),
        )
    )
    assert payload.status == "error"
    assert payload.message == "docs_root or mkdocs_file does not exist."


def test_check_language_structure_returns_error_when_docs_root_missing(tmp_path: Path) -> None:
    payload = CheckLanguageStructureResponse.model_validate(
        check_language_structure(docs_root=str(tmp_path / "missing"))
    )
    assert payload.status == "error"
    assert payload.message == "docs_root does not exist."


def test_scaffold_doc_returns_error_when_target_exists_without_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "existing.md"
    target.parent.mkdir()
    target.write_text("# Existing\n", encoding="utf-8")

    payload = ScaffoldDocResponse.model_validate(
        scaffold_doc(doc_path=str(target), title="Existing", overwrite=False)
    )

    assert payload.status == "error"
    assert payload.message == "Target doc already exists. Use overwrite=True to replace."


def test_scaffold_doc_adds_nav_section_when_missing_and_does_not_duplicate_entry(
    tmp_path: Path,
) -> None:
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: demo\n", encoding="utf-8")
    target = tmp_path / "docs" / "created.md"

    first = ScaffoldDocResponse.model_validate(
        scaffold_doc(doc_path=str(target), title="Created", mkdocs_file=str(mkdocs))
    )
    second = ScaffoldDocResponse.model_validate(
        scaffold_doc(
            doc_path=str(target),
            title="Created",
            mkdocs_file=str(mkdocs),
            overwrite=True,
        )
    )

    assert first.status == "success"
    assert first.nav_updated is True
    assert second.status == "success"
    assert second.nav_updated is False


def test_check_docs_links_reports_external_links_when_mode_is_report(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("[External](https://example.com)\n", encoding="utf-8")

    payload = CheckDocsLinksResponse.model_validate(
        check_docs_links(docs_root=str(docs), external_mode="report")
    )

    assert payload.status == "success"
    assert payload.issues
    assert payload.issues[0].type == "external_unchecked"


def test_check_orphan_docs_handles_nested_nav_structures(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (docs / "nested.md").write_text("# Nested\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text(
        "nav:\n"
        "  - index.md\n"
        "  - Guide:\n"
        "      - guide.md\n"
        "      - Nested:\n"
        "          - nested.md\n",
        encoding="utf-8",
    )

    payload = CheckOrphanDocsResponse.model_validate(
        check_orphan_docs(docs_root=str(docs), mkdocs_file=str(mkdocs))
    )
    assert payload.status == "success"
    assert payload.orphans == []


def test_check_language_structure_flags_missing_h1_with_malformed_frontmatter(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "broken.md").write_text(
        "---\ntitle: Missing close frontmatter\nBody without h1\n",
        encoding="utf-8",
    )

    payload = CheckLanguageStructureResponse.model_validate(
        check_language_structure(docs_root=str(docs))
    )
    issue_types = {issue.type for issue in payload.issues}
    assert "missing_h1" in issue_types


def test_score_docs_quality_captures_empty_body_todo_long_line_and_missing_structure(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "empty.md").write_text(
        "---\ntitle: Empty\ndescription: No body\n---\n\n",
        encoding="utf-8",
    )
    (docs / "rough.md").write_text(
        "TODO this page is incomplete and intentionally has a very long line " + ("x" * 140) + "\n",
        encoding="utf-8",
    )
    (docs / "partial-frontmatter.md").write_text(
        "---\ntitle: Partial\n---\n\n# Partial\n",
        encoding="utf-8",
    )

    payload = ScoreDocsQualityResponse.model_validate(score_docs_quality(docs_root=str(docs)))
    details = [issue.detail for issue in payload.issues]
    categories = {issue.category for issue in payload.issues}

    assert payload.status == "warning"
    assert "structure" in categories
    assert "frontmatter" in categories
    assert "primitive-usage" in categories
    assert "code-hygiene" in categories
    assert any("Markdown body is empty." in detail for detail in details)
    assert any("Missing level-1 heading." in detail for detail in details)
    assert any("Missing YAML frontmatter block." in detail for detail in details)
    assert any("Missing frontmatter keys:" in detail for detail in details)
    assert any("TODO placeholder(s) remain in content." in detail for detail in details)
    assert any("line(s) exceed 120 characters." in detail for detail in details)


def test_to_nav_path_falls_back_to_filename_when_docs_segment_absent() -> None:
    assert validators_module._to_nav_path(Path("README.md")) == "README.md"  # noqa: SLF001


def test_scaffold_doc_with_framework_passes_through(tmp_path: Path) -> None:
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: demo\nnav:\n  - Home: index.md\n", encoding="utf-8")
    result = scaffold_doc(
        doc_path=str(tmp_path / "docs" / "fw.md"),
        title="Framework page",
        mkdocs_file=str(mkdocs),
        framework=FrameworkName.ZENSICAL,
    )
    payload = ScaffoldDocResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.framework == FrameworkName.ZENSICAL


def test_scaffold_doc_without_framework_defaults_to_none(tmp_path: Path) -> None:
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: demo\nnav:\n  - Home: index.md\n", encoding="utf-8")
    result = scaffold_doc(
        doc_path=str(tmp_path / "docs" / "nf.md"),
        title="No framework",
        mkdocs_file=str(mkdocs),
    )
    payload = ScaffoldDocResponse.model_validate(result)
    assert payload.status == "success"
    assert payload.framework is None


# ---------------------------------------------------------------------------
# Auto-detection and zensical.toml support for check_orphan_docs
# ---------------------------------------------------------------------------


def test_check_orphan_docs_auto_detects_mkdocs_yml_in_parent_dir(tmp_path: Path) -> None:
    """Orphan detection works when mkdocs.yml lives at project root (docs_root.parent)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    payload = CheckOrphanDocsResponse.model_validate(check_orphan_docs(docs_root=str(docs)))

    assert payload.status == "warning"
    assert "orphan.md" in payload.orphans
    assert "index.md" not in payload.orphans
    assert payload.detected_config is not None
    assert payload.detected_config.name == "mkdocs.yml"


def test_check_orphan_docs_detects_zensical_toml_in_parent_dir(tmp_path: Path) -> None:
    """Orphan detection works when zensical.toml lives at project root."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
    toml_cfg = tmp_path / "zensical.toml"
    toml_cfg.write_text(
        'nav = [{"Home" = "index.md"}]\n',
        encoding="utf-8",
    )

    payload = CheckOrphanDocsResponse.model_validate(check_orphan_docs(docs_root=str(docs)))

    assert payload.status == "warning"
    assert "orphan.md" in payload.orphans
    assert "index.md" not in payload.orphans
    assert payload.detected_config is not None
    assert payload.detected_config.name == "zensical.toml"


def test_check_orphan_docs_returns_error_when_no_config_found(tmp_path: Path) -> None:
    """Returns error with helpful message when no config file exists anywhere."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")

    payload = CheckOrphanDocsResponse.model_validate(check_orphan_docs(docs_root=str(docs)))

    assert payload.status == "error"
    assert payload.message is not None
    assert "No docs config found" in payload.message


def test_check_orphan_docs_detected_config_none_when_explicit_path_given(tmp_path: Path) -> None:
    """detected_config is None when caller supplies an explicit mkdocs_file."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    mkdocs = tmp_path / "mkdocs.yml"
    mkdocs.write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")

    payload = CheckOrphanDocsResponse.model_validate(
        check_orphan_docs(docs_root=str(docs), mkdocs_file=str(mkdocs))
    )

    assert payload.status == "success"
    assert payload.detected_config is None


def test_check_orphan_docs_zensical_toml_all_files_referenced(tmp_path: Path) -> None:
    """Returns success when all files are referenced in zensical.toml nav."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    toml_cfg = tmp_path / "zensical.toml"
    toml_cfg.write_text(
        'nav = [{"Home" = "index.md"}]\n',
        encoding="utf-8",
    )

    payload = CheckOrphanDocsResponse.model_validate(check_orphan_docs(docs_root=str(docs)))

    assert payload.status == "success"
    assert payload.orphans == []
    assert payload.detected_config is not None

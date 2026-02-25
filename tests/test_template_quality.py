"""Deep quality tests for template registries, brick integrity, and framework advantages.

Covers:
- Every BoilerplateBrickId has a registered brick with non-empty content.
- Every BoilerplateTemplateId has a registered template.
- Cross-links in brick content resolve to actual template output paths.
- All framework advantages cover the expected framework set.
- All advantage references have non-empty title and URL.
- Copilot asset template resolution chain covers every family.
- StrEnum parity: no orphaned enum members without registry entries.
"""

from __future__ import annotations

import re

import pytest

from mcp_zen_of_docs.domain.contracts import FrameworkName
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactFamily
from mcp_zen_of_docs.frameworks import list_framework_advantages
from mcp_zen_of_docs.frameworks import list_general_docs_references
from mcp_zen_of_docs.templates.boilerplate import DOC_BOILERPLATE_BRICK_REGISTRY
from mcp_zen_of_docs.templates.boilerplate import DOC_BOILERPLATE_REGISTRY
from mcp_zen_of_docs.templates.boilerplate import BoilerplateBrick
from mcp_zen_of_docs.templates.boilerplate import BoilerplateBrickId
from mcp_zen_of_docs.templates.boilerplate import BoilerplateTemplate
from mcp_zen_of_docs.templates.boilerplate import BoilerplateTemplateId
from mcp_zen_of_docs.templates.boilerplate import iter_doc_boilerplate_templates
from mcp_zen_of_docs.templates.copilot_assets import COPILOT_ASSET_TEMPLATE_REGISTRY
from mcp_zen_of_docs.templates.copilot_assets import CopilotAssetTemplate
from mcp_zen_of_docs.templates.copilot_assets import CopilotAssetTemplateId


# ---------------------------------------------------------------------------
# Boilerplate brick registry completeness
# ---------------------------------------------------------------------------


class TestBoilerplateBrickRegistry:
    """Every BoilerplateBrickId member maps to a registered brick with content."""

    def test_every_brick_id_has_registry_entry(self) -> None:
        registered_ids = {brick.brick_id for brick in DOC_BOILERPLATE_BRICK_REGISTRY}
        for member in BoilerplateBrickId:
            assert member in registered_ids, f"BoilerplateBrickId.{member.name} has no brick"

    def test_no_orphaned_registry_bricks(self) -> None:
        enum_ids = set(BoilerplateBrickId)
        for brick in DOC_BOILERPLATE_BRICK_REGISTRY:
            assert brick.brick_id in enum_ids, f"Registry brick {brick.brick_id!r} not in enum"

    def test_every_brick_has_nonempty_content(self) -> None:
        for brick in DOC_BOILERPLATE_BRICK_REGISTRY:
            assert brick.content.strip(), f"Brick {brick.brick_id!r} has empty content"

    def test_brick_content_starts_with_heading_or_text(self) -> None:
        for brick in DOC_BOILERPLATE_BRICK_REGISTRY:
            first_line = brick.content.lstrip().split("\n", 1)[0]
            assert first_line, f"Brick {brick.brick_id!r} has blank first line"

    def test_brick_instances_are_frozen(self) -> None:
        brick = DOC_BOILERPLATE_BRICK_REGISTRY[0]
        with pytest.raises(Exception):  # noqa: B017
            brick.content = "mutated"

    def test_brick_count_matches_enum_count(self) -> None:
        assert len(DOC_BOILERPLATE_BRICK_REGISTRY) == len(BoilerplateBrickId)

    def test_brick_ids_are_unique(self) -> None:
        ids = [brick.brick_id for brick in DOC_BOILERPLATE_BRICK_REGISTRY]
        assert len(ids) == len(set(ids)), "Duplicate brick IDs in registry"


# ---------------------------------------------------------------------------
# Boilerplate template registry completeness
# ---------------------------------------------------------------------------


class TestBoilerplateTemplateRegistry:
    """Every BoilerplateTemplateId maps to a composed template with valid bricks."""

    def test_every_template_id_has_registry_entry(self) -> None:
        registered_ids = {t.template_id for t in DOC_BOILERPLATE_REGISTRY}
        for member in BoilerplateTemplateId:
            assert member in registered_ids, f"BoilerplateTemplateId.{member.name} missing"

    def test_no_orphaned_registry_templates(self) -> None:
        enum_ids = set(BoilerplateTemplateId)
        for template in DOC_BOILERPLATE_REGISTRY:
            assert template.template_id in enum_ids

    def test_template_count_matches_enum_count(self) -> None:
        assert len(DOC_BOILERPLATE_REGISTRY) == len(BoilerplateTemplateId)

    def test_every_template_has_at_least_two_bricks(self) -> None:
        for template in DOC_BOILERPLATE_REGISTRY:
            assert len(template.bricks) >= 2, (
                f"Template {template.template_id!r} has fewer than 2 bricks"
            )

    def test_every_template_has_nonempty_content(self) -> None:
        for template in DOC_BOILERPLATE_REGISTRY:
            assert template.content.strip(), f"Template {template.template_id!r} has empty content"

    def test_template_content_ends_with_newline(self) -> None:
        for template in DOC_BOILERPLATE_REGISTRY:
            assert template.content.endswith("\n"), (
                f"Template {template.template_id!r} must end with newline"
            )

    def test_template_relative_paths_are_unique(self) -> None:
        paths = [t.relative_path for t in DOC_BOILERPLATE_REGISTRY]
        assert len(paths) == len(set(paths)), "Duplicate template output paths"

    def test_template_relative_paths_are_under_docs(self) -> None:
        for template in DOC_BOILERPLATE_REGISTRY:
            assert template.relative_path.parts[0] == "docs", (
                f"Template {template.template_id!r} path not under docs/"
            )

    def test_iter_returns_same_as_registry(self) -> None:
        assert iter_doc_boilerplate_templates() is DOC_BOILERPLATE_REGISTRY

    def test_template_instances_are_frozen(self) -> None:
        template = DOC_BOILERPLATE_REGISTRY[0]
        with pytest.raises(Exception):  # noqa: B017
            template.content = "mutated"


# ---------------------------------------------------------------------------
# Cross-link integrity: brick references to other templates
# ---------------------------------------------------------------------------


class TestBoilerplateCrossLinks:
    """Markdown cross-links in brick content resolve to known template output files."""

    _LINK_PATTERN = re.compile(r"\]\(\./([a-z_\-]+\.md)\)")

    def _known_filenames(self) -> set[str]:
        return {t.relative_path.name for t in DOC_BOILERPLATE_REGISTRY}

    def test_all_relative_links_resolve(self) -> None:
        known = self._known_filenames()
        # Also allow well-known files that are not templates
        known |= {"CODE_OF_CONDUCT.md"}
        for brick in DOC_BOILERPLATE_BRICK_REGISTRY:
            for match in self._LINK_PATTERN.finditer(brick.content):
                linked = match.group(1)
                assert linked in known, (
                    f"Brick {brick.brick_id!r} links to ./{linked} which is not a known template"
                )


# ---------------------------------------------------------------------------
# Framework advantages completeness
# ---------------------------------------------------------------------------

# The four authoring-profile frameworks that have advantages registered.
_ADVANTAGE_FRAMEWORKS = {
    FrameworkName.ZENSICAL,
    FrameworkName.VITEPRESS,
    FrameworkName.DOCUSAURUS,
    FrameworkName.STARLIGHT,
}


class TestFrameworkAdvantages:
    """Each profiled framework has advantages with valid references."""

    def test_all_profile_frameworks_covered(self) -> None:
        advantages = list_framework_advantages()
        covered = {a.framework for a in advantages}
        assert covered >= _ADVANTAGE_FRAMEWORKS, (
            f"Missing advantages for: {_ADVANTAGE_FRAMEWORKS - covered}"
        )

    def test_every_advantage_has_strengths(self) -> None:
        for adv in list_framework_advantages():
            assert len(adv.strengths) >= 2, f"{adv.framework} has fewer than 2 strengths"

    def test_every_advantage_has_references(self) -> None:
        for adv in list_framework_advantages():
            assert len(adv.references) >= 3, f"{adv.framework} has fewer than 3 references"

    def test_reference_titles_are_nonempty(self) -> None:
        for adv in list_framework_advantages():
            for ref in adv.references:
                assert ref.title.strip(), f"Empty title in {adv.framework} reference"

    def test_reference_urls_are_nonempty_and_start_with_https(self) -> None:
        for adv in list_framework_advantages():
            for ref in adv.references:
                assert ref.url.startswith("https://"), (
                    f"Non-HTTPS URL in {adv.framework}: {ref.url}"
                )


class TestGeneralDocsReferences:
    """General best-practice references are well-formed."""

    def test_at_least_three_references(self) -> None:
        refs = list_general_docs_references()
        assert len(refs) >= 3

    def test_every_reference_has_scope(self) -> None:
        for ref in list_general_docs_references():
            assert ref.scope.strip(), f"Empty scope on {ref.title!r}"

    def test_every_reference_url_is_https(self) -> None:
        for ref in list_general_docs_references():
            assert ref.url.startswith("https://"), f"Non-HTTPS: {ref.url}"


# ---------------------------------------------------------------------------
# Copilot asset template registry completeness
# ---------------------------------------------------------------------------


class TestCopilotAssetTemplateRegistry:
    """Copilot asset template registry covers expected IDs and families."""

    def test_every_template_id_has_registry_entry(self) -> None:
        registered_ids = {t.template_id for t in COPILOT_ASSET_TEMPLATE_REGISTRY}
        for member in CopilotAssetTemplateId:
            assert member in registered_ids, f"CopilotAssetTemplateId.{member.name} missing"

    def test_template_count_matches_enum_count(self) -> None:
        assert len(COPILOT_ASSET_TEMPLATE_REGISTRY) == len(CopilotAssetTemplateId)

    def test_every_template_has_nonempty_body(self) -> None:
        for template in COPILOT_ASSET_TEMPLATE_REGISTRY:
            assert template.body_template.strip(), (
                f"Template {template.template_id!r} has empty body_template"
            )

    def test_family_fallbacks_cover_all_artifact_families(self) -> None:
        covered_families = {
            t.family for t in COPILOT_ASSET_TEMPLATE_REGISTRY if t.family is not None
        }
        for family in CopilotArtifactFamily:
            assert family in covered_families, f"CopilotArtifactFamily.{family.name} uncovered"

    def test_default_template_exists(self) -> None:
        defaults = [
            t
            for t in COPILOT_ASSET_TEMPLATE_REGISTRY
            if t.template_id == CopilotAssetTemplateId.DEFAULT
        ]
        assert len(defaults) == 1

    def test_template_instances_are_frozen(self) -> None:
        template = COPILOT_ASSET_TEMPLATE_REGISTRY[0]
        with pytest.raises(Exception):  # noqa: B017
            template.body_template = "mutated"


# ---------------------------------------------------------------------------
# Type integrity
# ---------------------------------------------------------------------------


class TestTypeIntegrity:
    """All registry entries are proper Pydantic model instances."""

    def test_brick_types(self) -> None:
        for brick in DOC_BOILERPLATE_BRICK_REGISTRY:
            assert isinstance(brick, BoilerplateBrick)

    def test_template_types(self) -> None:
        for template in DOC_BOILERPLATE_REGISTRY:
            assert isinstance(template, BoilerplateTemplate)

    def test_copilot_template_types(self) -> None:
        for template in COPILOT_ASSET_TEMPLATE_REGISTRY:
            assert isinstance(template, CopilotAssetTemplate)

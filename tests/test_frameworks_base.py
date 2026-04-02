from collections.abc import Iterator
from pathlib import Path

import pytest

from mcp_zen_of_docs.frameworks import detect_best_framework
from mcp_zen_of_docs.frameworks import detect_frameworks
from mcp_zen_of_docs.frameworks import register_builtin_profiles
from mcp_zen_of_docs.frameworks.base import AuthoringProfile
from mcp_zen_of_docs.frameworks.base import clear_profile_registry
from mcp_zen_of_docs.frameworks.base import get_profile
from mcp_zen_of_docs.frameworks.base import iter_profiles
from mcp_zen_of_docs.frameworks.base import register_profile
from mcp_zen_of_docs.frameworks.starlight_profile import StarlightProfile
from mcp_zen_of_docs.frameworks.zensical_profile import ZensicalProfile
from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import StructureIssue
from mcp_zen_of_docs.models import SupportLevel


@pytest.fixture(autouse=True)
def _reset_registry() -> Iterator[None]:
    clear_profile_registry()
    yield
    clear_profile_registry()


class _DummyProfile(AuthoringProfile):
    @property
    def framework(self) -> FrameworkName:
        return FrameworkName.MKDOCS_MATERIAL

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        return FrameworkDetectionResult(
            framework=self.framework,
            support_level=SupportLevel.FULL,
            confidence=1.0,
            matched_signals=[project_root.as_posix()],
        )

    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        _ = topic
        if primitive is AuthoringPrimitive.FRONTMATTER:
            return "---\ntitle: Demo\n---\n"
        return None

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        if content.strip():
            return []
        return [
            StructureIssue(
                type="empty_content",
                file=file_path or "<memory>",
                detail="Content is empty.",
            )
        ]

    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        return (
            SupportLevel.FULL
            if primitive is AuthoringPrimitive.FRONTMATTER
            else SupportLevel.PARTIAL
        )


class _CustomZensicalProfile(_DummyProfile):
    @property
    def framework(self) -> FrameworkName:
        return FrameworkName.ZENSICAL


class _IncompleteProfile(AuthoringProfile):
    pass


def test_authoring_profile_is_abstract() -> None:
    with pytest.raises(TypeError):
        _IncompleteProfile()


def test_profile_registry_round_trip() -> None:
    profile = _DummyProfile()
    assert get_profile(FrameworkName.MKDOCS_MATERIAL) is None

    register_profile(profile)

    assert get_profile(FrameworkName.MKDOCS_MATERIAL) is profile
    assert iter_profiles() == (profile,)
    assert profile.migration_hints(FrameworkName.DOCUSAURUS) == []
    assert profile.migrate_content("demo", FrameworkName.DOCUSAURUS) == "demo"


def test_profile_registry_rejects_duplicate_without_replace() -> None:
    register_profile(_DummyProfile())
    with pytest.raises(ValueError):
        register_profile(_DummyProfile())


def test_profile_registry_replace_updates_entry() -> None:
    first = _DummyProfile()
    second = _DummyProfile()

    register_profile(first)
    register_profile(second, replace=True)

    assert get_profile(FrameworkName.MKDOCS_MATERIAL) is second


def test_register_builtin_profiles_registers_expected_frameworks() -> None:
    register_builtin_profiles()
    frameworks = {profile.framework for profile in iter_profiles()}
    assert frameworks == {
        FrameworkName.ZENSICAL,
        FrameworkName.DOCUSAURUS,
        FrameworkName.VITEPRESS,
        FrameworkName.STARLIGHT,
    }


def test_detect_frameworks_lazily_registers_builtin_profiles(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n")

    assert iter_profiles() == ()

    detect_frameworks(tmp_path)

    frameworks = {profile.framework for profile in iter_profiles()}
    assert frameworks == {
        FrameworkName.ZENSICAL,
        FrameworkName.DOCUSAURUS,
        FrameworkName.VITEPRESS,
        FrameworkName.STARLIGHT,
    }


def test_detect_frameworks_preserves_custom_profile_registration(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n")
    custom = _CustomZensicalProfile()
    register_profile(custom)

    results = detect_frameworks(tmp_path)

    assert get_profile(FrameworkName.ZENSICAL) is custom
    assert any(
        result.framework is FrameworkName.ZENSICAL and "custom" not in result.missing_signals
        for result in results
    )


def test_detect_best_framework_uses_priority_for_equal_confidence(tmp_path: Path) -> None:
    register_profile(_DummyProfile())
    register_profile(_CustomZensicalProfile())

    result = detect_best_framework(tmp_path)

    assert result is not None
    assert result.framework is FrameworkName.ZENSICAL


def test_builtin_profiles_expose_expected_primitive_support() -> None:
    register_builtin_profiles()
    zensical_profile = get_profile(FrameworkName.ZENSICAL)
    docusaurus_profile = get_profile(FrameworkName.DOCUSAURUS)
    vitepress_profile = get_profile(FrameworkName.VITEPRESS)
    starlight_profile = get_profile(FrameworkName.STARLIGHT)
    assert zensical_profile is not None
    assert docusaurus_profile is not None
    assert vitepress_profile is not None
    assert starlight_profile is not None
    assert zensical_profile.primitive_support(AuthoringPrimitive.ADMONITION) == SupportLevel.FULL
    assert (
        docusaurus_profile.primitive_support(AuthoringPrimitive.NAVIGATION_ENTRY)
        == SupportLevel.FULL
    )
    assert vitepress_profile.primitive_support(AuthoringPrimitive.SNIPPET) == SupportLevel.PARTIAL
    assert (
        starlight_profile.primitive_support(AuthoringPrimitive.ADMONITION) == SupportLevel.PARTIAL
    )


def test_builtin_profiles_detection_payloads_are_consistent(tmp_path: Path) -> None:
    register_builtin_profiles()
    for profile in iter_profiles():
        detection = profile.detect(tmp_path)
        assert detection.framework == profile.framework
        assert 0.0 <= detection.confidence <= 1.0
        assert detection.authoring_primitives


def test_builtin_profiles_validate_untyped_code_fences() -> None:
    register_builtin_profiles()
    content = "---\ntitle: Demo\n---\n\n# Demo\n\n```\nuntyped\n```\n"
    for profile in iter_profiles():
        issues = profile.validate(content, file_path="docs/demo.md")
        issue_types = {issue.type for issue in issues}
        assert "untyped_code_fence" in issue_types


def test_builtin_profiles_provide_migration_hints() -> None:
    register_builtin_profiles()
    profiles = {profile.framework: profile for profile in iter_profiles()}

    assert profiles[FrameworkName.DOCUSAURUS].migration_hints(FrameworkName.ZENSICAL)
    assert profiles[FrameworkName.VITEPRESS].migration_hints(FrameworkName.DOCUSAURUS)
    assert profiles[FrameworkName.STARLIGHT].migration_hints(FrameworkName.VITEPRESS)
    assert profiles[FrameworkName.ZENSICAL].migration_hints(FrameworkName.DOCUSAURUS)


def test_starlight_profile_detect_uses_package_signal_for_full_support(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies":{"@astrojs/starlight":"^0.30.0"}}')
    profile = StarlightProfile()

    detection = profile.detect(tmp_path)

    assert detection.support_level == SupportLevel.FULL
    assert "package.json:@astrojs/starlight" in detection.matched_signals


def test_starlight_profile_render_and_validate_edge_cases() -> None:
    profile = StarlightProfile()
    assert profile.render_snippet(AuthoringPrimitive.LINK) is None
    assert profile.render_snippet(AuthoringPrimitive.FRONTMATTER, topic="Demo") is not None

    empty_issues = profile.validate("", file_path="docs/empty.md")
    assert empty_issues[0].type == "empty_content"

    missing_structure = profile.validate("Body only", file_path="docs/body.md")
    issue_types = {issue.type for issue in missing_structure}
    assert "missing_frontmatter" in issue_types
    assert "missing_h1" in issue_types


def test_mkdocs_material_beats_generic_with_pyproject_signals(tmp_path: Path) -> None:
    """mkdocs.yml + material theme + pyproject zensical detects as mkdocs-material."""
    (tmp_path / "mkdocs.yml").write_text("theme:\n  name: material\n")
    (tmp_path / "pyproject.toml").write_text('[dependency-groups]\ndocs = ["zensical>=0.0.23"]\n')
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n")

    results = detect_frameworks(tmp_path)
    by_framework = {r.framework: r for r in results}

    material = by_framework[FrameworkName.MKDOCS_MATERIAL]
    generic = by_framework[FrameworkName.GENERIC_MARKDOWN]
    assert material.confidence > 0.5
    assert material.confidence > generic.confidence
    assert "mkdocs.yml" in material.matched_signals
    assert "theme:material" in material.matched_signals
    assert "pyproject:zensical" in material.matched_signals


def test_generic_markdown_confidence_reduced(tmp_path: Path) -> None:
    """Generic markdown detector has lower base confidence (0.25) for docs with .md files."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Hello\n")

    results = detect_frameworks(tmp_path)
    generic = next(r for r in results if r.framework == FrameworkName.GENERIC_MARKDOWN)
    assert generic.confidence == 0.25


def test_zensical_profile_detects_mkdocs_material_and_pyproject(tmp_path: Path) -> None:
    """ZensicalProfile detects mkdocs.yml with material theme and pyproject zensical dep."""
    (tmp_path / "mkdocs.yml").write_text("theme:\n  name: material\n")
    (tmp_path / "pyproject.toml").write_text('[dependency-groups]\ndocs = ["zensical>=0.0.23"]\n')

    profile = ZensicalProfile()
    result = profile.detect(tmp_path)
    assert result.confidence > 0.5
    assert "mkdocs.yml:material" in result.matched_signals
    assert "pyproject:zensical" in result.matched_signals
    assert result.support_level == SupportLevel.FULL

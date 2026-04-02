"""Framework authoring profiles, registry utilities, and detection helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkAdvantage
from mcp_zen_of_docs.models import FrameworkAdvantageReference
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import GeneralDocsReference
from mcp_zen_of_docs.models import SupportLevel

from .base import AuthoringProfile
from .base import clear_profile_registry
from .base import get_profile
from .base import iter_profiles
from .base import register_profile
from .docusaurus_profile import DocusaurusProfile
from .starlight_profile import StarlightProfile
from .vitepress_profile import VitePressProfile
from .zensical_profile import ZensicalProfile


_MATERIAL_PRIMITIVES: list[AuthoringPrimitive] = [
    AuthoringPrimitive.FRONTMATTER,
    AuthoringPrimitive.HEADING_H1,
    AuthoringPrimitive.ADMONITION,
    AuthoringPrimitive.CODE_FENCE,
    AuthoringPrimitive.NAVIGATION_ENTRY,
    AuthoringPrimitive.TABLE,
    AuthoringPrimitive.TABS,
    AuthoringPrimitive.IMAGE,
    AuthoringPrimitive.LINK,
]
_SPHINX_PRIMITIVES: list[AuthoringPrimitive] = [
    AuthoringPrimitive.HEADING_H1,
    AuthoringPrimitive.CODE_FENCE,
    AuthoringPrimitive.NAVIGATION_ENTRY,
    AuthoringPrimitive.TABLE,
    AuthoringPrimitive.LINK,
]
_GENERIC_PRIMITIVES: list[AuthoringPrimitive] = [
    AuthoringPrimitive.HEADING_H1,
    AuthoringPrimitive.CODE_FENCE,
    AuthoringPrimitive.TABLE,
    AuthoringPrimitive.TASK_LIST,
    AuthoringPrimitive.IMAGE,
    AuthoringPrimitive.LINK,
]
BUILTIN_PROFILES: tuple[AuthoringProfile, ...] = (
    ZensicalProfile(),
    DocusaurusProfile(),
    VitePressProfile(),
    StarlightProfile(),
)
_DETECTION_PRIORITY: dict[FrameworkName, int] = {
    FrameworkName.ZENSICAL: 70,
    FrameworkName.MKDOCS_MATERIAL: 60,
    FrameworkName.DOCUSAURUS: 50,
    FrameworkName.VITEPRESS: 40,
    FrameworkName.STARLIGHT: 30,
    FrameworkName.SPHINX: 20,
    FrameworkName.GENERIC_MARKDOWN: 10,
}
_FRAMEWORK_ADVANTAGES: tuple[FrameworkAdvantage, ...] = (
    FrameworkAdvantage(
        framework=FrameworkName.ZENSICAL,
        summary="Strong Python-native docs pipeline with rich MkDocs extension ecosystem.",
        strengths=[
            "First-class Python Markdown and extension support for advanced authoring primitives.",
            "Mkdocstrings integration enables API docs from Python docstrings with low friction.",
            "Theme customization and deployment flows are optimized for docs-as-code pipelines.",
            (
                "Theme customization with CSS variables and template overrides for branded"
                " documentation."
            ),
            "Mature deployment pipelines for GitHub Pages, Netlify, and self-hosted targets.",
        ],
        references=[
            FrameworkAdvantageReference(
                title="Zensical Getting Started",
                url="https://zensical.org/docs/get-started/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Python Markdown Extensions",
                url="https://zensical.org/docs/setup/extensions/python-markdown-extensions/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Mkdocstrings",
                url="https://zensical.org/docs/setup/extensions/mkdocstrings/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Setup Basics",
                url="https://zensical.org/docs/setup/basics/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Python Markdown",
                url="https://zensical.org/docs/setup/extensions/python-markdown/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Theme Customization",
                url="https://zensical.org/docs/setup/themes/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Deployment Guide",
                url="https://zensical.org/docs/deployment/",
            ),
            FrameworkAdvantageReference(
                title="Zensical Advanced Configuration",
                url="https://zensical.org/docs/setup/advanced/",
            ),
        ],
    ),
    FrameworkAdvantage(
        framework=FrameworkName.VITEPRESS,
        summary="Fast markdown-first authoring with strong navigation and theme APIs.",
        strengths=[
            (
                "Excellent markdown authoring ergonomics with custom containers and enhanced"
                " code blocks."
            ),
            "Flexible site/theme configuration for large docs navigation structures.",
            "Straightforward static deploy workflows across common hosting targets.",
            "Theme API enables building fully custom documentation experiences.",
            "Sidebar and navigation configuration scales to complex multi-section docs.",
        ],
        references=[
            FrameworkAdvantageReference(
                title="VitePress Markdown Guide",
                url="https://vitepress.dev/guide/markdown",
            ),
            FrameworkAdvantageReference(
                title="VitePress Site Config Reference",
                url="https://vitepress.dev/reference/site-config",
            ),
            FrameworkAdvantageReference(
                title="VitePress Deploy Guide",
                url="https://vitepress.dev/guide/deploy",
            ),
            FrameworkAdvantageReference(
                title="VitePress Theme API",
                url="https://vitepress.dev/reference/theme-api",
            ),
            FrameworkAdvantageReference(
                title="VitePress Sidebar & Navigation",
                url="https://vitepress.dev/guide/sidebar",
            ),
        ],
    ),
    FrameworkAdvantage(
        framework=FrameworkName.DOCUSAURUS,
        summary="Mature ecosystem for versioned docs, plugins, and operational scale.",
        strengths=[
            "Built-in versioning model for long-lived docs products.",
            "Plugin ecosystem supports search, analytics, and custom integrations.",
            "Strong markdown feature support with extensible site styling/layout controls.",
            (
                "Rich markdown features including Mermaid diagrams, math equations, and MDX"
                " components."
            ),
            (
                "Multi-platform deployment support with zero-config GitHub Pages, Netlify,"
                " and Vercel."
            ),
        ],
        references=[
            FrameworkAdvantageReference(
                title="Docusaurus Official Documentation",
                url="https://docusaurus.io/docs",
            ),
            FrameworkAdvantageReference(
                title="Docusaurus Versioning",
                url="https://docusaurus.io/docs/versioning",
            ),
            FrameworkAdvantageReference(
                title="Docusaurus Plugins",
                url="https://docusaurus.io/docs/plugins",
            ),
            FrameworkAdvantageReference(
                title="Docusaurus Markdown Features",
                url="https://docusaurus.io/docs/markdown-features",
            ),
            FrameworkAdvantageReference(
                title="Docusaurus Styling & Layout",
                url="https://docusaurus.io/docs/styling-layout",
            ),
            FrameworkAdvantageReference(
                title="Docusaurus Deployment",
                url="https://docusaurus.io/docs/deployment",
            ),
        ],
    ),
    FrameworkAdvantage(
        framework=FrameworkName.STARLIGHT,
        summary="Astro-based docs with strong component reuse and modern customization.",
        strengths=[
            "Composable component model for rich docs UX patterns.",
            "Theme and navigation controls work well for structured learning paths.",
            "Good deployment ergonomics for modern Jamstack workflows.",
            (
                "Component-based authoring enables reusable patterns like Tabs, Cards, and"
                " Aside elements."
            ),
            "Built-in sidebar and navigation with auto-generated breadcrumbs and pagination.",
        ],
        references=[
            FrameworkAdvantageReference(
                title="Starlight Getting Started",
                url="https://starlight.astro.build/getting-started/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Configuration Reference",
                url="https://starlight.astro.build/reference/configuration/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Deployment Guide",
                url="https://starlight.astro.build/guides/deployment/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Using Components",
                url="https://starlight.astro.build/components/using-components/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Pages Guide",
                url="https://starlight.astro.build/guides/pages/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Theme Customization",
                url="https://starlight.astro.build/guides/themes/",
            ),
            FrameworkAdvantageReference(
                title="Starlight Sidebar & Navigation",
                url="https://starlight.astro.build/guides/navigation/",
            ),
        ],
    ),
)


_GENERAL_DOCS_REFERENCES: tuple[GeneralDocsReference, ...] = (
    GeneralDocsReference(
        title="Google/Abseil Documentation Philosophy",
        url="https://abseil.io/resources/swe-book/html/ch10.html#design_docs",
        scope="Design docs methodology: clarity, audience focus, iterative development.",
    ),
    GeneralDocsReference(
        title="GitHub Docs Best Practices",
        url="https://docs.github.com/en/contributing/writing-for-github-docs/best-practices-for-github-docs",
        scope="README structure, contribution guidelines, and code documentation standards.",
    ),
    GeneralDocsReference(
        title="Documentation Done Right — A Developer's Guide",
        url="https://github.blog/developer-skills/documentation-done-right-a-developers-guide/",
        scope="Effective documentation covering clarity, organization, and maintenance.",
    ),
)


def _safe_text(path: Path) -> str:
    """Read UTF-8 text from ``path`` and return an empty string when missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _detect_mkdocs_material(project_root: Path) -> FrameworkDetectionResult:
    """Detect MkDocs Material signals from configuration files and dependency hints."""
    expected = [
        "mkdocs.yml",
        "mkdocs.yaml",
        "theme:material",
        "package.json:mkdocs-material",
        "pyproject:mkdocs-material",
        "pyproject:zensical",
    ]
    matched: list[str] = []
    mkdocs_path = project_root / "mkdocs.yml"
    alt_mkdocs_path = project_root / "mkdocs.yaml"
    for candidate in (mkdocs_path, alt_mkdocs_path):
        if candidate.exists():
            matched.append(candidate.name)
            mkdocs_data = yaml.safe_load(_safe_text(candidate)) or {}
            theme = mkdocs_data.get("theme")
            if (isinstance(theme, str) and theme.lower() == "material") or (
                isinstance(theme, dict) and str(theme.get("name", "")).lower() == "material"
            ):
                matched.append("theme:material")
    package_json = project_root / "package.json"
    if "mkdocs-material" in _safe_text(package_json):
        matched.append("package.json:mkdocs-material")
    pyproject_text = _safe_text(project_root / "pyproject.toml").lower()
    if pyproject_text:
        if "mkdocs-material" in pyproject_text:
            matched.append("pyproject:mkdocs-material")
        if "zensical" in pyproject_text:
            matched.append("pyproject:zensical")
    has_docs = (project_root / "docs").exists()
    support_level = SupportLevel.FULL if "theme:material" in matched else SupportLevel.PARTIAL
    if not matched and has_docs:
        support_level = SupportLevel.EXPERIMENTAL
    base = 0.1 if has_docs else 0.0
    strong_signals = {"mkdocs.yml", "mkdocs.yaml", "theme:material"}
    bonus = sum(0.25 if s in strong_signals else 0.2 for s in matched)
    confidence = min(1.0, base + bonus)
    return FrameworkDetectionResult(
        framework=FrameworkName.MKDOCS_MATERIAL,
        support_level=support_level,
        confidence=confidence,
        authoring_primitives=_MATERIAL_PRIMITIVES,
        matched_signals=matched,
        missing_signals=[signal for signal in expected if signal not in matched],
    )


def _detect_sphinx(project_root: Path) -> FrameworkDetectionResult:
    """Detect Sphinx signals from common config and dependency files."""
    expected = ["conf.py", "docs/conf.py", "requirements:sphinx", "pyproject:sphinx"]
    matched: list[str] = []
    if (project_root / "conf.py").exists():
        matched.append("conf.py")
    if (project_root / "docs" / "conf.py").exists():
        matched.append("docs/conf.py")
    if "sphinx" in _safe_text(project_root / "requirements.txt").lower():
        matched.append("requirements:sphinx")
    if "sphinx" in _safe_text(project_root / "pyproject.toml").lower():
        matched.append("pyproject:sphinx")
    support_level = SupportLevel.PARTIAL if matched else SupportLevel.EXPERIMENTAL
    confidence = min(0.95, 0.05 + (0.2 * len(matched)))
    return FrameworkDetectionResult(
        framework=FrameworkName.SPHINX,
        support_level=support_level,
        confidence=confidence,
        authoring_primitives=_SPHINX_PRIMITIVES,
        matched_signals=matched,
        missing_signals=[signal for signal in expected if signal not in matched],
    )


def _detect_generic_markdown(project_root: Path) -> FrameworkDetectionResult:
    """Fallback detector for generic Markdown docs under a ``docs`` directory."""
    expected = ["docs/**/*.md"]
    docs_root = project_root / "docs"
    markdown_files = list(docs_root.rglob("*.md")) if docs_root.exists() else []
    matched = ["docs/**/*.md"] if markdown_files else []
    confidence = 0.25 if markdown_files else 0.05
    return FrameworkDetectionResult(
        framework=FrameworkName.GENERIC_MARKDOWN,
        support_level=SupportLevel.PARTIAL if markdown_files else SupportLevel.EXPERIMENTAL,
        confidence=confidence,
        authoring_primitives=_GENERIC_PRIMITIVES,
        matched_signals=matched,
        missing_signals=[] if markdown_files else expected,
    )


def _ensure_builtin_profiles_registered() -> None:
    """Ensure built-in profile frameworks exist without overriding custom registrations."""
    registered = {profile.framework for profile in iter_profiles()}
    if all(profile.framework in registered for profile in BUILTIN_PROFILES):
        return
    register_builtin_profiles(replace=False)


def register_builtin_profiles(*, replace: bool = False) -> None:
    """Register built-in profiles without clobbering custom overrides by default."""
    for profile in BUILTIN_PROFILES:
        existing = get_profile(profile.framework)
        if existing is profile:
            continue
        if existing is None:
            register_profile(profile)
            continue
        if replace:
            register_profile(profile, replace=True)


def detect_frameworks(project_root: Path | str = ".") -> list[FrameworkDetectionResult]:
    """Return framework candidates sorted by descending detection confidence."""
    _ensure_builtin_profiles_registered()
    root = Path(project_root)
    detections = [profile.detect(root) for profile in iter_profiles()]
    detections.extend(
        (
            _detect_mkdocs_material(root),
            _detect_sphinx(root),
            _detect_generic_markdown(root),
        )
    )
    return sorted(
        detections,
        key=lambda result: (
            result.confidence,
            _DETECTION_PRIORITY.get(result.framework, 0),
        ),
        reverse=True,
    )


def detect_best_framework(project_root: Path | str = ".") -> FrameworkDetectionResult | None:
    """Return the highest-confidence framework candidate, if any are detected."""
    detections = detect_frameworks(project_root)
    return detections[0] if detections else None


def list_framework_advantages() -> list[FrameworkAdvantage]:
    """Return curated framework-specific advantage profiles and references."""
    return list(_FRAMEWORK_ADVANTAGES)


def list_general_docs_references() -> list[GeneralDocsReference]:
    """Return curated industry best-practice documentation references."""
    return list(_GENERAL_DOCS_REFERENCES)


__all__ = [
    "BUILTIN_PROFILES",
    "AuthoringProfile",
    "DocusaurusProfile",
    "StarlightProfile",
    "VitePressProfile",
    "ZensicalProfile",
    "clear_profile_registry",
    "detect_best_framework",
    "detect_frameworks",
    "get_profile",
    "iter_profiles",
    "list_framework_advantages",
    "list_general_docs_references",
    "register_builtin_profiles",
    "register_profile",
]

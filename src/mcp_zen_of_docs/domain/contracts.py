"""Domain-owned business contracts for framework and primitive semantics."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class FrameworkName(StrEnum):
    """Supported documentation framework identifiers.

    Attributes:
        MKDOCS_MATERIAL: Material for MkDocs — feature-rich theme with plugin ecosystem.
        ZENSICAL: Zensical — opinionated Markdown-first docs framework.
        DOCUSAURUS: Docusaurus — React-based documentation site generator by Meta.
        SPHINX: Sphinx — Python documentation generator with reStructuredText roots.
        VITEPRESS: VitePress — Vite-powered static site generator for Vue projects.
        STARLIGHT: Starlight — Astro-based documentation framework.
        GENERIC_MARKDOWN: Generic Markdown — plain Markdown without a specific framework.
    """

    MKDOCS_MATERIAL = "mkdocs-material"
    ZENSICAL = "zensical"
    DOCUSAURUS = "docusaurus"
    SPHINX = "sphinx"
    VITEPRESS = "vitepress"
    STARLIGHT = "starlight"
    GENERIC_MARKDOWN = "generic-markdown"


class AuthoringPrimitive(StrEnum):
    """Common authoring primitives used in documentation content.

    Each member represents a discrete content construct that documentation
    frameworks may support at varying levels.

    Attributes:
        FRONTMATTER: YAML frontmatter block at the top of a Markdown file.
        HEADING_H1: Top-level H1 heading.
        ADMONITION: Callout or alert block (note, warning, tip, etc.).
        CODE_FENCE: Fenced code block with optional language identifier.
        NAVIGATION_ENTRY: Entry in the site navigation or sidebar.
        SNIPPET: Reusable inline or block content snippet.
        TABLE: Markdown or HTML table.
        TASK_LIST: GitHub-flavoured task list with checkboxes.
        IMAGE: Embedded image with alt text and optional caption.
        LINK: Inline hyperlink or cross-reference.
        FOOTNOTE: Footnote reference and definition pair.
        TABS: Tabbed content panels.
        DIAGRAM: Embedded diagram (Mermaid, Graphviz, PlantUML).
        API_ENDPOINT: Structured API endpoint reference block.
        STEP_LIST: Numbered step-by-step procedure list.
        BADGE: Inline status badge (build, version, license).
        CARD_GRID: Grid of visual info cards (Material/Zensical-specific).
        BUTTON: Styled hyperlink rendered as a button.
        TOOLTIP: Hover tooltip attached to inline text.
        MATH: LaTeX or MathML mathematical expression.
        FORMATTING: Inline text formatting (bold, italic, strikethrough).
        ICONS_EMOJIS: Inline icon or emoji shortcode.
    """

    FRONTMATTER = "frontmatter"
    HEADING_H1 = "heading-h1"
    ADMONITION = "admonition"
    CODE_FENCE = "code-fence"
    NAVIGATION_ENTRY = "navigation-entry"
    SNIPPET = "snippet"
    TABLE = "table"
    TASK_LIST = "task-list"
    IMAGE = "image"
    LINK = "link"
    FOOTNOTE = "footnote"
    TABS = "tabs"
    DIAGRAM = "diagram"
    API_ENDPOINT = "api-endpoint"
    STEP_LIST = "step-list"
    BADGE = "badge"
    # Material for MkDocs / Zensical-specific
    CARD_GRID = "card-grid"
    BUTTON = "button"
    TOOLTIP = "tooltip"
    MATH = "math"
    FORMATTING = "formatting"
    ICONS_EMOJIS = "icons-emojis"


class SupportLevel(StrEnum):
    """Framework support coverage classification.

    Attributes:
        FULL: The primitive is natively and completely supported.
        PARTIAL: The primitive is supported with caveats or limited feature parity.
        EXPERIMENTAL: Support exists but is unstable or behind a feature flag.
        UNSUPPORTED: The primitive is not supported by the framework.
    """

    FULL = "full"
    PARTIAL = "partial"
    EXPERIMENTAL = "experimental"
    UNSUPPORTED = "unsupported"


class PrimitiveTranslationGuidance(BaseModel):
    """Domain guidance contract for primitive syntax translation.

    Carries support levels and optional rendered snippets for both source and
    target frameworks, along with actionable migration hints derived from domain
    rules and framework-specific knowledge.

    Attributes:
        source_support_level: Support classification in the source framework.
        target_support_level: Support classification in the target framework.
        source_snippet: Rendered primitive snippet for the source framework, or
            ``None`` when the primitive is unsupported.
        target_snippet: Rendered primitive snippet for the target framework, or
            ``None`` when the primitive is unsupported.
        hints: Ordered list of actionable migration guidance strings.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    source_support_level: SupportLevel = Field(description="Support in the source framework.")
    target_support_level: SupportLevel = Field(description="Support in the target framework.")
    source_snippet: str | None = Field(
        default=None,
        description="Rendered source framework snippet.",
    )
    target_snippet: str | None = Field(
        default=None,
        description="Rendered target framework snippet.",
    )
    hints: list[str] = Field(default_factory=list, description="Actionable migration guidance.")


class PrimitiveTranslationEvidence(BaseModel):
    """Observed compatibility evidence used to derive migration hints.

    Captures the primitive being translated, the two frameworks involved, their
    respective support levels, and optional rendered snippets for comparison.

    Attributes:
        primitive: Authoring primitive being translated between frameworks.
        source_framework: Documentation framework being migrated from.
        target_framework: Documentation framework being migrated to.
        source_support: Support level for the primitive in the source framework.
        target_support: Support level for the primitive in the target framework.
        source_snippet: Rendered primitive snippet for the source framework, or
            ``None`` when unsupported.
        target_snippet: Rendered primitive snippet for the target framework, or
            ``None`` when unsupported.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    primitive: AuthoringPrimitive = Field(description="Primitive being translated.")
    source_framework: FrameworkName = Field(description="Framework being migrated from.")
    target_framework: FrameworkName = Field(description="Framework being migrated to.")
    source_support: SupportLevel = Field(description="Source framework support level.")
    target_support: SupportLevel = Field(description="Target framework support level.")
    source_snippet: str | None = Field(
        default=None,
        description="Rendered source framework snippet.",
    )
    target_snippet: str | None = Field(
        default=None,
        description="Rendered target framework snippet.",
    )


def build_translation_hints(
    evidence: PrimitiveTranslationEvidence,
    *,
    target_framework_hints: list[str] | None = None,
) -> list[str]:
    """Apply domain migration rules to build actionable primitive translation hints.

    Inspects the evidence for unsupported primitives and differing source/target
    snippets, then appends any caller-supplied framework-specific hints.

    Args:
        evidence: Observed compatibility evidence containing the primitive,
            source and target frameworks, their support levels, and optional
            rendered snippets for direct comparison.
        target_framework_hints: Additional framework-specific hints to append
            after the rule-derived hints. Defaults to ``None``.

    Returns:
        Ordered list of actionable migration hint strings. May be empty when
        both frameworks fully support the primitive with identical syntax.
    """
    hints: list[str] = []
    if evidence.source_support is SupportLevel.UNSUPPORTED:
        hints.append(
            f"{evidence.source_framework.value} does not support "
            f"{evidence.primitive.value} directly."
        )
    if evidence.target_support is SupportLevel.UNSUPPORTED:
        hints.append(
            f"{evidence.target_framework.value} does not support "
            f"{evidence.primitive.value} directly."
        )
    if (
        evidence.source_snippet
        and evidence.target_snippet
        and evidence.source_snippet.strip() != evidence.target_snippet.strip()
    ):
        hints.append("Replace source syntax with target syntax shown in the target snippet.")
    if target_framework_hints:
        hints.extend(target_framework_hints)
    return hints


__all__ = [
    "AuthoringPrimitive",
    "FrameworkName",
    "PrimitiveTranslationEvidence",
    "PrimitiveTranslationGuidance",
    "SupportLevel",
    "build_translation_hints",
]

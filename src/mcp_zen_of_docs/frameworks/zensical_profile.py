"""Zensical framework authoring profile."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import StructureIssue
from mcp_zen_of_docs.models import SupportLevel

from .base import AuthoringProfile


__all__ = ["ZensicalProfile"]

if TYPE_CHECKING:
    from pathlib import Path

_CODE_FENCE_PATTERN = re.compile(r"^```([^\s`]*)", flags=re.MULTILINE)
_SUPPORT_MAP: dict[AuthoringPrimitive, SupportLevel] = dict.fromkeys(
    AuthoringPrimitive, SupportLevel.UNSUPPORTED
)
_SUPPORT_MAP.update(
    {
        AuthoringPrimitive.FRONTMATTER: SupportLevel.FULL,
        AuthoringPrimitive.HEADING_H1: SupportLevel.FULL,
        AuthoringPrimitive.ADMONITION: SupportLevel.FULL,
        AuthoringPrimitive.CODE_FENCE: SupportLevel.FULL,
        AuthoringPrimitive.NAVIGATION_ENTRY: SupportLevel.PARTIAL,
        AuthoringPrimitive.SNIPPET: SupportLevel.PARTIAL,
        AuthoringPrimitive.TABLE: SupportLevel.FULL,
        AuthoringPrimitive.TASK_LIST: SupportLevel.FULL,
        AuthoringPrimitive.IMAGE: SupportLevel.FULL,
        AuthoringPrimitive.LINK: SupportLevel.FULL,
        AuthoringPrimitive.FOOTNOTE: SupportLevel.FULL,
        AuthoringPrimitive.TABS: SupportLevel.FULL,
        AuthoringPrimitive.DIAGRAM: SupportLevel.FULL,
        AuthoringPrimitive.API_ENDPOINT: SupportLevel.PARTIAL,
        AuthoringPrimitive.STEP_LIST: SupportLevel.FULL,
        AuthoringPrimitive.BADGE: SupportLevel.FULL,
        # Material / Zensical-specific primitives
        AuthoringPrimitive.CARD_GRID: SupportLevel.FULL,
        AuthoringPrimitive.BUTTON: SupportLevel.FULL,
        AuthoringPrimitive.TOOLTIP: SupportLevel.FULL,
        AuthoringPrimitive.MATH: SupportLevel.FULL,
        AuthoringPrimitive.FORMATTING: SupportLevel.FULL,
        AuthoringPrimitive.ICONS_EMOJIS: SupportLevel.FULL,
    }
)
_SNIPPETS: dict[AuthoringPrimitive, str] = {
    AuthoringPrimitive.FRONTMATTER: (
        "---\ntitle: {topic}\ndescription: Page summary.\ntags: []\n---\n"
    ),
    AuthoringPrimitive.HEADING_H1: "# {topic}\n",
    AuthoringPrimitive.ADMONITION: "!!! note\n    Keep this page concise and actionable.\n",
    AuthoringPrimitive.CODE_FENCE: "```bash\nzensical build\n```\n",
    AuthoringPrimitive.SNIPPET: "!!! tip\n    Reuse this snippet for {topic} docs.\n",
    AuthoringPrimitive.TABS: (
        '=== "Option A"\n    Content for A.\n\n=== "Option B"\n    Content for B.\n'
    ),
    AuthoringPrimitive.DIAGRAM: "```mermaid\nflowchart LR\n    A[Start] --> B[End]\n```\n",
    AuthoringPrimitive.BADGE: (
        "![Build](https://img.shields.io/badge/build-passing-brightgreen)\n"
    ),
    AuthoringPrimitive.NAVIGATION_ENTRY: "- Topic: path/to/page.md\n",
    AuthoringPrimitive.TABLE: (
        "| Column A | Column B |\n|----------|----------|\n| value    | value    |\n"
    ),
    AuthoringPrimitive.TASK_LIST: "- [x] Completed task\n- [ ] Pending task\n",
    AuthoringPrimitive.IMAGE: '![Alt text](assets/image.png "Caption")\n',
    AuthoringPrimitive.LINK: "[Link text](https://example.com)\n",
    AuthoringPrimitive.FOOTNOTE: "Text with a footnote.[^1]\n\n[^1]: Footnote content.\n",
    AuthoringPrimitive.STEP_LIST: "1. First step\n2. Second step\n3. Third step\n",
    AuthoringPrimitive.API_ENDPOINT: (
        "```http\nGET /api/v1/resource\nAuthorization: Bearer <token>\n```\n"
    ),
    # Material / Zensical-specific primitives — require attr_list + md_in_html
    AuthoringPrimitive.CARD_GRID: (
        '<div class="grid cards" markdown>\n\n'
        "-   :material-star:{{ .lg .middle }} **{topic}**\n\n"
        "    ---\n\n"
        "    Short description of this item.\n\n"
        "    [:octicons-arrow-right-24: Learn more](page.md)\n\n"
        "-   :material-cog:{{ .lg .middle }} **Configuration**\n\n"
        "    ---\n\n"
        "    Configure {topic} with a single TOML block.\n\n"
        "    [:octicons-arrow-right-24: Reference](reference.md)\n\n"
        "</div>\n"
    ),
    AuthoringPrimitive.BUTTON: (
        "[Get started](getting-started.md){{ .md-button .md-button--primary }}"
        "  [View source](https://github.com){{ .md-button }}\n"
    ),
    AuthoringPrimitive.TOOLTIP: (
        "The :abbr:`MCP (Model Context Protocol)` server exposes 10 composite tools.\n\n"
        "*[MCP]: Model Context Protocol\n"
    ),
    AuthoringPrimitive.MATH: (
        "Inline: The quality score is $Q = \\frac{{s + f + p + h}}{{4}} \\times 100$.\n\n"
        "Block:\n\n"
        "$$\n"
        "Q = \\frac{{\\text{{structure}} + \\text{{frontmatter}}"
        " + \\text{{primitives}} + \\text{{hygiene}}}}{{4}} \\times 100\n"
        "$$\n"
    ),
    AuthoringPrimitive.FORMATTING: (
        "==Highlighted== text, ^^superscript^^, ~~strikethrough~~, "
        "H~2~O chemical formula.\n\n"
        "Keyboard shortcut: ++ctrl+shift+p++\n\n"
        "{{++Inserted++}} {{--deleted--}} {{~~old~>new~~}} critic markup.\n"
    ),
    AuthoringPrimitive.ICONS_EMOJIS: (
        ":material-check-circle:{{ .green }} All tests pass.\n"
        ":material-alert:{{ .orange }} Partial support — plugin required.\n"
        ":fontawesome-brands-github: [:octicons-mark-github-16: GitHub](https://github.com)\n"
    ),
}


class ZensicalProfile(AuthoringProfile):
    """Profile implementation for Zensical docs projects."""

    @property
    def framework(self) -> FrameworkName:
        """Return the framework identifier for this profile."""
        return FrameworkName.ZENSICAL

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        """Detect Zensical config signals in the project root."""
        signal_paths = ("zensical.toml", "zensical.yml", "zensical.yaml", ".zensical/config.yml")
        matched = [signal for signal in signal_paths if (project_root / signal).exists()]

        # Check mkdocs.yml / mkdocs.yaml with material theme as a Zensical signal.
        for mkdocs_name in ("mkdocs.yml", "mkdocs.yaml"):
            mkdocs_file = project_root / mkdocs_name
            if mkdocs_file.exists():
                import yaml  # noqa: PLC0415

                mkdocs_data = (
                    yaml.safe_load(
                        mkdocs_file.read_text(encoding="utf-8", errors="ignore"),
                    )
                    or {}
                )
                theme = mkdocs_data.get("theme")
                if (isinstance(theme, str) and theme.lower() == "material") or (
                    isinstance(theme, dict) and str(theme.get("name", "")).lower() == "material"
                ):
                    matched.append(f"{mkdocs_name}:material")

        # Check pyproject.toml for zensical dependency.
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_text = pyproject_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "zensical" in pyproject_text:
                matched.append("pyproject:zensical")

        support_level = SupportLevel.FULL if matched else SupportLevel.EXPERIMENTAL
        # zensical.toml is the primary project-level config — full confidence on its own
        if "zensical.toml" in matched:
            confidence = 1.0
        else:
            confidence = 0.3 + (0.25 * len(matched)) if matched else 0.15
        return FrameworkDetectionResult(
            framework=self.framework,
            support_level=support_level,
            confidence=min(confidence, 1.0),
            authoring_primitives=list(_SUPPORT_MAP),
            matched_signals=matched,
            missing_signals=[signal for signal in signal_paths if signal not in matched],
        )

    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        """Render a Zensical-flavored snippet for a primitive."""
        template = _SNIPPETS.get(primitive)
        if template is None:
            return None
        return template.format(topic=topic or "Documentation Topic")

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        """Validate content against Zensical authoring conventions."""
        file_ref = file_path or "<memory>"
        issues: list[StructureIssue] = []
        if not content.strip():
            return [
                StructureIssue(
                    type="empty_content",
                    file=file_ref,
                    detail="Content is empty. Add frontmatter and a top-level heading.",
                )
            ]
        if not content.startswith("---\n"):
            issues.append(
                StructureIssue(
                    type="missing_frontmatter",
                    file=file_ref,
                    detail=(
                        "Expected YAML frontmatter starting with '---' and including page metadata."
                    ),
                )
            )
        if not re.search(r"^#\s+\S+", content, flags=re.MULTILINE):
            issues.append(
                StructureIssue(
                    type="missing_h1",
                    file=file_ref,
                    detail="Expected a level-1 heading in the form '# Title'.",
                )
            )
        issues.extend(
            StructureIssue(
                type="untyped_code_fence",
                file=file_ref,
                detail="Code fence should include a language tag after ``` (for example ```bash).",
            )
            for match in _CODE_FENCE_PATTERN.finditer(content)
            if not match.group(1).strip()
        )
        return issues

    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        """Return support coverage for the requested primitive."""
        return _SUPPORT_MAP.get(primitive, SupportLevel.UNSUPPORTED)

    def migration_hints(self, source_framework: FrameworkName) -> list[str]:
        """Return Zensical-focused migration hints from another framework."""
        hints = [
            "Prefer MkDocs-compatible Markdown and avoid framework-specific MDX/Astro components.",
        ]
        if source_framework in {FrameworkName.DOCUSAURUS, FrameworkName.VITEPRESS}:
            hints.append(
                "Convert directive-style admonitions (`:::`) into MkDocs admonitions (`!!!`)."
            )
        if source_framework is FrameworkName.STARLIGHT:
            hints.append(
                "Replace Astro component syntax with plain Markdown blocks and fenced code."
            )
        return hints

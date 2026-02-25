"""Docusaurus framework authoring profile."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import StructureIssue
from mcp_zen_of_docs.models import SupportLevel

from .base import AuthoringProfile


__all__ = ["DocusaurusProfile"]

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
        AuthoringPrimitive.NAVIGATION_ENTRY: SupportLevel.FULL,
        AuthoringPrimitive.SNIPPET: SupportLevel.PARTIAL,
        AuthoringPrimitive.TABLE: SupportLevel.FULL,
        AuthoringPrimitive.TASK_LIST: SupportLevel.FULL,
        AuthoringPrimitive.IMAGE: SupportLevel.FULL,
        AuthoringPrimitive.LINK: SupportLevel.FULL,
        AuthoringPrimitive.FOOTNOTE: SupportLevel.PARTIAL,
        AuthoringPrimitive.TABS: SupportLevel.PARTIAL,
        AuthoringPrimitive.DIAGRAM: SupportLevel.PARTIAL,
        AuthoringPrimitive.API_ENDPOINT: SupportLevel.PARTIAL,
        AuthoringPrimitive.STEP_LIST: SupportLevel.FULL,
        AuthoringPrimitive.BADGE: SupportLevel.PARTIAL,
    }
)
_SNIPPETS: dict[AuthoringPrimitive, str] = {
    AuthoringPrimitive.FRONTMATTER: "---\ntitle: {topic}\nsidebar_position: 1\n---\n",
    AuthoringPrimitive.HEADING_H1: "# {topic}\n",
    AuthoringPrimitive.ADMONITION: ":::note\nUse MDX directives for callouts.\n:::\n",
    AuthoringPrimitive.CODE_FENCE: ("```tsx\nexport const Demo = () => <p>Hello</p>;\n```\n"),
    AuthoringPrimitive.SNIPPET: (
        "import Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n"
    ),
    AuthoringPrimitive.TABS: (
        "import Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n\n"
        '<Tabs>\n  <TabItem value="a" label="Option A">Content A</TabItem>\n'
        '  <TabItem value="b" label="Option B">Content B</TabItem>\n</Tabs>\n'
    ),
    AuthoringPrimitive.DIAGRAM: "```mermaid\nflowchart LR\n    A[Start] --> B[End]\n```\n",
    AuthoringPrimitive.BADGE: (
        "![Build](https://img.shields.io/badge/build-passing-brightgreen)\n"
    ),
    AuthoringPrimitive.NAVIGATION_ENTRY: (
        "{\n  type: 'doc',\n  id: 'my-page',\n  label: 'My Page',\n}\n"
    ),
    AuthoringPrimitive.TABLE: (
        "| Column A | Column B |\n|----------|----------|\n| value    | value    |\n"
    ),
    AuthoringPrimitive.TASK_LIST: "- [x] Completed task\n- [ ] Pending task\n",
    AuthoringPrimitive.IMAGE: "![Alt text](./assets/image.png)\n",
    AuthoringPrimitive.LINK: "[Link text](https://example.com)\n",
    AuthoringPrimitive.FOOTNOTE: "Text with footnote[^1].\n\n[^1]: The footnote.\n",
    AuthoringPrimitive.STEP_LIST: "1. First step\n2. Second step\n3. Third step\n",
    AuthoringPrimitive.API_ENDPOINT: (
        "```http\nGET /api/v1/resource\nAuthorization: Bearer <token>\n```\n"
    ),
}


class DocusaurusProfile(AuthoringProfile):
    """Profile implementation for Docusaurus docs projects."""

    @property
    def framework(self) -> FrameworkName:
        """Return the framework identifier for this profile."""
        return FrameworkName.DOCUSAURUS

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        """Detect Docusaurus by config files and package dependencies."""
        config_signals = (
            "docusaurus.config.ts",
            "docusaurus.config.js",
            "docusaurus.config.mjs",
            "docusaurus.config.cjs",
            "sidebars.ts",
            "sidebars.js",
        )
        matched = [signal for signal in config_signals if (project_root / signal).exists()]
        package_json = project_root / "package.json"
        if package_json.exists() and "@docusaurus/core" in package_json.read_text(
            encoding="utf-8", errors="ignore"
        ):
            matched.append("package.json:@docusaurus/core")
        support_level = (
            SupportLevel.FULL
            if any("docusaurus.config" in hit for hit in matched)
            else SupportLevel.PARTIAL
        )
        confidence = min(1.0, 0.2 + (0.18 * len(matched)))
        return FrameworkDetectionResult(
            framework=self.framework,
            support_level=support_level,
            confidence=confidence,
            authoring_primitives=list(_SUPPORT_MAP),
            matched_signals=matched,
            missing_signals=[signal for signal in config_signals if signal not in matched],
        )

    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        """Render a Docusaurus-flavored snippet for a primitive."""
        snippet = _SNIPPETS.get(primitive)
        if snippet is None:
            return None
        return snippet.format(topic=topic or "Documentation Topic")

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        """Validate content against Docusaurus authoring expectations."""
        file_ref = file_path or "<memory>"
        issues: list[StructureIssue] = []
        if not content.strip():
            return [
                StructureIssue(
                    type="empty_content",
                    file=file_ref,
                    detail="Content is empty. Add frontmatter and a page title before publishing.",
                )
            ]
        if not content.startswith("---\n"):
            issues.append(
                StructureIssue(
                    type="missing_frontmatter",
                    file=file_ref,
                    detail=(
                        "Expected YAML frontmatter starting with '---' "
                        "and including at least title."
                    ),
                )
            )
        if not re.search(r"^#\s+\S+", content, flags=re.MULTILINE) and "title:" not in content:
            issues.append(
                StructureIssue(
                    type="missing_title",
                    file=file_ref,
                    detail="Expected '# Title' heading or a 'title:' key in frontmatter.",
                )
            )
        issues.extend(
            StructureIssue(
                type="untyped_code_fence",
                file=file_ref,
                detail="Code fence should include a language tag after ``` (for example ```ts).",
            )
            for match in _CODE_FENCE_PATTERN.finditer(content)
            if not match.group(1).strip()
        )
        return issues

    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        """Return support coverage for the requested primitive."""
        return _SUPPORT_MAP.get(primitive, SupportLevel.UNSUPPORTED)

    def migration_hints(self, source_framework: FrameworkName) -> list[str]:
        """Return Docusaurus-focused migration hints from another framework."""
        hints = [
            "Prefer frontmatter with 'title' and optional 'sidebar_position' for docs pages.",
        ]
        if source_framework in {FrameworkName.ZENSICAL, FrameworkName.MKDOCS_MATERIAL}:
            hints.append(
                "Convert MkDocs-style admonitions (`!!! note`) "
                "to Docusaurus directives (`:::note`)."
            )
        if source_framework in {FrameworkName.STARLIGHT, FrameworkName.VITEPRESS}:
            hints.append(
                "Replace framework-specific tab/admonition components "
                "with Docusaurus MDX components."
            )
        return hints

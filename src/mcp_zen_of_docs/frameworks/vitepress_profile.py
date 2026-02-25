"""VitePress framework authoring profile."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import StructureIssue
from mcp_zen_of_docs.models import SupportLevel

from .base import AuthoringProfile


__all__ = ["VitePressProfile"]

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
        AuthoringPrimitive.TABS: SupportLevel.FULL,
        AuthoringPrimitive.DIAGRAM: SupportLevel.PARTIAL,
        AuthoringPrimitive.API_ENDPOINT: SupportLevel.PARTIAL,
        AuthoringPrimitive.STEP_LIST: SupportLevel.FULL,
        AuthoringPrimitive.BADGE: SupportLevel.PARTIAL,
    }
)
_SNIPPETS: dict[AuthoringPrimitive, str] = {
    AuthoringPrimitive.FRONTMATTER: "---\ntitle: {topic}\noutline: [2, 3]\n---\n",
    AuthoringPrimitive.HEADING_H1: "# {topic}\n",
    AuthoringPrimitive.ADMONITION: "::: info\nVitePress supports custom containers.\n:::\n",
    AuthoringPrimitive.CODE_FENCE: "```ts\nexport const enabled = true\n```\n",
    AuthoringPrimitive.SNIPPET: "```md\n@[code](/path/to/example.ts)\n```\n",
    AuthoringPrimitive.TABS: (
        "::: code-group\n```ts [TypeScript]\nconst x: number = 1\n```\n"
        "```js [JavaScript]\nconst x = 1\n```\n:::\n"
    ),
    AuthoringPrimitive.DIAGRAM: "```mermaid\nflowchart LR\n    A[Start] --> B[End]\n```\n",
    AuthoringPrimitive.BADGE: '<Badge type="info" text="v2.0" />\n',
    AuthoringPrimitive.NAVIGATION_ENTRY: "{ text: 'Page', link: '/path/to/page' },\n",
    AuthoringPrimitive.TABLE: (
        "| Column A | Column B |\n|----------|----------|\n| value    | value    |\n"
    ),
    AuthoringPrimitive.TASK_LIST: "- [x] Completed task\n- [ ] Pending task\n",
    AuthoringPrimitive.IMAGE: "![Alt text](./assets/image.png)\n",
    AuthoringPrimitive.LINK: "[Link text](https://example.com)\n",
    AuthoringPrimitive.FOOTNOTE: "Text with footnote.[^1]\n\n[^1]: The footnote.\n",
    AuthoringPrimitive.STEP_LIST: "1. First step\n2. Second step\n3. Third step\n",
    AuthoringPrimitive.API_ENDPOINT: (
        "```http\nGET /api/v1/resource\nAuthorization: Bearer <token>\n```\n"
    ),
}


class VitePressProfile(AuthoringProfile):
    """Profile implementation for VitePress docs projects."""

    @property
    def framework(self) -> FrameworkName:
        """Return the framework identifier for this profile."""
        return FrameworkName.VITEPRESS

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        """Detect VitePress signals in the project root."""
        config_signals = (".vitepress/config.ts", ".vitepress/config.js", ".vitepress/config.mjs")
        matched = [signal for signal in config_signals if (project_root / signal).exists()]
        package_json = project_root / "package.json"
        if package_json.exists() and "vitepress" in package_json.read_text(
            encoding="utf-8", errors="ignore"
        ):
            matched.append("package.json:vitepress")
        support_level = (
            SupportLevel.FULL
            if any(".vitepress/config" in hit for hit in matched)
            else SupportLevel.PARTIAL
        )
        confidence = min(1.0, 0.2 + (0.2 * len(matched)))
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
        """Render a VitePress-flavored snippet for a primitive."""
        snippet = _SNIPPETS.get(primitive)
        if snippet is None:
            return None
        return snippet.format(topic=topic or "Documentation Topic")

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        """Validate content against VitePress authoring conventions."""
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
        """Return VitePress-focused migration hints from another framework."""
        hints = [
            "Map navigation and sidebar structure into '.vitepress/config.*' after page migration.",
        ]
        if source_framework is FrameworkName.DOCUSAURUS:
            hints.append(
                "Convert Docusaurus MDX directives/components to VitePress container syntax."
            )
        if source_framework in {FrameworkName.ZENSICAL, FrameworkName.MKDOCS_MATERIAL}:
            hints.append(
                "Review MkDocs tab syntax (`===`) and migrate to VitePress tab/code-group blocks."
            )
        if source_framework is FrameworkName.STARLIGHT:
            hints.append(
                "Replace Astro component syntax with Markdown + VitePress container directives."
            )
        return hints

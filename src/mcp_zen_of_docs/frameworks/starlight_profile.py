"""Starlight framework authoring profile."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from mcp_zen_of_docs.models import AuthoringPrimitive
from mcp_zen_of_docs.models import FrameworkDetectionResult
from mcp_zen_of_docs.models import FrameworkName
from mcp_zen_of_docs.models import StructureIssue
from mcp_zen_of_docs.models import SupportLevel

from .base import AuthoringProfile


__all__ = ["StarlightProfile"]

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
        AuthoringPrimitive.ADMONITION: SupportLevel.PARTIAL,
        AuthoringPrimitive.CODE_FENCE: SupportLevel.FULL,
        AuthoringPrimitive.NAVIGATION_ENTRY: SupportLevel.PARTIAL,
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
    AuthoringPrimitive.FRONTMATTER: "---\ntitle: {topic}\ndescription: Quick summary.\n---\n",
    AuthoringPrimitive.HEADING_H1: "# {topic}\n",
    AuthoringPrimitive.ADMONITION: ":::tip\nStarlight supports Astro-flavored callouts.\n:::\n",
    AuthoringPrimitive.CODE_FENCE: "```astro\n---\nconst title = 'Hello';\n---\n```\n",
    AuthoringPrimitive.SNIPPET: '```mdx\n<Code from="./snippet.ts" />\n```\n',
    AuthoringPrimitive.TABS: (
        "import { Tabs, TabItem } from '@astrojs/starlight/components';\n\n"
        '<Tabs>\n  <TabItem label="Option A">Content A</TabItem>\n'
        '  <TabItem label="Option B">Content B</TabItem>\n</Tabs>\n'
    ),
    AuthoringPrimitive.DIAGRAM: "```mermaid\nflowchart LR\n    A[Start] --> B[End]\n```\n",
    AuthoringPrimitive.BADGE: (
        "import { Badge } from '@astrojs/starlight/components';\n\n"
        '<Badge text="New" variant="tip" />\n'
    ),
    AuthoringPrimitive.NAVIGATION_ENTRY: "{ label: 'Page', link: '/guides/page' },\n",
    AuthoringPrimitive.TABLE: (
        "| Column A | Column B |\n|----------|----------|\n| value    | value    |\n"
    ),
    AuthoringPrimitive.TASK_LIST: "- [x] Completed task\n- [ ] Pending task\n",
    AuthoringPrimitive.IMAGE: "![Alt text](../../assets/image.png)\n",
    # LINK is standard Markdown — no framework-specific snippet needed; render_snippet returns None
    AuthoringPrimitive.FOOTNOTE: "Text with footnote.[^1]\n\n[^1]: The footnote.\n",
    AuthoringPrimitive.STEP_LIST: "1. First step\n2. Second step\n3. Third step\n",
    AuthoringPrimitive.API_ENDPOINT: (
        "```http\nGET /api/v1/resource\nAuthorization: Bearer <token>\n```\n"
    ),
}


class StarlightProfile(AuthoringProfile):
    """Profile implementation for Astro Starlight docs projects."""

    @property
    def framework(self) -> FrameworkName:
        """Return the framework identifier for this profile."""
        return FrameworkName.STARLIGHT

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        """Detect Astro Starlight signals in the project root."""
        signal_paths = ("astro.config.mjs", "astro.config.ts", "astro.config.js")
        matched = [signal for signal in signal_paths if (project_root / signal).exists()]
        package_json = project_root / "package.json"
        if package_json.exists() and "@astrojs/starlight" in package_json.read_text(
            encoding="utf-8", errors="ignore"
        ):
            matched.append("package.json:@astrojs/starlight")
        support_level = (
            SupportLevel.FULL
            if "package.json:@astrojs/starlight" in matched
            else SupportLevel.PARTIAL
        )
        confidence = min(1.0, 0.2 + (0.2 * len(matched)))
        return FrameworkDetectionResult(
            framework=self.framework,
            support_level=support_level,
            confidence=confidence,
            authoring_primitives=list(_SUPPORT_MAP),
            matched_signals=matched,
            missing_signals=[signal for signal in signal_paths if signal not in matched],
        )

    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        """Render a Starlight-flavored snippet for a primitive."""
        snippet = _SNIPPETS.get(primitive)
        if snippet is None:
            return None
        return snippet.format(topic=topic or "Documentation Topic")

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        """Validate content against Starlight authoring conventions."""
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
                detail="Code fence should include a language tag after ``` (for example ```astro).",
            )
            for match in _CODE_FENCE_PATTERN.finditer(content)
            if not match.group(1).strip()
        )
        return issues

    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        """Return support coverage for the requested primitive."""
        return _SUPPORT_MAP.get(primitive, SupportLevel.UNSUPPORTED)

    def migration_hints(self, source_framework: FrameworkName) -> list[str]:
        """Return Starlight-focused migration hints from another framework."""
        hints = [
            "Prefer Astro/Starlight-native components for advanced UI primitives "
            "(tabs, badges, callouts).",
        ]
        if source_framework is FrameworkName.DOCUSAURUS:
            hints.append("Convert Docusaurus MDX components to Astro component imports/usage.")
        if source_framework is FrameworkName.VITEPRESS:
            hints.append(
                "Replace VitePress container directives with Starlight-compatible Astro syntax."
            )
        if source_framework in {FrameworkName.ZENSICAL, FrameworkName.MKDOCS_MATERIAL}:
            hints.append(
                "Translate MkDocs admonition blocks (`!!!`) into Starlight callout patterns."
            )
        return hints

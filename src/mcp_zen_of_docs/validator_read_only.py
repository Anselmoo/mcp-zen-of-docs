"""Read-only documentation validation helpers."""

from __future__ import annotations

import collections.abc
import re
import tomllib

from pathlib import Path
from typing import Literal

import yaml

from .frameworks import detect_best_framework
from .frameworks.material_profile import DEFAULT_FRONTMATTER_KEYS
from .models import AuthoringPrimitive
from .models import CheckDocsLinksRequest
from .models import CheckDocsLinksResponse
from .models import CheckLanguageStructureRequest
from .models import CheckLanguageStructureResponse
from .models import CheckOrphanDocsResponse
from .models import LinkIssue
from .models import QualityIssue
from .models import QualityScore
from .models import ScoreDocsQualityRequest
from .models import ScoreDocsQualityResponse
from .models import StructureIssue


__all__ = [
    "_find_and_load_docs_config",
    "check_docs_links",
    "check_language_structure",
    "check_orphan_docs",
    "score_docs_quality",
]


LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CODE_FENCE_PATTERN = re.compile(r"^```([^\s`]*)", flags=re.MULTILINE)
ADMONITION_PATTERN = re.compile(r"(^!!!\s+\w+|^:::\s*\w+|<Aside)", flags=re.MULTILINE)
TASK_LIST_PATTERN = re.compile(r"^\s*-\s+\[[ xX]\]\s+", flags=re.MULTILINE)
TABLE_PATTERN = re.compile(r"^\|.+\|\s*$", flags=re.MULTILINE)
TABS_PATTERN = re.compile(r'(^===\s+"|<Tabs|:::\s*code-group)', flags=re.MULTILINE)
DIAGRAM_PATTERN = re.compile(r"```(?:mermaid|graphviz|plantuml)", flags=re.MULTILINE)
API_ENDPOINT_PATTERN = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/[^\s`]+")
STEP_LIST_PATTERN = re.compile(r"^\d+\.\s+\S", flags=re.MULTILINE)
BADGE_PATTERN = re.compile(r"!\[[^\]]*]\([^)]*shields\.io[^)]*\)")
MIN_PRIMITIVE_VARIETY = 2
MAX_DOC_LINE_LENGTH = 120
_CONFIG_CANDIDATES: tuple[str, ...] = ("zensical.toml", "mkdocs.yml", "mkdocs.yaml")


def _load_docs_config(
    docs_root: Path,
) -> tuple[Path, dict[str, object]] | tuple[None, None]:
    """Detect and parse the framework config file."""
    for name in _CONFIG_CANDIDATES:
        candidate = docs_root / name
        if not candidate.exists():
            continue
        if candidate.suffix == ".toml":
            with candidate.open("rb") as fh:
                return candidate, tomllib.load(fh)
        with candidate.open() as fh:
            return candidate, yaml.safe_load(fh) or {}
    return None, None


def _find_and_load_docs_config(
    docs_root: Path,
) -> tuple[Path, dict[str, object]] | tuple[None, None]:
    """Find and parse the framework config file in docs_root or its parent."""
    for search_dir in (docs_root, docs_root.parent):
        for name in _CONFIG_CANDIDATES:
            candidate = search_dir / name
            if not candidate.exists():
                continue
            if candidate.suffix == ".toml":
                with candidate.open("rb") as fh:
                    return candidate, tomllib.load(fh)
            with candidate.open() as fh:
                return candidate, yaml.safe_load(fh) or {}
    return None, None


def _compute_code_hygiene(docs_root: Path) -> float:
    """Score code hygiene across all Markdown files in docs_root."""
    fence_pattern = re.compile(r"^[ \t]*(```+|~~~+)(.*)")

    total_lines = 0
    issue_lines = 0
    md_files = [
        path
        for path in (list(docs_root.rglob("*.md")) + list(docs_root.rglob("*.mdx")))
        if "includes" not in path.parts
    ]
    if not md_files:
        return 1.0

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        stack: list[tuple[str, int]] = []
        for line in content.splitlines():
            total_lines += 1
            if len(line) > MAX_DOC_LINE_LENGTH:
                issue_lines += 1
                continue
            match = fence_pattern.match(line)
            if not match:
                continue
            fence_chars, rest = match.group(1), match.group(2)
            fence_char = fence_chars[0]
            fence_len = len(fence_chars)
            rest_stripped = rest.strip()
            if (
                stack
                and stack[-1][0] == fence_char
                and fence_len >= stack[-1][1]
                and not rest_stripped
            ):
                stack.pop()
            else:
                lang = rest_stripped.split()[0].split("{")[0].split("[")[0] if rest_stripped else ""
                if not lang:
                    issue_lines += 1
                stack.append((fence_char, fence_len))

    if total_lines == 0:
        return 1.0

    ratio = issue_lines / total_lines
    return max(0.0, 1.0 - ratio * 10)


def _detect_primitives(frontmatter: dict[str, object], body: str) -> set[AuthoringPrimitive]:
    """Detect documentation primitives present in a page."""
    primitives: set[AuthoringPrimitive] = set()
    if frontmatter:
        primitives.add(AuthoringPrimitive.FRONTMATTER)
    primitive_checks = (
        (
            AuthoringPrimitive.HEADING_H1,
            re.search(r"^#\s+\S+", body, flags=re.MULTILINE)
            or re.search(r"<h1[\s>]", body, flags=re.IGNORECASE),
        ),
        (AuthoringPrimitive.ADMONITION, ADMONITION_PATTERN.search(body)),
        (AuthoringPrimitive.CODE_FENCE, CODE_FENCE_PATTERN.search(body)),
        (AuthoringPrimitive.TABLE, TABLE_PATTERN.search(body)),
        (AuthoringPrimitive.TASK_LIST, TASK_LIST_PATTERN.search(body)),
        (AuthoringPrimitive.IMAGE, re.search(r"!\[[^\]]*]\([^)]+\)", body)),
        (AuthoringPrimitive.LINK, LINK_PATTERN.search(body)),
        (AuthoringPrimitive.TABS, TABS_PATTERN.search(body)),
        (AuthoringPrimitive.DIAGRAM, DIAGRAM_PATTERN.search(body)),
        (AuthoringPrimitive.API_ENDPOINT, API_ENDPOINT_PATTERN.search(body)),
        (AuthoringPrimitive.STEP_LIST, STEP_LIST_PATTERN.search(body)),
        (AuthoringPrimitive.BADGE, BADGE_PATTERN.search(body)),
    )
    primitives.update(primitive for primitive, matched in primitive_checks if matched)
    return primitives


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _count_untyped_opening_fences(body: str) -> int:
    """Count opening code fences that have no language identifier."""
    untyped = 0
    stack: list[tuple[str, int]] = []
    fence_pattern = re.compile(r"^[ \t]*(```+|~~~+)(.*)")

    for line in body.splitlines():
        match = fence_pattern.match(line)
        if not match:
            continue
        fence_chars, rest = match.group(1), match.group(2)
        fence_char = fence_chars[0]
        fence_len = len(fence_chars)
        rest_stripped = rest.strip()

        if stack and stack[-1][0] == fence_char and fence_len >= stack[-1][1] and not rest_stripped:
            stack.pop()
            continue

        lang = rest_stripped.split()[0] if rest_stripped else ""
        lang = lang.split("{")[0].split("[")[0]
        if not lang:
            untyped += 1
        stack.append((fence_char, fence_len))

    return untyped


def _markdown_files(docs_root: Path) -> list[Path]:
    return sorted(
        path for path in docs_root.rglob("*.md") if path.is_file() and "includes" not in path.parts
    )


def _split_frontmatter(content: str) -> tuple[dict[str, object], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    raw = content[4:end]
    body = content[end + 5 :]
    return (yaml.safe_load(raw) or {}), body


def _flatten_nav(nav: object | None) -> set[str]:
    """Flatten navigation structures into a set of referenced file paths."""
    referenced: set[str] = set()
    if nav is None or isinstance(nav, (str, bytes)):
        return referenced
    if not isinstance(nav, collections.abc.Sequence):
        return referenced
    for item in nav:
        if isinstance(item, str):
            referenced.add(item)
            continue
        if isinstance(item, dict):
            for value in item.values():
                if isinstance(value, str):
                    referenced.add(value)
                elif isinstance(value, list):
                    referenced.update(_flatten_nav(value))
    return referenced


def _resolve_doc_target(file_path: Path, raw_target: str) -> Path:
    """Resolve a raw Markdown target relative to the file containing it."""
    target = raw_target.split("#", 1)[0].split("?", 1)[0]
    return (file_path.parent / target).resolve()


def check_docs_links(
    docs_root: Path | str = "docs", external_mode: str = "report"
) -> CheckDocsLinksResponse:
    """Check internal links and optionally report external links."""
    normalized_external_mode: Literal["report", "ignore"]
    normalized_external_mode = "report" if external_mode == "report" else "ignore"
    request = CheckDocsLinksRequest(
        docs_root=Path(docs_root),
        external_mode=normalized_external_mode,
    )
    docs_path = request.docs_root
    if not docs_path.exists():
        return CheckDocsLinksResponse(
            status="error",
            docs_root=request.docs_root,
            message="docs_root does not exist.",
        )

    issues: list[LinkIssue] = []
    for file_path in _markdown_files(docs_path):
        content = file_path.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(content):
            if raw_target.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if raw_target.startswith(("http://", "https://")):
                if request.external_mode == "report":
                    issues.append(
                        LinkIssue(type="external_unchecked", file=str(file_path), target=raw_target)
                    )
                continue
            target = _resolve_doc_target(file_path, raw_target)
            exists = target.exists() or (target.is_dir() and (target / "index.md").exists())
            if not exists:
                issues.append(
                    LinkIssue(type="missing_internal_link", file=str(file_path), target=raw_target)
                )

    missing_count = sum(1 for issue in issues if issue.type == "missing_internal_link")
    return CheckDocsLinksResponse(
        status="success" if missing_count == 0 else "warning",
        docs_root=request.docs_root,
        issues=issues,
        missing_internal_count=missing_count,
    )


def check_orphan_docs(
    docs_root: Path | str = "docs", mkdocs_file: Path | str | None = None
) -> CheckOrphanDocsResponse:
    """Find docs files that are not referenced in the nav configuration."""
    docs_path = Path(docs_root)
    explicit_path = Path(mkdocs_file) if mkdocs_file is not None else None
    if not docs_path.exists():
        return CheckOrphanDocsResponse(
            status="error",
            docs_root=docs_path,
            mkdocs_file=explicit_path or Path("mkdocs.yml"),
            message="docs_root or mkdocs_file does not exist.",
        )

    detected_config: Path | None = None
    if explicit_path is not None and explicit_path.exists():
        config_path: Path | None = explicit_path
        config_data: dict[str, object] | None = None
    elif explicit_path is not None:
        return CheckOrphanDocsResponse(
            status="error",
            docs_root=docs_path,
            mkdocs_file=explicit_path,
            message="docs_root or mkdocs_file does not exist.",
        )
    else:
        found_path, found_data = _find_and_load_docs_config(docs_path)
        if found_path is None:
            return CheckOrphanDocsResponse(
                status="error",
                docs_root=docs_path,
                mkdocs_file=Path("mkdocs.yml"),
                message="No docs config found (tried zensical.toml, mkdocs.yml, mkdocs.yaml).",
            )
        config_path = found_path
        config_data = found_data
        detected_config = found_path

    if config_data is None and config_path is not None:
        if config_path.suffix == ".toml":
            with config_path.open("rb") as fh:
                config_data = tomllib.load(fh)
        else:
            config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    nav_raw = (config_data or {}).get("nav")
    referenced = _flatten_nav(nav_raw)
    docs_files = {path.relative_to(docs_path).as_posix() for path in _markdown_files(docs_path)}
    orphans = sorted(docs_files - referenced)
    return CheckOrphanDocsResponse(
        status="success" if not orphans else "warning",
        docs_root=docs_path,
        mkdocs_file=config_path or Path("mkdocs.yml"),
        detected_config=detected_config,
        orphans=orphans,
    )


def check_language_structure(
    docs_root: Path | str = "docs",
    required_headers: list[str] | None = None,
    required_frontmatter: list[str] | None = None,
) -> CheckLanguageStructureResponse:
    """Validate markdown files against structure and frontmatter expectations."""
    request = CheckLanguageStructureRequest(
        docs_root=Path(docs_root),
        required_headers=required_headers,
        required_frontmatter=required_frontmatter,
    )
    docs_path = request.docs_root
    if not docs_path.exists():
        return CheckLanguageStructureResponse(
            status="error",
            docs_root=request.docs_root,
            message="docs_root does not exist.",
        )

    headers = request.required_headers or []
    required_keys = request.required_frontmatter or list(DEFAULT_FRONTMATTER_KEYS)
    issues: list[StructureIssue] = []
    for file_path in _markdown_files(docs_path):
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(content)
        issues.extend(
            StructureIssue(type="missing_frontmatter_key", file=str(file_path), detail=key)
            for key in required_keys
            if key not in frontmatter
        )
        if not re.search(r"^#\s+\S+", body, flags=re.MULTILINE):
            issues.append(
                StructureIssue(
                    type="missing_h1",
                    file=str(file_path),
                    detail="No level-1 heading found.",
                )
            )
        issues.extend(
            StructureIssue(type="missing_required_header", file=str(file_path), detail=header)
            for header in headers
            if header not in body
        )
        untyped_fences = _count_untyped_opening_fences(body)
        issues.extend(
            StructureIssue(
                type="untyped_code_fence",
                file=str(file_path),
                detail="Code fence missing language identifier.",
            )
            for _ in range(untyped_fences)
        )

    return CheckLanguageStructureResponse(
        status="success" if not issues else "warning",
        docs_root=request.docs_root,
        required_headers=headers,
        required_frontmatter=required_keys,
        issues=issues,
    )


def score_docs_quality(  # noqa: C901, PLR0912, PLR0915
    docs_root: Path | str = "docs",
) -> ScoreDocsQualityResponse:
    """Score docs quality across structure, frontmatter, primitive usage, and hygiene."""
    request = ScoreDocsQualityRequest(docs_root=Path(docs_root))
    docs_path = request.docs_root
    if not docs_path.exists():
        return ScoreDocsQualityResponse(
            status="error",
            docs_root=request.docs_root,
            message="docs_root does not exist.",
        )

    markdown_files = _markdown_files(docs_path)
    if not markdown_files:
        return ScoreDocsQualityResponse(
            status="error",
            docs_root=request.docs_root,
            message="No markdown files found under docs_root.",
        )

    component_scores: dict[str, int] = {
        "structure": 100,
        "frontmatter": 100,
        "primitive-usage": 100,
        "code-hygiene": 100,
    }
    issues: list[QualityIssue] = []
    suggestions: set[str] = set()
    detected_primitives: set[AuthoringPrimitive] = set()

    for file_path in markdown_files:
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(content)
        primitives = _detect_primitives(frontmatter, body)
        detected_primitives.update(primitives)

        if not body.strip():
            component_scores["structure"] -= 30
            issues.append(
                QualityIssue(
                    category="structure",
                    severity="high",
                    file=str(file_path),
                    detail="Markdown body is empty.",
                    suggestion="Add a focused heading and actionable content.",
                )
            )
            suggestions.add("Add meaningful body content to empty documentation pages.")
            continue

        if AuthoringPrimitive.HEADING_H1 not in primitives:
            component_scores["structure"] -= 12
            issues.append(
                QualityIssue(
                    category="structure",
                    severity="medium",
                    file=str(file_path),
                    detail="Missing level-1 heading.",
                    suggestion="Add a single H1 heading near the top of the file.",
                )
            )
            suggestions.add("Ensure each page has one clear H1 heading.")

        if not frontmatter:
            component_scores["frontmatter"] -= 20
            issues.append(
                QualityIssue(
                    category="frontmatter",
                    severity="high",
                    file=str(file_path),
                    detail="Missing YAML frontmatter block.",
                    suggestion="Add frontmatter with title and description metadata.",
                )
            )
            suggestions.add("Add frontmatter to all pages for navigation and metadata consistency.")
        else:
            missing_keys = [key for key in DEFAULT_FRONTMATTER_KEYS if key not in frontmatter]
            if missing_keys:
                component_scores["frontmatter"] -= 8 * len(missing_keys)
                issues.append(
                    QualityIssue(
                        category="frontmatter",
                        severity="medium",
                        file=str(file_path),
                        detail=f"Missing frontmatter keys: {', '.join(missing_keys)}.",
                        suggestion="Provide title and description keys in frontmatter.",
                    )
                )
                suggestions.add("Populate required frontmatter keys (title, description).")

        if len(primitives) < MIN_PRIMITIVE_VARIETY:
            component_scores["primitive-usage"] -= 10
            issues.append(
                QualityIssue(
                    category="primitive-usage",
                    severity="medium",
                    file=str(file_path),
                    detail="Limited primitive variety detected.",
                    suggestion="Add a supporting primitive like a link, table, or code fence.",
                )
            )
            suggestions.add(
                "Use supporting primitives (links, examples, callouts) to improve readability."
            )

        untyped_fences = _count_untyped_opening_fences(body)
        if untyped_fences:
            component_scores["primitive-usage"] -= min(20, 6 * untyped_fences)
            component_scores["code-hygiene"] -= min(20, 6 * untyped_fences)
            issues.append(
                QualityIssue(
                    category="code-hygiene",
                    severity="high",
                    file=str(file_path),
                    detail=f"{untyped_fences} code fence(s) missing language identifiers.",
                    suggestion="Annotate each code fence with a language (for example ```bash).",
                )
            )
            suggestions.add(
                "Always specify code fence languages for syntax highlighting and clarity."
            )

        todo_hits = len(re.findall(r"\bTODO\b", body))
        if todo_hits:
            component_scores["code-hygiene"] -= min(16, 4 * todo_hits)
            issues.append(
                QualityIssue(
                    category="code-hygiene",
                    severity="low",
                    file=str(file_path),
                    detail=f"{todo_hits} TODO placeholder(s) remain in content.",
                    suggestion="Replace TODO placeholders with concrete instructions or examples.",
                )
            )
            suggestions.add("Replace TODO placeholders before publishing docs.")

        long_lines = sum(1 for line in body.splitlines() if len(line) > MAX_DOC_LINE_LENGTH)
        if long_lines:
            issues.append(
                QualityIssue(
                    category="code-hygiene",
                    severity="low",
                    file=str(file_path),
                    detail=f"{long_lines} line(s) exceed 120 characters.",
                    suggestion="Wrap long lines to improve readability in diffs and editors.",
                )
            )

    richness_floor = max(0, 20 - (len(detected_primitives) * 2))
    component_scores["primitive-usage"] -= richness_floor
    hygiene_ratio = _compute_code_hygiene(docs_path)
    component_scores["code-hygiene"] = min(
        component_scores["code-hygiene"],
        round(hygiene_ratio * 100),
    )
    for key, score in component_scores.items():
        component_scores[key] = _clamp_score(score)

    quality_score = QualityScore(
        readability=round((component_scores["structure"] + component_scores["code-hygiene"]) / 2),
        completeness=round(
            (component_scores["frontmatter"] + component_scores["primitive-usage"]) / 2
        ),
        consistency=round(
            (
                component_scores["structure"]
                + component_scores["frontmatter"]
                + component_scores["code-hygiene"]
            )
            / 3
        ),
        overall=round(sum(component_scores.values()) / len(component_scores)),
    )

    best_detection = detect_best_framework(docs_path.parent)
    return ScoreDocsQualityResponse(
        status="success" if not issues else "warning",
        docs_root=request.docs_root,
        framework=best_detection.framework if best_detection else None,
        quality_score=quality_score,
        component_scores=component_scores,
        detected_primitives=sorted(detected_primitives, key=lambda primitive: primitive.value),
        issues=issues,
        suggestions=sorted(suggestions),
    )

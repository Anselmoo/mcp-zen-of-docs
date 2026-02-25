"""Documentation validator and scaffold tool implementations."""

from __future__ import annotations

import re
import tomllib

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import yaml

from .frameworks import detect_best_framework
from .frameworks.material_profile import DEFAULT_FRONTMATTER_KEYS
from .frameworks.material_profile import DEFAULT_SECTIONS
from .frameworks.material_profile import render_frontmatter
from .models import AuthoringPrimitive
from .models import BatchScaffoldRequest
from .models import BatchScaffoldResponse
from .models import CheckDocsLinksRequest
from .models import CheckDocsLinksResponse
from .models import CheckLanguageStructureRequest
from .models import CheckLanguageStructureResponse
from .models import CheckOrphanDocsRequest
from .models import CheckOrphanDocsResponse
from .models import FrameworkName
from .models import FrontmatterAuditRequest
from .models import FrontmatterAuditResponse
from .models import FrontmatterFileAudit
from .models import LinkIssue
from .models import NavIssue
from .models import NavIssueKind
from .models import QualityIssue
from .models import QualityScore
from .models import ScaffoldDocRequest
from .models import ScaffoldDocResponse
from .models import ScoreDocsQualityRequest
from .models import ScoreDocsQualityResponse
from .models import StructureIssue
from .models import SyncNavMode
from .models import SyncNavRequest
from .models import SyncNavResponse
from .templates import FRAMEWORK_INIT_SPECS


LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CODE_FENCE_PATTERN = re.compile(r"^```([^\s`]*)", flags=re.MULTILINE)
ADMONITION_PATTERN = re.compile(r"(^!!!\s+\w+|^:::\s*\w+|<Aside)", flags=re.MULTILINE)
TASK_LIST_PATTERN = re.compile(r"^\s*-\s+\[[ xX]\]\s+", flags=re.MULTILINE)
TABLE_PATTERN = re.compile(r"^\|.+\|\s*$", flags=re.MULTILINE)
TABS_PATTERN = re.compile(r'(^===\s+"|<Tabs|:::\s*code-group)', flags=re.MULTILINE)
DIAGRAM_PATTERN = re.compile(r"```(?:mermaid|graphviz|plantuml)", flags=re.MULTILINE)

# ---------------------------------------------------------------------------
# Internal helpers — TOML/YAML-agnostic config loader and code hygiene scorer
# ---------------------------------------------------------------------------

_CONFIG_CANDIDATES: tuple[str, ...] = ("zensical.toml", "mkdocs.yml", "mkdocs.yaml")


def _load_docs_config(
    docs_root: Path,
) -> tuple[Path, dict[str, object]] | tuple[None, None]:
    """Detect and parse the framework config file (TOML or YAML).

    Tries in order: ``zensical.toml`` → ``mkdocs.yml`` → ``mkdocs.yaml``.

    Returns:
        A ``(config_path, config_dict)`` pair, or ``(None, None)`` if none found.
    """
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


def _compute_code_hygiene(docs_root: Path) -> float:
    """Score code hygiene across all Markdown files in *docs_root*.

    Penalises lines exceeding ``MAX_DOC_LINE_LENGTH`` characters and unlabelled
    opening code fences.  Uses a proper fence stack so closing fences are never
    mistaken for unlabelled openers.

    Returns:
        A float in ``[0.0, 1.0]`` — 1.0 means no hygiene issues detected.
    """
    fence_pattern = re.compile(r"^[ \t]*(```+|~~~+)(.*)")

    total_lines = 0
    issue_lines = 0

    md_files = [
        p
        for p in (list(docs_root.rglob("*.md")) + list(docs_root.rglob("*.mdx")))
        if "includes" not in p.parts
    ]
    if not md_files:
        return 1.0

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Use a per-file fence stack so nested fences are handled correctly.
        stack: list[tuple[str, int]] = []
        for line in content.splitlines():
            total_lines += 1
            # Check long lines first (threshold consistent with MAX_DOC_LINE_LENGTH).
            if len(line) > MAX_DOC_LINE_LENGTH:
                issue_lines += 1
                continue
            m = fence_pattern.match(line)
            if not m:
                continue
            fence_chars, rest = m.group(1), m.group(2)
            fc = fence_chars[0]
            fl = len(fence_chars)
            rest_stripped = rest.strip()
            if stack and stack[-1][0] == fc and fl >= stack[-1][1] and not rest_stripped:
                stack.pop()
            else:
                lang = rest_stripped.split()[0].split("{")[0].split("[")[0] if rest_stripped else ""
                if not lang:
                    issue_lines += 1
                stack.append((fc, fl))

    if total_lines == 0:
        return 1.0

    ratio = issue_lines / total_lines
    return max(0.0, 1.0 - ratio * 10)  # amplify so a 10% issue rate → 0.0


API_ENDPOINT_PATTERN = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/[^\s`]+")
STEP_LIST_PATTERN = re.compile(r"^\d+\.\s+\S", flags=re.MULTILINE)
BADGE_PATTERN = re.compile(r"!\[[^\]]*]\([^)]*shields\.io[^)]*\)")
MIN_PRIMITIVE_VARIETY = 2
MAX_DOC_LINE_LENGTH = 120


def _detect_primitives(frontmatter: dict[str, object], body: str) -> set[AuthoringPrimitive]:
    primitives: set[AuthoringPrimitive] = set()
    if frontmatter:
        primitives.add(AuthoringPrimitive.FRONTMATTER)
    primitive_checks = (
        # Detect Markdown H1 OR HTML <h1> tag (for pages using HTML hero blocks)
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
    """Count opening code fences that have no language identifier.

    Uses a proper stack to handle nested fences (e.g. 4-backtick outer fence
    containing 3-backtick inner fences), so closing fences are never mistaken
    for unlabelled openers.
    """
    untyped = 0
    # Each stack entry is (fence_char, fence_length)
    stack: list[tuple[str, int]] = []
    fence_pattern = re.compile(r"^[ \t]*(```+|~~~+)(.*)")

    for line in body.splitlines():
        m = fence_pattern.match(line)
        if not m:
            continue
        fence_chars, rest = m.group(1), m.group(2)
        fc = fence_chars[0]
        fl = len(fence_chars)
        rest_stripped = rest.strip()

        # Closing fence: same char type, at least as long, no trailing content
        if stack and stack[-1][0] == fc and fl >= stack[-1][1] and not rest_stripped:
            stack.pop()
            continue

        # Opening fence — check for language identifier
        lang = rest_stripped.split()[0] if rest_stripped else ""
        # Strip attribute syntax like {.python} or [Tab A]
        lang = lang.split("{")[0].split("[")[0]
        if not lang:
            untyped += 1
        stack.append((fc, fl))

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


def _flatten_nav(nav: Sequence[object] | None) -> set[str]:
    referenced: set[str] = set()
    if not nav:
        return referenced
    for entry in nav:
        if isinstance(entry, str) and entry.endswith(".md"):
            referenced.add(entry)
            continue
        if isinstance(entry, dict):
            for value in entry.values():
                if isinstance(value, str) and value.endswith(".md"):
                    referenced.add(value)
                elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    referenced.update(_flatten_nav(value))
    return referenced


def _resolve_doc_target(base_file: Path, link_target: str) -> Path:
    cleaned = link_target.split("#", 1)[0].split("?", 1)[0]
    return (base_file.parent / cleaned).resolve()


def check_docs_links(
    docs_root: Path | str = "docs", external_mode: str = "report"
) -> CheckDocsLinksResponse:
    """Check internal links and report external links.

    Scans all Markdown files under *docs_root* for hyperlinks, verifies that
    internal links resolve to existing files, and optionally surfaces external
    URLs for human review.

    Args:
        docs_root: Root directory containing Markdown documentation files.
            Defaults to ``"docs"``.
        external_mode: How to handle external (``http://``, ``https://``)
            links. ``"report"`` surfaces them as issues; ``"ignore"`` skips
            them silently. Defaults to ``"report"``.

    Returns:
        Response with status, list of link issues, and count of broken
        internal links.
    """
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
    docs_root: Path | str = "docs", mkdocs_file: Path | str = "mkdocs.yml"
) -> CheckOrphanDocsResponse:
    """Find docs files that are not referenced in mkdocs nav.

    Compares the set of Markdown files on disk under *docs_root* against
    the paths declared in the MkDocs ``nav`` configuration and returns any
    files that are not referenced.

    Args:
        docs_root: Root directory containing Markdown documentation files.
            Defaults to ``"docs"``.
        mkdocs_file: Path to the MkDocs configuration file that defines
            the ``nav`` structure. Defaults to ``"mkdocs.yml"``.

    Returns:
        Response with status, sorted list of orphan file paths relative to
        *docs_root*, and an error message when either path does not exist.
    """
    request = CheckOrphanDocsRequest(docs_root=Path(docs_root), mkdocs_file=Path(mkdocs_file))
    docs_path = request.docs_root
    mkdocs_path = request.mkdocs_file
    if not docs_path.exists() or not mkdocs_path.exists():
        return CheckOrphanDocsResponse(
            status="error",
            docs_root=request.docs_root,
            mkdocs_file=request.mkdocs_file,
            message="docs_root or mkdocs_file does not exist.",
        )

    mkdocs_data = yaml.safe_load(mkdocs_path.read_text(encoding="utf-8")) or {}
    referenced = _flatten_nav(mkdocs_data.get("nav"))
    docs_files = {path.relative_to(docs_path).as_posix() for path in _markdown_files(docs_path)}
    orphans = sorted(docs_files - referenced)
    return CheckOrphanDocsResponse(
        status="success" if not orphans else "warning",
        docs_root=request.docs_root,
        mkdocs_file=request.mkdocs_file,
        orphans=orphans,
    )


def check_language_structure(
    docs_root: Path | str = "docs",
    required_headers: list[str] | None = None,
    required_frontmatter: list[str] | None = None,
) -> CheckLanguageStructureResponse:
    """Validate markdown files against a Material-oriented writing profile.

    Checks each Markdown file in *docs_root* for the presence of required
    frontmatter keys and heading strings, and reports detected authoring
    primitives per file.

    Args:
        docs_root: Root directory containing Markdown documentation files.
            Defaults to ``"docs"``.
        required_headers: List of heading strings that must appear in each
            Markdown file. When ``None``, no heading requirements are enforced.
        required_frontmatter: List of frontmatter key names that must be
            present in each file's YAML frontmatter block. When ``None``,
            no frontmatter requirements are enforced.

    Returns:
        Response with status, per-file structure issues, and an error message
        when *docs_root* does not exist.
    """
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
                    type="missing_h1", file=str(file_path), detail="No level-1 heading found."
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
    """Score docs quality across structure, frontmatter, primitive usage, and code hygiene.

    Evaluates all Markdown files under *docs_root* across four dimensions:
    structural conventions, frontmatter completeness, authoring primitive
    usage breadth, and code fence hygiene.

    Args:
        docs_root: Root directory containing Markdown documentation files
            to score. Defaults to ``"docs"``.

    Returns:
        Response with an aggregated quality score (0-100), per-category
        component scores, detected primitives, quality issues, and
        actionable improvement suggestions.
    """
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
            # Report the issue but do NOT deduct from the shared component score here.
            # Long-line impact is captured by the global _compute_code_hygiene ratio
            # (applied below) so that many files with a few long lines each do not
            # collectively drive the score to zero through unbounded accumulation.
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
    # Incorporate global code-hygiene ratio (long lines, unlabelled fences)
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


def _append_nav_entry(mkdocs_path: Path, title: str, nav_path: str) -> bool:
    content = mkdocs_path.read_text(encoding="utf-8")
    entry = f"  - {title}: {nav_path}"
    if entry in content:
        return False
    if "nav:" in content:
        updated = content.rstrip() + f"\n{entry}\n"
    else:
        updated = content.rstrip() + f"\n\nnav:\n{entry}\n"
    mkdocs_path.write_text(updated, encoding="utf-8")
    return True


def _to_nav_path(path: Path) -> str:
    parts = list(path.parts)
    if "docs" in parts:
        idx = parts.index("docs")
        return Path(*parts[idx + 1 :]).as_posix()
    return path.name


def scaffold_doc(  # noqa: PLR0913
    doc_path: Path | str,
    title: str,
    *,
    add_to_nav: bool = True,
    mkdocs_file: Path | str = "mkdocs.yml",
    description: str = "",
    overwrite: bool = False,
    framework: FrameworkName | None = None,
) -> ScaffoldDocResponse:
    """Create a documentation page scaffold and optionally append it to nav.

    Writes a new Markdown file with YAML frontmatter, an H1 heading, and
    default section stubs. The file path is resolved relative to the
    framework's canonical docs root unless an absolute path is given.

    Args:
        doc_path: Relative or absolute path for the new document.
        title: Human-readable page title used in the H1 heading and nav entry.
        add_to_nav: When ``True``, appends the new page to the MkDocs ``nav``
            in *mkdocs_file*. Defaults to ``True``.
        mkdocs_file: Path to the MkDocs configuration file used for nav
            updates. Defaults to ``"mkdocs.yml"``.
        description: Short description written into the frontmatter block.
            Defaults to an empty string.
        overwrite: When ``True``, replaces an existing file at *doc_path*.
            Defaults to ``False``.
        framework: Framework context used to resolve the docs root directory.
            When ``None``, ``"docs/"`` is used as a fallback.

    Returns:
        Response with status, resolved document path, title, nav update
        flag, and an error message when the target already exists and
        *overwrite* is ``False``.
    """
    request = ScaffoldDocRequest(
        doc_path=Path(doc_path),
        title=title,
        add_to_nav=add_to_nav,
        mkdocs_file=Path(mkdocs_file),
        description=description,
        overwrite=overwrite,
        framework=framework,
    )
    raw_path = request.doc_path
    # Resolve the framework-native docs root, falling back to "docs/" for unknown frameworks.
    if request.framework is not None and request.framework in FRAMEWORK_INIT_SPECS:
        fw_docs_root = FRAMEWORK_INIT_SPECS[request.framework].docs_root
    else:
        fw_docs_root = Path("docs")

    first_part = raw_path.parts[0] if raw_path.parts else None
    target_path = (
        raw_path
        if first_part is not None and first_part == str(fw_docs_root).split("/")[0]
        else fw_docs_root / raw_path
    )
    if target_path.exists() and not request.overwrite:
        return ScaffoldDocResponse(
            status="error",
            doc_path=target_path,
            message="Target doc already exists. Use overwrite=True to replace.",
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = render_frontmatter(title=request.title, description=request.description)
    body = f"{frontmatter}\n# {request.title}\n\n" + "".join(
        f"## {section}\n\nTODO: add content.\n\n" for section in DEFAULT_SECTIONS
    )
    target_path.write_text(body, encoding="utf-8")

    nav_updated = False
    mkdocs_path = request.mkdocs_file
    if request.add_to_nav and mkdocs_path.exists():
        nav_path = _to_nav_path(target_path)
        nav_updated = _append_nav_entry(mkdocs_path, request.title, nav_path)

    return ScaffoldDocResponse(
        status="success",
        doc_path=target_path,
        title=request.title,
        add_to_nav=request.add_to_nav,
        nav_updated=nav_updated,
        framework=request.framework,
    )


def batch_scaffold_docs(
    request: BatchScaffoldRequest,
) -> BatchScaffoldResponse:
    """Create multiple documentation page scaffolds in one call.

    Delegates to :func:`scaffold_doc` for each page in the request and
    aggregates results. Pages that fail (e.g. file already exists without
    ``overwrite=True``) are reported as skipped.

    Args:
        request: Batch scaffold request containing a list of page specs,
            a shared framework override, and a shared ``overwrite`` flag.

    Returns:
        Response with the list of per-page scaffold results and a list of
        skipped page paths.
    """
    created: list[ScaffoldDocResponse] = []
    skipped: list[str] = []
    for page in request.pages:
        fw = request.framework or page.framework
        result = scaffold_doc(
            doc_path=page.doc_path,
            title=page.title,
            add_to_nav=page.add_to_nav,
            mkdocs_file=page.mkdocs_file,
            description=page.description,
            overwrite=page.overwrite,
            framework=fw,
        )
        if result.status == "error":
            skipped.append(str(page.doc_path))
        else:
            created.append(result)
    status: Literal["success", "warning", "error"] = "success"
    if skipped and not created:
        status = "error"
    elif skipped:
        status = "warning"
    return BatchScaffoldResponse(
        status=status,
        created=created,
        skipped=skipped,
        total=len(request.pages),
    )


# ---------------------------------------------------------------------------
# audit_frontmatter
# ---------------------------------------------------------------------------

_FRONTMATTER_FENCE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, object] | None:
    """Return frontmatter dict or None if no YAML block found."""
    m = _FRONTMATTER_FENCE.match(text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


def _first_paragraph(body: str) -> str:
    """Extract the first non-empty paragraph from Markdown body text."""
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else ""


def audit_frontmatter_impl(request: FrontmatterAuditRequest) -> FrontmatterAuditResponse:
    """Audit (and optionally repair) frontmatter across a documentation directory.

    Inspects each Markdown file in *request.docs_root* for the presence and
    completeness of YAML frontmatter. When repair mode is enabled and required
    keys are specified, missing keys are added with placeholder values.

    Args:
        request: Frontmatter audit request specifying the docs directory,
            required frontmatter keys, and optional repair settings.

    Returns:
        Response with per-file audit results, counts of files with issues,
        and an error message when the docs directory does not exist.
    """
    docs_root = request.docs_root.expanduser().resolve()
    if not docs_root.is_dir():
        return FrontmatterAuditResponse(
            status="error",
            docs_root=str(request.docs_root),
            files_audited=0,
            files_with_gaps=0,
        )

    md_files = sorted(docs_root.rglob("*.md"))
    audits: list[FrontmatterFileAudit] = []
    files_with_gaps = 0
    files_repaired = 0

    for md_file in md_files:
        raw = md_file.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(raw)
        has_fm = fm is not None
        present_keys = list(fm.keys()) if fm else []
        missing = [k for k in request.required_keys if k not in (fm or {})]

        repaired = False
        if missing and request.fix:
            # Build minimal frontmatter patch
            body = _FRONTMATTER_FENCE.sub("", raw, count=1) if has_fm else raw
            patch: dict[str, str] = {}
            for key in missing:
                if key == "description":
                    patch[key] = _first_paragraph(body) or f"Documentation for {md_file.stem}."
                else:
                    patch[key] = md_file.stem.replace("-", " ").replace("_", " ").title()

            if has_fm:
                # Inject keys into existing frontmatter block
                merged = {**(fm or {}), **patch}
                new_fm_text = yaml.dump(merged, default_flow_style=False, allow_unicode=True)
                new_raw = _FRONTMATTER_FENCE.sub(f"---\n{new_fm_text}---\n", raw, count=1)
            else:
                new_fm_text = yaml.dump(patch, default_flow_style=False, allow_unicode=True)
                new_raw = f"---\n{new_fm_text}---\n\n{raw}"

            md_file.write_text(new_raw, encoding="utf-8")
            repaired = True
            files_repaired += 1
            present_keys = list({**fm, **patch}.keys()) if fm else list(patch.keys())
            missing = []

        audit = FrontmatterFileAudit(
            file_path=str(md_file.relative_to(docs_root)),
            has_frontmatter=has_fm,
            present_keys=present_keys,
            missing_keys=missing,
            repaired=repaired,
        )
        audits.append(audit)
        if audit.missing_keys:
            files_with_gaps += 1

    status: Literal["success", "warning", "error"] = "success"
    if files_with_gaps:
        status = "warning"

    return FrontmatterAuditResponse(
        status=status,
        docs_root=str(request.docs_root),
        files_audited=len(md_files),
        files_with_gaps=files_with_gaps,
        files_repaired=files_repaired,
        audits=audits,
    )


# ---------------------------------------------------------------------------
# sync_nav
# ---------------------------------------------------------------------------

_NAV_PARSERS: dict[str, str] = {
    "mkdocs.yml": "mkdocs",
    "mkdocs.yaml": "mkdocs",
}


def _collect_docs_files(docs_dir: Path) -> list[str]:
    """Return sorted list of .md paths relative to docs_dir."""
    return sorted(str(p.relative_to(docs_dir)) for p in docs_dir.rglob("*.md"))


def _extract_mkdocs_nav_paths(nav_yaml: object, base: str = "") -> list[str]:
    """Recursively extract file paths from a MkDocs nav structure."""
    paths: list[str] = []
    if isinstance(nav_yaml, list):
        for item in nav_yaml:
            paths.extend(_extract_mkdocs_nav_paths(item, base))
    elif isinstance(nav_yaml, dict):
        for value in nav_yaml.values():
            paths.extend(_extract_mkdocs_nav_paths(value, base))
    elif isinstance(nav_yaml, str):
        paths.append(nav_yaml)
    return paths


def _generate_mkdocs_nav(files: list[str]) -> str:
    """Generate a minimal MkDocs nav block string from a list of file paths."""
    lines = ["nav:"]
    for f in files:
        stem = Path(f).stem.replace("-", " ").replace("_", " ").title()
        lines.append(f"  - {stem}: {f}")
    return "\n".join(lines)


def _detect_framework_for_root(root: Path, override: FrameworkName | None) -> FrameworkName | None:
    """Detect framework for root, respecting an override."""
    if override is not None:
        return override
    fw_result = detect_best_framework(root)
    return fw_result.framework if fw_result is not None else None


def _load_nav_file(root: Path) -> tuple[Path | None, str | None]:
    """Return (path, content) for the first found MkDocs nav config, else (None, None)."""
    for candidate in ("mkdocs.yml", "mkdocs.yaml"):
        p = root / candidate
        if p.exists():
            return p, p.read_text(encoding="utf-8")
    return None, None


def _build_nav_issues(nav_set: set[str], disk_set: set[str]) -> list[NavIssue]:
    """Return ordered list of NavIssue objects for mismatches between nav and disk."""
    return [
        NavIssue(path=path, issue_kind=NavIssueKind.NAV_MISSING_FILE)
        for path in sorted(nav_set - disk_set)
    ] + [
        NavIssue(path=path, issue_kind=NavIssueKind.FILE_MISSING_FROM_NAV)
        for path in sorted(disk_set - nav_set)
    ]


def _repair_mkdocs_nav(nav_file_path: Path, nav_content: str, nav_generated: str) -> int:
    """Write repaired nav into mkdocs.yml. Returns number of issues resolved."""
    try:
        parsed_cfg = yaml.safe_load(nav_content) or {}
        parsed_cfg["nav"] = yaml.safe_load(nav_generated.split("nav:\n", 1)[1]) or []
        new_content = yaml.dump(
            parsed_cfg, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        nav_file_path.write_text(new_content, encoding="utf-8")
    except (yaml.YAMLError, IndexError):
        return 0
    else:
        return -1  # caller replaces issues with empty list
    return 0


def sync_nav_impl(request: SyncNavRequest) -> SyncNavResponse:
    """Audit, generate, or repair navigation config for a docs project.

    In ``audit`` mode, compares the nav declared in the MkDocs configuration
    against Markdown files on disk and reports mismatches. In ``generate``
    mode, produces a fresh nav block from disk files without writing it. In
    ``repair`` mode, writes a corrected nav back to the config file.

    Args:
        request: Nav sync request specifying project root, docs directory,
            nav config file, sync mode, and optional framework override.

    Returns:
        Response with status, nav issue list, optional generated nav YAML,
        and count of issues resolved when operating in repair mode.
    """
    root = request.project_root.expanduser().resolve()
    detected_fw = _detect_framework_for_root(root, request.framework)
    nav_file_path, nav_content = _load_nav_file(root)

    docs_dir = root / "docs" if (root / "docs").is_dir() else root
    disk_files = _collect_docs_files(docs_dir)

    nav_files: list[str] = []
    if nav_content is not None:
        try:
            parsed = yaml.safe_load(nav_content) or {}
            nav_files = _extract_mkdocs_nav_paths(parsed.get("nav", []))
        except yaml.YAMLError:
            pass

    issues = _build_nav_issues(set(nav_files), set(disk_files))
    nav_generated: str | None = None
    files_repaired = 0

    if request.mode in (SyncNavMode.GENERATE, SyncNavMode.REPAIR):
        nav_generated = _generate_mkdocs_nav(disk_files)
        if request.mode == SyncNavMode.REPAIR and nav_file_path and nav_content:
            result = _repair_mkdocs_nav(nav_file_path, nav_content, nav_generated)
            if result == -1:
                files_repaired = len(issues)
                issues = []

    status: Literal["success", "warning", "error"] = "success"
    if issues:
        status = "warning"

    return SyncNavResponse(
        status=status,
        framework=detected_fw,
        mode=request.mode,
        nav_file=str(nav_file_path) if nav_file_path else None,
        issues=issues,
        nav_generated=nav_generated,
        files_repaired=files_repaired,
    )

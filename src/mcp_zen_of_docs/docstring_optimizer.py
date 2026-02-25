"""Docstring audit and optimization for Python, TypeScript, Go, Rust, Java, and C#.

Provides regex-based symbol scanning, docstring-presence detection, canonical stub
generation, and file patching — all without external native dependencies.
"""

from __future__ import annotations

import ast
import re

from pathlib import Path  # noqa: TC003

from .models import DocstringAuditRequest
from .models import DocstringAuditResponse
from .models import DocstringLanguage
from .models import DocstringOptimizerRequest
from .models import DocstringOptimizerResponse
from .models import DocstringStyle
from .models import DocstringSymbol


__all__ = [
    "audit_docstrings_impl",
    "detect_language",
    "optimize_docstrings_impl",
]

# ---------------------------------------------------------------------------
# Static registry data
# ---------------------------------------------------------------------------

_STYLE_MATRIX: dict[DocstringLanguage, DocstringStyle] = {
    DocstringLanguage.PYTHON: DocstringStyle.GOOGLE,
    DocstringLanguage.TYPESCRIPT: DocstringStyle.TSDOC,
    DocstringLanguage.GO: DocstringStyle.GODOC,
    DocstringLanguage.RUST: DocstringStyle.RUSTDOC,
    DocstringLanguage.JAVA: DocstringStyle.JAVADOC,
    DocstringLanguage.CSHARP: DocstringStyle.XMLDOC,
}

_EXT_LANGUAGE_MAP: dict[str, DocstringLanguage] = {
    ".py": DocstringLanguage.PYTHON,
    ".ts": DocstringLanguage.TYPESCRIPT,
    ".tsx": DocstringLanguage.TYPESCRIPT,
    ".js": DocstringLanguage.TYPESCRIPT,
    ".jsx": DocstringLanguage.TYPESCRIPT,
    ".go": DocstringLanguage.GO,
    ".rs": DocstringLanguage.RUST,
    ".java": DocstringLanguage.JAVA,
    ".cs": DocstringLanguage.CSHARP,
}

# Each entry: (pattern, kind_label)
# Pattern must have a named group `name`.
_SYMBOL_PATTERNS: dict[DocstringLanguage, list[tuple[re.Pattern[str], str]]] = {
    DocstringLanguage.PYTHON: [
        (
            re.compile(r"^(?P<indent>\s*)(?:async\s+)?def\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"),
            "function",
        ),
        (
            re.compile(r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"),
            "class",
        ),
    ],
    DocstringLanguage.TYPESCRIPT: [
        (
            re.compile(
                r"^(?P<indent>\s*)(?:export\s+)?(?:async\s+)?function\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)"
            ),
            "function",
        ),
        (
            re.compile(
                r"^(?P<indent>\s*)(?:export\s+)?(?:abstract\s+)?class\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)"
            ),
            "class",
        ),
        (
            re.compile(
                r"^(?P<indent>\s*)(?:export\s+)?(?:readonly\s+)?(?:public\s+)?(?:async\s+)?(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*\("
            ),
            "method",
        ),
    ],
    DocstringLanguage.GO: [
        (
            re.compile(r"^func\s+(?:\([^)]+\)\s+)?(?P<name>[A-Z][A-Za-z0-9_]*)"),
            "function",
        ),
        (
            re.compile(r"^type\s+(?P<name>[A-Z][A-Za-z0-9_]*)\s+struct"),
            "struct",
        ),
        (
            re.compile(r"^type\s+(?P<name>[A-Z][A-Za-z0-9_]*)\s+interface"),
            "interface",
        ),
    ],
    DocstringLanguage.RUST: [
        (
            re.compile(r"^pub\s+(?:async\s+)?fn\s+(?P<name>[a-z_][A-Za-z0-9_]*)"),
            "function",
        ),
        (
            re.compile(r"^pub\s+(?:struct|enum)\s+(?P<name>[A-Z][A-Za-z0-9_]*)"),
            "struct",
        ),
        (
            re.compile(r"^pub\s+trait\s+(?P<name>[A-Z][A-Za-z0-9_]*)"),
            "trait",
        ),
    ],
    DocstringLanguage.JAVA: [
        (
            re.compile(
                r"^\s*(?:public|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
            ),
            "method",
        ),
        (
            re.compile(
                r"^\s*(?:public|protected)\s+(?:abstract\s+)?(?:static\s+)?(?:final\s+)?class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
            ),
            "class",
        ),
    ],
    DocstringLanguage.CSHARP: [
        (
            re.compile(
                r"^\s*(?:public|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:override\s+)?(?:virtual\s+)?(?:\w+\s+)+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
            ),
            "method",
        ),
        (
            re.compile(
                r"^\s*(?:public|protected|internal)\s+(?:abstract\s+)?(?:static\s+)?(?:sealed\s+)?(?:partial\s+)?class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
            ),
            "class",
        ),
    ],
}

# Pattern to detect whether a docstring already follows a declaration.
# Matched against the line immediately after the declaration (stripped).
_DOCSTRING_START_PATTERNS: dict[DocstringLanguage, re.Pattern[str]] = {
    DocstringLanguage.PYTHON: re.compile(r'^\s*("""|\'\'\')'),
    DocstringLanguage.TYPESCRIPT: re.compile(r"^\s*/\*\*"),
    DocstringLanguage.GO: re.compile(r"^\s*//"),
    DocstringLanguage.RUST: re.compile(r"^\s*///"),
    DocstringLanguage.JAVA: re.compile(r"^\s*/\*\*"),
    DocstringLanguage.CSHARP: re.compile(r"^\s*///"),
}

# Canonical docstring stub templates per style.
# Placeholders: {name} — symbol name, {kind} — symbol kind.
_STUB_TEMPLATES: dict[DocstringStyle, str] = {
    DocstringStyle.GOOGLE: (
        '"""{name} {kind}.\n\n'
        "Args:\n"
        "    param: Description.\n\n"
        "Returns:\n"
        "    Description.\n\n"
        "Raises:\n"
        "    ValueError: Description.\n"
        '"""'
    ),
    DocstringStyle.NUMPY: (
        '"""{name} {kind}.\n\n'
        "Parameters\n"
        "----------\n"
        "param : type\n"
        "    Description.\n\n"
        "Returns\n"
        "-------\n"
        "type\n"
        "    Description.\n"
        '"""'
    ),
    DocstringStyle.TSDOC: (
        "/**\n"
        " * {name} — {kind}.\n"
        " *\n"
        " * @param param - Description.\n"
        " * @returns Description.\n"
        " */"
    ),
    DocstringStyle.JSDOC: (
        "/**\n"
        " * {name} — {kind}.\n"
        " *\n"
        " * @param {{type}} param - Description.\n"
        " * @returns {{type}} Description.\n"
        " */"
    ),
    DocstringStyle.GODOC: "// {name} — {kind}.",
    DocstringStyle.RUSTDOC: (
        "/// {name} — {kind}.\n"
        "///\n"
        "/// # Arguments\n"
        "///\n"
        "/// * `param` - Description.\n"
        "///\n"
        "/// # Returns\n"
        "///\n"
        "/// Description."
    ),
    DocstringStyle.JAVADOC: (
        "/**\n * {name} — {kind}.\n *\n * @param param Description.\n * @return Description.\n */"
    ),
    DocstringStyle.XMLDOC: (
        "/// <summary>\n"
        "/// {name} — {kind}.\n"
        "/// </summary>\n"
        '/// <param name="param">Description.</param>\n'
        "/// <returns>Description.</returns>"
    ),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def detect_language(source_path: Path) -> DocstringLanguage:
    """Detect the programming language from the file extension.

    Args:
        source_path: Path to the source file.

    Returns:
        The matched DocstringLanguage enum value.

    Raises:
        ValueError: If the extension is not recognised.
    """
    suffix = source_path.suffix.lower()
    language = _EXT_LANGUAGE_MAP.get(suffix)
    if language is None:
        supported = ", ".join(sorted(_EXT_LANGUAGE_MAP.keys()))
        msg = f"Unsupported file extension '{suffix}'. Supported extensions: {supported}"
        raise ValueError(msg)
    return language


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scan_symbols(
    lines: list[str],
    language: DocstringLanguage,
    *,
    include_private: bool = False,
) -> list[tuple[int, str, str]]:
    """Scan source lines for public symbol declarations.

    Args:
        lines: Source file lines (1-indexed by position, i.e., lines[0] is line 1).
        language: Target language for pattern matching.
        include_private: When True, private/unexported symbols are included.

    Returns:
        List of (1-based line number, symbol name, symbol kind) tuples.
    """
    if language == DocstringLanguage.PYTHON:
        return _scan_python_ast(lines, include_private=include_private)
    patterns = _SYMBOL_PATTERNS.get(language, [])
    found: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(lines, start=1):
        for pattern, kind in patterns:
            m = pattern.match(line)
            if m:
                name = m.group("name")
                if not include_private and _is_private(name, language):
                    break
                found.append((lineno, name, kind))
                break
    return found


def _scan_python_ast(
    lines: list[str],
    *,
    include_private: bool = False,
) -> list[tuple[int, str, str]]:
    """Scan Python source using ast.parse for accurate symbol detection.

    Falls back to regex on SyntaxError.

    Args:
        lines: Source file lines.
        include_private: When True, symbols starting with ``_`` are included.

    Returns:
        Sorted list of (1-based line number, symbol name, symbol kind) tuples.
    """
    source = "\n".join(lines)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Graceful fallback to regex-based scanning
        return _scan_symbols_regex(lines, include_private=include_private)

    found: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if include_private or not node.name.startswith("_"):
                found.append((node.lineno, node.name, "class"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            include_private or not node.name.startswith("_")
        ):
            found.append((node.lineno, node.name, "function"))
    return sorted(found, key=lambda t: t[0])


def _scan_symbols_regex(
    lines: list[str],
    *,
    include_private: bool = False,
) -> list[tuple[int, str, str]]:
    """Regex fallback for Python symbol scanning (used on SyntaxError).

    Args:
        lines: Source file lines.
        include_private: When True, private symbols are included.

    Returns:
        List of (1-based line number, symbol name, symbol kind) tuples.
    """
    patterns = _SYMBOL_PATTERNS.get(DocstringLanguage.PYTHON, [])
    found: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(lines, start=1):
        for pattern, kind in patterns:
            m = pattern.match(line)
            if m:
                name = m.group("name")
                if not include_private and name.startswith("_"):
                    break
                found.append((lineno, name, kind))
                break
    return found


def _is_private(name: str, language: DocstringLanguage) -> bool:
    """Return True if the symbol name is considered private in the given language."""
    if language == DocstringLanguage.PYTHON:
        return name.startswith("_")
    if language in {DocstringLanguage.GO, DocstringLanguage.RUST}:
        return name[0].islower() if name else True
    return False


def _has_docstring(
    lines: list[str],
    decl_lineno: int,
    language: DocstringLanguage,
) -> str | None:
    """Check whether a docstring immediately follows the declaration.

    For multi-line declarations (function args spanning multiple lines), we scan
    forward from the declaration until we find an opening brace/colon or a comment.

    Args:
        lines: Source file lines (list, 0-indexed access; decl_lineno is 1-based).
        decl_lineno: 1-based line number of the symbol declaration.
        language: Source language for pattern selection.

    Returns:
        The existing docstring text (first line) if present, None otherwise.
    """
    pattern = _DOCSTRING_START_PATTERNS.get(language)
    if pattern is None:
        return None
    # Check up to 5 lines after the declaration for the docstring opener
    for offset in range(1, 6):
        idx = decl_lineno - 1 + offset  # 0-based index
        if idx >= len(lines):
            break
        candidate = lines[idx]
        if pattern.match(candidate):
            return candidate.strip()
        # Stop scanning if we hit a blank line followed by more code (not a docstring)
        stripped = candidate.strip()
        if stripped and not stripped.startswith(("#", "//", "/*", "'''", '"""', "///", "/**")):
            # Encountered real code without a docstring opener
            break
    return None


def _generate_stub(
    name: str,
    kind: str,
    style: DocstringStyle,
    indent: str = "",
    context_hint: str | None = None,
) -> str:
    """Render a canonical docstring stub for the given symbol.

    Args:
        name: Symbol name.
        kind: Symbol kind (function, class, etc.).
        style: Target docstring style.
        indent: Indentation string to prepend to multi-line stubs.
        context_hint: Optional context to include in the stub summary.

    Returns:
        Rendered stub string, indented correctly.
    """
    template = _STUB_TEMPLATES.get(style, _STUB_TEMPLATES[DocstringStyle.GOOGLE])
    raw = template.format(name=name, kind=kind)
    _ = context_hint  # reserved for future stub enrichment
    if not indent:
        return raw
    # Indent all lines except the first (for inline insertion)
    lines = raw.splitlines()
    return "\n".join(
        (indent + line if i > 0 and line.strip() else line) for i, line in enumerate(lines)
    )


def _infer_indent(decl_line: str, language: DocstringLanguage) -> str:
    """Infer the indentation for the docstring from the declaration line."""
    base = len(decl_line) - len(decl_line.lstrip())
    if language == DocstringLanguage.PYTHON:
        # Python docstring is indented one level deeper than the def/class
        return " " * (base + 4)
    return " " * base


# ---------------------------------------------------------------------------
# Public impl functions
# ---------------------------------------------------------------------------


def audit_docstrings_impl(request: DocstringAuditRequest) -> DocstringAuditResponse:  # noqa: C901, PLR0912
    """Audit a source file (or directory) for undocumented public symbols.

    Args:
        request: DocstringAuditRequest specifying source path, language, and thresholds.

    Returns:
        DocstringAuditResponse with coverage metrics and list of missing symbols.
    """
    source = request.source_path

    # Resolve language
    try:
        language = request.language or detect_language(source)
    except ValueError as exc:
        return DocstringAuditResponse(
            status="error",
            source_path=source,
            language=DocstringLanguage.PYTHON,  # fallback placeholder
            style=DocstringStyle.GOOGLE,
            total_symbols=0,
            documented_symbols=0,
            coverage=0.0,
            missing=[],
            message=str(exc),
        )

    style = _STYLE_MATRIX[language]

    # Collect files to scan
    files: list[Path] = []
    if source.is_dir():
        ext = next((e for e, lang in _EXT_LANGUAGE_MAP.items() if lang == language), None)
        if ext:
            files = sorted(source.rglob(f"*{ext}"))
    elif source.is_file():
        files = [source]
    else:
        return DocstringAuditResponse(
            status="error",
            source_path=source,
            language=language,
            style=style,
            total_symbols=0,
            documented_symbols=0,
            coverage=0.0,
            missing=[],
            message=f"Path does not exist: {source}",
        )

    total = 0
    documented = 0
    missing: list[DocstringSymbol] = []

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            continue

        file_lines = text.splitlines()
        symbols = _scan_symbols(file_lines, language, include_private=request.include_private)

        for lineno, name, kind in symbols:
            total += 1
            existing = _has_docstring(file_lines, lineno, language)
            if existing:
                documented += 1
            else:
                indent = _infer_indent(file_lines[lineno - 1], language)
                stub = _generate_stub(name, kind, style, indent)
                missing.append(
                    DocstringSymbol(
                        name=name,
                        kind=kind,
                        line=lineno,
                        existing_comment=None,
                        suggested_docstring=stub,
                        language=language,
                    )
                )

    coverage = documented / total if total > 0 else 1.0
    status: str = "success"
    if total == 0:
        status = "warning"
        msg = "No symbols found. Check that the language and file path are correct."
    elif coverage < request.min_coverage:
        status = "warning"
        msg = f"Coverage {coverage:.1%} is below the minimum threshold {request.min_coverage:.1%}."
    else:
        msg = f"Coverage {coverage:.1%} meets the minimum threshold of {request.min_coverage:.1%}."

    return DocstringAuditResponse(
        status=status,
        source_path=source,
        language=language,
        style=style,
        total_symbols=total,
        documented_symbols=documented,
        coverage=coverage,
        missing=missing,
        message=msg,
    )


def optimize_docstrings_impl(request: DocstringOptimizerRequest) -> DocstringOptimizerResponse:  # noqa: C901, PLR0911, PLR0912
    """Insert canonical docstring stubs for undocumented symbols in a source file.

    When overwrite=False (default), the patched file content is returned as a string
    without modifying any file on disk.  When overwrite=True, the file is updated in
    place and written_path is set in the response.

    Args:
        request: DocstringOptimizerRequest with source path, language, style, and options.

    Returns:
        DocstringOptimizerResponse with patched content or written path.
    """
    source = request.source_path

    # Resolve language and style
    try:
        language = request.language or detect_language(source)
    except ValueError as exc:
        return DocstringOptimizerResponse(
            status="error",
            source_path=source,
            language=DocstringLanguage.PYTHON,
            style=DocstringStyle.GOOGLE,
            symbols_optimized=0,
            symbols_skipped=0,
            message=str(exc),
        )

    style = request.style or _STYLE_MATRIX[language]

    if source.is_dir():
        if not request.overwrite:
            return DocstringOptimizerResponse(
                status="error",
                source_path=source,
                language=language,
                style=style,
                symbols_optimized=0,
                symbols_skipped=0,
                message=(
                    "Directory mode requires overwrite=True. "
                    "Set overwrite=True to patch files in place."
                ),
            )
        ext = next((e for e, lang in _EXT_LANGUAGE_MAP.items() if lang == language), None)
        files = sorted(source.rglob(f"*{ext}")) if ext else []
        if not files:
            return DocstringOptimizerResponse(
                status="warning",
                source_path=source,
                language=language,
                style=style,
                symbols_optimized=0,
                symbols_skipped=0,
                message=f"No {language.value} files found in {source}.",
            )
        total_optimized = 0
        total_skipped = 0
        for file_path in files:
            sub_req = DocstringOptimizerRequest(
                source_path=file_path,
                language=language,
                style=style,
                overwrite=True,
                include_private=request.include_private,
                context_hint=request.context_hint,
            )
            sub_resp = optimize_docstrings_impl(sub_req)
            total_optimized += sub_resp.symbols_optimized
            total_skipped += sub_resp.symbols_skipped
        return DocstringOptimizerResponse(
            status="success",
            source_path=source,
            language=language,
            style=style,
            symbols_optimized=total_optimized,
            symbols_skipped=total_skipped,
            written_path=source,
            message=(
                f"Inserted {total_optimized} docstring stub(s) across "
                f"{len(files)} file(s) in {source}."
            ),
        )

    if not source.is_file():
        return DocstringOptimizerResponse(
            status="error",
            source_path=source,
            language=language,
            style=style,
            symbols_optimized=0,
            symbols_skipped=0,
            message=f"Source path is not a file: {source}",
        )

    try:
        original_text = source.read_text(encoding="utf-8")
    except OSError as exc:
        return DocstringOptimizerResponse(
            status="error",
            source_path=source,
            language=language,
            style=style,
            symbols_optimized=0,
            symbols_skipped=0,
            message=f"Cannot read file: {exc}",
        )

    original_lines = original_text.splitlines()
    symbols = _scan_symbols(original_lines, language, include_private=request.include_private)

    # Build list of (decl_lineno, stub_text) for symbols without docstrings.
    # Process from bottom to top to keep line-number offsets stable.
    insertions: list[tuple[int, str]] = []
    skipped = 0

    for lineno, name, kind in symbols:
        existing = _has_docstring(original_lines, lineno, language)
        if existing:
            skipped += 1
            continue
        indent = _infer_indent(original_lines[lineno - 1], language)
        stub = _generate_stub(name, kind, style, indent, request.context_hint)
        insertions.append((lineno, stub))

    if not insertions:
        return DocstringOptimizerResponse(
            status="success",
            source_path=source,
            language=language,
            style=style,
            symbols_optimized=0,
            symbols_skipped=skipped,
            output=original_text if not request.overwrite else None,
            written_path=None,
            message="All symbols are already documented.",
        )

    # Apply insertions from bottom to top to avoid line-number drift
    patched = list(original_lines)
    for lineno, stub in sorted(insertions, key=lambda x: x[0], reverse=True):
        stub_lines = stub.splitlines()
        # Insert stub lines after the declaration line (index = lineno, 0-based)
        insert_idx = lineno  # 0-based: after line `lineno` (1-based)
        for i, stub_line in enumerate(stub_lines):
            patched.insert(insert_idx + i, stub_line)

    patched_text = "\n".join(patched)
    if original_text.endswith("\n"):
        patched_text += "\n"

    optimized = len(insertions)

    if request.overwrite:
        try:
            source.write_text(patched_text, encoding="utf-8")
        except OSError as exc:
            return DocstringOptimizerResponse(
                status="error",
                source_path=source,
                language=language,
                style=style,
                symbols_optimized=0,
                symbols_skipped=skipped,
                message=f"Cannot write file: {exc}",
            )
        return DocstringOptimizerResponse(
            status="success",
            source_path=source,
            language=language,
            style=style,
            symbols_optimized=optimized,
            symbols_skipped=skipped,
            written_path=source,
            message=f"Inserted {optimized} docstring stub(s) into {source}.",
        )

    return DocstringOptimizerResponse(
        status="success",
        source_path=source,
        language=language,
        style=style,
        symbols_optimized=optimized,
        symbols_skipped=skipped,
        output=patched_text,
        message=f"Generated {optimized} docstring stub(s) (dry run — file not modified).",
    )

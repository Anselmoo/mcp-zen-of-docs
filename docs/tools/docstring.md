---
title: docstring
description: Audit docstring coverage in source code and generate canonical stub docstrings for undocumented symbols.
tags:
  - tools
  - docstring
---

# docstring

> Audits docstring coverage in Python source code and generates canonical stubs for undocumented symbols.

`mode="audit"` is read-only and safe to run any time — it reports which functions, classes, and methods lack docstrings. `mode="optimize"` with `overwrite=true` writes stubs directly into your source files. Always commit before using `overwrite=true`. Use `docstring` to close the gap between your code and the API reference that [generate](generate.md) produces from those docstrings.

---

## Modes

| Mode | What it does |
|------|-------------|
| `audit` | Reports coverage: which symbols lack docstrings (default) |
| `optimize` | Generates stub docstrings for every undocumented symbol |

---

## When to use it

Run `audit` any time to see coverage gaps — it makes no changes. Run `optimize` when you're ready to write stubs, then fill in the implementation-specific details. Always run `audit` first to understand the scope before committing to `overwrite=true`.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Operation mode. Default: `"audit"` |
| `source_path` | path | No | File or directory to scan. Default: `"."` |
| `language` | string | No | Source language — auto-detected from file extensions |
| `style` | string | No | Docstring style: `"google"`, `"numpy"`, `"sphinx"` |
| `min_coverage` | float | No | Coverage threshold; audit warns when below this value. Default: `0.8` |
| `include_private` | bool | No | Include `_private` and `__dunder__` symbols. Default: `false` |
| `overwrite` | bool | No | Write stubs directly into source files (`optimize` only). Default: `false` |
| `context_hint` | string | No | Domain hint to improve stub quality, e.g. `"FastMCP server"` |

---

## Examples

**Audit docstring coverage**

```json
{
  "tool": "docstring",
  "arguments": {
    "mode": "audit",
    "source_path": "src/mcp_zen_of_docs",
    "style": "google",
    "min_coverage": 0.8
  }
}
```

Returns:

```json
{
  "coverage": 0.63,
  "threshold": 0.80,
  "status": "below_threshold",
  "summary": {
    "total_symbols": 48,
    "documented": 30,
    "undocumented": 18
  },
  "undocumented": [
    { "file": "src/mcp_zen_of_docs/validators.py", "symbol": "check_nav_drift",      "kind": "function", "line": 42 },
    { "file": "src/mcp_zen_of_docs/validators.py", "symbol": "score_completeness",   "kind": "function", "line": 89 },
    { "file": "src/mcp_zen_of_docs/scaffold.py",   "symbol": "ScaffoldOptions",      "kind": "class",    "line": 15 },
    { "file": "src/mcp_zen_of_docs/scaffold.py",   "symbol": "ScaffoldOptions.write","kind": "method",   "line": 31 }
  ]
}
```

---

**Generate stubs, preview without writing (`overwrite=false`)**

```json
{
  "tool": "docstring",
  "arguments": {
    "mode": "optimize",
    "source_path": "src/mcp_zen_of_docs/validators.py",
    "style": "google",
    "overwrite": false,
    "context_hint": "documentation quality validator"
  }
}
```

Returns a preview of the generated stubs without touching any files:

```json
{
  "stubs_generated": 2,
  "would_write": false,
  "stubs": [
    {
      "file": "src/mcp_zen_of_docs/validators.py",
      "symbol": "check_nav_drift",
      "line": 42,
      "stub": "\"\"\"Check for drift between the navigation config and files on disk.\n\nCompares nav entries in mkdocs.yml against the actual Markdown files in\ndocs_root and returns a list of discrepancies.\n\nArgs:\n    docs_root: Path to the documentation root directory.\n    nav_config: Parsed navigation structure from the config file.\n\nReturns:\n    A list of NavDriftIssue objects describing missing or extra entries.\n\"\"\""
    }
  ]
}
```

---

**Write stubs in place (`overwrite=true`)**

Before:

```python
def check_nav_drift(docs_root: Path, nav_config: dict) -> list[NavDriftIssue]:
    entries = _load_nav_entries(nav_config)
    actual = set(_find_markdown_files(docs_root))
    ...
```

After `optimize` with `overwrite=true`:

```python
def check_nav_drift(docs_root: Path, nav_config: dict) -> list[NavDriftIssue]:
    """Check for drift between the navigation config and files on disk.

    Compares nav entries in mkdocs.yml against the actual Markdown files in
    docs_root and returns a list of discrepancies.

    Args:
        docs_root: Path to the documentation root directory.
        nav_config: Parsed navigation structure from the config file.

    Returns:
        A list of NavDriftIssue objects describing missing or extra entries.
    """
    entries = _load_nav_entries(nav_config)
    actual = set(_find_markdown_files(docs_root))
    ...
```

!!! warning "`overwrite=true` modifies source files"
    `optimize` rewrites your `.py` files directly. Always commit your work first. The stubs are canonical skeletons — fill in implementation-specific details after generation.

!!! tip "Use `context_hint` for better stubs"
    `context_hint="FastMCP tool handler returning JSON"` produces stubs that mention the MCP response format in their `Returns:` section.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **generate**

    Generate API reference docs from the docstrings you just wrote.

    [:octicons-arrow-right-24: Read generate](generate.md)

-   :octicons-arrow-right-24: **validate**

    Validate the documentation pages that reference the symbols you documented.

    [:octicons-arrow-right-24: Read validate](validate.md)

</div>

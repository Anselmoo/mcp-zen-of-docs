---
title: code-doc
description: Audit docstring coverage or generate docstring stubs from the public CLI.
tags:
  - tools
  - cli
  - code-doc
---

# code-doc

> Public CLI command family for source-code documentation coverage.

`code-doc` exposes the docstring workflow in task-shaped terminal commands. Under the hood it wraps the richer [docstring](docstring.md) tooling.

---

## Subcommands

| Subcommand | What it does |
|------------|---------------|
| `code-doc coverage` | Audit docstring coverage for a file or directory |
| `code-doc stubs` | Generate canonical docstring stubs for undocumented symbols |

---

## Examples

```bash
# Audit Python docstring coverage
mcp-zen-of-docs --human code-doc coverage src/ --language python --min-coverage 0.9

# Generate stubs without overwriting files
mcp-zen-of-docs --human code-doc stubs src/module.py --language python
```

Use `code-doc coverage` first to measure the gap. Use `code-doc stubs` when you want generated placeholders for the missing symbols.

---

## Related commands

- [`page`](page.md) — publish the resulting API docs pages
- [`docstring`](docstring.md) — underlying MCP-oriented docstring reference

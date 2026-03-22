---
title: diagram
description: Create Mermaid diagrams from plain English or render Mermaid source to SVG and PNG.
tags:
  - tools
  - cli
  - diagram
---

# diagram

> Public CLI command family for documentation diagrams.

`diagram` is the task-shaped CLI wrapper around the diagram modes of [generate](generate.md).

---

## Subcommands

| Subcommand | What it does |
|------------|---------------|
| `diagram create` | Turn a plain-language description into Mermaid source |
| `diagram render` | Render Mermaid source to SVG or PNG |

---

## Examples

```bash
# Generate Mermaid from a description
mcp-zen-of-docs --human diagram create "Docs release flow with review and publish" --type flowchart

# Render Mermaid source to SVG
mcp-zen-of-docs --human diagram render "flowchart TD; A-->B;" --output-format svg
```

Use `diagram create` when you want help generating Mermaid syntax. Use `diagram render` when you already have Mermaid and want a file or inline SVG output.

---

## Related commands

- [`asset`](asset.md) — generate badges, headers, and other visual assets
- [`generate`](generate.md) — underlying MCP-oriented reference

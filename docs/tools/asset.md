---
title: asset
description: Generate visual documentation assets or write raw SVG files through the human-facing CLI.
tags:
  - tools
  - cli
  - asset
---

# asset

> Public CLI command family for documentation visuals.

`asset` wraps the visual-asset modes of [generate](generate.md) in a smaller CLI surface.

---

## Subcommands

| Subcommand | Best for |
|------------|----------|
| `asset create` | Generate a badge, header, icon, or similar asset from parameters |
| `asset write-svg` | Save raw SVG markup and optionally convert it to PNG |

---

## Examples

```bash
# Generate an icon-style asset
mcp-zen-of-docs --human asset create icons --title "Docs icons"

# Write raw SVG markup to disk
mcp-zen-of-docs --human asset write-svg docs/assets/logo.svg --svg-file ./logo.svg
```

Use `asset create` when the CLI should generate the design. Use `asset write-svg` when you already have SVG markup and just want file handling or PNG conversion.

---

## Related commands

- [`diagram`](diagram.md) — create or render Mermaid diagrams
- [`generate`](generate.md) — underlying MCP-oriented asset reference

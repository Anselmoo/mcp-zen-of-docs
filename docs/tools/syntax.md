---
title: syntax
description: Check primitive support or translate framework syntax through task-shaped CLI commands.
tags:
  - tools
  - cli
  - syntax
---

# syntax

> Public CLI command family for framework-native authoring syntax.

`syntax` is the CLI-friendly replacement for the more MCP-shaped [profile](profile.md) command family.

---

## Subcommands

| Subcommand | What it does |
|------------|---------------|
| `syntax check` | Check whether a framework supports a primitive and optionally render it |
| `syntax convert` | Show how one primitive maps between two frameworks |

---

## Examples

```bash
# Check support for admonitions in Zensical
mcp-zen-of-docs --human syntax check admonition --framework zensical

# Translate tabs from Zensical to Docusaurus
mcp-zen-of-docs --human syntax convert tabs --from zensical --to docusaurus
```

Use `syntax check` before you write a page and want to confirm the right authoring primitive. Use `syntax convert` when migrating docs between frameworks.

---

## Related commands

- [`page`](page.md) — write or scaffold docs pages
- [`profile`](profile.md) — underlying MCP-oriented profile reference

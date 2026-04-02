---
title: page
description: Create docs pages with task-shaped CLI commands for scaffolding, enrichment, and full first drafts.
tags:
  - tools
  - cli
  - page
---

# page

> Public CLI command family for creating and updating documentation pages.

`page` is the human-facing wrapper around the underlying [scaffold](scaffold.md) tool. It exists so terminal users can think in tasks instead of MCP modes.

---

## Choose the right subcommand

| Subcommand | Best for |
|------------|----------|
| `page new` | Create a scaffold with frontmatter and structure |
| `page fill` | Fill TODO sections in an existing scaffold |
| `page write` | Generate a fuller first draft from a topic |
| `page batch-new` | Create multiple scaffolds from JSON input |

---

## Examples

```bash
# Create a page scaffold
mcp-zen-of-docs --human page new docs/getting-started.md --title "Getting started"

# Fill TODO sections in an existing page
mcp-zen-of-docs --human page fill docs/getting-started.md --content "Add prerequisites and first steps"

# Generate a fuller draft
mcp-zen-of-docs --human page write docs/guides/release-flow.md --topic "Docs release flow"
```

If you accidentally type `page --new`, the CLI now corrects you with a human error message instead of a traceback.

---

## Related commands

- [`validate`](validate.md) — audit the page after writing
- [`syntax`](syntax.md) — check primitive support before editing
- [`scaffold`](scaffold.md) — underlying MCP-oriented page generation reference

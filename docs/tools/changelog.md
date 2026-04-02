---
title: changelog
description: Generate a structured changelog entry from git history with the public CLI.
tags:
  - tools
  - cli
  - changelog
---

# changelog

> Public CLI command for release notes and changelog generation.

`changelog` is the standalone human-facing entrypoint for changelog generation from git history.

---

## Example

```bash
mcp-zen-of-docs --human changelog 1.2.0 --since-tag 1.1.0 --format keep-a-changelog
```

Use a release version such as `1.2.0` or `v1.2.0`. The command parses commits since the supplied tag and groups them into changelog categories.

---

## Related commands

- [`validate`](validate.md) — audit docs before publishing release notes
- [`generate`](generate.md) — underlying MCP-oriented generation reference

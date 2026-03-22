---
title: integrations
description: Generate AI and editor integration templates such as Copilot instructions and config files.
tags:
  - tools
  - cli
  - integrations
---

# integrations

> Public CLI command family for AI and editor setup artifacts.

`integrations` is the human-facing wrapper around the integration and Copilot-related generation tooling.

---

## Subcommands

| Subcommand | Best for |
|------------|----------|
| `integrations init` | Generate editor or AI config templates for a project |
| `integrations artifact` | Generate an instruction, prompt, or agent artifact |

---

## Examples

```bash
# Generate integration templates for the current repository
mcp-zen-of-docs --human integrations init --project-root .

# Generate an instruction artifact
mcp-zen-of-docs --human integrations artifact instruction docs-workflow --content "Use validate before shipping docs."
```

In human mode the CLI now shows a concise summary of suggested files instead of dumping the full generated file bodies into the terminal.

---

## Related commands

- [`setup`](setup.md) — bootstrap the rest of the docs workflow
- [`copilot`](copilot.md) — underlying MCP-oriented Copilot reference

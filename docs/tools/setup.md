---
title: setup
description: Bootstrap docs work for a project with a safe setup guide or framework-native structure.
tags:
  - tools
  - cli
  - setup
---

# setup

> Public CLI command for bootstrapping docs work in a repository.

`setup` is the human-facing entrypoint for the onboarding workflow. Running `setup` without a subcommand prints a concise setup guide. Use `setup init` when you want framework-native starter structure instead of a checklist.

Under the hood, this CLI surface wraps the richer [onboard](onboard.md) tool.

---

## Common paths

| Command | Use it when |
|---------|-------------|
| `setup` | You want a safe checklist and next steps |
| `setup --mode skeleton` | You want guide-only onboarding output |
| `setup init <framework>` | You want framework-native docs structure created |

---

## Examples

```bash
# Safe first-run checklist
mcp-zen-of-docs --human setup --project-root . --mode skeleton

# Initialise a framework-specific docs structure
mcp-zen-of-docs --human setup init zensical --project-root .
```

---

## Related commands

- [`status`](status.md) — see what is already configured
- [`validate`](validate.md) — audit the result after setup
- [`onboard`](onboard.md) — underlying MCP-oriented onboarding reference

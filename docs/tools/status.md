---
title: status
description: Summarize detected docs framework and readiness in one human-facing CLI command.
tags:
  - tools
  - cli
  - status
---

# status

> Public CLI command for checking whether a project is ready for docs work.

`status` is the human-facing replacement for running separate detection and readiness checks in the terminal. It combines the most useful signals into one summary: detected framework, initialization state, and the next action to take.

---

## When to use it

Use `status` when you have just opened a repository and want to know:

- which docs framework was detected
- whether docs setup artifacts already exist
- what command to run next

If you need the lower-level MCP-oriented surfaces, see [detect](detect.md).

---

## Example

```bash
mcp-zen-of-docs --human status --project-root .
```

Typical output:

```text
Success: Status
Project root: .
Framework: zensical

Initialized: Yes
Readiness level: Not initialized
Next steps
  - Run `mcp-zen-of-docs validate` to audit docs quality.
  - Use `mcp-zen-of-docs page write` to draft a new page.
```

---

## Related commands

- [`setup`](setup.md) — bootstrap docs work for the project
- [`validate`](validate.md) — audit docs quality
- [`page`](page.md) — create or draft a documentation page

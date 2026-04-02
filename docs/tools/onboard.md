---
title: onboard
description: Bootstrap docs setup artifacts, starter pages, and contributor guidance for a project.
tags:
  - tools
  - onboard
---

# onboard

> Bootstrap docs work from the terminal with a task-shaped command, a shorter `setup` alias, and JSON output when automation needs the raw contract.

`onboard` is the docs bootstrap command group. For terminal users, the most important behavior changes are:

- `setup` is a direct alias for `onboard`
- `onboard full` is the primary task-shaped entry point
- interactive terminals get short human summaries, while `--json` preserves the underlying payload

The command does **not** claim to be a fantasy all-in-one docs platform. It generates contributor guidance, setup artifacts, and optional starter boilerplate that match the shipped implementation.

---

## Main command vs subcommands

### `onboard full`

This is the human-facing entry point. It accepts `--mode` to control how far the flow goes:

| `--mode` value | What it does |
|----------------|--------------|
| `skeleton` | Generate onboarding guidance only |
| `init` | Generate setup artifacts only |
| `boilerplate` | Generate starter docs files only |
| `full` | Run guide + init + boilerplate |

### Other `onboard` subcommands

| Subcommand | Purpose |
|------------|---------|
| `onboard plan` | Generate a docs page plan |
| `onboard phase` | Run one named pipeline phase |
| `onboard install` | Run an ephemeral installer in a fresh environment |
| `onboard init <framework>` | Initialize a framework's canonical structure |

---

## Human mode vs automation mode

- **TTY / `--human`** — focused terminal output for people, such as onboarding guidance or a summary of generated artifacts.
- **`--json`** — raw payloads for scripts, CI, and tests.

The underlying response model is the same either way; only the presentation changes.

---

## `onboard full` flags

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--project-root` | path | No | Root of the project to onboard. Default: `.` |
| `--project-name` | string | No | Project name used in generated pages. Default: `Project` |
| `--mode` | string | No | One of `skeleton`, `init`, `boilerplate`, or `full` |
| `--output-file` | path | No | Write the onboarding guide to a file |
| `--include-checklist` | bool | No | Include the checklist in guide output. Default: `true` |
| `--include-shell-scripts` | bool | No | Emit shell helper scripts. Default: `true` |
| `--deploy-provider` | string | No | Deployment target for docs workflow generation |
| `--gate-confirmed` | bool | No | Required when running `--mode boilerplate` directly |
| `--shell-target` | string | No | Restrict emitted shell script targets |
| `--overwrite` | bool | No | Allow generated files to replace existing ones |

---

## Behavior notes that matter

### `setup` is just the shorter name

These commands are equivalent:

```bash
mcp-zen-of-docs setup full --project-root . --mode skeleton
mcp-zen-of-docs onboard full --project-root . --mode skeleton
```

### `full` mode is the comprehensive path

When `--mode full` runs successfully, it combines:

1. onboarding guidance
2. setup artifact generation
3. starter docs boilerplate

### Direct `boilerplate` mode is gated

If you call `--mode boilerplate` directly, pass `--gate-confirmed` so the CLI knows you intentionally want starter docs written.

---

## Examples

### Human guide-only flow

```bash
mcp-zen-of-docs --human setup full \
  --project-root ./my-fastapi-project \
  --project-name "FastAPI Toolkit" \
  --mode skeleton
```

Representative output starts with:

```text
Success: Onboard project
Project name: FastAPI Toolkit
Mode: skeleton
```

### Raw JSON init flow

```bash
mcp-zen-of-docs --json setup full \
  --project-root ./my-fastapi-project \
  --project-name "FastAPI Toolkit" \
  --mode init
```

Use this when another tool needs fields like `init_result`, `deploy_pipelines`, or `shell_scripts`.

### Full bootstrap

```bash
mcp-zen-of-docs onboard full \
  --project-root ./my-fastapi-project \
  --project-name "FastAPI Toolkit"
```

### Boilerplate only

```bash
mcp-zen-of-docs onboard full \
  --project-root ./my-fastapi-project \
  --project-name "FastAPI Toolkit" \
  --mode boilerplate \
  --gate-confirmed
```

### Framework-specific structure init

```bash
mcp-zen-of-docs onboard init zensical --project-root ./my-fastapi-project
```

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **theme**

    Customise the visual identity that onboard generated.

    [:octicons-arrow-right-24: Read theme](theme.md)

-   :octicons-arrow-right-24: **validate**

    Run quality checks after onboard finishes to confirm everything is correct.

    [:octicons-arrow-right-24: Read validate](validate.md)

</div>

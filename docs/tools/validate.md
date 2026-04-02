---
title: validate
description: Run documentation quality checks — links, orphaned files, structure, frontmatter, nav sync, and quality scoring.
tags:
  - tools
  - validate
---

# validate

> Validate the docs surface with short human summaries in the terminal and raw contracts in `--json` mode.

`validate` is now best understood as a **command group**, not one catch-all mode.

- `validate all` checks **links**, **orphans**, and **structure**.
- `validate score` returns the quality score.
- `validate frontmatter` audits frontmatter keys and can fix them.
- `validate nav` audits or syncs navigation.

That distinction matters because the redesigned CLI no longer pretends `validate all` is also the auto-fix entry point for every docs concern.

---

## Human mode vs automation mode

- **TTY / `--human`** — prints a concise summary such as `Config: /path/to/mkdocs.yml (auto-detected)` and only expands sections that need attention.
- **`--json`** — emits the full payload, including `detected_config`, `checks`, `total_issue_count`, and the nested check responses.

If you omit `--mkdocs-file`, `validate all` tries to auto-detect the config file near the docs root.

---

## Commands

| Command | Purpose |
|---------|---------|
| `validate all` | Run links/orphans/structure checks |
| `validate score` | Compute the docs quality score |
| `validate frontmatter` | Audit required frontmatter keys and optionally fix them |
| `validate nav` | Audit or sync navigation config |

---

## `validate all` flags

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--docs-root` | path | No | Root of the docs directory. Default: `docs` |
| `--mkdocs-file` | path | No | Explicit config file. If omitted, the CLI attempts auto-detection |
| `--external-mode` | string | No | External link handling. Default: `report` |
| `--required-header` | string | No | Repeat to require specific headers |
| `--required-frontmatter` | string | No | Repeat to require specific frontmatter keys during structure validation |
| `--check` | string | No | Repeat to limit checks to `links`, `orphans`, or `structure` |

---

## Examples

### Human validation summary

```bash
mcp-zen-of-docs --human validate all \
  --docs-root docs \
  --check orphans
```

Representative output:

```text
Success: Validate docs
Docs root: /path/to/docs
Config: /path/to/mkdocs.yml (auto-detected)
Checks: orphans
✓ No issues found
```

### Raw JSON for automation

```bash
mcp-zen-of-docs --json validate all \
  --docs-root docs \
  --check links
```

Use JSON mode when a script needs fields such as `detected_config` or `total_issue_count`.

### Score the docs set

```bash
mcp-zen-of-docs --json validate score --docs-root docs
```

### Audit and fix frontmatter keys

```bash
mcp-zen-of-docs validate frontmatter \
  --docs-root docs \
  --required-key title \
  --required-key description \
  --fix
```

### Sync navigation

```bash
mcp-zen-of-docs validate nav \
  --project-root . \
  --mode sync
```

!!! warning "Commands that can modify files"
    `validate frontmatter --fix` and `validate nav --mode sync` can rewrite files. `validate all` is report-oriented.

---

## What changed in the redesigned CLI

- `validate all` now clearly communicates **auto-detected config** behavior.
- Human mode suppresses clean sections so you see the signal first.
- `--json` keeps the raw payload intact for tests and CI.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **generate**

    Generate reference docs, diagrams, and changelogs automatically.

    [:octicons-arrow-right-24: Read generate](generate.md)

-   :octicons-arrow-right-24: **scaffold**

    Fix missing pages that validate flagged as orphaned or structurally incomplete.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

</div>

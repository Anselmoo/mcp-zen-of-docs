---
title: validate
description: Run documentation quality checks — links, frontmatter, nav sync, and quality scoring.
tags:
  - tools
  - validate
---

# validate

> Audits documentation quality across links, frontmatter, nav, and structure — and auto-fixes what it can.

Before you commit, validate that links work, frontmatter is complete, and the nav matches the file structure. `validate` audits across four dimensions and returns specific, actionable issues. Pass `fix=true` to repair nav drift and missing frontmatter keys automatically.

---

## Modes

| Mode | What it checks |
|------|---------------|
| `all` | Runs every validator in sequence (default) |
| `score` | Returns a 0.0–1.0 quality score with per-dimension breakdown |
| `frontmatter` | Audits frontmatter keys across all pages in `docs_root` |
| `nav` | Audits or syncs the navigation config against actual files on disk |

---

## When to use it

Run `validate` after every batch of scaffolded pages and before any deployment. Use `mode="score"` in CI to fail the build when quality drops below a threshold. Use `fix=true` after adding or removing pages to keep the nav in sync.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Which checks to run. Default: `"all"` |
| `docs_root` | path | No | Root of the docs directory. Default: `"docs"` |
| `fix` | bool | No | Automatically repair issues where possible. Default: `false` |
| `required_frontmatter` | string[] | No | Keys every page must declare, e.g. `["title","description","tags"]` |
| `required_headers` | string[] | No | H2 headings every page must include, e.g. `["Examples"]` |
| `nav_mode` | string | No | For `nav` mode: `"audit"` (report) or `"sync"` (fix). Default: `"audit"` |
| `external_mode` | string | No | Whether to check external links: `"report"` or `"ignore"`. Default: `"report"` |
| `checks` | string[] | No | Subset of checks: `"links"`, `"structure"`, `"frontmatter"`, `"nav"` |
| `mkdocs_file` | path | No | Nav config to validate against. Default: `"mkdocs.yml"` |

---

## Quality score bands

| Score | Status | Typical cause |
|-------|:------:|--------------|
| 0.90–1.00 | ✅ Excellent | Production-ready |
| 0.75–0.89 | 🟡 Good | Minor gaps — missing descriptions on a few pages |
| 0.60–0.74 | 🟠 Fair | Significant frontmatter gaps or nav drift |
| 0.40–0.59 | 🔴 Poor | Many broken links or pages without headings |
| 0.00–0.39 | ❌ Failing | Docs not usable — run `onboard` first |

---

## Examples

**Full audit with specific errors**

```json
{
  "tool": "validate",
  "arguments": { "mode": "all", "docs_root": "./docs" }
}
```

Returns:

```json
{
  "status": "failed",
  "score": 0.71,
  "issues": [
    {
      "check": "frontmatter",
      "severity": "error",
      "file": "docs/guides/authentication.md",
      "message": "Missing required frontmatter key: 'description'"
    },
    {
      "check": "nav",
      "severity": "warning",
      "message": "Nav entry 'guides/old-setup.md' points to a file that does not exist"
    },
    {
      "check": "links",
      "severity": "error",
      "file": "docs/tools/validate.md",
      "message": "Broken internal link: '../guides/quickstart.md' (file not found)"
    }
  ],
  "passed": ["structure", "external_links"]
}
```

---

**Auto-fix nav drift (`fix=true`)**

```json
{
  "tool": "validate",
  "arguments": { "mode": "nav", "nav_mode": "sync", "fix": true }
}
```

Returns:

```json
{
  "status": "fixed",
  "changes": [
    {
      "action": "removed",
      "nav_entry": "guides/old-setup.md",
      "reason": "File no longer exists on disk"
    },
    {
      "action": "added",
      "nav_entry": "guides/authentication.md",
      "reason": "File exists on disk but was missing from nav"
    }
  ],
  "nav_file_updated": "zensical.toml"
}
```

!!! warning "`fix=true` modifies files"
    `fix=true` rewrites `zensical.toml` (or `mkdocs.yml`) and may add frontmatter to source files. Commit your work before running it.

---

**Quality score for CI**

```json
{
  "tool": "validate",
  "arguments": {
    "mode": "score",
    "required_frontmatter": ["title", "description", "tags"]
  }
}
```

Returns:

```json
{
  "score": 0.87,
  "dimensions": {
    "completeness": 0.92,
    "clarity": 0.85,
    "navigation": 1.00,
    "links": 0.72
  },
  "recommendation": "3 external links returned 404. Run with external_mode='report' to see details."
}
```

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **generate**

    Generate reference docs, diagrams, and changelogs automatically.

    [:octicons-arrow-right-24: Read generate](generate.md)

-   :octicons-arrow-right-24: **scaffold**

    Fix missing pages that validate flagged as orphaned or unlinked.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

</div>

---
title: scaffold
description: Create, batch-create, enrich, or fully write documentation pages using framework-native primitives.
tags:
  - tools
  - scaffold
---

# scaffold

> Creates complete, publication-ready documentation pages using your framework's native syntax.

Write a new documentation page with the correct framework syntax — no more copying wrong admonition syntax from the wrong docs. `scaffold` uses the detected framework profile to produce frontmatter, section headings, admonitions, code blocks, and content tabs in a single call. Unlike [story](story.md), which works from prose intent, `scaffold` takes concrete paths and structural descriptions — use it when you know exactly where the page lives.

---

## Modes

| Mode | What it does |
|------|-------------|
| `write` | Produces a complete, ready-to-publish page (default) |
| `single` | Creates a stub with frontmatter and empty section headings |
| `batch` | Creates multiple stubs in one call from a `pages` spec |
| `enrich` | Fills `TODO` placeholders in an existing scaffold file |

---

## When to use it

Use `scaffold` when you know the page's path, title, and rough content. It's the right tool for creating new pages one at a time or in batch, with automatic nav registration. Use `story` instead when you know the concept but aren't sure how to structure it.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Operation mode. Default: `"write"` |
| `doc_path` | path | Conditional | Output path relative to `docs_root`. Required for `write` and `single` |
| `title` | string | No | Page title and frontmatter `title` value |
| `topic` | string | No | What the page covers — guides content generation |
| `description` | string | No | Frontmatter `description` value |
| `content_hints` | string | No | Key points to include — bullet list or prose |
| `audience` | string | No | Target reader — shapes tone and depth |
| `sections` | string[] | No | Section headings to include |
| `framework` | string | No | Auto-detected from `docs_root` if omitted |
| `docs_root` | path | No | Root of the docs directory. Default: `"docs"` |
| `mkdocs_file` | path | No | Nav config to update. Default: `"mkdocs.yml"` |
| `add_to_nav` | bool | No | Add the new page to the nav config. Default: `true` |
| `overwrite` | bool | No | Replace the file if it already exists. Default: `false` |
| `pages` | object[] | Conditional | Page specs for `batch` mode |
| `sections_to_enrich` | string[] | No | Specific sections to fill in `enrich` mode |
| `output_path` | path | No | Absolute output path (overrides `docs_root` + `doc_path`) |

---

## Examples

**Write a complete page (`mode="write"`)**

```json
{
  "tool": "scaffold",
  "arguments": {
    "mode": "write",
    "doc_path": "guides/authentication.md",
    "title": "Authentication",
    "topic": "How to add API key auth to FastAPI endpoints",
    "audience": "backend developers"
  }
}
```

The generated `docs/guides/authentication.md` opens with:

```markdown
---
title: Authentication
description: Add API key authentication to FastAPI endpoints.
tags:
  - guides
  - authentication
---

# Authentication

FastAPI makes it straightforward to protect endpoints with API keys using the
`HTTPBearer` security scheme. This guide covers the three most common patterns.

...

!!! note "Choose the right scheme"
    API keys suit server-to-server calls. For user-facing apps, prefer OAuth 2.0
    with PKCE.
```

Because `add_to_nav=true` (the default), the page is immediately registered in `zensical.toml`.

!!! tip "Use `content_hints` for precision"
    Pass a bullet list of key points as `content_hints` to steer what goes in each section without writing the whole page yourself.

---

**Batch-create stubs (`mode="batch"`)**

```json
{
  "tool": "scaffold",
  "arguments": {
    "mode": "batch",
    "pages": [
      { "doc_path": "frameworks/zensical.md",    "title": "Zensical" },
      { "doc_path": "frameworks/docusaurus.md",  "title": "Docusaurus" },
      { "doc_path": "frameworks/vitepress.md",   "title": "VitePress" },
      { "doc_path": "frameworks/starlight.md",   "title": "Starlight" }
    ]
  }
}
```

Returns:

```json
{
  "created": [
    "docs/frameworks/zensical.md",
    "docs/frameworks/docusaurus.md",
    "docs/frameworks/vitepress.md",
    "docs/frameworks/starlight.md"
  ],
  "nav_updated": true,
  "skipped": []
}
```

Each stub contains frontmatter, an `# H1`, and `## Overview`, `## Configuration`, `## Examples` sections with `TODO` markers — ready for `enrich` mode.

---

**Fill an existing stub (`mode="enrich"`)**

```json
{
  "tool": "scaffold",
  "arguments": {
    "mode": "enrich",
    "doc_path": "frameworks/vitepress.md",
    "topic": "VitePress configuration and file structure",
    "framework": "vitepress",
    "sections_to_enrich": ["Overview", "Examples"]
  }
}
```

`enrich` rewrites only sections containing `TODO` markers. Sections you've already written are left untouched.

!!! warning "`overwrite=false` by default"
    `scaffold` never replaces an existing file unless you pass `overwrite=true`. If a file exists, the call returns an error with the file path — no silent data loss.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **validate**

    Check the quality and correctness of the pages scaffold just wrote.

    [:octicons-arrow-right-24: Read validate](validate.md)

-   :octicons-arrow-right-24: **story**

    Need richer narrative prose rather than structured stubs? Use story instead.

    [:octicons-arrow-right-24: Read story](story.md)

</div>

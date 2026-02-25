---
title: Why Zen Docs
description: Why AI-generated docs fail without framework awareness — and what mcp-zen-of-docs does about it.
tags:
  - guides
  - philosophy
---

# Why Zen Docs

**AI often generates the wrong markup when it lacks framework context.**

---

## The Problem

- Zensical, Docusaurus, VitePress, and Starlight all use *different syntax* for the same concepts.
- General-purpose AI models train on all four frameworks at once — output is a statistical blend, not your project's dialect.
- One wrong primitive (e.g. `!!! note` in a Docusaurus project) renders as raw text. No error. Just broken docs.

---

## The Solution

mcp-zen-of-docs detects your framework first, then emits the correct syntax for every primitive.
The same workflow fits GitHub Copilot, Copilot CLI, Cursor, Claude Desktop, and other MCP-capable clients.

| Primitive | Zensical | Docusaurus | VitePress | Starlight |
|-----------|----------|------------|-----------|-----------|
| Note admonition | `!!! note "Title"` | `:::note` | `::: info` | `<Aside type="note">` |
| Content tab | `=== "Tab"` | `<TabItem>` | `::: code-group` | `<TabItem>` |
| Code block | ` ```python title=...` | ` ```python title=...` | ` ```python` | ` ```python` |
| Grid cards | `<div class="grid cards">` | Not native | Not native | Not native |

---

## What You Get

| Framework | How it's detected | mcp-zen-of-docs generates |
|-----------|-------------------|--------------------------|
| **Zensical** | `zensical.toml` / `mkdocs.yml` | `!!! note`, `=== "Tab"`, grid cards, Mermaid |
| **Docusaurus** | `docusaurus.config.js` / `.ts` | `:::note`, `<TabItem>`, MDX components |
| **VitePress** | `.vitepress/config.*` | `::: info`, `::: code-group`, Vue containers |
| **Starlight** | `astro.config.mjs` / `.ts` | `<Aside>`, `<TabItem>`, Astro MDX |

---

## What's Next

→ [Quickstart](../quickstart.md) — install mcp-zen-of-docs and detect your framework in 2 minutes.

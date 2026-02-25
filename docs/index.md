---
title: Home
description: A FastMCP v2 MCP server with 10 tools, four primary framework profiles, and supplemental detection for MkDocs Material, Sphinx, and generic Markdown.
template: home.html
tags:
  - home
  - overview
---

<div class="grid cards" markdown>

-   :material-telescope: **Detect & Profile**

    ---

    Identifies your docs framework from config files in milliseconds. Returns the full
    primitive support matrix so every generated snippet uses the right syntax.

    [:octicons-arrow-right-24: detect](tools/detect.md) · [:octicons-arrow-right-24: profile](tools/profile.md)

-   :material-palette: **Generate & Theme**

    ---

    Creates pages, diagrams, SVG assets, CSS themes, and VS Code Copilot instruction files —
    all framework-aware, all correct on the first try.

    [:octicons-arrow-right-24: generate](tools/generate.md) · [:octicons-arrow-right-24: theme](tools/theme.md)

-   :material-check-all: **Validate & Score**

    ---

    Checks links, frontmatter, nav sync, and page length. Returns a numeric quality score
    you can run in CI or enforce before merging.

    [:octicons-arrow-right-24: validate](tools/validate.md)

</div>

---

## Why this exists

AI assistants know Markdown. They don't know *which* framework's dialect you use. Ask one
to add a prerequisites note and you get `!!! note "Prerequisites"` — valid MkDocs syntax.
You're on Docusaurus. It renders as raw text. Fixing one snippet takes seconds; fixing it
across a 40-page docs site takes an afternoon.

The root cause is that the four primary authoring profiles in this server — Zensical, Docusaurus,
VitePress, and Starlight — reinvent many of the same 22 canonical documentation primitives
(admonitions, tabs, code fences, API blocks, badges, diagrams, cards…) with incompatible syntax.
An AI trained on mixed sources can't reliably
pick the right dialect without explicit context.

`mcp-zen-of-docs` provides that context as a live MCP server. It detects your framework,
loads the matching primitive profile, and passes the correct syntax rules to every tool call.
It also recognizes MkDocs Material, Sphinx, and generic Markdown projects as supplemental
detected contexts. Generated content renders correctly the first time. See the full argument in
[Why Zen Docs](guides/why-zen-docs.md).

---

## Tools

| Tool | What it does | Primary use case |
|------|-------------|-----------------|
| [`detect`](tools/detect.md) | Identifies framework from config files | First call in any session |
| [`profile`](tools/profile.md) | Returns primitive support matrix for a framework | Check which primitives are native vs plugin |
| [`scaffold`](tools/scaffold.md) | Creates, enriches, or fully writes doc pages | Generate a new page with correct syntax |
| [`validate`](tools/validate.md) | Checks links, frontmatter, nav sync; scores quality | CI gate or pre-merge check |
| [`generate`](tools/generate.md) | Creates diagrams, SVGs, changelogs, reference docs | Visual assets and release notes |
| [`onboard`](tools/onboard.md) | Full project onboarding in one command | Bootstrap docs for a new project |
| [`theme`](tools/theme.md) | Generates CSS/JS theme files with brand colours | Custom styling without manual CSS |
| [`copilot`](tools/copilot.md) | Creates VS Code Copilot instruction/agent files | Persistent docs context in Copilot |
| [`docstring`](tools/docstring.md) | Audits and generates Python docstrings | Source code documentation coverage |
| [`story`](tools/story.md) | Composes structured docs from a prose prompt | Long-form content with deterministic structure |

See [Tools Overview](tools/index.md) for the full reference.

---

## Get started in 30 seconds

```bash
uvx --from mcp-zen-of-docs mcp-zen-of-docs-server
```

Add it to GitHub Copilot in VS Code:

```json
{
  "servers": {
    "zen-of-docs": {
      "command": "uvx",
      "args": ["--from", "mcp-zen-of-docs", "mcp-zen-of-docs-server"]
    }
  }
}
```

Then ask: *"Detect my docs framework."* That's it. See [Quickstart](quickstart.md) for
Copilot CLI, Cursor, Claude Desktop, Docker, and one-click installers.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Quickstart**

    Connect to your AI client and run your first tool call in under two minutes.

    [:octicons-arrow-right-24: Get started](quickstart.md)

-   :octicons-arrow-right-24: **Tools Overview**

    All ten tools with modes, parameters, and return values.

    [:octicons-arrow-right-24: Browse tools](tools/index.md)

</div>

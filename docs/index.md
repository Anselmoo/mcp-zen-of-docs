---
title: Home
description: A FastMCP v2 MCP server for framework-aware documentation workflows, visual assets, and quality checks.
template: home.html
tags:
  - home
  - overview
---

<div class="grid cards" markdown>

-   :material-telescope: **Detect & Profile**

    ---

    Identify the docs framework that is actually present, then resolve the right primitive syntax before an assistant writes a single line.

    [:octicons-arrow-right-24: detect](tools/detect.md) · [:octicons-arrow-right-24: profile](tools/profile.md)

-   :material-palette: **Generate & Theme**

    ---

    Create pages, diagrams, SVG assets, and theme files that fit the target framework instead of generic Markdown defaults.

    [:octicons-arrow-right-24: generate](tools/generate.md) · [:octicons-arrow-right-24: theme](tools/theme.md)

-   :material-check-all: **Validate & Score**

    ---

    Check links, frontmatter, navigation sync, and quality signals before a docs change ships.

    [:octicons-arrow-right-24: validate](tools/validate.md)

</div>

---

## Why this exists

AI assistants are good at writing Markdown. They are not automatically good at writing the
*right dialect* of Markdown for the site in front of them.

Ask for a note on a Docusaurus page and an assistant might return MkDocs syntax. Ask for tabs
in Starlight and it might answer with a VitePress container. The wording can be excellent while
the rendered result is still broken.

`mcp-zen-of-docs` fixes that problem by turning framework context into a first-class input. It
detects the docs stack, loads the matching authoring profile, and gives every tool the rules it
needs to emit native syntax for 22 canonical documentation primitives.

If you want the longer case for why this matters, start with [Why Zen Docs](guides/why-zen-docs.md).

---

## Advanced features

<section class="zen-advanced-band" id="advanced-features" data-visual="advanced-features">
  <div class="zen-advanced-grid">
    <article class="zen-advanced-card zen-advanced-card--wide">
      <p class="zen-advanced-card__eyebrow">System setup</p>
      <h3>Onboard inherited docs without reverse-engineering the stack</h3>
      <p><code>onboard</code> combines context detection, readiness checks, scaffolding, and theme wiring so a new or inherited docs project can become AI-ready in one guided pass.</p>
      <p><a href="tools/onboard.md">Explore onboard</a> · <a href="quickstart.md">Start with quickstart</a></p>
    </article>
    <article class="zen-advanced-card">
      <p class="zen-advanced-card__eyebrow">Source truth</p>
      <h3>Translate primitives across frameworks</h3>
      <p>Use <code>profile</code> to compare support levels, render native snippets, and translate constructs like admonitions, tabs, and card grids between framework dialects.</p>
      <p><a href="tools/profile.md">Read profile</a> · <a href="frameworks/index.md">Compare frameworks</a></p>
    </article>
    <article class="zen-advanced-card">
      <p class="zen-advanced-card__eyebrow">Visual layer</p>
      <h3>Generate assets and themes that belong to the docs system</h3>
      <p>Create SVGs, badges, diagrams, and brand-aware theme files so the docs site feels designed, not assembled from disconnected snippets.</p>
      <p><a href="tools/generate.md">Read generate</a> · <a href="tools/theme.md">Read theme</a></p>
    </article>
    <article class="zen-advanced-card">
      <p class="zen-advanced-card__eyebrow">Workflow memory</p>
      <h3>Keep AI output aligned across long-running documentation work</h3>
      <p>Use <code>copilot</code>, <code>docstring</code>, and <code>story</code> to encode conventions, close code-doc drift, and turn rough prompts into structured long-form docs.</p>
      <p><a href="tools/copilot.md">Copilot assets</a> · <a href="tools/docstring.md">Docstring coverage</a> · <a href="tools/story.md">Narrative docs</a></p>
    </article>
  </div>
</section>

---

## Tools at a glance

| Tool | What it does | Best starting use |
|------|--------------|-------------------|
| [`detect`](tools/detect.md) | Detect framework context and readiness | First call in any new project or session |
| [`profile`](tools/profile.md) | Query primitive support and render native snippets | Resolve framework-specific syntax before writing |
| [`scaffold`](tools/scaffold.md) | Create, enrich, or fully write docs pages | Generate a correct page skeleton quickly |
| [`validate`](tools/validate.md) | Audit quality, frontmatter, links, and nav state | Gate docs changes before merge |
| [`generate`](tools/generate.md) | Produce diagrams, SVGs, changelogs, and reference assets | Build the visual and reference layer |
| [`onboard`](tools/onboard.md) | Bootstrap docs structure and configuration | Stand up a new or inherited docs site |
| [`theme`](tools/theme.md) | Generate CSS/JS theme files and configuration | Apply a coherent visual system |
| [`copilot`](tools/copilot.md) | Create Copilot instruction, prompt, and agent assets | Preserve docs conventions in AI-assisted work |
| [`docstring`](tools/docstring.md) | Audit and generate Python docstrings | Improve API reference readiness |
| [`story`](tools/story.md) | Compose narrative docs from prose intent | Turn rough ideas into structured long-form pages |

See [Tools Overview](tools/index.md) for the full reference and workflow map.

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

Then ask your assistant to run the standard workflow:

```text
detect → profile → act
```

For installation targets, MCP client setup, and the first real workflow, continue to [Quickstart](quickstart.md).

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Quickstart**

    Connect the server, run the first tool call, and see the workflow end to end.

    [:octicons-arrow-right-24: Get started](quickstart.md)

-   :octicons-arrow-right-24: **Frameworks**

    Compare the primary profiles and the supplemental detected contexts.

    [:octicons-arrow-right-24: Compare frameworks](frameworks/index.md)

-   :octicons-arrow-right-24: **Guides**

    Learn the concepts behind Detect → Profile → Act and the 22 canonical primitives.

    [:octicons-arrow-right-24: Browse guides](guides/index.md)

</div>

---
title: generate
description: Generate diagrams, visual assets, reference documentation, and changelogs from source code and git history.
tags:
  - tools
  - generate
---

# generate

> Produces diagrams, visual assets, reference docs, and changelogs from source material.

`generate` turns descriptions, source code, and git history into publishable documentation artefacts. Use it when you need to produce something *from source material* — a prose description, a running server, or a git log — rather than write something from scratch.

---

## Modes

| Mode | What it produces |
|------|----------------|
| `visual` | SVG visual assets — page headers, badges, social cards (default) |
| `diagram` | Mermaid diagram source from a prose description |
| `render` | Renders Mermaid source to SVG or PNG |
| `svg` | Saves raw SVG markup to a file on disk |
| `reference` | MCP tool reference, CLI command docs, or authoring primitive pack |
| `changelog` | Changelog from git commits in Keep a Changelog format |

---

## When to use it

Use `generate` after scaffolding the page structure when you need diagrams, brand assets, an API reference, or a release changelog. `onboard` calls `generate` internally during full pipeline runs.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | What to generate. Default: `"visual"` |
| `topic` | string | No | Subject for `visual` or `diagram` generation |
| `description` | string | No | Prose description for `diagram` mode |
| `diagram_type` | string | No | Mermaid type: `flowchart`, `sequenceDiagram`, `classDiagram`, `erDiagram`. Default: `"flowchart"` |
| `direction` | string | No | Flowchart direction: `LR`, `TD`, `BT`, `RL` |
| `mermaid_source` | string | Conditional | Mermaid source string. Required for `render` mode |
| `output_format` | string | No | Output format for `render` mode: `"svg"` or `"png"`. Default: `"svg"` |
| `output_path` | path | No | Where to save the file |
| `overwrite` | bool | No | Replace existing output file. Default: `false` |
| `reference_kind` | string | No | Reference doc type: `"mcp-tools"`, `"cli"`, `"authoring"`. Default: `"mcp-tools"` |
| `since_tag` | string | No | Git tag to start changelog from |
| `version` | string | No | Release version label for changelog |
| `asset_kind` | string | No | Visual asset type: `"badge"`, `"header"`, `"social-card"` |
| `primary_color` | hex | No | Brand colour for visual assets. Default: `"#5C6BC0"` |
| `title` | string | No | Title text for visual assets |
| `subtitle` | string | No | Subtitle text for visual assets |
| `source_file` | path | No | Source file for `reference` mode |

---

## Examples

=== "Visual badge"

    **Generate a documentation quality badge**

    ```json
    {
      "tool": "generate",
      "arguments": {
        "mode": "visual",
        "asset_kind": "badge",
        "title": "mcp-zen-of-docs",
        "subtitle": "documentation quality",
        "primary_color": "#1de9b6",
        "output_path": "docs/assets/badge.svg"
      }
    }
    ```

    Returns:

    ```json
    {
      "output_path": "docs/assets/badge.svg",
      "format": "svg",
      "dimensions": { "width": 320, "height": 80 },
      "asset_kind": "badge"
    }
    ```

    Embed in Markdown with:

    ```markdown
    ![Docs Quality](assets/badge.svg)
    ```

=== "Mermaid diagram"

    **Generate a flowchart from a description**

    ```json
    {
      "tool": "generate",
      "arguments": {
        "mode": "diagram",
        "description": "The Detect → Profile → Act pattern",
        "direction": "LR"
      }
    }
    ```

    Returns Mermaid source to paste into a fenced block in any page:

    ````markdown
    ```mermaid
    flowchart LR
        A["project_root"] --> B["detect"]
        B -->|framework + config_path| C["profile"]
        C -->|primitive syntax| D["scaffold / validate / generate"]
    ```
    ````

=== "Changelog"

    **Generate a changelog from git commits**

    ```json
    {
      "tool": "generate",
      "arguments": {
        "mode": "changelog",
        "since_tag": "v0.1.0",
        "version": "0.2.0",
        "output_path": "docs/changelog.md"
      }
    }
    ```

    Produces `docs/changelog.md` in Keep a Changelog format:

    ```markdown
    ## [0.2.0] - 2025-06-14

    ### Added
    - `generate` tool: `changelog` mode now supports `--since-tag` (#42)
    - `validate` tool: `score` mode with per-dimension breakdown (#38)

    ### Fixed
    - `detect` no longer crashes on empty repos with no docs directory (#45)
    ```

=== "Reference docs"

    **Generate MCP tool reference from server introspection**

    ```json
    {
      "tool": "generate",
      "arguments": {
        "mode": "reference",
        "reference_kind": "mcp-tools",
        "output_path": "docs/reference/api.md"
      }
    }
    ```

    Returns:

    ```json
    {
      "output_path": "docs/reference/api.md",
      "tools_documented": 10,
      "parameters_documented": 87,
      "examples_included": 10
    }
    ```

!!! note "diagram vs render"
    `mode="diagram"` generates Mermaid source text to paste into Markdown. `mode="render"` takes Mermaid source and produces a binary SVG or PNG file for standalone image use.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **onboard**

    `onboard` calls `generate` internally to produce reference docs and assets for new projects.

    [:octicons-arrow-right-24: Read onboard](onboard.md)

-   :octicons-arrow-right-24: **theme**

    Pair generated visual assets with a custom CSS theme for a consistent brand look.

    [:octicons-arrow-right-24: Read theme](theme.md)

</div>

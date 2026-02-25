---
title: Authoring Primitives
description: The 22 canonical primitive identifiers used by mcp-zen-of-docs, plus the most common framework-native syntax patterns.
tags:
  - guides
  - primitives
---

# Authoring Primitives

A **primitive** is a canonical documentation concept in the mcp-zen-of-docs code surface. The
server currently exposes 22 primitive identifiers through `AuthoringPrimitive`. Syntax differs by
framework; the concept does not. The `profile` tool resolves any primitive to its framework-native
form.

---

## The 22 canonical primitives

| Identifier | What it represents |
|-----------|--------------------|
| `frontmatter` | YAML metadata block at the top of a page |
| `heading-h1` | Page-level H1 heading |
| `admonition` | Callout block such as note, warning, or tip |
| `code-fence` | Fenced code block with optional language and metadata |
| `navigation-entry` | Sidebar, nav, or table-of-contents entry |
| `snippet` | Reusable inline or block include/content snippet |
| `table` | Markdown or HTML table |
| `task-list` | Checkbox task list |
| `image` | Embedded image with alt text and optional caption/title |
| `link` | Inline link or cross-reference |
| `footnote` | Footnote reference plus definition |
| `tabs` | Tabbed panels for alternative content |
| `diagram` | Mermaid, Graphviz, or similar diagram block |
| `api-endpoint` | Structured endpoint/reference section |
| `step-list` | Ordered procedural list for walkthroughs |
| `badge` | Inline badge for version, status, or build state |
| `card-grid` | Multi-card layout/grid |
| `button` | Link styled as a call-to-action button |
| `tooltip` | Hover-revealed explanatory text |
| `math` | Inline or display math notation |
| `formatting` | Inline emphasis beyond plain prose (highlight, superscript, etc.) |
| `icons-emojis` | Inline iconography and emoji shortcodes |

!!! tip "Code-truth note"
    The identifiers above match the source enum used by the MCP server. The examples below focus on
    the most common author-facing patterns rather than exhaustively showing all 22 primitives.

---

## Common syntax reference

### heading-h1, link, and basic formatting

=== "All frameworks"

    ```markdown
    # H1  **bold**, _italic_, ~~strikethrough~~, [link](url)
    ```

### frontmatter

=== "Zensical"

    ```yaml
    ---
    title: Page Title
    tags:
      - guides
    ---
    ```

=== "Docusaurus / Starlight"

    ```yaml
    ---
    title: Page Title
    sidebar_position: 1
    ---
    ```

    Starlight uses `sidebar: { order: 1 }` instead of `sidebar_position`.

### admonition

=== "Zensical"

    ```markdown
    !!! note "Title"
        Content indented 4 spaces.
    ```

=== "Docusaurus"

    ```markdown
    :::note Title
    Content here.
    :::
    ```

=== "VitePress"

    ```markdown
    ::: info Title
    Content here.
    :::
    ```

=== "Starlight"

    ```mdx
    import { Aside } from '@astrojs/starlight/components'
    <Aside type="note" title="Title">Content here.</Aside>
    ```

### button

=== "Zensical"

    ```markdown
    [Primary](url){ .md-button .md-button--primary }
    [Secondary](url){ .md-button }
    ```

No native button primitive in Docusaurus, VitePress, or Starlight — use a custom CSS class or component.

### code-fence

=== "All frameworks"

    ```python title="my_module.py"
    return f"Hello, {name}"
    ```
    VitePress uses `[my_module.py]` instead of `title="my_module.py"`.

### tabs

=== "Zensical"

    ```markdown
    === "Tab name"

        Content — blank line after header, 4-space indent on all content.
    ```

=== "Docusaurus / Starlight"

    ```mdx
    import Tabs from '@theme/Tabs'
    import TabItem from '@theme/TabItem'
    <Tabs>
      <TabItem value="a" label="Tab name">Content here.</TabItem>
    </Tabs>
    ```

VitePress supports `::: code-group` for code-only tabs, not general content tabs.

### table

=== "All frameworks"

    ```markdown
    | Column A | Column B |
    |----------|:--------:|
    | left     | center   |
    ```

### diagram

=== "Zensical / VitePress"

    ```mermaid
    flowchart LR
        A[Input] --> B[Process] --> C[Output]
    ```

Docusaurus/Starlight use the same Mermaid syntax after enabling a plugin. Docusaurus: `@docusaurus/theme-mermaid`. Starlight: `starlight-mermaid`.

### footnote

=== "Zensical / VitePress"

    ```markdown
    A sentence with a footnote.[^1]
    [^1]: The footnote text.
    ```

Not supported in Docusaurus or Starlight — use `remark-footnotes` or inline parenthetical notes.

### formatting

=== "Zensical"

    ```markdown
    ==highlighted==   ^^underline^^   H^2^O   CO~2~
    ```

Only GFM `~~strikethrough~~` is available in Docusaurus, VitePress, and Starlight. Other extensions require custom CSS.

### card-grid

=== "Zensical"

    ```markdown
    <div class="grid cards" markdown>

    -   :material-star: **Card title**

        ---

        Body. [:octicons-arrow-right-24: Link](page.md)

    </div>
    ```

No native grid primitive in Docusaurus, VitePress, or Starlight — use a custom React/Vue component or CSS grid.

### icons-emojis

=== "Zensical"

    ```markdown
    :material-check-circle:   :octicons-star-24:   :smile:
    ```

=== "Starlight"

    ```mdx
    import { Icon } from '@astrojs/starlight/components'
    <Icon name="star" />  <Icon name="approve-check-circle" />
    ```

### image

=== "All frameworks"

    ```markdown
    ![Alt text](path/to/image.png "Optional title")
    ```

### task-list and step-list

=== "All frameworks"

    ```markdown
    - Unordered item
    - [ ] Task (unchecked)
    - [x] Task (checked)
    1. Ordered item
    ```

    `task-list` maps directly to checkbox syntax. `step-list` is the same ordered-list concept used
    when the server generates procedural walkthroughs.

### math

=== "All frameworks"

    ```markdown
    Inline: $E = mc^2$
    Display: $$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
    ```

    Zensical: native. Docusaurus/VitePress: add `remark-math` + `rehype-katex`. Starlight: add `starlight-math`.

### tooltip

=== "Zensical"

    ```markdown
    [Hover me](page.md "This text appears on hover")
    *[HTML]: HyperText Markup Language
    The HTML spec is long.
    ```

Not supported in Docusaurus, VitePress, or Starlight — abbreviation expansion and hover tooltips require custom components.

### badge, snippet, navigation-entry, and api-endpoint

These four primitives are part of the canonical source vocabulary, but they are usually expressed
through project-specific patterns rather than one universal Markdown shape:

- `badge` — inline status badges in README/docs landing pages
- `snippet` — reusable include or shared-content mechanism
- `navigation-entry` — framework-specific sidebar/nav configuration
- `api-endpoint` — structured endpoint sections in API docs

Use `profile` when you need the exact framework-native guidance for one of these primitives.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **profile tool**

    Resolve or translate any primitive to its framework-native syntax programmatically.

    [:octicons-arrow-right-24: Read more](../tools/profile.md)

-   :octicons-arrow-right-24: **Frameworks overview**

    Full primitive support matrix and framework comparison.

    [:octicons-arrow-right-24: Compare frameworks](../frameworks/index.md)

</div>

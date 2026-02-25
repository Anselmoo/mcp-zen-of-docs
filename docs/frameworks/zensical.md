---
title: Zensical
description: Using mcp-zen-of-docs with Zensical — the default framework with full native primitive support.
tags:
  - frameworks
  - zensical
---

# Zensical

Zensical is a Python documentation framework built on MkDocs + Material — the default for `mcp-zen-of-docs`. All authoring primitives are supported natively; no extra packages required for admonitions, tabs, diagrams, or card grids.

**Use Zensical when** you write Python projects, want a docs-as-code pipeline, or need `mkdocstrings` API docs generated from source docstrings.

---

## Detection

`detect` identifies Zensical from these signals, in priority order:

| Signal | Confidence |
|---|:---:|
| `zensical.toml` in project root | 1.0 — exact match |
| `zensical.yml` / `zensical.yaml` | High |
| `.zensical/config.yml` | High |
| `mkdocs.yml` with `theme: material` | High |
| `pyproject.toml` containing `zensical` | Medium |

---

## Key primitives

**Admonitions** — rendered by the `admonition` extension:

```markdown
!!! note "Title"
    Content indented 4 spaces.

??? warning "Collapsible (click to expand)"
    Hidden until clicked. Requires `pymdownx.details`.
```

**Content tabs** — requires `pymdownx.tabbed`:

```markdown
=== "Python"

    ```python
    print("hello")
    ```

=== "Bash"

    ```bash
    echo hello
    ```
```

**Card grid** — requires `attr_list` + `md_in_html`:

```markdown
<div class="grid cards" markdown>

-   :material-star: **Card title**

    ---

    Description text.

    [:octicons-arrow-right-24: Learn more](page.md)

</div>
```

---

## Extensions config

Add these to `zensical.toml` for full primitive support:

```toml
markdown_extensions = [
  "admonition",
  "attr_list",
  "md_in_html",
  "pymdownx.highlight",
  "pymdownx.superfences",
  "pymdownx.tabbed",
  "pymdownx.details",
  "pymdownx.emoji",
]

[project.theme.features]
"content.tabs.link" = true
```

Use the `theme` tool to generate this block automatically.

---

## What scaffold produces

When `scaffold` runs in a Zensical project it emits:

- YAML frontmatter (`title`, `description`, `tags`)
- `# Heading` matching the title
- Framework-native admonitions (`!!! note`)
- Extension-aware code fences (`` ```python ``)
- Nav entry appended to `zensical.toml` automatically

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Docusaurus**

    See how the same primitives look in a React-based framework.

    [:octicons-arrow-right-24: Read more](docusaurus.md)

</div>

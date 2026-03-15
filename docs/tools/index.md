---
title: Tools
description: All ten mcp-zen-of-docs tools at a glance — what each one does, when to use it, and how they fit together.
tags:
  - tools
  - overview
---

# Tools

Ten MCP tools. Multiple modes. One framework-aware documentation workflow.

Use this page as the operating map for the server. The dependable baseline is simple:
detect the project, profile the primitive, then use the creation or quality tools that fit the job.

If you are new to the server, start with [Quickstart](../quickstart.md), then come back here to choose the next tool intentionally.

<figure class="chapter-banner">
    <img src="../assets/chapters/tools-studio.svg" alt="An illustration of modular tool cards connected by a calm workflow line." />
</figure>

---

## All tools at a glance

| Tool | What it does | When to use it |
|------|--------------|----------------|
| [detect](detect.md) | Identify framework context and readiness | First step in any workflow |
| [profile](profile.md) | Query primitive support and render native snippets | Before writing framework-specific markup |
| [scaffold](scaffold.md) | Create or enrich docs pages | Generate a new page or fill gaps in an existing one |
| [validate](validate.md) | Check links, frontmatter, navigation, and quality | Before merge or before publishing |
| [generate](generate.md) | Produce diagrams, SVGs, changelogs, and reference assets | Build the visual and reference layer |
| [onboard](onboard.md) | Bootstrap a docs project and wire defaults | Starting from zero or inheriting a docs site |
| [theme](theme.md) | Generate CSS/JS theme files and config | Apply a visual system without manual CSS archaeology |
| [copilot](copilot.md) | Create Copilot instruction, prompt, and agent assets | Encode documentation conventions for AI workflows |
| [docstring](docstring.md) | Audit and generate Python docstrings | Improve source-to-reference coverage |
| [story](story.md) | Compose narrative docs from prose intent | Turn rough product or technical ideas into structured docs |

!!! tip "Recommended baseline"
    Use [`detect`](detect.md) first, confirm the relevant primitive with [`profile`](profile.md), then move into `scaffold`, `generate`, `story`, or `validate`.

---

## By category

### :mag: Discovery

| Tool | Primary use |
|------|-------------|
| [detect](detect.md) | Identify the framework and project readiness signals |
| [profile](profile.md) | Resolve primitive support, caveats, and native syntax |

> These tools provide the context that makes the rest of the workflow reliable.

### :hammer: Creation

| Tool | Primary use |
|------|-------------|
| [scaffold](scaffold.md) | Create or enrich docs pages |
| [generate](generate.md) | Produce diagrams, SVGs, badges, changelogs, and reference assets |
| [onboard](onboard.md) | Stand up an AI-ready docs project structure |

> Use these when you are building pages, assets, or a full docs foundation.

### :white_check_mark: Quality

| Tool | Primary use |
|------|-------------|
| [validate](validate.md) | Audit docs quality and structural correctness |
| [docstring](docstring.md) | Improve code-to-doc parity for Python APIs |

> Use these before publishing or when cleaning up an inherited docs set.

### :paintbrush: Workflow

| Tool | Primary use |
|------|-------------|
| [theme](theme.md) | Generate and wire a coherent visual layer |
| [copilot](copilot.md) | Preserve docs conventions in AI-assisted editing |
| [story](story.md) | Produce longer narrative documentation from intent |

> Use these to shape how documentation gets written, maintained, and visually expressed.

---

## Typical workflows

### Starting from scratch

```text
detect → onboard → theme → validate
```

Use `detect` to confirm the environment, `onboard` to scaffold the docs surface, `theme` to establish the presentation layer, and `validate` to catch structural issues before publishing.

### Adding a new page

```text
detect → profile → scaffold → validate
```

`profile` is the key step here: it resolves the primitive rules that keep the page native to the detected framework.

### Improving an existing docs set

```text
detect → validate → scaffold enrich → docstring → validate
```

Start with the gaps you can measure, then use generation and enrichment tools to close them.

### Migrating between frameworks

```text
detect → profile translate → story/scaffold → validate
```

Translation is strongest when the source and target frameworks are both explicit. Keep [Detect → Profile → Act](../guides/detect-profile-act.md) nearby for the operating model.

---

## How they connect

The tools are designed to cooperate, not to act as isolated commands.

- [`detect`](detect.md) establishes source-truth context.
- [`profile`](profile.md) resolves what the current framework can support.
- Creation tools use that context to write native output.
- Quality tools surface what still needs attention.

For the conceptual model behind that flow, read [Detect → Profile → Act](../guides/detect-profile-act.md) and [Authoring Primitives](../guides/primitives.md).

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **detect**

    Start here when you need framework context or readiness signals.

    [:octicons-arrow-right-24: Read detect](detect.md)

-   :octicons-arrow-right-24: **profile**

    Resolve primitives, support levels, and framework-native snippets.

    [:octicons-arrow-right-24: Read profile](profile.md)

-   :octicons-arrow-right-24: **Guides**

    Step back from the commands and learn the mental model.

    [:octicons-arrow-right-24: Browse guides](../guides/index.md)

</div>

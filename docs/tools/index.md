---
title: Tools
description: All ten mcp-zen-of-docs tools at a glance — what each one does, when to use it, and how they connect.
tags:
  - tools
  - overview
---

# Tools

Ten tools. One responsibility each. Together they cover the full documentation lifecycle —
from detecting a framework on a first run to generating changelogs and enforcing authoring
standards with Copilot instructions.

Use this page as the command map for the server. If you're not sure where to begin, start with
the discovery tools, move into creation, and finish with validation.

If you're coming from [Quickstart](../quickstart.md), the same flow applies whether you use GitHub Copilot,
Copilot CLI, Cursor, Claude Desktop, or another MCP client.

<figure class="chapter-banner">
    <img src="../assets/chapters/tools-studio.svg" alt="An illustration of modular tool cards connected by a calm workflow line." />
</figure>

---

## All tools at a glance

| Tool | One-line description | When to use it |
|------|---------------------|----------------|
| [detect](detect.md) | Identify the docs framework from config files | First step in any workflow; gate for CI pipelines |
| [profile](profile.md) | Query primitive support and resolve native syntax | Before writing admonitions, tabs, or grids |
| [scaffold](scaffold.md) | Create or write complete documentation pages | Creating new pages with correct framework syntax |
| [validate](validate.md) | Check quality — links, frontmatter, nav, score | After scaffolding; pre-deployment quality gate |
| [generate](generate.md) | Produce diagrams, visual assets, reference docs, changelogs | Artefacts from source material (code, git history) |
| [onboard](onboard.md) | Full project setup from zero in one command | New project or inherited undocumented codebase |
| [theme](theme.md) | Generate brand CSS and extension config blocks | Applying custom colours or enabling MkDocs extensions |
| [copilot](copilot.md) | Create VS Code Copilot instruction/prompt/agent files | Encoding docs conventions for AI-assisted editing |
| [docstring](docstring.md) | Audit and stub source code docstrings | Closing the gap between code and API reference docs |
| [story](story.md) | Compose narrative docs from prose intent | Explaining concepts without knowing the final structure |

!!! tip "Start here"
    New to the server? Run `detect` first, confirm the framework with `profile`, then use
    `scaffold` or `story` to generate content that already matches your docs stack.

---

## By category

### :mag: Discovery

| Tool | Primary use |
|------|-------------|
| [detect](detect.md) | Identify the framework from config files |
| [profile](profile.md) | Query primitive support and resolve native syntax |

> Run these first. They identify the framework before any other tool acts.

### :hammer: Creation

| Tool | Primary use |
|------|-------------|
| [scaffold](scaffold.md) | Create and write complete documentation pages |
| [generate](generate.md) | Produce diagrams, visual assets, and changelogs |
| [onboard](onboard.md) | Full project setup from zero in one command |

> Build pages, assets, and full project structures.

### :white_check_mark: Quality

| Tool | Primary use |
|------|-------------|
| [validate](validate.md) | Check links, frontmatter, nav, and quality score |
| [docstring](docstring.md) | Audit and stub source code docstrings |

> Audit standards and enforce correctness before publishing.

### :paintbrush: Workflow

| Tool | Primary use |
|------|-------------|
| [theme](theme.md) | Generate brand CSS and extension config blocks |
| [copilot](copilot.md) | Create VS Code Copilot instruction and agent files |
| [story](story.md) | Compose narrative docs from prose intent |

> Shape the visual identity, AI assistance, and narrative docs.

---

## Typical workflows

### Starting from scratch

```text
onboard → theme → validate → generate (reference)
```

`onboard` sets up the framework, scaffolds pages, and applies a default theme; `validate` checks the result; `generate reference` produces the API docs.

### Adding a new page

```text
detect → profile → scaffold (write) → validate
```

`detect` confirms the framework; `profile` resolves the correct admonition syntax; `scaffold` writes the complete page; `validate` checks links and frontmatter.

### Maintaining existing docs

```text
validate (score) → docstring (audit) → scaffold (enrich) → validate
```

`validate` surfaces quality gaps; `docstring` finds undocumented symbols; `scaffold enrich` fills TODO sections; `validate` confirms the score improved.

### Migrating between frameworks

```text
detect → profile (translate) → story (migration_mode=guide) → validate
```

`detect` identifies the current framework; `profile translate` maps each primitive; `story` writes the migration guide; `validate` checks the output.

### Publishing

```text
validate (all, fix=true) → generate (changelog) → generate (visual badge)
```

Final pre-publish sweep: fix nav drift, generate the release changelog, produce the documentation quality badge.

---

## How they connect

Every tool that accepts a `project_root` parameter calls [detect](detect.md) internally —
you never need to specify the framework explicitly if your project root is set correctly.
Tools pass their outputs forward: `detect` feeds `profile`, `profile` feeds `scaffold`,
and `validate` catches anything that went wrong.

The underlying pattern is **Detect → Profile → Act**. See
[Detect → Profile → Act](../guides/detect-profile-act.md) for a full explanation.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **detect**

    Start here. It's the foundation every other tool builds on.

    [:octicons-arrow-right-24: Read detect](detect.md)

-   :octicons-arrow-right-24: **Quickstart**

    A 5-minute walkthrough using all ten tools on a real project.

    [:octicons-arrow-right-24: Read quickstart](../quickstart.md)

</div>

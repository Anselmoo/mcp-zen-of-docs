---
title: story
description: Compose structured documentation narratives from prose prompts using deterministic orchestration semantics.
tags:
  - tools
  - story
---

# story

> Composes structured documentation from a prose prompt using a deterministic module pipeline.

`story` takes a description of what you want to explain and returns structured Markdown. Unlike [scaffold](scaffold.md), which requires explicit paths and section headings, `story` works from intent — you describe the narrative and it determines the structure. The same prompt always produces the same structural shape, making `story` safe in automated pipelines.

---

## When to use it

Use `story` when you know what concept to explain but aren't sure how to structure it. Use `scaffold` instead when you know the exact path, title, and sections. Use `story` with `migration_mode` when porting docs from one framework to another.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | **Yes** | The documentation story to compose |
| `modules` | string[] | No | Doc modules to include: `"overview"`, `"examples"`, `"reference"`, `"guide"`, `"faq"` |
| `audience` | string | No | Target reader — shapes tone and assumed knowledge |
| `context` | object | No | Extra key-value context passed to the orchestrator |
| `migration_mode` | string | No | Migration processing: `"guide"` or `"reference"` |
| `migration_source_framework` | string | No | Source framework for migration stories |
| `migration_target_framework` | string | No | Target framework for migration stories |
| `migration_improve_clarity` | bool | No | Rewrite unclear passages. Default: `true` |
| `migration_strengthen_structure` | bool | No | Enforce heading hierarchy. Default: `true` |
| `migration_enrich_examples` | bool | No | Add framework-specific code examples. Default: `false` |
| `auto_advance` | bool | No | Automatically advance through all modules |
| `enable_runtime_loop` | bool | No | Enable iterative refinement loop |
| `runtime_max_turns` | int | No | Max refinement turns when `enable_runtime_loop=true` |
| `include_onboarding_guidance` | bool | No | Append onboarding next-steps section. Default: `false` |

---

## Module pipeline

Each module maps to a content strategy:

| Module | Content strategy |
|--------|----------------|
| `overview` | Lead paragraph + context — what and why |
| `examples` | Concrete code or config examples with realistic output |
| `reference` | Parameter or API table with type/default/description |
| `guide` | Step-by-step walkthrough with numbered steps |
| `faq` | Question-and-answer pairs for common edge cases |

If `modules` is not specified, `story` infers the best set from the prompt.

---

## Examples

**Explain a technical concept**

```json
{
  "tool": "story",
  "arguments": {
    "prompt": "Explain how mcp-zen-of-docs handles framework detection across Zensical, Docusaurus, VitePress, and Starlight — what config files it looks for and how it resolves conflicts in monorepos.",
    "audience": "new contributors",
    "modules": ["overview", "examples"]
  }
}
```

Returns a complete Markdown page opening with:

```markdown
---
title: Framework Detection
description: How mcp-zen-of-docs identifies your documentation framework from config files.
---

# Framework Detection

Framework detection is the foundation of every tool in mcp-zen-of-docs. Before
scaffolding a page or validating links, the server needs to know which framework
owns the docs directory — and that means finding the right config file.

Detection scans `project_root` in priority order. The first config file found wins.
Priority matters in monorepos where a project may have both a `mkdocs.yml` (for a
library's own docs) and a nested `docusaurus.config.js` (for a separate website).
...
```

---

**Write a migration guide**

```json
{
  "tool": "story",
  "arguments": {
    "prompt": "Write a migration guide for moving docs from MkDocs to Docusaurus.",
    "migration_mode": "guide",
    "migration_source_framework": "zensical",
    "migration_target_framework": "docusaurus",
    "migration_enrich_examples": true
  }
}
```

Migration mode activates three additional passes: a clarity pass (rewrites passive voice), a structure pass (normalises heading levels), and an examples pass (adds before/after code blocks for each primitive). Returns a multi-section guide covering file structure comparison, admonition syntax, content tab migration, nav config migration, and CI/CD workflow updates.

---

**FAQ page from domain context**

```json
{
  "tool": "story",
  "arguments": {
    "prompt": "Write an FAQ page about common docstring errors in Python projects.",
    "modules": ["faq"],
    "audience": "junior Python developers",
    "context": { "style": "google", "tool": "mkdocstrings" }
  }
}
```

Returns a page with 6–8 Q&A pairs covering missing `__init__.py`, empty vs missing docstrings, how to document `*args` and `**kwargs` in Google style, and type annotation conflicts.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **scaffold**

    Need a page at a specific path with explicit sections? Use scaffold instead.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    Understand the orchestration pattern that story uses under the hood.

    [:octicons-arrow-right-24: Read the guide](../guides/detect-profile-act.md)

</div>

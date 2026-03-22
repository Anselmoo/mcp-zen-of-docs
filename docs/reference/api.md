---
title: API Reference
description: Auto-generated Python API reference for mcp-zen-of-docs, plus a concise tool parameter reference.
tags:
  - reference
  - api
---

# API Reference

This page brings together two different reference surfaces:

1. **Python model reference** generated from the codebase.
2. **CLI + tool parameter reference** for the public commands.

Use this page when you need precise signatures. If you want the narrative workflow, start with [Tools](../tools/index.md) or [Quickstart](../quickstart.md) first.

<figure class="chapter-banner">
    <img src="../../assets/chapters/api-constellation.svg" alt="An API illustration showing a calm constellation of connected reference nodes." />
</figure>

---

## CLI contract summary

The redesigned CLI exposes one top-level binary:

```text
mcp-zen-of-docs [--human|--json] COMMAND [ARGS]...
```

Key behavior to remember:

- **TTY / `--human`** prints concise terminal summaries.
- **`--json`** preserves the raw payload for automation.
- **`setup`** is the public CLI entrypoint for onboarding work.
- **`validate`** without a subcommand runs the standard read-only validation checks.
- **`story`** human mode returns warning/success summaries, while `--json` preserves orchestration details such as `question_items`, `answer_slots`, and `pipeline_context`.

---

## Python models

::: mcp_zen_of_docs.domain.contracts
    options:
      members:
        - FrameworkName
        - AuthoringPrimitive
        - SupportLevel
        - PrimitiveSupport
        - PrimitiveTranslationGuidance

::: mcp_zen_of_docs.models
    options:
      members:
        - PipelineContext
        - ToolSignature
        - LinkIssue
        - StructureIssue
        - QualityIssue
      show_source: false

---

## Command reference shortcuts

### status

```text
mcp-zen-of-docs status [--project-root PATH]
```

### setup

```text
mcp-zen-of-docs setup [--mode skeleton|init|boilerplate|full] ...
mcp-zen-of-docs setup init <framework> [--project-root PATH]
```

### validate

```text
mcp-zen-of-docs validate [--docs-root PATH] [--mkdocs-file PATH] [--check links|orphans|structure] ...
mcp-zen-of-docs validate score [--docs-root PATH]
mcp-zen-of-docs validate frontmatter [--docs-root PATH] [--required-key TEXT] [--fix]
mcp-zen-of-docs validate nav [--project-root PATH] [--mode audit|sync]
```

### page

```text
mcp-zen-of-docs page new <path> [--title TEXT] ...
mcp-zen-of-docs page fill <path> [--content TEXT] ...
mcp-zen-of-docs page write <path> [--topic TEXT] ...
mcp-zen-of-docs page batch-new [--pages-json PATH|--plan-response-json PATH] ...
```

### syntax

```text
mcp-zen-of-docs syntax check <primitive> --framework <framework>
mcp-zen-of-docs syntax convert <primitive> --from <framework> --to <framework>
```

### diagram / asset / integrations / code-doc / changelog

```text
mcp-zen-of-docs diagram create <description> [--type flowchart|sequence|...]
mcp-zen-of-docs diagram render <mermaid-source> [--output-format svg|png]
mcp-zen-of-docs asset create <kind> [--title TEXT]
mcp-zen-of-docs asset write-svg <output-path> [--svg-markup TEXT|--svg-file PATH]
mcp-zen-of-docs integrations init [--project-root PATH]
mcp-zen-of-docs integrations artifact <instruction|prompt|agent> <file-stem> ...
mcp-zen-of-docs code-doc coverage <path> [--language python|javascript|typescript|go|java|rust]
mcp-zen-of-docs code-doc stubs <path> [--language ...]
mcp-zen-of-docs changelog <version> [--since-tag TAG] [--format keep-a-changelog|github-release]
```

---

## Tool parameters

Quick-reference for all 10 MCP tools. For narrative explanations and workflow guidance, see the [Tools](../tools/index.md) section.

### detect

```text
detect(mode="full", project_root=".")
```

Modes: `full` · `context` · `readiness`

---

### profile

```text
profile(
    mode="show",
    framework=None,
    primitive=None,
    source_framework=None,
    target_framework=None,
    topic=None,
    resolution_mode=None,
)
```

Modes: `show` · `resolve` · `translate`

---

### scaffold

```text
scaffold(
    mode="write",
    doc_path=None,
    title=None,
    topic=None,
    description="",
    audience=None,
    framework=None,
    docs_root="docs",
    mkdocs_file="mkdocs.yml",
    sections=None,
    content_hints=None,
    add_to_nav=True,
    overwrite=False,
    output_path=None,
    pages=None,
    sections_to_enrich=None,
    content="",
)
```

Modes: `write` · `single` · `batch` · `enrich`

---

### validate

```text
validate(
    mode="all",
    docs_root="docs",
    mkdocs_file="mkdocs.yml",
    project_root=".",
    fix=False,
    required_frontmatter=None,
    required_headers=None,
    checks=None,
    nav_mode="audit",
    external_mode="report",
)
```

---

### generate

```text
generate(mode, ...)
```

Use the dedicated [generate](../tools/generate.md) page for the full mode-by-mode surface.

---

### onboard

```text
onboard(project_root=".", framework=None, ...)
```

---

### theme

```text
theme(mode, output_dir="docs/stylesheets", ...)
```

---

### copilot

```text
copilot(mode, output_dir=".github", ...)
```

---

### docstring

```text
docstring(mode, target=None, ...)
```

---

### story

```text
story(mode, prompt, ...)
```

---

## Next reference surfaces

- Read [Tools](../tools/index.md) for workflow context.
- Read [profile](../tools/profile.md) when you need primitive-level support and snippet resolution.
- Read [Frameworks](../frameworks/index.md) when you are comparing framework behavior at a higher level.

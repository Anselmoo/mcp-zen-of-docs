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
2. **Tool parameter reference** for the public MCP commands.

Use this page when you need precise signatures. If you want the narrative workflow, start with [Tools](../tools/index.md) or [Quickstart](../quickstart.md) first.

<figure class="chapter-banner">
    <img src="../../assets/chapters/api-constellation.svg" alt="An API illustration showing a calm constellation of connected reference nodes." />
</figure>

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

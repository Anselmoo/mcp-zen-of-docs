---
title: API Reference
description: Auto-generated Python API reference for mcp-zen-of-docs, plus a complete tool parameter reference.
tags:
  - reference
  - api
---

# API Reference

This page combines two views of the mcp-zen-of-docs surface:

1. **[Python model reference](#python-models)** — auto-generated from Google-style docstrings.
2. **[Tool parameter reference](#tool-parameters)** — concise call signatures for all 10 tools.

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

Quick-reference for all 10 MCP tools. For narrative explanations, see the
[Tools](../tools/index.md) section.

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

Modes: `all` · `score` · `frontmatter` · `nav`

---

### generate

```text
generate(
    mode="visual",
    topic=None,
    description="System overview",
    diagram_type="flowchart",
    direction=None,
    mermaid_source=None,
    output_format="svg",
    output_path=None,
    overwrite=False,
    convert_to_png=False,
    asset_kind=None,
    asset_prompt=None,
    title=None,
    subtitle=None,
    primary_color="#5C6BC0",
    background_color="#F8F9FA",
    style_notes=None,
    target_size_hint=None,
    source_file=None,
    line_start=None,
    line_end=None,
    reference_kind="mcp-tools",
    kind=None,
    version=None,
    since_tag=None,
    repository_url=None,
    source_host=None,
    fmt="keep-a-changelog",
    target=None,
    operation=None,
    svg_markup=None,
    source_svg=None,
    png_output_path=None,
    project_root=".",
)
```

Modes: `visual` · `diagram` · `render` · `svg` · `reference` · `changelog`

---

### onboard

```text
onboard(
    mode="full",
    project_root=".",
    project_path=None,
    framework=None,
    docs_root="docs",
    scaffold_docs=False,
    deploy_provider="github-pages",
    production_url=None,
    staging_url=None,
    dev_url=None,
    phase="constitution",
    onboard_mode="skeleton",
    scope="full",
    force=False,
    include_checklist=True,
    include_shell_scripts=True,
    include_memories=None,
    include_references=None,
    shell_targets=None,
    copy_artifacts=None,
    output_file=None,
    init_framework=None,
    installer="uvx",
    package=None,
    args=None,
    source_subdir=None,
    stdin_input=None,
    analysis_depth=None,
    command=None,
    project_name="Project",
    project_name_alias=None,
    artifacts_dir=".zen-of-docs",
)
```

Modes: `full` · `init` · `phase` · `plan` · `install`

---

### theme

```text
theme(
    mode="css",
    framework="zensical",
    primary_color="#1de9b6",
    accent_color="#7c4dff",
    dark_mode=True,
    font_body=None,
    font_code=None,
    output_dir="docs/stylesheets",
    output_format="toml",
    theme_name="custom",
    target="css-and-js",
    extensions=None,
    include_examples=True,
)
```

Modes: `css` · `extensions`

---

### copilot

```text
copilot(
    mode="artifact",
    kind="instruction",
    title=None,
    content="",
    description=None,
    apply_to="**",
    file_stem=None,
    overwrite=False,
    project_root=".",
    platform="copilot",
    agent="agent",
    tools=None,
    include_tools=True,
)
```

Modes: `artifact` · `config`
Kinds: `instruction` · `prompt` · `agent`

---

### docstring

```text
docstring(
    mode="audit",
    source_path=".",
    language=None,
    style=None,
    min_coverage=0.8,
    include_private=False,
    overwrite=False,
    context_hint=None,
)
```

Modes: `audit` · `optimize`

---

### story

```text
story(
    prompt,
    modules=None,
    audience=None,
    context=None,
    migration_mode=None,
    migration_source_framework=None,
    migration_target_framework=None,
    migration_improve_clarity=True,
    migration_strengthen_structure=True,
    migration_enrich_examples=False,
    auto_advance=None,
    enable_runtime_loop=None,
    runtime_max_turns=None,
    include_onboarding_guidance=False,
)
```

---
title: onboard
description: Run the complete docs onboarding pipeline — detect, plan, scaffold, theme, and configure deployment in one command.
tags:
  - tools
  - onboard
---

# onboard

> Runs the complete docs setup pipeline — detect, plan, scaffold, theme, and CI wiring in one call.

`onboard` chains every other tool together: it detects the framework, analyses the codebase to plan a page structure, scaffolds all the stubs, applies a theme, and optionally outputs a CI/CD deployment config — all in a single conversation turn.

---

## Modes

| Mode | What it does |
|------|-------------|
| `full` | Runs the entire onboarding pipeline end-to-end (default) |
| `init` | Initialises the framework folder structure only (no content) |
| `phase` | Executes one named pipeline phase independently |
| `plan` | Analyses the project and returns a page plan without writing files |
| `install` | Runs an ephemeral framework CLI install (useful in fresh environments) |

---

## When to use it

Use `onboard` when starting a documentation project from zero or inheriting an undocumented codebase. For projects that already have docs, use [scaffold](scaffold.md), [validate](validate.md), or [generate](generate.md) directly. Run `mode="plan"` first on large projects to review the proposed page structure before committing to a full scaffold.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Pipeline mode. Default: `"full"` |
| `project_root` | path | No | Root of the project to onboard. Default: `"."` |
| `framework` | string | No | Auto-detected from `project_root` if omitted |
| `docs_root` | path | No | Where to write the docs directory. Default: `"docs"` |
| `project_name` | string | No | Project name used in generated pages. Default: `"Project"` |
| `project_name_alias` | string | No | Short name or acronym |
| `scaffold_docs` | bool | No | Write page stubs after the plan phase. Default: `false` |
| `deploy_provider` | string | No | Deployment target for CI config. Default: `"github-pages"` |
| `production_url` | string | No | Canonical URL for the built site |
| `staging_url` | string | No | Staging URL for preview builds |
| `phase` | string | No | Starting phase for `phase` mode. Default: `"constitution"` |
| `onboard_mode` | string | No | Scaffold depth: `"skeleton"` or `"full"`. Default: `"skeleton"` |
| `include_checklist` | bool | No | Append a post-onboarding checklist. Default: `true` |
| `include_memories` | bool | No | Persist project context for future tool calls |
| `include_references` | bool | No | Generate an API reference page |
| `output_file` | path | No | Save the onboarding report to a file |

---

## Pipeline phases

When `mode="full"`, these phases run in sequence:

| Phase | What it does |
|-------|-------------|
| **Constitution** | Detects framework, reads existing nav, establishes docs root |
| **Codebase analysis** | Scans `project_root` for modules, CLI entry points, public APIs |
| **Page plan** | Produces a structured list of pages with titles and section outlines |
| **Scaffold** | Creates all planned pages *(only when `scaffold_docs=true`)* |
| **Theme** | Generates `extra.css` and `extra.js` with sensible defaults |
| **Checklist** | Returns next steps specific to your project |

---

## Examples

**Plan without writing files (`mode="plan"`)**

```json
{
  "tool": "onboard",
  "arguments": {
    "mode": "plan",
    "project_root": "./my-fastapi-project",
    "project_name": "FastAPI Toolkit"
  }
}
```

Returns:

```json
{
  "framework": "zensical",
  "project_name": "FastAPI Toolkit",
  "page_plan": [
    { "path": "index.md",              "title": "FastAPI Toolkit",  "sections": ["Overview", "Installation", "Quick start"] },
    { "path": "quickstart.md",         "title": "Quickstart",       "sections": ["Prerequisites", "Installation", "First request"] },
    { "path": "reference/api.md",      "title": "API Reference",    "sections": ["Endpoints", "Authentication", "Error codes"] },
    { "path": "guides/auth.md",        "title": "Authentication",   "sections": ["API keys", "OAuth 2.0", "JWT"] },
    { "path": "guides/deployment.md",  "title": "Deployment",       "sections": ["Docker", "GitHub Actions", "Environment variables"] },
    { "path": "contributing/index.md", "title": "Contributing",     "sections": ["Setup", "Tests", "PR checklist"] }
  ]
}
```

---

**Full onboard with scaffold (`scaffold_docs=true`)**

```json
{
  "tool": "onboard",
  "arguments": {
    "mode": "full",
    "project_root": "./my-fastapi-project",
    "project_name": "FastAPI Toolkit",
    "scaffold_docs": true,
    "production_url": "https://fastapi-toolkit.dev"
  }
}
```

Console output:

```text
✓ Phase 1 — Constitution
  Framework:   zensical
  Config:      zensical.toml
  Docs root:   docs/

✓ Phase 2 — Codebase analysis
  Modules:     src/fastapi_toolkit/ (12 files)
  CLI:         Yes (typer app at src/fastapi_toolkit/cli.py)
  Public API:  42 exported symbols

✓ Phase 3 — Page plan
  6 pages planned

✓ Phase 4 — Scaffold
  docs/index.md              ✓ created
  docs/quickstart.md         ✓ created
  docs/reference/api.md      ✓ created
  docs/guides/auth.md        ✓ created
  docs/guides/deployment.md  ✓ created
  docs/contributing/index.md ✓ created

✓ Phase 5 — Theme
  docs/stylesheets/extra.css  ✓ created
  docs/javascripts/extra.js   ✓ created
```

Returns a post-onboarding checklist:

```markdown
## Post-onboarding checklist

- [ ] Review and customise each page in `docs/`
- [ ] Set `site_url = "https://fastapi-toolkit.dev"` in `zensical.toml`
- [ ] Add the GitHub Actions workflow: `.github/workflows/docs.yml`
- [ ] Run `validate` to confirm quality score >= 0.80
- [ ] Run `generate` in `reference` mode to build the API reference
```

---

**Initialise directory structure only (`mode="init"`)**

```json
{
  "tool": "onboard",
  "arguments": {
    "mode": "init",
    "framework": "docusaurus",
    "project_root": "./new-project"
  }
}
```

Creates the Docusaurus directory structure without scaffolding any content pages.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **theme**

    Customise the visual identity that onboard generated.

    [:octicons-arrow-right-24: Read theme](theme.md)

-   :octicons-arrow-right-24: **validate**

    Run quality checks after onboard finishes to confirm everything is correct.

    [:octicons-arrow-right-24: Read validate](validate.md)

</div>

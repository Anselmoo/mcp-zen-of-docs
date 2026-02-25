---
agent: agent
description: 'Execute scaffold and enrich operations for each docs page'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Docs Implement Phase

Execute the scaffold and enrich operations to create and populate documentation
pages. This is the **fifth and final phase** of the docs pipeline.

## What This Phase Does

1. Scaffolds each documentation page from the task list.
2. Enriches scaffold stubs by replacing TODO placeholders with content.
3. Validates the final docs site for link integrity, orphan pages, and quality.

## Prerequisites

- **Constitution phase** must be complete.
- **Specify phase** must be complete (framework and primitives resolved).
- **Plan phase** must be complete (page plan finalized).
- **Tasks phase** must be complete (ordered task list available).

## Expected Inputs

- Task list from the tasks phase (doc paths, titles, nav preferences).
- Content to inject during enrichment (section text, code examples).
- Framework name for framework-native syntax.

## Expected Outputs

- Scaffold files created at each `doc_path`.
- Enriched pages with TODO placeholders replaced.
- Navigation entries appended to the framework config (e.g., `mkdocs.yml`).
- Validation report confirming links, structure, and quality score.

## Instructions

Run the following MCP tools in task-list order:

1. **`batch_scaffold_docs`** or **`scaffold_doc`** (per page) — Create the
   scaffold stubs for all planned pages.
2. **`enrich_doc`** (per page) — Replace TODO placeholders with real content.
   Provide the `content` and optionally `sections_to_enrich` for targeted
   enrichment.
3. **`validate_docs`** with `checks: ["links", "orphans", "structure"]` —
   Run the full validation suite on the completed docs.
4. **`score_docs_quality`** — Score the final documentation quality and
   compare against the baseline from the tasks phase.

## Example Invocation

```
batch_scaffold_docs({
  "pages": [
    { "doc_path": "docs/getting-started.md", "title": "Getting Started" },
    { "doc_path": "docs/api-reference.md", "title": "API Reference" }
  ],
  "docs_root": "docs"
})

enrich_doc({
  "doc_path": "docs/getting-started.md",
  "content": "## Installation\n\npip install my-package\n\n## Quick Start\n\n..."
})

validate_docs({
  "docs_root": "docs",
  "checks": ["links", "orphans", "structure"]
})

score_docs_quality({ "docs_root": "docs" })
```

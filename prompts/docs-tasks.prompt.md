---
agent: agent
description: 'Generate actionable task list from the docs page plan'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Docs Tasks Phase

Generate an actionable task list from the page plan. Each task maps to a
concrete scaffold-and-enrich operation. This is the **fourth phase** of the
docs pipeline.

## What This Phase Does

1. Converts the page plan into scaffold tasks — one per documentation page.
2. Assigns enrichment priorities based on page dependencies.
3. Produces a task checklist suitable for sequential or parallel execution.

## Prerequisites

- **Constitution phase** must be complete.
- **Specify phase** must be complete (authoring profile known).
- **Plan phase** must be complete (page plan with paths and dependencies).

## Expected Inputs

- Page plan output from the plan phase (list of page paths and titles).
- Detected framework name.
- Docs root directory.

## Expected Outputs

- Ordered task list where each task specifies:
  - The doc path to scaffold.
  - The page title.
  - Whether the page needs enrichment.
  - Dependencies on other pages.
- Score baseline from current docs quality.

## Instructions

Run the following MCP tools:

1. **`score_docs_quality`** — Establish the current quality baseline before
   scaffolding new pages.
2. For each page in the plan, prepare a task entry using **`scaffold_doc`**
   parameters (do not execute yet — collect the task list first).
3. **`compose_docs_story`** — Optionally compose a story summarizing the task
   breakdown and execution order.

Output the full task list as a numbered checklist. Each entry should include
the `doc_path`, `title`, and any `add_to_nav` preferences. This list drives
the **implement** phase.

## Example Invocation

```
score_docs_quality({ "docs_root": "docs" })

# For each planned page, record a task:
# Task 1: scaffold_doc({ "doc_path": "docs/getting-started.md", "title": "Getting Started" })
# Task 2: scaffold_doc({ "doc_path": "docs/api-reference.md", "title": "API Reference" })
# Task 3: scaffold_doc({ "doc_path": "docs/tutorials/first-steps.md", "title": "First Steps" })
```

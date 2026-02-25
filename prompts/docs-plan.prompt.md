---
agent: agent
description: 'Create ordered page plan with dependencies for docs site'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Docs Plan Phase

Create a structured, ordered page plan with dependency tracking for the
documentation site. This is the **third phase** of the docs pipeline.

## What This Phase Does

1. Generates a structured page plan based on the detected framework and project
   context.
2. Maps page dependencies so content is authored in the correct order.
3. Validates the planned structure against docs quality rules.

## Prerequisites

- **Constitution phase** must be complete (skeleton initialized).
- **Specify phase** must be complete (authoring profile resolved, story
  composed).

## Expected Inputs

- Project root directory.
- Detected framework name.
- Docs root directory (defaults to `docs`).
- Scope — `"full"` for complete site plan or a narrower scope.

## Expected Outputs

- Ordered list of documentation pages with paths and dependencies.
- Page plan metadata including navigation structure.
- Validation results confirming structural integrity.

## Instructions

Run the following MCP tools in order:

1. **`plan_docs`** — Generate the structured page plan with dependency ordering.
2. **`validate_docs`** with `checks: ["structure"]` — Validate the planned
   structure is consistent and complete.

Review the page plan output. Confirm page ordering respects dependencies and
that the navigation hierarchy is scannable before proceeding to the **tasks**
phase.

## Example Invocation

```
plan_docs({
  "project_root": ".",
  "docs_root": "docs",
  "scope": "full"
})
validate_docs({
  "docs_root": "docs",
  "checks": ["structure"]
})
```

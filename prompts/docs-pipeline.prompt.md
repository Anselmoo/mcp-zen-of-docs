---
agent: agent
description: 'Run the full docs pipeline: constitution → specify → plan → tasks → implement'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Full Docs Pipeline

Run the complete documentation pipeline end-to-end. This master command
orchestrates all five phases in sequence:

1. **Constitution** — Detect framework, assess readiness, generate skeleton.
2. **Specify** — Profile authoring primitives, compose specification story.
3. **Plan** — Generate structured page plan with dependencies.
4. **Tasks** — Convert plan into actionable scaffold/enrich task list.
5. **Implement** — Execute scaffolding, enrichment, and validation.

## Prerequisites

- None — this command runs the full pipeline from scratch.

## Expected Inputs

- Project root directory (defaults to `.`).
- Project name.
- Target audience (e.g., `"developers"`).
- Docs root directory (defaults to `docs`).

## Instructions

Execute each phase in order. Do **not** skip phases — each phase depends on
outputs from the previous one.

### Phase 1: Constitution

```
detect_docs_context({ "project_root": "." })
detect_project_readiness({ "project_root": "." })
onboard_project({ "project_root": ".", "mode": "skeleton", "project_name": "MyProject" })
```

Confirm the detected framework before continuing.

### Phase 2: Specify

```
get_authoring_profile()
resolve_primitive({ "framework": "<detected>", "primitive": "admonition" })
compose_docs_story({
  "prompt": "Specify documentation scope and structure",
  "audience": "developers"
})
```

Review the authoring profile and primitive support matrix.

### Phase 3: Plan

```
plan_docs({ "project_root": ".", "docs_root": "docs", "scope": "full" })
validate_docs({ "docs_root": "docs", "checks": ["structure"] })
```

Confirm the page plan and dependency ordering.

### Phase 4: Tasks

```
score_docs_quality({ "docs_root": "docs" })
```

Build the task list from the page plan. Each task is a `scaffold_doc` +
`enrich_doc` pair.

### Phase 5: Implement

```
batch_scaffold_docs({ "pages": [...], "docs_root": "docs" })
enrich_doc({ "doc_path": "docs/<page>.md", "content": "..." })
validate_docs({ "docs_root": "docs", "checks": ["links", "orphans", "structure"] })
score_docs_quality({ "docs_root": "docs" })
```

After implementation, compare the final quality score against the baseline
from Phase 4 to measure improvement.

## Phase Dependency Chain

```
constitution → specify → plan → tasks → implement
```

Each phase produces artifacts consumed by the next. If any phase fails,
resolve the issue before advancing.

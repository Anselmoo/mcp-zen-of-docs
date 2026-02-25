---
agent: agent
description: 'Create docs specification with authoring profile and primitives'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Docs Specify Phase

Create the documentation specification by profiling the target framework's
authoring capabilities and resolving primitive support. This is the **second
phase** of the docs pipeline.

## What This Phase Does

1. Retrieves the full authoring profile for the detected framework.
2. Resolves support levels for each of the 16 authoring primitives.
3. Composes a docs story that captures the specification narrative — audience,
   modules, and content scope.

## Prerequisites

- **Constitution phase** must be complete (framework detected, skeleton
  initialized).

## Expected Inputs

- Detected framework name from the constitution phase.
- Target audience description (e.g., `"developers"`, `"end users"`).
- Optional modules list to scope the specification.

## Expected Outputs

- Authoring profile with the full primitive support matrix.
- Resolved primitives showing native syntax per framework.
- A composed docs story capturing the specification intent.

## Instructions

Run the following MCP tools in order:

1. **`get_authoring_profile`** — Retrieve the framework's authoring capability
   profile with all 16 primitives.
2. **`resolve_primitive`** for key primitives — Verify native syntax for
   admonitions, code blocks, content tabs, and other critical primitives.
3. **`compose_docs_story`** — Compose a specification story describing the
   documentation scope, audience, and module structure.

Review the authoring profile to confirm which primitives are `native`,
`plugin`, `custom`, or `unsupported` before proceeding to the **plan** phase.

## Example Invocation

```
get_authoring_profile()
resolve_primitive({ "framework": "zensical", "primitive": "admonition" })
resolve_primitive({ "framework": "zensical", "primitive": "code-fence" })
compose_docs_story({
  "prompt": "Specify documentation for a Python library with API reference and tutorials",
  "audience": "developers",
  "modules": ["api-reference", "tutorials", "getting-started"]
})
```

---
agent: agent
description: 'Establish docs quality standards and project constitution'
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
---

# Docs Constitution Phase

Establish the documentation quality standards and project constitution for this
repository. This is the **first phase** of the docs pipeline and must run before
all other phases.

## What This Phase Does

1. Detects the documentation framework and project context.
2. Assesses project readiness for docs workflows.
3. Runs onboarding to generate the skeleton constitution artifacts
   (instructions, agents, prompts scaffolds, and initial config).

## Prerequisites

- None — this is the entry point of the pipeline.

## Expected Inputs

- The project root directory (defaults to `.`).
- Optionally a preferred framework name (`zensical`, `docusaurus`, `vitepress`,
  or `starlight`).

## Expected Outputs

- `.mcp-zen-of-docs/` state directory with initialization artifacts.
- `.github/instructions/` with coding and docs instruction files.
- `prompts/` directory scaffold.
- Detected framework context and readiness assessment.

## Instructions

Run the following MCP tools in order:

1. **`detect_docs_context`** — Detect the docs framework and runtime context.
2. **`detect_project_readiness`** — Assess readiness gates for docs workflows.
3. **`onboard_project`** with `mode: "skeleton"` — Generate the constitution
   skeleton (instructions, agents, directory scaffolds).

Review the outputs and confirm the detected framework is correct before
proceeding to the **specify** phase.

## Example Invocation

```
detect_docs_context({ "project_root": "." })
detect_project_readiness({ "project_root": "." })
onboard_project({ "project_root": ".", "mode": "skeleton", "project_name": "MyProject" })
```

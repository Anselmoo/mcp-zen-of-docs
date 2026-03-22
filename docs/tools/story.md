---
title: story
description: Compose structured documentation narratives from prose prompts using deterministic orchestration semantics.
tags:
  - tools
  - story
---

# story

> Turn prose intent into a documentation narrative, with a human warning/success flow for terminals and a raw JSON contract for automation.

`story` has two intentional surfaces:

- **Human mode** (`--human`, or a real TTY) returns either a focused **warning** that asks for missing context or a **success** view that prints the final narrative.
- **`--json` mode** preserves the raw orchestration payload, including `question_items`, `answer_slots`, `turn_plan`, and `pipeline_context`.

That split is the whole point of the redesign: people read summaries, tools parse contracts.

---

## When to use it

Use `story` when you know what concept to explain but are not sure how to structure it. Use [scaffold](scaffold.md) instead when you already know the exact path, title, and sections. Use migration mode when you want the story pipeline to rewrite docs toward a target framework.

---

## Human mode behavior

In human mode, `story` expects enough context to answer four questions:

1. Who is this for?
2. What should the reader achieve?
3. What is in or out of scope?
4. What constraints must the story respect?

If those are missing, the command returns a **warning** with:

- a `Required info` section listing the missing questions
- a `How to continue` section showing the exact flags to add next

Once the context is sufficient, the command returns **success** and prints the final narrative instead of the orchestration internals.

!!! note "Raw JSON still exists"
    Nothing about the MCP or automation contract was removed. Use `--json` when you need the full response structure for scripts, tests, or editor integrations.

---

## Public CLI flags

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--prompt` | string | **Yes** | The story request to compose |
| `--audience` | string | No | Target reader |
| `--module` | string | No | Repeat to request specific modules |
| `--context key=value` | string | No | Add flat story context without constructing JSON |
| `--context-json` | object | No | Pass structured story context as JSON |
| `--interactive` | bool | No | Prompt for missing required context in human mode |
| `--include-onboarding-guidance` | bool | No | Append onboarding guidance when available |
| `--migration-mode` | string | No | Migration strategy: `same-target` or `cross-target` |
| `--migration-source-framework` | string | No | Source framework for migration flows |
| `--migration-target-framework` | string | No | Target framework for migration flows |
| `--migration-improve-clarity` | bool | No | Improve clarity during migration. Default: `true` |
| `--migration-strengthen-structure` | bool | No | Strengthen structure during migration. Default: `true` |
| `--migration-enrich-examples` | bool | No | Add richer examples during migration. Default: `false` |
| `--output-dir` | path | No | Write the final story to a Markdown file |

---

## Examples

### Human success path

```bash
mcp-zen-of-docs --human story \
  --prompt "Ship deterministic docs stories" \
  --audience "platform engineers" \
  --context goal="typed contracts" \
  --context scope="story generation" \
  --context constraints="deterministic output"
```

Representative output:

```text
Success: Compose docs story
Title: Ship deterministic docs stories

Narrative
  Target audience: platform engineers.
  ...
```

### Human warning path

```bash
mcp-zen-of-docs --human story \
  --prompt "A simple story"
```

Representative output:

```text
Warning: Compose docs story
Additional context is required to complete the story.

Required info
  - Who is the target audience for this story?
  - What is the primary goal this story should help the reader achieve?
  ...

How to continue
  - Re-run with the missing values as flags, or use a TTY terminal to answer prompts interactively.
  - Add --audience "<target audience>".
  - Add --context-json '{"goal":"...", "scope":"...", "constraints":"..."}'.
```

### Raw JSON for automation

```bash
mcp-zen-of-docs --json story \
  --prompt "A simple story"
```

Use this mode when you need the underlying fields directly, such as:

- `story.question_items`
- `story.answer_slots`
- `story.turn_plan`
- `pipeline_context`

### Migration flow

```bash
mcp-zen-of-docs --json story \
  --prompt "Migrate the contributor guide to Docusaurus" \
  --migration-mode cross-target \
  --migration-source-framework zensical \
  --migration-target-framework docusaurus \
  --migration-enrich-examples
```

Use migration mode when the narrative needs to reflect framework differences, not just explain a concept.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **scaffold**

    Need a page at a specific path with explicit sections? Use scaffold instead.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    Understand the orchestration pattern that story uses under the hood.

    [:octicons-arrow-right-24: Read the guide](../guides/detect-profile-act.md)

</div>

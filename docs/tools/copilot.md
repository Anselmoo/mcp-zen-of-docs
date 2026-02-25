---
title: copilot
description: Create VS Code Copilot instruction, prompt, and agent files that encode your documentation conventions project-wide.
tags:
  - tools
  - copilot
---

# copilot

> Creates VS Code Copilot instruction, prompt, and agent files that encode your docs conventions project-wide.

`copilot` generates `.instructions.md`, `.prompt.md`, and `.agent.md` artefacts so every AI suggestion stays consistent with your project's authoring standards. Instruction files apply automatically to matching file patterns; prompt files become reusable slash commands; agent files define autonomous workflows with tool lists.

---

## Modes

| Mode | What it produces |
|------|----------------|
| `artifact` | A single `.instructions.md`, `.prompt.md`, or `.agent.md` file (default) |
| `config` | An agent configuration block (JSON or YAML) |

---

## When to use it

Run `copilot` once after [onboard](onboard.md) to lock in your authoring style project-wide. Update instruction files whenever your conventions change — Copilot picks up the new rules automatically on the next request.

---

## Artifact kinds

| Kind | Output path | When VS Code applies it |
|------|-------------|------------------------|
| `instruction` | `.github/instructions/<stem>.instructions.md` | Automatically, to files matching `apply_to` glob |
| `prompt` | `.github/prompts/<stem>.prompt.md` | When the user invokes the slash command |
| `agent` | `.github/agents/<stem>.agent.md` | When the user references the agent by name |

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Operation mode. Default: `"artifact"` |
| `kind` | string | No | Artefact kind: `"instruction"`, `"prompt"`, `"agent"`. Default: `"instruction"` |
| `title` | string | No | Artefact title shown in VS Code UI |
| `description` | string | No | Short description of what the artefact does |
| `content` | string | No | Body content — rules, workflow steps, or tool list |
| `apply_to` | glob | No | File pattern for instruction scope. Default: `"**"` |
| `file_stem` | string | No | Output filename without extension |
| `overwrite` | bool | No | Replace an existing file. Default: `false` |
| `include_tools` | bool | No | Include MCP tool list in agent artefacts. Default: `true` |
| `tools` | string[] | No | Specific tools to list in agent artefacts |
| `platform` | string | No | Target platform. Default: `"copilot"` |
| `project_root` | path | No | Project root for saving artefacts. Default: `"."` |

---

## Examples

**Create an instruction file for Zensical authoring conventions**

```json
{
  "tool": "copilot",
  "arguments": {
    "mode": "artifact",
    "kind": "instruction",
    "apply_to": "docs/**/*.md",
    "file_stem": "zensical-docs"
  }
}
```

Writes `.github/instructions/zensical-docs.instructions.md`:

```markdown
---
applyTo: "docs/**/*.md"
---

# Zensical Documentation Standards

When authoring documentation pages for this project:

## Frontmatter
- Every page MUST include `title`, `description`, and `tags` frontmatter keys.
- Tags must include `"tools"` plus the tool name for pages in `docs/tools/`.

## Admonitions
- Use `!!! note` for supplementary information.
- Use `!!! warning` for actions that modify files or have side effects.
- Never use raw `**Bold:**` labels as a substitute for admonitions.

## Code blocks
- Always specify a language: ```json, ```text, ```bash.
- Use ```text for CLI prompts. Use ```json for structured return values.

## Content tabs
- Use `=== "Tab name"` syntax (Zensical-native). Do NOT use HTML `<Tabs>` components.
```

---

**Create a reusable prompt for scaffolding tool pages**

```json
{
  "tool": "copilot",
  "arguments": {
    "mode": "artifact",
    "kind": "prompt",
    "file_stem": "scaffold-tool-page"
  }
}
```

Writes `.github/prompts/scaffold-tool-page.prompt.md`. Type `/scaffold-tool-page` in Copilot Chat to invoke it with a `${toolName}` variable.

---

**Create an agent file with MCP tools listed**

```json
{
  "tool": "copilot",
  "arguments": {
    "mode": "artifact",
    "kind": "agent",
    "file_stem": "docs-writer",
    "include_tools": true
  }
}
```

Writes `.github/agents/docs-writer.agent.md`:

```markdown
---
name: "Docs Writer"
description: "Writes, validates, and improves documentation pages using mcp-zen-of-docs tools."
tools:
  - mcp: detect_docs_context
  - mcp: resolve_primitive
  - mcp: write_doc
  - mcp: validate_docs
---

# Docs Writer Agent

## Workflow
1. Call `detect_docs_context` to identify the framework.
2. Call `resolve_primitive` to confirm syntax before writing.
3. Use `write_doc` to produce complete pages — no TODO placeholders.
4. Call `validate_docs` with `checks: ["links", "structure"]` after every write.
```

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **docstring**

    Audit the source code your Copilot instructions describe.

    [:octicons-arrow-right-24: Read docstring](docstring.md)

-   :octicons-arrow-right-24: **theme**

    Generate the CSS and extension config your instruction file references.

    [:octicons-arrow-right-24: Read theme](theme.md)

</div>

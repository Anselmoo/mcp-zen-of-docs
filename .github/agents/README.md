# Agent Definitions

This directory contains VS Code Copilot agent definitions for the `mcp-zen-of-docs` project.

Each `*.agent.md` file defines a persistent agent with YAML frontmatter (`name`, `description`, `tools`)
and a Markdown system prompt body.

## Agents

| Agent | Description |
|-------|-------------|
| `docs-init` | Init lifecycle behavior and documentation setup |
| `zen-docs-reviewer` | Code review for project standards and Pydantic compliance |
| `zen-docs-architect` | Documentation framework architecture and primitives |
| `zen-docs-writer` | Expert documentation content writer — `write_doc`, `enrich_doc`, `compose_docs_story` |
| `zen-docs-creator` | SVG and visual asset creator — `create_svg_asset`, `generate_visual_asset`, `render_diagram` |
| `pydantic-engineer` | Pydantic v2, FastMCP v2, and Python 3.12+ engineering |

## Canonical Tool Set

All `zen-docs-*` agents share the following canonical tool list:

```yaml
tools: [vscode, execute/testFailure, execute/getTerminalOutput, execute/awaitTerminal, execute/killTerminal, execute/createAndRunTask, execute/runInTerminal, execute/runTests, read, agent, edit, search, web, browser, 'zen-of-docs/*', ai-agent-guidelines/gap-frameworks-analyzers, ai-agent-guidelines/l9-distinguished-engineer-prompt-builder, 'context7/*', 'serena/*', 'zen-of-languages/*', todo]
```

This list is the single source of truth. The `COPILOT_DEFAULT_TOOLS` constant in
`src/mcp_zen_of_docs/models.py` mirrors this list and is used by generated artifacts.

## Convention

- One file per agent capability.
- All zen-docs agents include `create`, `delete`, and `terminal` permissions for full file management.
- Keep agent files deterministic and source-controlled.

---
agent: agent
tools: [read, agent, edit, search, web, 'zen-of-docs/*', todo]
description: 'Prompt template with deterministic initialization checklist guidance.'
---

# Prompt template with deterministic initialization checklist guidance.

## Prompt Modes

Choose the right mode for the task:

- **`ask`** — Use for read-only questions: explain code, summarize docs,
  check conventions. No files are modified.
- **`edit`** — Use for inline edits: fix a heading, update frontmatter,
  reformat a table. Works on the current file.
- **`agent`** — Use for multi-step workflows: scaffold docs, run validation,
  generate boilerplate across multiple files.

## Available Tools (agent mode)

| Tool          | Purpose                                    |
| ------------- | ------------------------------------------ |
| `codebase`    | Search and read files across the repository |
| `editFiles`   | Create or modify files                      |
| `terminal`    | Run shell commands (build, test, lint)      |
| `fetch`       | Retrieve external URLs                      |
| `githubRepo`  | Query GitHub repository metadata            |

## Checklist

1. Confirm `.mcp-zen-of-docs/init/state.json` exists.
2. Confirm required instruction files are present in `.github/instructions/`.
3. Verify agent definitions exist in `.github/agents/`.
4. Run focused tests for generators, infrastructure adapters, and domain specs.
5. Validate docs structure with `validate_docs` before committing.

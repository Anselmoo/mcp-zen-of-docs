---
applyTo: "**"
---

# Project Instructions

Baseline repository instructions consumed by Copilot.

## How Instructions Work

Instruction files (`.instructions.md`) are automatically applied by
Copilot when you work on files matching the `applyTo` glob pattern in
frontmatter. They shape Copilot's suggestions without explicit invocation.

### `applyTo` Pattern Examples

| Pattern                  | Scope                            |
| ------------------------ | -------------------------------- |
| `"**"`                   | All files in the repository      |
| `"src/**/*.py"`          | Python files under `src/`        |
| `"docs/**/*.md"`         | Markdown docs files              |
| `"tests/**"`             | All test files                   |

### Instructions vs Prompts

- **Instructions** are passive — applied automatically to matching files.
- **Prompts** are active — invoked explicitly via slash commands.
- Use instructions for coding conventions, style rules, and project context.
- Use prompts for repeatable workflows like scaffolding or reviews.

## Documentation Standards

- Every documentation page should have a clear purpose and audience.
- Use framework-native authoring primitives for admonitions, code blocks, and tabs.
- Keep navigation structure flat and scannable.
- Validate links and structure before committing.

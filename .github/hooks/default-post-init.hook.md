---
hook_target: 'post-init-enrich'
---

# Copilot Extension Hook

- **Hook target:** `post-init-enrich`
- **Required baseline artifact:** `true`
- **Design summary:** Default extension hook contract to enrich generated init artifacts.

## What Are Extension Hooks?

Extension hooks are scripts that run during `mcp-zen-of-docs` init
workflows. They allow projects to customize the initialization process
without modifying core templates.

### Hook Lifecycle

| Phase       | When It Runs                                    |
| ----------- | ----------------------------------------------- |
| `pre-init`  | Before scaffold generation — validate inputs     |
| `post-init` | After scaffold generation — apply customizations |

### Pre-Init Hooks

Run before any files are generated. Use these to:
- Validate required configuration exists.
- Check environment prerequisites.
- Abort early if preconditions are not met.

### Post-Init Hooks

Run after scaffold files are written. Use these to:
- Apply project-specific customizations to generated files.
- Register generated files with other tools (linters, CI).
- Run validation or formatting on generated output.

## Contract

- Document preconditions and expected inputs.
- Keep implementation additive and backward-compatible.
- Hook scripts must be idempotent — safe to run multiple times.

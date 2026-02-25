"""Static Copilot artifact content templates with proper YAML frontmatter."""

from __future__ import annotations

import os

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactContract
from mcp_zen_of_docs.domain.copilot_artifact_spec import CopilotArtifactFamily


class CopilotAssetTemplateId(StrEnum):
    """Stable identifiers for Copilot asset body templates."""

    AGENTS_DIRECTORY_README = "agents-directory-readme"
    PROMPTS_DIRECTORY_README = "prompts-directory-readme"
    INSTRUCTIONS_PROJECT = "instructions-project"
    INSTRUCTIONS_DOCS = "instructions-docs"
    INSTRUCTIONS_SRC_PYTHON = "instructions-src-python"
    INSTRUCTIONS_TESTS = "instructions-tests"
    INSTRUCTIONS_YAML = "instructions-yaml"
    INSTRUCTIONS_CONFIG = "instructions-config"
    INSTRUCTIONS_ENV = "instructions-env"
    FAMILY_INSTRUCTIONS = "family-instructions"
    FAMILY_PROMPTS = "family-prompts"
    FAMILY_AGENTS = "family-agents"
    FAMILY_EXTENSION_HOOKS = "family-extension-hooks"
    # Specific agent templates (matched by artifact_id)
    AGENT_DOCS_INIT = "agent-docs-init"
    AGENT_DOCS_ORCHESTRATOR = "agent-docs-orchestrator"
    AGENT_PYDANTIC_ENGINEER = "agent-pydantic-engineer"
    AGENT_MULTI_FRAMEWORK = "agent-multi-framework"
    DEFAULT = "default"


class CopilotAssetTemplate(BaseModel):
    """Template descriptor keyed by artifact id or artifact family."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False, frozen=True)

    template_id: CopilotAssetTemplateId = Field(description="Stable template identifier.")
    artifact_id: str | None = Field(
        default=None,
        description="Exact artifact_id match key when present.",
    )
    family: CopilotArtifactFamily | None = Field(
        default=None,
        description="Family fallback match key when artifact_id is not provided.",
    )
    body_template: str = Field(
        description="Format string used to produce deterministic body content."
    )


COPILOT_ASSET_TEMPLATE_REGISTRY: tuple[CopilotAssetTemplate, ...] = (
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.AGENTS_DIRECTORY_README,
        artifact_id="agents.directory-readme",
        body_template=(
            "# Agent Definitions\n\n"
            "This directory contains **`.agent.md`** files — repository-local agent\n"
            "definitions for GitHub Copilot Chat.\n\n"
            "## What Are Agent Files?\n\n"
            "Each `.agent.md` file defines a custom Copilot agent that team members\n"
            "can invoke with `@agent-name` in VS Code Copilot Chat. Agents carry\n"
            "persistent system prompts, tool access, and domain-specific instructions.\n\n"
            "See the [VS Code custom agents docs]"
            "(https://code.visualstudio.com/docs/copilot/copilot-customization) "
            "for details.\n\n"
            "## Agents\n\n"
            "| Agent | Role | Delegates to |\n"
            "|-------|------|--------------|\n"
            "| `docs-orchestrator` | Top-level pipeline coordinator | all agents |\n"
            "| `docs-init` | Init lifecycle, onboarding, scaffold, validate | `zen-docs-architect` |\n"  # noqa: E501
            "| `zen-docs-architect` | Framework architecture, primitive planning | `pydantic-engineer` |\n"  # noqa: E501
            "| `zen-docs-reviewer` | Standards compliance, Pydantic/code review | — |\n"
            "| `pydantic-engineer` | FastMCP v2, Pydantic v2, model migration | `zen-docs-reviewer` |\n"  # noqa: E501
            "| `multi-framework` | Docusaurus / VitePress / Starlight guidance | `zen-docs-architect` |\n\n"  # noqa: E501
            "## Invocation\n\n"
            "Reference an agent by name in your Copilot chat:\n\n"
            "```text\n"
            "@docs-orchestrator Run the full docs pipeline. Framework: zensical. Target: 95+.\n"
            "@docs-init Detect framework and onboard the project.\n"
            "@pydantic-engineer Migrate validate_docs_tool return type to a Pydantic model.\n"
            "@multi-framework Show native primitive support matrix for Starlight.\n"
            "```\n\n"
            "## Conventions\n\n"
            "- **One file per agent** — keep ownership and scope clear.\n"
            '- All agents use `agents: ["*"]` and the full tool set:\n'
            "  `zen-of-docs/*`, `context7/*`, `serena/*`, `zen-of-languages/*`, `todo`.\n"
            "- Keep agent files deterministic and source-controlled.\n\n"
            "## Example Frontmatter\n\n"
            "```yaml\n"
            "---\n"
            'agents: ["*"]\n'
            "name: 'docs-reviewer'\n"
            "description: 'Reviews documentation for clarity and completeness'\n"
            "tools: ['read', 'agent', 'edit', 'zen-of-docs/*', 'context7/*', 'serena/*']\n"
            "---\n"
            "```\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.PROMPTS_DIRECTORY_README,
        artifact_id="prompts.directory-readme",
        body_template=(
            "# Prompt Templates\n\n"
            "This directory contains **`.prompt.md`** files — reusable prompt\n"
            "templates for GitHub Copilot Chat.\n\n"
            "## What Are Prompt Files?\n\n"
            "Each `.prompt.md` file defines a reusable prompt that appears in\n"
            "the Copilot Chat slash-command menu. Prompts support three modes:\n\n"
            "| Mode    | Behaviour                                          |\n"
            "| ------- | -------------------------------------------------- |\n"
            "| `ask`   | Read-only — answers questions without editing files |\n"
            "| `edit`  | Applies inline edits to the current file            |\n"
            "| `agent` | Full agentic mode with tool access                  |\n\n"
            "## Required Frontmatter\n\n"
            "```yaml\n"
            "---\n"
            "agent: 'agent'            # ask | edit | agent\n"
            "tools: ['read', 'agent', 'edit', 'search', 'web', 'zen-of-docs/*', 'context7/*', 'serena/*', 'todo']\n"  # noqa: E501
            "description: 'Short description shown in command palette'\n"
            "---\n"
            "```\n\n"
            "## Conventions\n\n"
            "- Keep prompt files deterministic and reviewable.\n"
            "- Prefer additive prompt evolution over destructive rewrites.\n"
            "- Use descriptive filenames: `init-docs.prompt.md`, `review-nav.prompt.md`.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_PROJECT,
        artifact_id="instructions.core",
        body_template=(
            "# Project Instructions\n\n"
            "{summary}\n\n"
            "## Scope\n\n"
            "- Applies repository-wide for baseline coding and documentation behavior.\n"
            "- Keep changes deterministic, typed, and test-backed.\n\n"
            "## Core Rules\n\n"
            "- Prefer additive changes over destructive rewrites.\n"
            "- Keep Pydantic models and typed contracts aligned.\n"
            "- Run lint and tests after non-trivial edits.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_DOCS,
        artifact_id="instructions.docs",
        body_template=(
            "# Docs Instructions\n\n"
            "{summary}\n\n"
            "## Scope\n\n"
            "- Targets markdown documentation pages under the docs root.\n"
            "- Default scope is `docs/**/*.md`.\n\n"
            "## Docs Quality Rules\n\n"
            "- Keep one topic per page and clear heading structure.\n"
            "- Use framework-native primitives for admonitions, tabs, and code blocks.\n"
            "- Prefer concise examples that are runnable and verifiable.\n"
            "- Validate internal links and navigation consistency.\n\n"
            "## Optional Override\n\n"
            "- Set `MCP_ZEN_OF_DOCS_DOCS_APPLY_TO_OVERRIDE` to customize docs scope.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_SRC_PYTHON,
        artifact_id="instructions.src-python",
        body_template=(
            "# Source Python Instructions\n\n"
            "{summary}\n\n"
            "## Source Rules\n\n"
            "- Use `from __future__ import annotations` and explicit `__all__`.\n"
            "- Keep strict typing and Pydantic-first contracts.\n"
            "- Avoid broad exception handling and avoid silent fallbacks.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_TESTS,
        artifact_id="instructions.tests",
        body_template=(
            "# Testing Instructions\n\n"
            "{summary}\n\n"
            "## Test Rules\n\n"
            "- Use pytest naming with clear scenario-focused assertions.\n"
            "- Cover behavior changes with deterministic tests.\n"
            "- Prefer fast, isolated tests before end-to-end additions.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_YAML,
        artifact_id="instructions.yaml",
        body_template=(
            "# YAML Instructions\n\n"
            "{summary}\n\n"
            "## YAML Rules\n\n"
            "- Preserve key ordering and indentation style already in file.\n"
            "- Keep workflow conditions explicit and non-ambiguous.\n"
            "- Prefer pinned action major versions and reproducible steps.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_CONFIG,
        artifact_id="instructions.config",
        body_template=(
            "# Configuration Instructions\n\n"
            "{summary}\n\n"
            "## Config Rules\n\n"
            "- Keep config changes minimal and schema-consistent.\n"
            "- Avoid magic defaults; document intentional non-standard values.\n"
            "- Preserve comments and structure in hand-maintained config files.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.INSTRUCTIONS_ENV,
        artifact_id="instructions.env",
        body_template=(
            "# Environment File Instructions\n\n"
            "{summary}\n\n"
            "## Env Rules\n\n"
            "- Never commit real secrets.\n"
            "- Document required variables and safe defaults.\n"
            "- Keep naming consistent across `.env*` files and deployment configs.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.FAMILY_INSTRUCTIONS,
        family=CopilotArtifactFamily.INSTRUCTIONS,
        body_template=(
            "# Project Instructions\n\n"
            "{summary}\n\n"
            "## How Instructions Work\n\n"
            "Instruction files (`.instructions.md`) are automatically applied by\n"
            "Copilot when you work on files matching the `applyTo` glob pattern in\n"
            "frontmatter. They shape Copilot's suggestions without explicit invocation.\n\n"
            "### `applyTo` Pattern Examples\n\n"
            "| Pattern                  | Scope                            |\n"
            "| ------------------------ | -------------------------------- |\n"
            '| `"**"`                   | All files in the repository      |\n'
            '| `"src/**/*.py"`          | Python files under `src/`        |\n'
            '| `"docs/**/*.md"`         | Markdown docs files              |\n'
            '| `"tests/**"`             | All test files                   |\n\n'
            "### Instructions vs Prompts\n\n"
            "- **Instructions** are passive — applied automatically to matching files.\n"
            "- **Prompts** are active — invoked explicitly via slash commands.\n"
            "- Use instructions for coding conventions, style rules, and project context.\n"
            "- Use prompts for repeatable workflows like scaffolding or reviews.\n\n"
            "## Documentation Standards\n\n"
            "- Every documentation page should have a clear purpose and audience.\n"
            "- Use framework-native authoring primitives for admonitions, code blocks, and tabs.\n"
            "- Keep navigation structure flat and scannable.\n"
            "- Validate links and structure before committing.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.FAMILY_PROMPTS,
        family=CopilotArtifactFamily.PROMPTS,
        body_template=(
            "# {summary}\n\n"
            "## Prompt Modes\n\n"
            "Choose the right mode for the task:\n\n"
            "- **`ask`** — Read-only questions: explain code, summarize docs,\n"
            "  check conventions. No files are modified.\n"
            "- **`edit`** — Inline edits: fix a heading, update frontmatter,\n"
            "  reformat a table. Works on the current file.\n"
            "- **`agent`** — Multi-step workflows: scaffold docs, run validation,\n"
            "  generate boilerplate across multiple files.\n\n"
            "## Available Tools\n\n"
            "| Tool | Purpose |\n"
            "| ---- | ------- |\n"
            "| `zen-of-docs/*` | Framework detection, primitive rendering, validation |\n"
            "| `context7/*` | Live library documentation lookup |\n"
            "| `serena/*` | Symbol-level code navigation and editing |\n"
            "| `zen-of-languages/*` | Code quality analysis |\n"
            "| `github/search_code` | Search GitHub code at scale |\n"
            "| `github/search_repositories` | Discover reference repos |\n"
            "| `ms-python.python/*` | Python environment management |\n"
            "| `todo` | Task tracking |\n\n"
            "## Checklist\n\n"
            "1. Confirm `.mcp-zen-of-docs/init/state.json` exists.\n"
            "2. Confirm required instruction files are present in `.github/instructions/`.\n"
            "3. Verify agent definitions exist in `.github/agents/`.\n"
            "4. Run focused tests for generators, infrastructure adapters, and domain specs.\n"
            "5. Validate docs structure with `validate_docs` before committing.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.FAMILY_AGENTS,
        family=CopilotArtifactFamily.AGENTS,
        body_template=(
            "# {summary}\n\n"
            "You are an AI documentation agent operating within the mcp-zen-of-docs\n"
            "multi-agent system.\n\n"
            "## Role & Responsibilities\n\n"
            "- Inspect existing init artifacts and docs structure.\n"
            "- Generate missing documentation scaffolds using deterministic templates.\n"
            "- Validate generated output against framework conventions.\n"
            "- Delegate specialised sub-tasks to the appropriate sub-agent\n"
            "  (`zen-docs-architect`, `zen-docs-reviewer`, `pydantic-engineer`).\n"
            "- Avoid non-deterministic content "
            "(timestamps, random IDs, environment-dependent text).\n\n"
            "## Orchestration Pattern\n\n"
            "```\n"
            "@docs-orchestrator  ──►  @docs-init  ──►  @zen-docs-architect\n"
            "                    ──►  @pydantic-engineer  ──►  @zen-docs-reviewer\n"
            "                    ──►  @multi-framework\n"
            "```\n\n"
            "## Tools\n\n"
            "This agent has access to: `zen-of-docs/*`, `context7/*`, `serena/*`,\n"
            "`zen-of-languages/*`, `todo`, `github/search_code`,\n"
            "`ms-python.python/*`.\n\n"
            "## Workflow\n\n"
            "1. **Detect** — identify framework via `detect_docs_context`.\n"
            "2. **Profile** — load the authoring profile for the detected framework.\n"
            "3. **Act** — generate, validate, score, and iterate until quality ≥95.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.FAMILY_EXTENSION_HOOKS,
        family=CopilotArtifactFamily.EXTENSION_HOOKS,
        body_template=(
            "# Copilot Extension Hook\n\n"
            "- **Hook target:** `{hook_target}`\n"
            "- **Required baseline artifact:** `{required}`\n"
            "- **Design summary:** {summary}\n\n"
            "## What Are Extension Hooks?\n\n"
            "Extension hooks are scripts that run during `mcp-zen-of-docs` init\n"
            "workflows. They allow projects to customize the initialization process\n"
            "without modifying core templates.\n\n"
            "### Hook Lifecycle\n\n"
            "| Phase       | When It Runs                                    |\n"
            "| ----------- | ----------------------------------------------- |\n"
            "| `pre-init`  | Before scaffold generation — validate inputs     |\n"
            "| `post-init` | After scaffold generation — apply customizations |\n\n"
            "### Pre-Init Hooks\n\n"
            "Run before any files are generated. Use these to:\n"
            "- Validate required configuration exists.\n"
            "- Check environment prerequisites.\n"
            "- Abort early if preconditions are not met.\n\n"
            "### Post-Init Hooks\n\n"
            "Run after scaffold files are written. Use these to:\n"
            "- Apply project-specific customizations to generated files.\n"
            "- Register generated files with other tools (linters, CI).\n"
            "- Run validation or formatting on generated output.\n\n"
            "## Contract\n\n"
            "- Document preconditions and expected inputs.\n"
            "- Keep implementation additive and backward-compatible.\n"
            "- Hook scripts must be idempotent — safe to run multiple times.\n"
        ),
    ),
    # ── Specific agent templates ─────────────────────────────────────────────
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.AGENT_DOCS_INIT,
        artifact_id="agents.docs-init",
        body_template=(
            "# docs-init — Init Lifecycle Agent\n\n"
            "You are the **init lifecycle agent** for `mcp-zen-of-docs`. Your job is\n"
            "to orchestrate the full documentation onboarding workflow.\n\n"
            "## Responsibilities\n\n"
            "- Detect the documentation framework via `detect_docs_context`.\n"
            "- Assess project readiness with `detect_project_readiness`.\n"
            "- Scaffold Copilot artifacts (agents, prompts, instructions) via `onboard_project`.\n"
            "- Validate docs structure and surface orphaned pages or broken links.\n"
            "- Delegate architecture questions to `@zen-docs-architect`.\n\n"
            "## Workflow\n\n"
            "1. **Detect** — `detect_docs_context` + `detect_project_readiness`.\n"
            "2. **Onboard** — `onboard_project(mode='full')` if readiness gate passes.\n"
            "3. **Validate** — `validate_docs(checks=['links','orphans','structure'])`.\n"
            "4. **Score** — `score_docs_quality`. Target ≥95/100.\n"
            "5. **Iterate** — if score < 95, delegate to `@zen-docs-architect` and repeat.\n\n"
            "## Gotchas\n\n"
            "- Never use `enrich_doc` on multi-section files — it appends under every heading.\n"
            "- Use `serena-create_text_file` or `edit` for targeted file updates.\n"
            "- The `compose_docs_story` tool only accepts these module names:\n"
            "  `structure`, `concepts`, `architecture`, `standards`, `connector`.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.AGENT_DOCS_ORCHESTRATOR,
        artifact_id="agents.docs-orchestrator",
        body_template=(
            "# docs-orchestrator — Top-Level Pipeline Coordinator\n\n"
            "You are the **orchestrator** for the mcp-zen-of-docs documentation pipeline.\n"
            "Coordinate the specialist sub-agents to run the full docs generation,\n"
            "validation, and scoring cycle.\n\n"
            "## Sub-Agents\n\n"
            "| Agent | Trigger condition |\n"
            "|-------|-------------------|\n"
            "| `@docs-init` | New project or missing init state |\n"
            "| `@zen-docs-architect` | Framework architecture / primitive planning |\n"
            "| `@pydantic-engineer` | Pydantic model migration, typed returns |\n"
            "| `@zen-docs-reviewer` | Quality gate, standards compliance |\n"
            "| `@multi-framework` | Cross-framework primitive comparison |\n\n"
            "## Pipeline\n\n"
            "```\n"
            "detect → onboard → scaffold → validate → score → iterate\n"
            "```\n\n"
            "1. Call `@docs-init` to detect and onboard.\n"
            "2. Call `@zen-docs-architect` to plan and scaffold missing pages.\n"
            "3. Call `@pydantic-engineer` if typed model migration is needed.\n"
            "4. Call `@zen-docs-reviewer` for final quality gate (target ≥95).\n"
            "5. Report final score. Open GitHub issues for remaining gaps.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.AGENT_PYDANTIC_ENGINEER,
        artifact_id="agents.pydantic-engineer",
        body_template=(
            "# pydantic-engineer — FastMCP v2 + Pydantic v2 Specialist\n\n"
            "You are a Pydantic v2 and FastMCP v2 expert. You migrate `dict[str, object]`\n"
            "returns to typed Pydantic models, add `Field(description=...)` annotations,\n"
            "and ensure every public tool follows the project's engineering standards.\n\n"
            "## Responsibilities\n\n"
            "- Identify tools returning raw `dict` — replace with Pydantic `BaseModel`.\n"
            "- Ensure every model field has `Field(description=...)`.\n"
            "- Use `StrEnum` for all categorical values.\n"
            "- Use `pathlib.Path` for filesystem parameters.\n"
            "- Apply `frozen=True` on result and config models.\n"
            "- Update tests to assert `isinstance(result, PydanticModel)`.\n\n"
            "## Tools\n\n"
            "- `serena/*` — symbol-level navigation and body replacement.\n"
            "- `context7/*` — live Pydantic / FastMCP documentation lookup.\n"
            "- `zen-of-languages/*` — code quality analysis for Python.\n"
            "- `ms-python.python/*` — Python environment and package management.\n\n"
            "## Non-Negotiable Patterns\n\n"
            "```python\n"
            "# Every tool input and output is a Pydantic BaseModel\n"
            "class MyRequest(BaseModel):\n"
            "    field: str = Field(description='...')\n\n"
            "class MyResponse(BaseModel, frozen=True):\n"
            "    result: str = Field(description='...')\n\n"
            "@app.tool\n"
            "async def my_tool(request: MyRequest) -> MyResponse: ...\n"
            "```\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.AGENT_MULTI_FRAMEWORK,
        artifact_id="agents.multi-framework",
        body_template=(
            "# multi-framework — Cross-Framework Documentation Advisor\n\n"
            "You are the cross-framework advisor for `mcp-zen-of-docs`. You help users\n"
            "understand authoring primitive support across Zensical, Docusaurus,\n"
            "VitePress, and Starlight, and guide migration between frameworks.\n\n"
            "## Supported Frameworks\n\n"
            "| Framework | Config file | Primitive highlight |\n"
            "|-----------|-------------|---------------------|\n"
            "| Zensical (MkDocs) | `mkdocs.yml` | Admonitions `!!! note` |\n"
            "| Docusaurus | `docusaurus.config.js/ts` | Admonitions `:::note` |\n"
            "| VitePress | `.vitepress/config.*` | Admonitions `::: info` |\n"
            "| Starlight | `astro.config.mjs/ts` | `<Aside>` component |\n\n"
            "## Responsibilities\n\n"
            "- Compare primitive support matrices across frameworks.\n"
            "- Translate authoring primitives between framework dialects.\n"
            "- Detect the current framework via `detect_docs_context`.\n"
            "- Render framework-native snippets via `resolve_primitive`.\n"
            "- Advise on migration path when switching frameworks.\n\n"
            "## Workflow\n\n"
            "1. Detect framework — `detect_docs_context`.\n"
            "2. Load authoring profile — `get_authoring_profile`.\n"
            "3. Resolve primitive — `resolve_primitive(framework, primitive, mode='render')`.\n"
            "4. If translation needed — `translate_primitives(source, target, primitive)`.\n"
        ),
    ),
    CopilotAssetTemplate(
        template_id=CopilotAssetTemplateId.DEFAULT,
        body_template=(
            "# Copilot Artifact\n\n"
            "{summary}\n\n"
            "## Usage\n\n"
            "This file was generated by `mcp-zen-of-docs` as part of the Copilot\n"
            "customization scaffold. Edit it to match your project's needs.\n\n"
            "For more information on Copilot customization, see the\n"
            "[VS Code docs](https://code.visualstudio.com/docs/copilot/copilot-customization).\n"
        ),
    ),
)

_TEMPLATES_BY_ARTIFACT_ID: dict[str, CopilotAssetTemplate] = {
    template.artifact_id: template
    for template in COPILOT_ASSET_TEMPLATE_REGISTRY
    if template.artifact_id is not None
}
_TEMPLATES_BY_FAMILY: dict[CopilotArtifactFamily, CopilotAssetTemplate] = {
    template.family: template
    for template in COPILOT_ASSET_TEMPLATE_REGISTRY
    if template.family is not None
}
_DEFAULT_TEMPLATE = next(
    template
    for template in COPILOT_ASSET_TEMPLATE_REGISTRY
    if template.template_id is CopilotAssetTemplateId.DEFAULT
)
_DOCS_APPLY_TO_OVERRIDE_ENV = "MCP_ZEN_OF_DOCS_DOCS_APPLY_TO_OVERRIDE"


def _resolve_template(asset: CopilotArtifactContract) -> CopilotAssetTemplate:
    """Resolve the best-matching template for a Copilot artifact contract.

    Resolution priority: exact artifact_id match → family fallback → default template.
    """
    if asset.artifact_id in _TEMPLATES_BY_ARTIFACT_ID:
        return _TEMPLATES_BY_ARTIFACT_ID[asset.artifact_id]
    return _TEMPLATES_BY_FAMILY.get(asset.family, _DEFAULT_TEMPLATE)


def _resolve_instruction_apply_to(asset: CopilotArtifactContract) -> str:
    """Resolve applyTo for instruction artifacts with optional docs override."""
    if asset.artifact_id == "instructions.docs":
        override = os.getenv(_DOCS_APPLY_TO_OVERRIDE_ENV, "").strip()
        if override:
            return override
    return asset.apply_to or "**"


def _build_yaml_frontmatter(asset: CopilotArtifactContract) -> str:
    """Build YAML frontmatter appropriate for the artifact's family type.

    Instructions get ``applyTo``, prompts get ``mode``/``tools``/``description``,
    agents get ``agents``/``name``/``description``/``tools``.
    """
    lines = ["---"]
    if asset.family is CopilotArtifactFamily.INSTRUCTIONS:
        lines.append(f'applyTo: "{_resolve_instruction_apply_to(asset)}"')
    elif asset.family is CopilotArtifactFamily.PROMPTS:
        lines.append("mode: 'agent'")
        lines.append(
            "tools: ["
            + ", ".join(
                f"'{t}'"
                for t in [
                    "read",
                    "agent",
                    "edit",
                    "search",
                    "web",
                    "zen-of-docs/*",
                    "context7/*",
                    "serena/*",
                    "zen-of-languages/*",
                    "todo",
                    "github/search_code",
                    "github/search_repositories",
                    "ms-python.python/getPythonEnvironmentInfo",
                    "ms-python.python/getPythonExecutableCommand",
                    "ms-python.python/installPythonPackage",
                    "ms-python.python/configurePythonEnvironment",
                ]
            )
            + "]"
        )
        lines.append(f"description: '{asset.summary}'")
    elif asset.family is CopilotArtifactFamily.AGENTS:
        # Skip frontmatter for README scaffolds.
        if asset.relative_path.name == "README.md":
            return ""
        agent_name = asset.relative_path.stem.replace(".agent", "")
        lines.append('agents: ["*"]')
        lines.append(f"name: '{agent_name}'")
        lines.append(f"description: '{asset.summary}'")
        lines.append(
            "tools: ["
            + ", ".join(
                f"'{t}'"
                for t in [
                    "read",
                    "agent",
                    "edit",
                    "search",
                    "web",
                    "zen-of-docs/*",
                    "context7/*",
                    "serena/*",
                    "zen-of-languages/*",
                    "todo",
                    "github/search_code",
                    "github/search_repositories",
                    "ms-python.python/getPythonEnvironmentInfo",
                    "ms-python.python/getPythonExecutableCommand",
                    "ms-python.python/installPythonPackage",
                    "ms-python.python/configurePythonEnvironment",
                ]
            )
            + "]"
        )
    elif asset.family is CopilotArtifactFamily.EXTENSION_HOOKS:
        hook = asset.hook_target.value if asset.hook_target else "unknown"
        lines.append(f"hook_target: '{hook}'")
    else:
        return ""
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_copilot_asset_content(asset: CopilotArtifactContract) -> str:
    """Return deterministic markdown content for one Copilot artifact contract."""
    frontmatter = _build_yaml_frontmatter(asset)
    hook_target = asset.hook_target.value if asset.hook_target is not None else "unknown"
    template = _resolve_template(asset)
    body = template.body_template.format(
        summary=asset.summary,
        required=str(asset.required).lower(),
        hook_target=hook_target,
    )
    return frontmatter + body


__all__ = [
    "COPILOT_ASSET_TEMPLATE_REGISTRY",
    "CopilotAssetTemplate",
    "CopilotAssetTemplateId",
    "render_copilot_asset_content",
]

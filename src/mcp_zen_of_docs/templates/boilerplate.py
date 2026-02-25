"""Typed documentation boilerplate template registry."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class BoilerplateBrickId(StrEnum):
    """Stable identifiers for reusable markdown bricks."""

    INDEX_TITLE = "index-title"
    INDEX_OVERVIEW = "index-overview"
    INDEX_LINKS = "index-links"
    INDEX_GETTING_STARTED = "index-getting-started"
    TOC_TITLE = "toc-title"
    TOC_PRIMARY_NAV = "toc-primary-nav"
    TOC_CONTRIBUTOR_WORKFLOW = "toc-contributor-workflow"
    API_TITLE = "api-title"
    API_GUIDELINES = "api-guidelines"
    API_ENDPOINT_TEMPLATE = "api-endpoint-template"
    STANDARDS_TITLE = "standards-title"
    STANDARDS_SCOPE = "standards-scope"
    STANDARDS_AUDIENCE = "standards-audience"
    STANDARDS_SOURCE_OF_TRUTH = "standards-source-of-truth"
    STANDARDS_NAVIGATION = "standards-navigation"
    STANDARDS_REVIEW = "standards-review"
    ARCHITECTURE_TITLE = "architecture-title"
    ARCHITECTURE_COMPONENTS = "architecture-components"
    ARCHITECTURE_DECISION_LOG = "architecture-decision-log"
    ARCHITECTURE_RELATED_DOCS = "architecture-related-docs"
    CONTRIBUTING_TITLE = "contributing-title"
    CONTRIBUTING_CODE_OF_CONDUCT = "contributing-code-of-conduct"
    CONTRIBUTING_GETTING_STARTED = "contributing-getting-started"
    CONTRIBUTING_PULL_REQUEST = "contributing-pull-request"
    CONTRIBUTING_DOCS_CHANGES = "contributing-docs-changes"
    CONTRIBUTING_REVIEW_PROCESS = "contributing-review-process"
    CHANGELOG_TITLE = "changelog-title"
    CHANGELOG_FORMAT = "changelog-format"
    CHANGELOG_UNRELEASED = "changelog-unreleased"
    CHANGELOG_TEMPLATE_ENTRY = "changelog-template-entry"
    QUICKSTART_TITLE = "quickstart-title"
    QUICKSTART_PREREQUISITES = "quickstart-prerequisites"
    QUICKSTART_INSTALLATION = "quickstart-installation"
    QUICKSTART_FIRST_RUN = "quickstart-first-run"
    QUICKSTART_NEXT_STEPS = "quickstart-next-steps"
    TROUBLESHOOTING_TITLE = "troubleshooting-title"
    TROUBLESHOOTING_COMMON_ISSUES = "troubleshooting-common-issues"
    TROUBLESHOOTING_DIAGNOSTICS = "troubleshooting-diagnostics"
    TROUBLESHOOTING_GETTING_HELP = "troubleshooting-getting-help"
    DEPLOYMENT_TITLE = "deployment-title"
    DEPLOYMENT_PREREQUISITES = "deployment-prerequisites"
    DEPLOYMENT_ENVIRONMENTS = "deployment-environments"
    DEPLOYMENT_CI_CD = "deployment-ci-cd"
    DEPLOYMENT_ROLLBACK = "deployment-rollback"


class BoilerplateTemplateId(StrEnum):
    """Stable identifiers for bundled boilerplate templates."""

    DOCS_INDEX = "docs-index"
    DOCS_TOC = "docs-toc"
    DOCS_API = "docs-api"
    DOCS_STANDARDS = "docs-standards"
    DOCS_ARCHITECTURE = "docs-architecture"
    DOCS_CONTRIBUTING = "docs-contributing"
    DOCS_CHANGELOG = "docs-changelog"
    DOCS_QUICKSTART = "docs-quickstart"
    DOCS_TROUBLESHOOTING = "docs-troubleshooting"
    DOCS_DEPLOYMENT = "docs-deployment"


class BoilerplateBrick(BaseModel):
    """Reusable markdown unit for lego-brick template composition."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False, frozen=True)

    brick_id: BoilerplateBrickId = Field(description="Stable brick identifier.")
    content: str = Field(description="Deterministic brick content.")


class BoilerplateTemplate(BaseModel):
    """One deterministic markdown boilerplate template contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False, frozen=True)

    template_id: BoilerplateTemplateId = Field(description="Stable template identifier.")
    relative_path: Path = Field(description="Repository-relative output path.")
    bricks: tuple[BoilerplateBrick, ...] = Field(
        description="Ordered content bricks used to compose the template."
    )
    content: str = Field(description="Deterministic template body content.")


DOC_BOILERPLATE_BRICK_REGISTRY: tuple[BoilerplateBrick, ...] = (
    BoilerplateBrick(brick_id=BoilerplateBrickId.INDEX_TITLE, content="# Project Documentation"),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.INDEX_OVERVIEW,
        content=(
            "## Overview\n\n"
            "Provide a concise summary covering the following:\n\n"
            "- **Purpose** — What problem does this project solve and why does it exist?\n"
            "- **Audience** — Who are the primary users (developers, operators, end-users)?\n"
            "- **Scope** — What is included in this documentation "
            "and what is intentionally excluded?\n"
            "- **Ownership** — Which team or individual maintains this project and its docs?\n"
            "- **Status** — Current project maturity (alpha, beta, stable, deprecated)."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.INDEX_LINKS,
        content=(
            "## Documentation map\n\n"
            "- [Table of contents](./toc.md)\n"
            "- [API reference](./api.md)\n"
            "- [Documentation standards](./standards.md)\n"
            "- [Architecture overview](./architecture.md)"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.INDEX_GETTING_STARTED,
        content=(
            "## Getting started\n\n"
            "- Run setup scripts generated by `init_project`.\n"
            "- Validate docs with `check_language_structure` and `check_docs_links`."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TOC_TITLE,
        content="# Documentation Table of Contents",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TOC_PRIMARY_NAV,
        content=(
            "## Primary navigation\n\n"
            "1. [Project documentation home](./index.md)\n"
            "2. [API reference](./api.md)\n"
            "3. [Documentation standards](./standards.md)\n"
            "4. [Architecture overview](./architecture.md)"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TOC_CONTRIBUTOR_WORKFLOW,
        content=(
            "## Contributor workflow\n\n"
            "1. Confirm init state with `check_init_status`.\n"
            "2. Update canonical pages before derivative docs.\n"
            "3. Run docs validation checks before opening a PR."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.API_TITLE,
        content="# API Reference",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.API_GUIDELINES,
        content=(
            "## Endpoint documentation standards\n\n"
            "- Include HTTP method, route path, and authentication "
            "requirements for every endpoint.\n"
            "- Define request schema (parameters, headers, body) "
            "using OpenAPI/Swagger conventions.\n"
            "- Define response schema with status codes, body shape, and error contract.\n"
            "- Document rate limits, pagination behavior, "
            "and idempotency guarantees where applicable.\n"
            "- Link to source ownership and relevant [architecture decisions](./architecture.md).\n"
            "- Provide `curl` or SDK examples for each endpoint to support quick integration."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.API_ENDPOINT_TEMPLATE,
        content=(
            "## Endpoint template\n\n"
            "### `METHOD /path`\n\n"
            "- **Purpose:**\n"
            "- **Auth:**\n"
            "- **Inputs:**\n"
            "- **Outputs:**\n"
            "- **Failure modes:**"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_TITLE,
        content="# Documentation Standards",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_SCOPE,
        content=(
            "## 1) Scope and non-scope\n\n"
            "- Every net-new doc must declare what it covers and what it intentionally excludes.\n"
            "- If content is exploratory or future-facing, mark it as non-shipping guidance."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_AUDIENCE,
        content=(
            "## 2) Audience and prerequisites\n\n"
            "- Every page must name the primary audience (for example: contributor, operator, "
            "reviewer).\n"
            "- Every page must list prerequisites before procedural steps."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_SOURCE_OF_TRUTH,
        content=(
            "## 3) Canonical-source policy\n\n"
            "- Each topic has one canonical source file.\n"
            "- Summary or duplicate pages must link back to the canonical source and avoid drift.\n"
            "- Update canonical source first, then synchronize derivative pages."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_NAVIGATION,
        content=(
            "## 4) IA depth and cross-linking\n\n"
            "- Keep docs navigation depth to 3 levels or fewer.\n"
            "- Every page should include at least one inbound or outbound related-doc link.\n"
            "- Use `check_orphan_docs` to prevent stranded pages."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.STANDARDS_REVIEW,
        content=(
            "## 5) Docs-as-code ownership and review\n\n"
            "- Treat docs changes like code changes: open PR, request review, and run checks.\n"
            "- Required checks: `check_language_structure`, `check_docs_links`, and docs build.\n"
            "- Block merge when docs updates change behavior but omit source-of-truth updates."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.ARCHITECTURE_TITLE,
        content="# Architecture",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.ARCHITECTURE_COMPONENTS,
        content=(
            "## Components\n\n"
            "Use the [C4 model](https://c4model.com/) levels to structure this section:\n\n"
            "### System context\n\n"
            "- Describe how this system fits into the broader "
            "ecosystem and its external dependencies.\n\n"
            "### Container diagram\n\n"
            "- List the major deployable units (services, databases, message queues).\n"
            "- State the technology choice and runtime for each container.\n\n"
            "### Component responsibilities\n\n"
            "| Component | Owner | Responsibility | Key interfaces |\n"
            "| --------- | ----- | -------------- | -------------- |\n"
            "| *Name*    | *Team/person* | *One-sentence purpose* | *APIs, events, files* |\n\n"
            "- Document ownership and on-call responsibilities for each component.\n"
            "- Link to relevant [Architecture Decision Records]"
            "(#decision-log) for design rationale."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.ARCHITECTURE_DECISION_LOG,
        content=(
            "## Decision log\n\n"
            "Record architectural decisions using the ADR "
            "(Architecture Decision Record) format:\n\n"
            "### Template\n\n"
            "- **ADR-NNN: Title** (YYYY-MM-DD)\n"
            "- **Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX\n"
            "- **Context:** What is the issue or problem that motivates this decision?\n"
            "- **Decision:** What is the change that is being proposed or adopted?\n"
            "- **Consequences:** What are the tradeoffs and implications of this decision?\n\n"
            "Keep the decision log in reverse-chronological order (newest first)."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.ARCHITECTURE_RELATED_DOCS,
        content=(
            "## Related docs\n\n"
            "- [Documentation home](./index.md)\n"
            "- [Table of contents](./toc.md)\n"
            "- [API reference](./api.md)"
        ),
    ),
    # -- Contributing bricks --
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_TITLE,
        content="# Contributing",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_CODE_OF_CONDUCT,
        content=(
            "## Code of conduct\n\n"
            "This project follows a code of conduct to ensure "
            "a welcoming and inclusive environment.\n\n"
            "- Read the full [Code of Conduct](./CODE_OF_CONDUCT.md) before participating.\n"
            "- Report violations to the project maintainers "
            "via the contact method listed in the code of conduct.\n"
            "- All contributors, reviewers, and maintainers are expected to uphold these standards."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_GETTING_STARTED,
        content=(
            "## Getting started\n\n"
            "### Fork and clone\n\n"
            "1. Fork the repository on GitHub.\n"
            "2. Clone your fork locally: `git clone <your-fork-url>`.\n"
            "3. Add the upstream remote: `git remote add upstream <original-repo-url>`.\n\n"
            "### Local development setup\n\n"
            "1. Install the required runtime and toolchain (see [Quickstart](./quickstart.md)).\n"
            "2. Install dependencies: `uv sync` or the project-specific install command.\n"
            "3. Run the test suite to confirm a clean baseline: `uv run pytest`.\n\n"
            "### Branch naming\n\n"
            "Use descriptive branch names with a category prefix:\n\n"
            "- `feat/add-search-endpoint` — new features\n"
            "- `fix/null-pointer-on-login` — bug fixes\n"
            "- `docs/update-api-reference` — documentation changes\n"
            "- `refactor/extract-auth-module` — code restructuring"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_PULL_REQUEST,
        content=(
            "## Pull request guidelines\n\n"
            "### Title format\n\n"
            "Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.\n\n"
            "### Description template\n\n"
            "1. **What** — Describe the change in one sentence.\n"
            "2. **Why** — Link to the issue or explain the motivation.\n"
            "3. **How** — Summarize the implementation approach.\n"
            "4. **Testing** — Describe how the change was verified.\n\n"
            "### Review checklist\n\n"
            "- [ ] Tests pass locally (`uv run pytest`)\n"
            "- [ ] Lint passes (`uv run ruff check`)\n"
            "- [ ] Documentation updated if behavior changed\n"
            "- [ ] No breaking changes without migration notes"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_DOCS_CHANGES,
        content=(
            "## Making documentation changes\n\n"
            "1. Edit Markdown files in the `docs/` directory.\n"
            "2. Preview locally by running the docs server (e.g., `mkdocs serve` or equivalent).\n"
            "3. Validate links and structure: `check_docs_links` and `check_language_structure`.\n"
            "4. Ensure new pages are added to the navigation in the site config.\n"
            "5. Include screenshots or diagrams for UI-related documentation where helpful."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CONTRIBUTING_REVIEW_PROCESS,
        content=(
            "## Review process\n\n"
            "- **Response time** — Maintainers aim to provide "
            "initial review feedback within 3 business days.\n"
            "- **Who reviews** — PRs are assigned based on `CODEOWNERS`; documentation PRs may be "
            "reviewed by any maintainer.\n"
            "- **Iteration** — Address review comments with "
            "fixup commits; the reviewer will squash on merge.\n"
            "- **Approval** — At least one maintainer approval is required before merge.\n"
            "- **CI checks** — All status checks must pass before merge is allowed."
        ),
    ),
    # -- Changelog bricks --
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CHANGELOG_TITLE,
        content="# Changelog",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CHANGELOG_FORMAT,
        content=(
            "## Format\n\n"
            "This changelog follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) "
            "convention and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
            "### Change categories\n\n"
            "- **Added** — New features or capabilities.\n"
            "- **Changed** — Changes to existing functionality.\n"
            "- **Deprecated** — Features that will be removed in a future release.\n"
            "- **Removed** — Features that have been removed.\n"
            "- **Fixed** — Bug fixes.\n"
            "- **Security** — Vulnerability patches and security improvements."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CHANGELOG_UNRELEASED,
        content=(
            "## [Unreleased]\n\n"
            "### Added\n\n"
            "- *Describe new features here.*\n\n"
            "### Changed\n\n"
            "- *Describe changes to existing features here.*\n\n"
            "### Fixed\n\n"
            "- *Describe bug fixes here.*\n\n"
            "### Removed\n\n"
            "- *Describe removed features here.*"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.CHANGELOG_TEMPLATE_ENTRY,
        content=(
            "## [0.1.0] — YYYY-MM-DD\n\n"
            "### Added\n\n"
            "- Initial project scaffolding and documentation structure.\n"
            "- Core API endpoints for primary use case.\n"
            "- CI/CD pipeline with automated testing and linting.\n\n"
            "### Fixed\n\n"
            "- *No fixes in initial release.*"
        ),
    ),
    # -- Quickstart bricks --
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.QUICKSTART_TITLE,
        content="# Quickstart",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.QUICKSTART_PREREQUISITES,
        content=(
            "## Prerequisites\n\n"
            "Before you begin, ensure you have the following installed:\n\n"
            "- **Python** ≥ 3.12 (check with `python --version`)\n"
            "- **uv** — fast Python package manager "
            "(install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)\n"
            "- **Git** ≥ 2.30 for repository operations\n"
            "- A terminal with UTF-8 support"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.QUICKSTART_INSTALLATION,
        content=(
            "## Installation\n\n"
            "```bash\n"
            "# Clone the repository\n"
            "git clone <repository-url>\n"
            "cd <project-directory>\n\n"
            "# Install dependencies\n"
            "uv sync\n\n"
            "# Verify installation\n"
            "uv run python -c \"import <package_name>; print('OK')\"\n"
            "```"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.QUICKSTART_FIRST_RUN,
        content=(
            "## First run\n\n"
            "```bash\n"
            "# Run the default entry point\n"
            "uv run <package_name>\n\n"
            "# Or start the development server\n"
            "uv run <package_name> serve --reload\n"
            "```\n\n"
            "You should see output confirming the server is running. "
            "Visit `http://localhost:8000` to verify."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.QUICKSTART_NEXT_STEPS,
        content=(
            "## Next steps\n\n"
            "Now that the project is running locally, explore these resources:\n\n"
            "- [API reference](./api.md) — Detailed endpoint documentation and schemas.\n"
            "- [Architecture overview](./architecture.md) — "
            "System design and component responsibilities.\n"
            "- [Contributing guide](./contributing.md) — "
            "How to submit changes and open pull requests.\n"
            "- [Troubleshooting](./troubleshooting.md) — Solutions for common setup issues."
        ),
    ),
    # -- Troubleshooting bricks --
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TROUBLESHOOTING_TITLE,
        content="# Troubleshooting",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TROUBLESHOOTING_COMMON_ISSUES,
        content=(
            "## Common issues\n\n"
            "### Dependencies fail to install\n\n"
            "- **Symptom:** `uv sync` exits with a resolver error.\n"
            "- **Cause:** Python version mismatch or stale lock file.\n"
            "- **Fix:** Verify `python --version` meets the minimum requirement, "
            "then run `uv lock --upgrade` and retry.\n\n"
            "### Tests fail on a clean checkout\n\n"
            "- **Symptom:** `uv run pytest` reports import errors or missing fixtures.\n"
            "- **Cause:** Dependencies not installed or virtual environment not activated.\n"
            "- **Fix:** Run `uv sync` to install all dependencies, then retry.\n\n"
            "### Docs build produces warnings\n\n"
            "- **Symptom:** Documentation build emits broken-link or missing-page warnings.\n"
            "- **Cause:** New pages not added to navigation config, or stale cross-references.\n"
            "- **Fix:** Run `check_docs_links` to identify broken references and update navigation."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TROUBLESHOOTING_DIAGNOSTICS,
        content=(
            "## Diagnostics\n\n"
            "Collect the following information before reporting an issue:\n\n"
            "```bash\n"
            "# System and runtime info\n"
            "python --version\n"
            "uv --version\n"
            "git --version\n\n"
            "# Project state\n"
            "git log --oneline -5\n"
            "uv run pytest --co -q  # list collected tests without running\n"
            "```\n\n"
            "Include the output of these commands in your bug report "
            "to help maintainers reproduce the issue."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.TROUBLESHOOTING_GETTING_HELP,
        content=(
            "## Getting help\n\n"
            "- **GitHub Issues** — Search [existing issues](../../issues) "
            "before opening a new one. Use issue templates when available.\n"
            "- **GitHub Discussions** — Ask questions and share ideas in "
            "[Discussions](../../discussions).\n"
            "- **Pull requests** — If you have a fix, open a PR and reference the related issue.\n"
            "- See the [Contributing guide](./contributing.md) "
            "for detailed contribution instructions."
        ),
    ),
    # -- Deployment bricks --
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_TITLE,
        content="# Deployment",
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_PREREQUISITES,
        content=(
            "## Pre-deployment checklist\n\n"
            "Complete every item before deploying to any environment:\n\n"
            "- [ ] All tests pass on the target branch (`uv run pytest`)\n"
            "- [ ] Linting passes with no errors (`uv run ruff check`)\n"
            "- [ ] Documentation builds without warnings\n"
            "- [ ] Version number bumped in `pyproject.toml` (follow [Semantic Versioning](https://semver.org/))\n"
            "- [ ] [Changelog](./changelog.md) updated with release notes\n"
            "- [ ] Dependency lock file is up to date (`uv lock`)"
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_ENVIRONMENTS,
        content=(
            "## Environments\n\n"
            "| Environment | Purpose | URL | Branch | Approval required |\n"
            "| ----------- | ------- | --- | ------ | ----------------- |\n"
            "| Development | Integration testing "
            "| `<!-- TODO: set dev URL -->` | `develop` | No |\n"
            "| Staging | Pre-production validation "
            "| `<!-- TODO: set staging URL -->` | `release/*` | Team lead |\n"
            "| Production | Live environment "
            "| `<!-- TODO: set production URL -->` | `main` | 2 maintainers |\n\n"
            "### Environment-specific configuration\n\n"
            "- Use environment variables (never hard-coded secrets) for all credentials.\n"
            "- Configuration differences between environments "
            "should be documented in a `.env.example` file.\n"
            "- Feature flags control progressive rollout of new functionality."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_CI_CD,
        content=(
            "## CI/CD pipeline\n\n"
            "The deployment pipeline runs automatically on push to protected branches.\n\n"
            "### Pipeline stages\n\n"
            "1. **Lint** — Static analysis with `ruff` and type checking.\n"
            "2. **Test** — Full test suite with coverage reporting.\n"
            "3. **Build** — Package the application and build documentation.\n"
            "4. **Deploy** — Push to the target environment (see [Environments](#environments)).\n"
            "5. **Verify** — Post-deployment smoke tests and health checks.\n\n"
            "### Triggers\n\n"
            "- Push to `develop` → deploy to Development.\n"
            "- Push to `release/*` → deploy to Staging (requires approval).\n"
            "- Push to `main` → deploy to Production (requires 2 approvals)."
        ),
    ),
    BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_ROLLBACK,
        content=(
            "## Rollback procedures\n\n"
            "### When to rollback\n\n"
            "- Health check failures after deployment.\n"
            "- Error rate exceeds the defined threshold (e.g., >1% 5xx responses).\n"
            "- Critical functionality is broken as reported by smoke tests.\n\n"
            "### Rollback steps\n\n"
            "1. Revert the merge commit on the target branch: `git revert <merge-sha>`.\n"
            "2. Push the revert to trigger the CI/CD pipeline.\n"
            "3. Verify the rollback deployment via health checks and smoke tests.\n"
            "4. Open a post-incident issue documenting the failure and root cause.\n\n"
            "### Verification\n\n"
            "- Confirm the previous stable version is serving traffic.\n"
            "- Check application logs for error resolution.\n"
            "- Notify the team in the appropriate communication channel."
        ),
    ),
)

_BRICKS_BY_ID: dict[BoilerplateBrickId, BoilerplateBrick] = {
    brick.brick_id: brick for brick in DOC_BOILERPLATE_BRICK_REGISTRY
}


def _compose_template(
    *,
    template_id: BoilerplateTemplateId,
    relative_path: Path,
    brick_ids: tuple[BoilerplateBrickId, ...],
) -> BoilerplateTemplate:
    """Compose a boilerplate template from ordered brick IDs.

    Joins brick content with double newlines and appends a trailing newline.
    """
    bricks = tuple(_BRICKS_BY_ID[brick_id] for brick_id in brick_ids)
    content = "\n\n".join(brick.content for brick in bricks).rstrip() + "\n"
    return BoilerplateTemplate(
        template_id=template_id,
        relative_path=relative_path,
        bricks=bricks,
        content=content,
    )


DOC_BOILERPLATE_REGISTRY: tuple[BoilerplateTemplate, ...] = (
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_INDEX,
        relative_path=Path("docs/index.md"),
        brick_ids=(
            BoilerplateBrickId.INDEX_TITLE,
            BoilerplateBrickId.INDEX_OVERVIEW,
            BoilerplateBrickId.INDEX_LINKS,
            BoilerplateBrickId.INDEX_GETTING_STARTED,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_TOC,
        relative_path=Path("docs/toc.md"),
        brick_ids=(
            BoilerplateBrickId.TOC_TITLE,
            BoilerplateBrickId.TOC_PRIMARY_NAV,
            BoilerplateBrickId.TOC_CONTRIBUTOR_WORKFLOW,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_API,
        relative_path=Path("docs/api.md"),
        brick_ids=(
            BoilerplateBrickId.API_TITLE,
            BoilerplateBrickId.API_GUIDELINES,
            BoilerplateBrickId.API_ENDPOINT_TEMPLATE,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_STANDARDS,
        relative_path=Path("docs/standards.md"),
        brick_ids=(
            BoilerplateBrickId.STANDARDS_TITLE,
            BoilerplateBrickId.STANDARDS_SCOPE,
            BoilerplateBrickId.STANDARDS_AUDIENCE,
            BoilerplateBrickId.STANDARDS_SOURCE_OF_TRUTH,
            BoilerplateBrickId.STANDARDS_NAVIGATION,
            BoilerplateBrickId.STANDARDS_REVIEW,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_ARCHITECTURE,
        relative_path=Path("docs/architecture.md"),
        brick_ids=(
            BoilerplateBrickId.ARCHITECTURE_TITLE,
            BoilerplateBrickId.ARCHITECTURE_COMPONENTS,
            BoilerplateBrickId.ARCHITECTURE_DECISION_LOG,
            BoilerplateBrickId.ARCHITECTURE_RELATED_DOCS,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_CONTRIBUTING,
        relative_path=Path("docs/contributing.md"),
        brick_ids=(
            BoilerplateBrickId.CONTRIBUTING_TITLE,
            BoilerplateBrickId.CONTRIBUTING_CODE_OF_CONDUCT,
            BoilerplateBrickId.CONTRIBUTING_GETTING_STARTED,
            BoilerplateBrickId.CONTRIBUTING_PULL_REQUEST,
            BoilerplateBrickId.CONTRIBUTING_DOCS_CHANGES,
            BoilerplateBrickId.CONTRIBUTING_REVIEW_PROCESS,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_CHANGELOG,
        relative_path=Path("docs/changelog.md"),
        brick_ids=(
            BoilerplateBrickId.CHANGELOG_TITLE,
            BoilerplateBrickId.CHANGELOG_FORMAT,
            BoilerplateBrickId.CHANGELOG_UNRELEASED,
            BoilerplateBrickId.CHANGELOG_TEMPLATE_ENTRY,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_QUICKSTART,
        relative_path=Path("docs/quickstart.md"),
        brick_ids=(
            BoilerplateBrickId.QUICKSTART_TITLE,
            BoilerplateBrickId.QUICKSTART_PREREQUISITES,
            BoilerplateBrickId.QUICKSTART_INSTALLATION,
            BoilerplateBrickId.QUICKSTART_FIRST_RUN,
            BoilerplateBrickId.QUICKSTART_NEXT_STEPS,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_TROUBLESHOOTING,
        relative_path=Path("docs/troubleshooting.md"),
        brick_ids=(
            BoilerplateBrickId.TROUBLESHOOTING_TITLE,
            BoilerplateBrickId.TROUBLESHOOTING_COMMON_ISSUES,
            BoilerplateBrickId.TROUBLESHOOTING_DIAGNOSTICS,
            BoilerplateBrickId.TROUBLESHOOTING_GETTING_HELP,
        ),
    ),
    _compose_template(
        template_id=BoilerplateTemplateId.DOCS_DEPLOYMENT,
        relative_path=Path("docs/deployment.md"),
        brick_ids=(
            BoilerplateBrickId.DEPLOYMENT_TITLE,
            BoilerplateBrickId.DEPLOYMENT_PREREQUISITES,
            BoilerplateBrickId.DEPLOYMENT_ENVIRONMENTS,
            BoilerplateBrickId.DEPLOYMENT_CI_CD,
            BoilerplateBrickId.DEPLOYMENT_ROLLBACK,
        ),
    ),
)


def render_deployment_environments_brick(
    *,
    dev_url: str | None = None,
    staging_url: str | None = None,
    production_url: str | None = None,
) -> BoilerplateBrick:
    """Render the deployment environments brick with project-specific URLs.

    When URLs are ``None``, a ``<!-- TODO -->`` placeholder is emitted instead
    of ``example.com`` so that reviewers can easily spot missing configuration.
    """
    dev = f"`{dev_url}`" if dev_url else "`<!-- TODO: set dev URL -->`"
    stg = f"`{staging_url}`" if staging_url else "`<!-- TODO: set staging URL -->`"
    prod = f"`{production_url}`" if production_url else "`<!-- TODO: set production URL -->`"
    return BoilerplateBrick(
        brick_id=BoilerplateBrickId.DEPLOYMENT_ENVIRONMENTS,
        content=(
            "## Environments\n\n"
            "| Environment | Purpose | URL | Branch | Approval required |\n"
            "| ----------- | ------- | --- | ------ | ----------------- |\n"
            f"| Development | Integration testing | {dev} | `develop` | No |\n"
            f"| Staging | Pre-production validation | {stg}"
            " | `release/*` | Team lead |\n"
            f"| Production | Live environment | {prod}"
            " | `main` | 2 maintainers |\n\n"
            "### Environment-specific configuration\n\n"
            "- Use environment variables (never hard-coded secrets)"
            " for all credentials.\n"
            "- Configuration differences between environments "
            "should be documented in a `.env.example` file.\n"
            "- Feature flags control progressive rollout"
            " of new functionality."
        ),
    )


def iter_doc_boilerplate_templates() -> tuple[BoilerplateTemplate, ...]:
    """Return boilerplate templates in deterministic registry order."""
    return DOC_BOILERPLATE_REGISTRY


__all__ = [
    "DOC_BOILERPLATE_BRICK_REGISTRY",
    "DOC_BOILERPLATE_REGISTRY",
    "BoilerplateBrick",
    "BoilerplateBrickId",
    "BoilerplateTemplate",
    "BoilerplateTemplateId",
    "iter_doc_boilerplate_templates",
    "render_deployment_environments_brick",
]

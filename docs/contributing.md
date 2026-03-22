# Contributing

## Code of conduct

This project follows a code of conduct to ensure a welcoming and inclusive environment.

- Read the full [Code of Conduct](./CODE_OF_CONDUCT.md) before participating.
- Report violations to the project maintainers via the contact method listed in the code of conduct.
- All contributors, reviewers, and maintainers are expected to uphold these standards.

## Getting started

### Fork and clone

1. Fork the repository on GitHub.
2. Clone your fork locally: `git clone <your-fork-url>`.
3. Add the upstream remote: `git remote add upstream <original-repo-url>`.

### Local development setup

1. Install the required runtime and toolchain (see [Quickstart](./quickstart.md)).
2. Install dependencies: `uv sync` or the project-specific install command.
3. Run the test suite to confirm a clean baseline: `uv run pytest`.

### Branch naming

Use descriptive branch names with a category prefix:

- `feat/add-search-endpoint` — new features
- `fix/null-pointer-on-login` — bug fixes
- `docs/update-api-reference` — documentation changes
- `refactor/extract-auth-module` — code restructuring

## Pull request guidelines

### Title format

Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.

### Description template

1. **What** — Describe the change in one sentence.
2. **Why** — Link to the issue or explain the motivation.
3. **How** — Summarize the implementation approach.
4. **Testing** — Describe how the change was verified.

### Review checklist

- [ ] Tests pass locally (`uv run pytest`)
- [ ] Lint passes (`uv run ruff check`)
- [ ] Documentation updated if behavior changed
- [ ] No breaking changes without migration notes

## Making documentation changes

1. Edit Markdown files in the `docs/` directory.
2. Preview locally by running the docs server (e.g., `mkdocs serve` or equivalent).
3. Validate links and structure: `check_docs_links` and `check_language_structure`.
4. Ensure new pages are added to the navigation in the site config.
5. Include screenshots or diagrams for UI-related documentation where helpful.

## Review process

- **Response time** — Maintainers aim to provide initial review feedback within 3 business days.
- **Who reviews** — PRs are assigned based on `CODEOWNERS`; documentation PRs may be reviewed by any maintainer.
- **Iteration** — Address review comments with fixup commits; the reviewer will squash on merge.
- **Approval** — At least one maintainer approval is required before merge.
- **CI checks** — All status checks must pass before merge is allowed.

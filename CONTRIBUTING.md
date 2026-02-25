# Contributing to mcp-zen-of-docs

Thanks for contributing.

The full contributor docs live in [`docs/contributing/`](docs/contributing/index.md), but this file gives GitHub readers the quick path.

## Quick start

```bash
git clone https://github.com/Anselmoo/mcp-zen-of-docs
cd mcp-zen-of-docs
uv sync --group dev --group docs
```

Run the main checks before opening a PR:

```bash
uv run pytest
uv run poe lint
uv run poe type-check
uv run poe docs-serve
```

## Where to look

- Development guide: [`docs/contributing/development.md`](docs/contributing/development.md)
- Add a framework: [`docs/contributing/adding-framework.md`](docs/contributing/adding-framework.md)
- Add a primitive: [`docs/contributing/adding-primitive.md`](docs/contributing/adding-primitive.md)

## Expectations

- Keep changes focused and typed.
- Add or update tests when behavior changes.
- Update the docs when the user-facing experience changes.
- Prefer clarity and correctness over cleverness.

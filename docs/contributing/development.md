---
title: Development
description: Set up the mcp-zen-of-docs dev environment, run tests, and submit a pull request.
tags:
  - contributing
  - development
---

# Development

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) — the package manager used by this project

---

## Setup

```bash
git clone https://github.com/your-org/mcp-zen-of-docs
cd mcp-zen-of-docs
uv sync --group dev --group docs
```

---

## Run the server locally

```bash
uv run mcp-zen-of-docs-server
```

Or use the Poe task shortcut:

```bash
uv run poe serve
```

---

## Local docs preview

```bash
uv run poe docs-serve
```

Opens at `http://localhost:8000`. Hot-reloads on file changes. Equivalent to running
`uv run zensical serve` directly.

---

## Tests

```bash
uv run pytest                          # all tests
uv run pytest --cov=mcp_zen_of_docs   # with coverage
uv run pytest -k "test_detect"        # filter by name
```

Coverage target: **≥ 90%**. New code without tests will not be merged.

---

## Linting and type checking

```bash
uv run poe lint        # ruff check
uv run poe format      # ruff format
uv run poe type-check  # ty check
```

All checks must pass before opening a PR.

---

## Adding a new tool

Follow these four steps in order:

1. **`src/mcp_zen_of_docs/models.py`** — add the input/output Pydantic models with
   `Field(description=...)` on every field.
2. **`src/mcp_zen_of_docs/generators.py`** — implement the core logic function. Keep it
   pure: no MCP imports, no side effects beyond filesystem writes.
3. **`src/mcp_zen_of_docs/server.py`** — register the tool with `@mcp.tool()`. The
   function signature must use the models from step 1.
4. **`tests/test_<toolname>.py`** — write tests covering the happy path and at least one
   error case. Run `uv run pytest` to confirm they pass.

---

## PR checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run poe lint`)
- [ ] Type checking passes (`uv run poe type-check`)
- [ ] New public functions have Google-style docstrings
- [ ] New Pydantic models have `Field(description=...)` on every field

---

## What's Next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Adding a Framework**

    Extend mcp-zen-of-docs to support a new docs framework.

    [:octicons-arrow-right-24: Read the guide](adding-framework.md)

-   :octicons-arrow-right-24: **Adding a Primitive**

    Add a new authoring primitive to an existing framework profile.

    [:octicons-arrow-right-24: Read the guide](adding-primitive.md)

</div>

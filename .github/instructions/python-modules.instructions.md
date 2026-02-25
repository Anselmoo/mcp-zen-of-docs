---
applyTo: "**/*.py"
---

# Python Module Standards

Every Python module in this project must follow these conventions:

## Module Header

```python
"""Module docstring — one-line summary."""

from __future__ import annotations

__all__ = ["PublicClass", "public_function"]
```

## Required in Every Module

1. `from __future__ import annotations` — first import after docstring
2. `__all__` — explicit public API surface
3. Google-style docstring at module level

## Type Annotations

- 100% type-annotated — all function parameters, return types, variables where non-obvious
- Use `| None` union syntax (enabled by future annotations), not `Optional[X]`
- Use `pathlib.Path`, not `str`, for filesystem paths
- Use `StrEnum` members, not raw strings, for categorical values

## Error Handling

- Use the `ZenDocsError` custom exception hierarchy
- Never bare `except:` or `except Exception:`
- Catch specific exceptions

## No `print()`

- Use `structlog` or `logging` with `rich.logging.RichHandler`
- Never use `print()` for output

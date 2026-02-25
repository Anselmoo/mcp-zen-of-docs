---
applyTo: "tests/**"
---

# Testing Guidelines

## Standards

- Use `pytest` + `pytest-asyncio` for async tool tests
- Coverage target: ≥90%
- Google-style test names: `test_<function>_<scenario>`

## What to Test

1. **Pydantic model validation** — Verify models accept valid data and reject invalid
2. **Tool return types** — Assert every tool returns the correct Pydantic response model
3. **Framework detection** — Each profile correctly identifies its framework from config files
4. **Primitive rendering** — Each supported primitive renders valid syntax per framework
5. **Support matrix completeness** — All 16 primitives mapped for every profile
6. **Edge cases** — Missing files, invalid paths, empty content

## Patterns

```python
import pytest
from mcp_zen_of_docs.models import SnippetRequest, SnippetResponse, FrameworkName

def test_snippet_response_is_pydantic_model():
    """Tool returns a typed Pydantic model, not a dict."""
    result = generate_snippet_impl(request)
    assert isinstance(result, SnippetResponse)
    assert result.framework == FrameworkName.ZENSICAL

@pytest.mark.asyncio
async def test_tool_returns_typed_response():
    """Async tool integration test."""
    ...
```

## Run Commands

- `uv run pytest` — run all tests
- `uv run pytest --cov=mcp_zen_of_docs` — with coverage
- `uv run pytest -k "test_admonition"` — run specific tests

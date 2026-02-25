---
applyTo: "src/mcp_zen_of_docs/server.py"
---

# MCP Server Tool Registration

This file registers all `@app.tool` functions for the FastMCP server.

## Rules

1. **Typed returns only** — Every tool returns a Pydantic response model, never `dict[str, object]`
2. **Pydantic parameters** — Use Pydantic `BaseModel` for complex inputs. Simple tools can use scalar params with `Field()`
3. **`async def`** — Use async for tools that perform I/O (file reads, subprocess calls)
4. **Delegation** — Tools delegate to `generators.py` or `validators.py` for business logic. Keep this file slim.
5. **Docstrings** — Google-style docstring on every tool (FastMCP uses them for MCP tool descriptions)

## Pattern

```python
from .models import SnippetRequest, SnippetResponse

@app.tool
async def generate_snippet(request: SnippetRequest) -> SnippetResponse:
    """Generate a framework-native documentation snippet for any authoring primitive."""
    return await generate_snippet_impl(request)
```

## Migration

Current tools return `dict[str, object]`. Each must be migrated to return a Pydantic model from `models.py`.

---
applyTo: "src/mcp_zen_of_docs/models.py,src/mcp_zen_of_docs/**/models*.py"
---

# Pydantic Model Guidelines

All data structures in this project use Pydantic `BaseModel`.

## Mandatory Patterns

- Every field has `Field(description="...")` — no bare field declarations
- Use `StrEnum` for categorical values (`FrameworkName`, `AuthoringPrimitive`, `SupportLevel`)
- Use `frozen=True` on result/config models for immutability
- Use `pathlib.Path` for filesystem paths, never `str`
- Use `| None` unions for optional fields, never magic strings like `""` or `"auto"`
- Numeric scores use `Field(ge=0.0, le=1.0)` constraints

## StrEnum Definitions

```python
class FrameworkName(StrEnum):
    ZENSICAL = "zensical"
    DOCUSAURUS = "docusaurus"
    VITEPRESS = "vitepress"
    STARLIGHT = "starlight"

class AuthoringPrimitive(StrEnum):
    # 16 values: markdown, frontmatter, admonitions, buttons, code_blocks,
    # content_tabs, data_tables, diagrams, footnotes, formatting, grids,
    # icons_emojis, images, lists, math, tooltips

class SupportLevel(StrEnum):
    NATIVE = "native"
    PLUGIN = "plugin"
    CUSTOM = "custom"
    UNSUPPORTED = "unsupported"
```

## Response Models

Every tool returns a typed Pydantic model. Never return `dict[str, object]`.

```python
# CORRECT
class SnippetResponse(BaseModel):
    framework: FrameworkName
    snippet: str = Field(description="Generated Markdown/MDX snippet")

# WRONG
def generate_snippet(...) -> dict[str, object]:  # Never
```

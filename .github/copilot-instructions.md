# Copilot Instructions — mcp-zen-of-docs

## Project Identity

This is `mcp-zen-of-docs`, a **universal documentation quality MCP server** built with FastMCP v2. It provides AI-powered tools for generating, validating, and scoring documentation across four frameworks: **Zensical**, **Docusaurus**, **VitePress**, and **Starlight**. The project deeply understands 16 authoring primitives (admonitions, code blocks, content tabs, diagrams, etc.) with native syntax per framework.

## Quality Reference Implementations

Two MCP servers serve as quality benchmarks for this project's engineering standards:

- **`mcp_context7`** (Context7 MCP server) — Clean tool design, minimal surface area, Pydantic-first parameter models, clear docstrings.
- **`mcp_zen-of-language`** (Zen of Language MCP server) — Comprehensive multi-tool architecture, repository analysis patterns, structured scoring, rule-based analysis with typed results.

When in doubt about patterns or code quality, reference how these servers handle similar concerns.

## Python Engineering Standards

### Non-Negotiable Requirements

1. **Pydantic everywhere** — Every tool input, output, configuration model, and internal data structure uses `pydantic.BaseModel` with `Field(description=...)` on every parameter. FastMCP v2 natively supports Pydantic models as tool parameters and return types.

2. **No `dict[str, object]` returns** — All tool functions return Pydantic response models, never raw dicts. The current codebase returns `dict[str, object]` — this must be migrated to typed Pydantic models.

3. **`StrEnum` for categoricals** — Use `enum.StrEnum` (Python 3.12+) for all categorical values:
   - `FrameworkName` — `zensical`, `docusaurus`, `vitepress`, `starlight`
   - `AuthoringPrimitive` — 16 values: `markdown`, `frontmatter`, `admonitions`, `buttons`, `code_blocks`, `content_tabs`, `data_tables`, `diagrams`, `footnotes`, `formatting`, `grids`, `icons_emojis`, `images`, `lists`, `math`, `tooltips`
   - `SupportLevel` — `native`, `plugin`, `custom`, `unsupported`

4. **`pathlib.Path` throughout** — Never use raw `str` for filesystem paths. Tool parameters accepting paths use `Path` with Pydantic validation.

5. **`from __future__ import annotations`** — Every module starts with this import for modern annotation syntax.

### FastMCP v2 Idioms

```python
# CORRECT: Pydantic model as tool input, typed response
class SnippetRequest(BaseModel):
    primitive: AuthoringPrimitive = Field(description="Which authoring primitive to generate")
    framework: FrameworkName | None = Field(default=None, description="Target framework (auto-detected if omitted)")

class SnippetResponse(BaseModel):
    framework: FrameworkName
    snippet: str = Field(description="The generated Markdown/MDX snippet")
    support_level: SupportLevel

@app.tool
async def generate_snippet(request: SnippetRequest) -> SnippetResponse:
    """Generate a framework-native documentation snippet for any authoring primitive."""
    ...

# WRONG: Raw dict returns, untyped parameters
@app.tool
def generate_snippet(primitive: str, framework: str = "auto") -> dict[str, object]:  # ← Never do this
    ...
```

### Python 3.11+ Features to Use

- `StrEnum` — for all enumerations (not plain `str` constants)
- `tomllib` — for TOML parsing (stdlib, no external dependency)
- `match/case` — for framework dispatch where it improves readability
- `TypeAlias` and `type` statements where appropriate
- `ExceptionGroup` — if aggregating multiple validation errors

### CLI (Optional)

If CLI entry points are needed beyond the MCP server:
- **Typer** (`typer>=0.15.0`) for argument parsing — Pydantic-powered, auto-generates `--help`
- **Rich** (`rich>=13.0.0`) for terminal output — tables, panels, syntax highlighting, progress bars
- Use `rich.console.Console` for structured output, never bare `print()`

### Code Quality

| Aspect | Standard |
|--------|----------|
| Types | 100% type-annotated, strict pyright/mypy compatible |
| Linting | `ruff` with `target-version = "py312"`, `line-length = 100` |
| Testing | `pytest` + `pytest-asyncio`, coverage target ≥90% |
| Docstrings | Google-style on all public functions and classes |
| Imports | Absolute within package, `from __future__ import annotations` in every file |
| Errors | Custom `ZenDocsError` hierarchy, never bare `except:` |
| Logging | `structlog` or `logging` with `rich.logging.RichHandler`, never `print()` |
| Exports | Every module defines `__all__` for explicit public API |
| Config | Pydantic `BaseSettings` for environment-based config |
| Immutability | `frozen=True` on Pydantic models for config and results |
| Sentinels | `None` with `| None` unions for optional fields, never magic strings |

## Architecture

### Core Concepts

- **4 Frameworks**: Zensical (primary/default), Docusaurus, VitePress, Starlight
- **16 Authoring Primitives**: The universal building blocks of documentation (see `AuthoringPrimitive` enum)
- **AuthoringProfile**: Abstract base class — each framework provides a concrete profile with render methods, detection logic, and support-level mappings
- **Detect → Profile → Act**: Tools auto-detect the framework from config files, load the appropriate profile, then generate/validate

### Module Structure

```
src/mcp_zen_of_docs/
├── __init__.py
├── __main__.py
├── server.py              # FastMCP app, all @app.tool registrations
├── models.py              # All Pydantic models (StrEnums, request/response models)
├── generators.py          # Generation logic (snippets, scaffolds, onboarding)
├── validators.py          # Validation logic (links, structure, quality scoring)
├── frameworks/
│   ├── __init__.py        # get_profile(), detect_framework(), list_frameworks()
│   ├── base.py            # AuthoringProfile ABC
│   ├── zensical_profile.py
│   ├── docusaurus_profile.py
│   ├── vitepress_profile.py
│   └── starlight_profile.py
└── primitives/            # Per-primitive rendering logic (optional, for complex primitives)
```

### Design Principles

1. **Pydantic-native**: Every tool input and output is a Pydantic `BaseModel`.
2. **Profile-driven**: No hardcoded framework assumptions outside profiles.
3. **Primitive-first**: A "snippet" is always tied to a named `AuthoringPrimitive` enum member.
4. **Detect → Profile → Act**: Auto-detection, then delegation.
5. **Backward compatible**: Existing tool signatures preserved during migration.
6. **Offline-first**: All generation is local and deterministic.
7. **Testable by design**: Pydantic models enable property-based testing; profiles are pure functions.

## Agent Workflow Guidelines

### When Implementing New Tools

1. Define the Pydantic request/response models in `models.py` first
2. Implement the business logic in `generators.py` or `validators.py`
3. Register the `@app.tool` in `server.py` with `async def` and typed parameters
4. Add tests in `tests/` with Pydantic model assertions
5. Verify all tests pass with `python -m pytest`

### When Adding Framework Support

1. Create the profile in `frameworks/{name}_profile.py`
2. Implement the `AuthoringProfile` ABC — especially `render_primitive()` and `detect()`
3. Register it in `frameworks/__init__.py`
4. Add the primitive support matrix (which of the 16 are native/plugin/custom/unsupported)
5. Add tests covering at least the native primitives

### When Modifying Existing Code

- Check if `dict[str, object]` returns exist — replace with Pydantic models
- Ensure `Field(description=...)` is on every model field
- Use `StrEnum` values, never raw strings for framework names or primitives
- Run `ruff check` and `python -m pytest` after every change

## The Zen of Documentation

1. Clarity over cleverness
2. Structure reveals intent
3. Primitives are universal — frameworks are dialects
4. Beauty is functional — good formatting aids comprehension
5. One page, one idea
6. Navigation is a contract with the reader
7. Frontmatter is metadata, not decoration
8. Code examples must run
9. Every admonition earns its place
10. Documentation is a product, not an afterthought

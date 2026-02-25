---
applyTo: "src/mcp_zen_of_docs/frameworks/**"
---

# Framework Profile Guidelines

Each framework has a profile implementing the `AuthoringProfile` ABC.

## AuthoringProfile ABC Contract

Every profile must implement:
- `name` → `FrameworkName` enum value
- `detect(project_root: Path) -> FrameworkDetectionResult | None` — detect framework from config files
- `render_primitive(primitive, **kwargs) -> str` — render a given primitive in native syntax
- `support_matrix() -> dict[AuthoringPrimitive, SupportLevel]` — all 16 primitives mapped
- `config_file_patterns() -> list[str]` — glob patterns for framework config files

## Framework Config Files for Detection

| Framework  | Config Files                         |
|-----------|--------------------------------------|
| Zensical  | `mkdocs.yml`, `mkdocs.yaml`         |
| Docusaurus| `docusaurus.config.js`, `.ts`        |
| VitePress | `.vitepress/config.js`, `.ts`, `.mts`|
| Starlight | `astro.config.mjs`, `astro.config.ts`|

## Primitive Rendering

Each primitive has framework-specific syntax. Examples:
- **Admonitions**: Zensical `!!! note`, Docusaurus `:::note`, VitePress `::: info`, Starlight `<Aside>`
- **Code blocks**: Zensical `pymdownx.highlight`, Docusaurus Prism, VitePress Shiki, Starlight Expressive Code
- **Content tabs**: Zensical `=== "Tab"`, Docusaurus `<Tabs>/<TabItem>`, VitePress `::: code-group`, Starlight `<Tabs>`

## Rules

- Profile modules import only from `models.py` and `frameworks/base.py`
- No cross-profile imports
- Use `match/case` for primitive dispatch where it improves readability
- Lazy-import heavy dependencies to keep startup fast

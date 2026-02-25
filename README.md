<p align="center">
  <img src="https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/docs/assets/zen-docs-header.svg?raw=true" alt="mcp-zen-of-docs — Universal Documentation Quality MCP Server" width="100%"/>
</p>

<h1 align="center">mcp-zen-of-docs</h1>

<p align="center">
  <em>📝 Write documentation the way the framework intended.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/mcp-zen-of-docs"><img src="https://img.shields.io/pypi/v/mcp-zen-of-docs?style=flat-square&color=0ea27a" alt="PyPI"></a>
  <a href="https://pypi.org/project/mcp-zen-of-docs"><img src="https://img.shields.io/pypi/pyversions/mcp-zen-of-docs?style=flat-square" alt="Python"></a>
  <a href="https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Anselmoo/mcp-zen-of-docs?style=flat-square" alt="License"></a>
  <a href="https://github.com/Anselmoo/mcp-zen-of-docs/actions"><img src="https://img.shields.io/github/actions/workflow/status/Anselmoo/mcp-zen-of-docs/cicd.yml?style=flat-square&label=CI" alt="CI"></a>
  <a href="https://anselmoo.github.io/mcp-zen-of-docs/"><img src="https://img.shields.io/badge/docs-zensical-0ea27a?style=flat-square" alt="Docs"></a>
</p>

<p align="center">
  <a href="https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D"><img src="https://img.shields.io/badge/VS_Code-Install_MCP-007ACC?style=flat-square&logo=visualstudiocode&logoColor=white" alt="Install in VS Code"></a>
  <a href="https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D&quality=insiders"><img src="https://img.shields.io/badge/VS_Code_Insiders-Install_MCP-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white" alt="Install in VS Code Insiders"></a>
  <a href="https://github.com/Anselmoo/mcp-zen-of-docs/pkgs/container/mcp-zen-of-docs"><img src="https://img.shields.io/badge/Docker-GHCR-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
</p>

---

An **MCP server for AI assistants** that brings documentation quality tooling into your editor.
Connect it to Claude Desktop, VS Code Copilot, or Cursor and your AI can detect your framework,
scaffold pages in native syntax, validate structure, and generate visual assets — all inside the conversation.

<!-- --8<-- [start:what-you-get] -->

- **4 primary framework profiles** — Zensical, Docusaurus, VitePress, Starlight
- **3 supplemental detected contexts** — MkDocs Material, Sphinx, and generic Markdown
- **22 canonical authoring primitives** — frontmatter, tabs, diagrams, API endpoint blocks, badges, and more
- **10 composite MCP tools** — detect, profile, scaffold, validate, generate, onboard, theme, copilot, docstring, story
- **530+ tests** with pytest and Pydantic v2 type safety throughout
- **CLI interface** for local scripts, CI pipelines, and standalone runs

<!-- --8<-- [end:what-you-get] -->

## Why MCP

<!-- --8<-- [start:why-mcp] -->

MCP turns documentation quality from a standalone report into an interactive authoring loop.
Instead of switching between tools, your editor calls `mcp-zen-of-docs` directly — your AI
detects the framework, scaffolds a page in its native syntax, validates it, and generates
assets all in the same conversation.

- **Less context switching** — scaffold, validate, and score without leaving your editor.
- **Framework-native output** — no generic Markdown; every snippet uses the right syntax.
- **Consistent quality** — the same ten Zen principles applied to every page, every time.

<!-- --8<-- [end:why-mcp] -->

## Zen Philosophy

<!-- --8<-- [start:zen-philosophy] -->

Zen of Docs treats documentation quality as an engineering constraint, not a style preference.
Every framework profile encodes the authoring primitives that make docs maintainable in that
ecosystem, with a quality scorer that surfaces structural problems before they ship.

- **Framework-native quality** over generic Markdown linting.
- **Primitive-first scaffolding** beyond copy-pasting templates.
- **Actionable scoring** through the ten principles of The Zen of Documentation.

The project is guided by the **[Zen of Documentation](https://anselmoo.github.io/mcp-zen-of-docs/philosophy/)**
— ten language-agnostic principles that drive every tool decision.

<p align="center">
  <img src="https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/docs/assets/illustration-zen-principles.svg?raw=true" alt="The Zen of Documentation — 10 guiding principles" width="100%"/>
</p>

<!-- --8<-- [end:zen-philosophy] -->

## Quickstart

```bash
# MCP server (IDE and agent workflows)
uvx --from mcp-zen-of-docs mcp-zen-of-docs-server

# CLI without installing
uvx --from mcp-zen-of-docs mcp-zen-of-docs --help

# Or install globally
pip install mcp-zen-of-docs

# Scaffold a documentation page
mcp-zen-of-docs scaffold doc --doc-path docs/new-page.md --title "My Page"

# Validate your docs
mcp-zen-of-docs validate all --docs-root docs

# Score documentation quality
mcp-zen-of-docs validate score --docs-root docs
```

## MCP Tools at a Glance

<p align="center">
  <img src="https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/docs/assets/illustration-mcp-tools.svg?raw=true" alt="mcp-zen-of-docs tool workflow diagram" width="100%"/>
</p>

The MCP server exposes **10 composite tools** across the full documentation lifecycle:

| Tool | Purpose |
|------|---------|
| `detect` | Framework detection · project readiness checks |
| `profile` | Authoring profile lookup · primitive resolution · syntax translation |
| `scaffold` | Create and enrich documentation pages in native syntax |
| `validate` | Links · orphans · frontmatter · structure · quality scoring |
| `generate` | SVG visuals · Mermaid diagrams · reference docs |
| `onboard` | Project init · boilerplate scaffolding · pipeline planning |
| `theme` | Custom CSS, JS, and MkDocs extension generation |
| `copilot` | GitHub Copilot instruction files and agent configuration |
| `docstring` | Docstring audit and quality optimization |
| `story` | Multi-module documentation narrative composition |

See the full [API Reference](https://anselmoo.github.io/mcp-zen-of-docs/reference/api/) for parameters, modes, and examples.

## Choose Your Path

- **New user**: [Quickstart](https://anselmoo.github.io/mcp-zen-of-docs/quickstart/) → [Tools](https://anselmoo.github.io/mcp-zen-of-docs/tools/) → [Guides](https://anselmoo.github.io/mcp-zen-of-docs/guides/)
- **Author**: [Guides](https://anselmoo.github.io/mcp-zen-of-docs/guides/) → [Authoring Primitives](https://anselmoo.github.io/mcp-zen-of-docs/guides/primitives/) → [Frameworks](https://anselmoo.github.io/mcp-zen-of-docs/frameworks/)
- **Contributor**: [Contributing](https://anselmoo.github.io/mcp-zen-of-docs/contributing/) → [Development](https://anselmoo.github.io/mcp-zen-of-docs/contributing/development/) → [Adding a Framework](https://anselmoo.github.io/mcp-zen-of-docs/contributing/adding-framework/)
- **AI-agent workflow**: [Quickstart](https://anselmoo.github.io/mcp-zen-of-docs/quickstart/) → [Tools](https://anselmoo.github.io/mcp-zen-of-docs/tools/) → [API Reference](https://anselmoo.github.io/mcp-zen-of-docs/reference/api/)

## Naming Guide

Keep these names distinct to avoid setup confusion:

- **Package name**: `mcp-zen-of-docs`
- **CLI command**: `mcp-zen-of-docs`
- **MCP server command**: `mcp-zen-of-docs-server`
- **Compatibility CLI alias**: `mcp-zen-of-docs-cli`
- **MCP client server key**: `zen-of-docs`

## Installation

### MCP Integration

Add the server to your MCP client configuration.

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zen-of-docs": {
      "command": "uvx",
      "args": ["--from", "mcp-zen-of-docs", "mcp-zen-of-docs-server"]
    }
  }
}
```

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "zen-of-docs": {
      "command": "uvx",
      "args": ["--from", "mcp-zen-of-docs", "mcp-zen-of-docs-server"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "zen-of-docs": {
      "command": "uvx",
      "args": ["--from", "mcp-zen-of-docs", "mcp-zen-of-docs-server"]
    }
  }
}
```

### One-Click (VS Code)

| Method | VS Code | VS Code Insiders |
|------|---------|------------------|
| **UVX** | [![Install](https://img.shields.io/badge/Install-007ACC?style=flat-square&logo=python&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D) | [![Install](https://img.shields.io/badge/Install-24bfa5?style=flat-square&logo=python&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D&quality=insiders) |
| **Docker** | [![Install](https://img.shields.io/badge/Install-007ACC?style=flat-square&logo=docker&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22--rm%22%2C%22-i%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-zen-of-docs%3Alatest%22%5D%7D) | [![Install](https://img.shields.io/badge/Install-24bfa5?style=flat-square&logo=docker&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22--rm%22%2C%22-i%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-zen-of-docs%3Alatest%22%5D%7D&quality=insiders) |

### Docker

```bash
# MCP server via Docker
docker run --rm -i ghcr.io/anselmoo/mcp-zen-of-docs:latest

# CLI via Docker
docker run --rm ghcr.io/anselmoo/mcp-zen-of-docs:latest mcp-zen-of-docs --help
```

## Documentation

Full documentation: **[anselmoo.github.io/mcp-zen-of-docs](https://anselmoo.github.io/mcp-zen-of-docs/)**

## Development

```bash
uv sync --group dev --group docs
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group docs zensical serve
```

## Contributing

See [Adding a Framework](https://anselmoo.github.io/mcp-zen-of-docs/contributing/adding-framework/) and [Development Guide](https://anselmoo.github.io/mcp-zen-of-docs/contributing/development/) to get started.

## License

[MIT](https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/LICENSE)

---

<p align="center">
  <img src="https://github.com/Anselmoo/mcp-zen-of-docs/blob/main/docs/assets/social-card.svg?raw=true" alt="mcp-zen-of-docs social card" width="100%"/>
</p>

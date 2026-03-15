---
title: Quickstart
description: Install mcp-zen-of-docs, connect it to your AI client, and run the first framework-aware workflow.
tags:
  - quickstart
  - installation
---

# Quickstart

**The problem:** a great answer can still fail if it uses the wrong docs syntax for the target framework.

`mcp-zen-of-docs` closes that gap by detecting the docs stack first, then resolving the native syntax the page actually needs.

<figure class="chapter-banner">
  <img src="../assets/chapters/quickstart-path.svg" alt="A calm quickstart illustration showing a path with milestones toward a sunrise." />
</figure>

---

## 1. Install

```bash
# Recommended zero-install MCP runtime
uvx --from mcp-zen-of-docs mcp-zen-of-docs-server

# Or run the published container
docker run --rm -i ghcr.io/anselmoo/mcp-zen-of-docs:latest
```

If you want the CLI instead of the MCP server:

```bash
uvx --from mcp-zen-of-docs mcp-zen-of-docs --help
```

### Quick installers for VS Code

| Method | VS Code | VS Code Insiders |
|------|---------|------------------|
| **UVX** | [![Install](https://img.shields.io/badge/Install-007ACC?style=flat-square&logo=python&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D) | [![Install](https://img.shields.io/badge/Install-24bfa5?style=flat-square&logo=python&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22mcp-zen-of-docs%22%2C%22mcp-zen-of-docs-server%22%5D%7D&quality=insiders) |
| **Docker** | [![Install](https://img.shields.io/badge/Install-007ACC?style=flat-square&logo=docker&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22--rm%22%2C%22-i%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-zen-of-docs%3Alatest%22%5D%7D) | [![Install](https://img.shields.io/badge/Install-24bfa5?style=flat-square&logo=docker&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=zen-of-docs&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22--rm%22%2C%22-i%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-zen-of-docs%3Alatest%22%5D%7D&quality=insiders) |

### Naming guide

- **Package name**: `mcp-zen-of-docs`
- **CLI command**: `mcp-zen-of-docs`
- **MCP server command**: `mcp-zen-of-docs-server`
- **MCP client server key**: `zen-of-docs`

---

## 2. Connect your AI client

### GitHub Copilot in VS Code

Add this to `.vscode/mcp.json`:

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

### GitHub Copilot CLI

Launch `copilot` in your docs repository, run `/mcp`, and register a server named `zen-of-docs` with:

- command: `uvx`
- args: `--from mcp-zen-of-docs mcp-zen-of-docs-server`

### Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop after saving the file.

### Cursor

Add this to `.cursor/mcp.json`:

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

---

## 3. Run the first real workflow

The most reliable pattern is:

```text
detect → profile → act
```

Start with a concrete request such as:

```text
Add a prerequisites note to the quickstart page.
```

A framework-aware assistant should then:

1. Call [`detect`](tools/detect.md) to identify the docs stack.
2. Call [`profile`](tools/profile.md) to resolve the primitive you need.
3. Use that result when it writes or updates the page.

If you want the full explanation of that pattern, read [Detect → Profile → Act](guides/detect-profile-act.md).

---

## 4. What good output looks like

A correct answer is not just well written. It also renders correctly in the target docs stack.

- Zensical should receive Zensical-compatible syntax.
- Docusaurus should receive Docusaurus-compatible syntax.
- VitePress and Starlight should receive their own native forms and caveats.

That is what `mcp-zen-of-docs` is designed to provide: source-truth context before content generation.

---

## First questions

**What if my config file lives in a subdirectory?**
Pass `project_root` explicitly to [`detect`](tools/detect.md), for example `project_root=./docs-site`.

**Can I use this with GitHub Copilot?**
Yes. Use `.vscode/mcp.json` for Copilot in VS Code, or `/mcp` in Copilot CLI, then use the [`copilot`](tools/copilot.md) tool to generate instruction assets.

**What should I read after setup?**
Start with the tool references for [`detect`](tools/detect.md) and [`profile`](tools/profile.md), then continue to [Troubleshooting](guides/troubleshooting.md) if the target project is unusual.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Tools overview**

    See all 10 tools and how they fit together.

    [:octicons-arrow-right-24: Browse tools](tools/index.md)

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    Learn the operating model behind the workflow.

    [:octicons-arrow-right-24: Read the guide](guides/detect-profile-act.md)

-   :octicons-arrow-right-24: **Troubleshooting**

    Handle unusual layouts, detection misses, and rendering issues.

    [:octicons-arrow-right-24: Read troubleshooting](guides/troubleshooting.md)

</div>

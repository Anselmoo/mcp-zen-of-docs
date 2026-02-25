---
title: Quickstart
description: Install mcp-zen-of-docs and connect it to your AI client in under two minutes.
tags:
  - quickstart
  - installation
---

# Quickstart

**The problem:** You ask an AI assistant to add a warning to your Docusaurus page. It writes
`!!! warning` — valid MkDocs syntax. Wrong framework. It renders as raw text.

mcp-zen-of-docs fixes this by detecting your framework first and generating native syntax every time.

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

This makes the server available to GitHub Copilot in your workspace.

### GitHub Copilot CLI

Launch `copilot` in your docs repository, run `/mcp`, and register a server named
`zen-of-docs` with:

- command: `uvx`
- args: `--from mcp-zen-of-docs mcp-zen-of-docs-server`

Then ask:

```text
Detect my docs framework.
```

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

Restart Claude Desktop. All 10 tools register automatically.

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

## 3. Ask your assistant to write a page

Open a conversation in your docs project and type:

```text
Add a prerequisites note to the quickstart page.
```

**Without this server** — your assistant guesses `!!! note` (MkDocs syntax).

**With this server:**

1. Your assistant calls `detect` → reads `docusaurus.config.js` → confirms Docusaurus 3.x
2. Your assistant calls `profile` → maps "note admonition" to the Docusaurus native form
3. Your assistant writes:

```markdown
:::note Prerequisites

Node.js 18+ and npm are required before continuing.

:::
```

The right syntax. First try.

---

## First questions

**Do I need to re-run `detect` each conversation?**
No. Detection is cached per session. A new conversation auto-detects on the first tool call.

**What if my config file is in a subdirectory?**
Pass `project_root` explicitly: `detect project_root=./my-docs-subdir`. See [troubleshooting](guides/troubleshooting.md).

**Can I use this with GitHub Copilot?**
Yes. Use `.vscode/mcp.json` for GitHub Copilot in VS Code, or `/mcp` in Copilot CLI to
register the server. Then use the [`copilot` tool](tools/copilot.md) to generate
`.instructions.md` files that encode your framework conventions.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Tools overview**

    See all 10 tools and what each one does.

    [:octicons-arrow-right-24: Browse tools](tools/index.md)

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    Why auto-detection produces correct output every time.

    [:octicons-arrow-right-24: Read the guide](guides/detect-profile-act.md)

</div>

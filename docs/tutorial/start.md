---
title: Tutorial
description: A compact hands-on walkthrough of the core Detect -> Profile -> Act workflow.
icon: material/file-document-outline
status: stable
hide:
  - navigation
---

# Tutorial

This mini tutorial shows the shortest useful workflow in the project: detect the framework,
resolve the correct authoring syntax, then generate or validate content with confidence.

## 1. Detect the framework

Ask your MCP client to inspect the project root first:

```text
Detect my docs framework.
```

That gives the server the context every other tool depends on.

## 2. Resolve the right syntax

Next, ask for the primitive profile you care about:

```text
Show me how this project handles admonitions, tabs, and diagrams.
```

Now the assistant knows which syntax is native, plugin-based, or unsupported.

## 3. Act on that context

Use the result to scaffold, enrich, or validate pages:

```text
Create a quickstart page with setup steps for GitHub Copilot, Claude Desktop, and Cursor.
```

## What to do after the tutorial

- Go to [Quickstart](../quickstart.md) for install instructions
- Go to [Tools](../tools/index.md) for the full command set
- Go to [Troubleshooting](../guides/troubleshooting.md) if detection fails

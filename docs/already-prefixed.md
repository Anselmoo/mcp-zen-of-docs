---
title: Prefixed
description: An internal example page used to confirm generated paths and prefixed content render cleanly.
icon: material/file-document-outline
status: stable
hide:
  - navigation
---

# Prefixed

This page is intentionally simple. It exists so the project can verify that generated documentation
with pre-prefixed paths still builds, routes, and renders correctly.

## Why keep it?

- it protects initialization and scaffolding flows in tests
- it gives the docs builder a stable fixture page
- it avoids shipping public `TODO` placeholders if the page is discovered directly

## If you were looking for user docs

- [Quickstart](quickstart.md)
- [Guides](guides/index.md)
- [Tools](tools/index.md)

Those pages are the maintained public entry points.

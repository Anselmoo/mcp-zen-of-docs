---
title: Contributing
description: How to contribute to mcp-zen-of-docs — from local setup to new framework and primitive support.
tags:
  - contributing
  - overview
---

# Contributing

Contributions are welcome. This page is the shortest route to the right contributor guide for the change you want to make.

<figure class="chapter-banner">
    <img src="../assets/chapters/contributing-workbench.svg" alt="A collaborative workbench illustration for the contributing chapter." />
</figure>

---

<div class="grid cards" markdown>

-   :material-code-braces: **Setting up locally**

    ---

    Install the dev environment, run checks, and understand the local workflow before you change behavior.

    [:octicons-arrow-right-24: Read development](development.md)

-   :material-plus-box: **Adding framework support**

    ---

    Implement the `AuthoringProfile` contract and register a new framework profile in the built-in registry.

    [:octicons-arrow-right-24: Read add a framework](adding-framework.md)

-   :material-puzzle-plus: **Adding a primitive**

    ---

    Extend the 22 canonical authoring primitives and teach each primary profile how to support or reject it deliberately.

    [:octicons-arrow-right-24: Read add a primitive](adding-primitive.md)

</div>

---

## Before you edit

Use the source of truth in the codebase when contributor docs and memory disagree.

- `src/mcp_zen_of_docs/frameworks/base.py` defines the `AuthoringProfile` contract.
- `src/mcp_zen_of_docs/domain/contracts.py` defines `FrameworkName`, `AuthoringPrimitive`, and `SupportLevel`.
- `src/mcp_zen_of_docs/frameworks/__init__.py` wires the built-in profiles and registration flow.

## Recommended contribution flow

1. Read the most specific contributor guide for the change.
2. Make the code and docs changes together.
3. Run the relevant existing checks before you open a PR.
4. Keep the Zen of Documentation principles in mind: clarity, structure, and correctness first.

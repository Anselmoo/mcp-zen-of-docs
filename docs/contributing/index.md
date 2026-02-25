---
title: Contributing
description: How to contribute to mcp-zen-of-docs — bug fixes, new frameworks, and new primitives.
tags:
  - contributing
  - overview
---

# Contributing

Contributions are welcome. This page is the shortest path to shipping a useful change.

Start with the development guide if you're setting up the project locally. If you're extending
the server, go straight to the framework or primitive guides and follow the existing patterns.

<figure class="chapter-banner">
    <img src="../assets/chapters/contributing-workbench.svg" alt="A collaborative workbench illustration for the contributing chapter." />
</figure>

---

<div class="grid cards" markdown>

-   :material-code-braces: **Development**

    ---

    Set up the dev environment, run tests, and submit a PR.

    [:octicons-arrow-right-24: Read](development.md)

-   :material-plus-box: **Add a Framework**

    ---

    Implement the `AuthoringProfile` ABC for a new docs framework.

    [:octicons-arrow-right-24: Read](adding-framework.md)

-   :material-puzzle-plus: **Add a Primitive**

    ---

    Extend the 16 primitives with a new universal authoring concept.

    [:octicons-arrow-right-24: Read](adding-primitive.md)

</div>

---

## Guiding principle

A contribution that makes docs generation more reliable for one framework is worth more
than one that adds a feature nobody asked for. Correctness first. Features second.

## Recommended contribution flow

1. Read the relevant guide.
2. Run the local quality checks before you open a PR.
3. Add or update docs when the behavior changes.
4. Keep the Zen of Documentation principles in mind: clarity, structure, and correctness first.

---
title: Frameworks
description: Compare the four primary framework profiles and the supplemental contexts that mcp-zen-of-docs can detect automatically.
tags:
  - frameworks
  - overview
  - support-matrix
---

# Frameworks

One MCP server, four primary authoring profiles, and several supplemental detected contexts.

`mcp-zen-of-docs` reads the project first, then adapts its output to the framework it finds. This page is the editorial compatibility map; [`profile`](../tools/profile.md) remains the source of truth when you need exact support levels or rendered snippets.

<figure class="chapter-banner">
    <img src="../assets/chapters/frameworks-bridge.svg" alt="An illustration showing four framework islands connected by a shared bridge." />
</figure>

---

## How detection works

`detect` looks for framework signals in priority order and returns the strongest match.

| Signal | Framework/context | Notes |
|---|---|---|
| `zensical.toml`, `zensical.yml`, `zensical.yaml`, `.zensical/config.yml` | Zensical | Highest-confidence profile match |
| `mkdocs.yml` / `mkdocs.yaml` with Material/Zensical cues | MkDocs Material / Zensical-adjacent context | Supplemental or compatibility detection |
| `docusaurus.config.ts` / `.js` / `.mjs` / `.cjs` | Docusaurus | Direct framework signal |
| `.vitepress/config.ts` / `.js` / `.mjs` | VitePress | Direct framework signal |
| `astro.config.mjs` / `.ts` / `.js` | Starlight | Direct framework signal |
| `package.json` dependency hints | Docusaurus / VitePress / Starlight | Used as supporting evidence |
| `conf.py` or common Sphinx layouts | Sphinx | Supplemental detected context |
| `docs/**/*.md` with no stronger signal | Generic Markdown | Fallback context |

When multiple signals match, the highest-confidence result wins.

---

## Admonitions: the most visible syntax difference

This is usually the first place framework drift shows up.

| Framework | Current built-in snippet shape |
|---|---|
| Zensical | `!!! note` |
| Docusaurus | `:::note` |
| VitePress | `::: info` |
| Starlight | `:::tip` (currently documented as partial support in the built-in profile) |

Use [`profile`](../tools/profile.md) with `mode="resolve"` and `resolution_mode="render"` when you need the exact current snippet.

---

## Primary authoring profiles

| | Zensical | Docusaurus | VitePress | Starlight |
|--|:---:|:---:|:---:|:---:|
| Config surface | `zensical.*`, `.zensical/config.yml`, compatible MkDocs signals | `docusaurus.config.*` | `.vitepress/config.*` | `astro.config.*` |
| Base stack | Python / MkDocs-oriented | React / MDX | Vite / Vue | Astro |
| Strength | Markdown-first authoring depth | App-adjacent docs and MDX | Fast Vue-native docs | Astro ecosystem and content collections |
| Best fit | Python-heavy docs workflows | React product docs | Vue/Vite docs sites | Astro sites with docs as a core content area |

---

## Support levels in practice

The built-in profiles classify primitives with four support levels:

- **Full** — native and complete support
- **Partial** — works with caveats or reduced parity
- **Experimental** — available but not yet a stable default
- **Unsupported** — not currently supported by the profile

That language is more precise than a simple yes/no or plugin/custom badge. Use it whenever you are deciding whether to scaffold, translate, or hand-author a construct.

---

## Supplemental detected contexts

These contexts are part of the detection surface, but they do not currently have the same authored profile depth as the four primary frameworks above.

| Context | What the server can do today |
|---|---|
| MkDocs Material | Detect config and infer a useful Markdown-first primitive subset |
| Sphinx | Detect common signals and return a narrower compatibility surface |
| Generic Markdown | Fall back to a plain Markdown context when no stronger framework match exists |

---

## Common questions

**Which framework should I choose for a new project?**
Choose the framework that fits the surrounding stack. Then use `detect` and `profile` to make the syntax rules explicit for the AI workflow.

**Which page is authoritative when the editorial summary and runtime behavior differ?**
[`profile`](../tools/profile.md) is the source of truth for the current built-in support matrix and rendered snippets.

**Where should I learn the primitive model itself?**
Start with [Authoring Primitives](../guides/primitives.md), then read [Detect → Profile → Act](../guides/detect-profile-act.md).

---

## What's next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **profile**

    Query the live support matrix and render native snippets.

    [:octicons-arrow-right-24: Read profile](../tools/profile.md)

-   :octicons-arrow-right-24: **Authoring Primitives**

    Learn the 22 canonical constructs the profiles reason about.

    [:octicons-arrow-right-24: Read primitives](../guides/primitives.md)

</div>

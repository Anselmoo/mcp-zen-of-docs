---
title: Frameworks
description: Compare the four primary framework profiles, plus the supplemental contexts that mcp-zen-of-docs can detect automatically.
tags:
  - frameworks
  - overview
  - support-matrix
---

# Frameworks

One MCP server, four primary authoring profiles, and three supplemental detected contexts — it
detects yours automatically. Every tool reads your config files first, identifies the framework
or fallback context, then emits syntax that works in your project. You rarely need to specify
`framework=` explicitly.

This page is the compatibility map. Use it when you want to understand what is native,
what needs a plugin, and which trade-offs matter before you scaffold or migrate docs.

<figure class="chapter-banner">
    <img src="../assets/chapters/frameworks-bridge.svg" alt="An illustration showing four framework islands connected by a shared bridge." />
</figure>

---

## How detection works

`detect` scans for config file fingerprints in priority order:

| Config file or signal | Framework/context | Notes |
|---|---|---|
| `zensical.toml` | Zensical | Full confidence — exact match |
| `zensical.yml` / `zensical.yaml` | Zensical | High confidence |
| `mkdocs.yml` / `mkdocs.yaml` with `theme: material` | MkDocs Material | Supplemental detected context |
| `docusaurus.config.ts` / `.js` / `.mjs` / `.cjs` | Docusaurus | High confidence |
| `.vitepress/config.ts` / `.js` / `.mjs` | VitePress | High confidence |
| `astro.config.mjs` / `.ts` / `.js` | Starlight | High confidence |
| `package.json:@docusaurus/core` | Docusaurus | Medium — used as secondary signal |
| `package.json:vitepress` | VitePress | Medium — used as secondary signal |
| `package.json:@astrojs/starlight` | Starlight | Medium — used as secondary signal |
| `conf.py` / `docs/conf.py` / Sphinx deps | Sphinx | Supplemental detected context |
| `docs/**/*.md` with no stronger match | Generic Markdown | Fallback context for plain Markdown projects |

When multiple signals match, the highest-confidence result wins.

---

## Admonition syntax — the most visible difference

This is the primitive that looks most different across frameworks. `scaffold` and `story` emit the correct variant automatically.

| Framework | Syntax |
|---|---|
| Zensical | `!!! note "Title"` |
| Docusaurus | `:::note Title` … `:::` |
| VitePress | `::: info Title` … `:::` |
| Starlight | `<Aside type="note" title="Title">…</Aside>` (`.mdx` files only) |

---

## Primary authoring profiles

| | Zensical | Docusaurus | VitePress | Starlight |
|--|:---:|:---:|:---:|:---:|
| Config file | `zensical.toml` | `docusaurus.config.js` | `.vitepress/config.*` | `astro.config.*` |
| Language | Python | JS / TS | JS / TS | JS / TS |
| Base | MkDocs + Material | React | Vue | Astro |
| MDX support | — | ✓ | — | ✓ |
| Native Mermaid | ✓ | plugin | ✓ | plugin |
| Native math | plugin | plugin | ✓ | plugin |
| Component syntax | Markdown attrs | JSX / MDX | Vue containers | Astro MDX |

---

## Supplemental detected contexts

These contexts are part of the source-truth detection surface, but they do not currently have the
same authored profile depth as the four primary frameworks above.

| Context | What the server can do today |
|---|---|
| MkDocs Material | Detect config and infer a useful partial primitive set for Markdown-first docs projects |
| Sphinx | Detect common config/dependency signals and report a narrower partial primitive set |
| Generic Markdown | Fallback detection for plain `docs/**/*.md` projects without a stronger framework match |

---

## Common authoring patterns across the four primary profiles

This is a reader-friendly summary of the most commonly compared constructs. Use `profile` for the
exact, code-backed support matrix and the full list of 22 canonical primitive identifiers.

| Pattern | Zensical | Docusaurus | VitePress | Starlight |
|---|---|---|---|---|
| `admonition` | Native | Native | Native | Native |
| `button` | Native | Component/custom | Component/custom | Component/custom |
| `code-fence` | Native | Native | Native | Native |
| `tabs` | Native | Component/plugin | Native | Component |
| `diagram` | Native | Plugin | Native | Plugin |
| `footnote` | Native | Plugin/custom | Native | Mixed/custom |
| `math` | Plugin/native extension path | Plugin | Native | Plugin |
| `card-grid` | Native | Component/custom | Component/custom | Component/custom |
| `tooltip` | Native | Native browser/component patterns | Custom/component | Native component patterns |

---

## Which framework should I use?

| I want to… | Use |
|---|---|
| Start a new Python-based docs site | **Zensical** — deepest native primitive support, zero JS toolchain |
| Build docs alongside a React app | **Docusaurus** — MDX, versioning, i18n out of the box |
| Embed docs into a Vue/Vite project | **VitePress** — native Vue components, fast builds |
| Build docs alongside an Astro site | **Starlight** — Astro components, content collections |

!!! note "Already have a project?"
    Run `detect` — mcp-zen-of-docs identifies your framework from existing config files. No choice needed.

---

## What's Next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Zensical**

    The default framework — deepest authoring support among the primary profiles.

    [:octicons-arrow-right-24: Read more](zensical.md)

-   :octicons-arrow-right-24: **Authoring Primitives**

    What each primitive means and how it maps across frameworks.

    [:octicons-arrow-right-24: Read more](../guides/primitives.md)

</div>

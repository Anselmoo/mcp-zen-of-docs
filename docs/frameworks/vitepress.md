---
title: VitePress
description: Using mcp-zen-of-docs with VitePress — a Vue-powered static site generator with built-in math and Mermaid.
tags:
  - frameworks
  - vitepress
---

# VitePress

VitePress is Vue-powered, built on Vite, and ships with the lowest plugin footprint of the four frameworks. Math (KaTeX) and Mermaid diagrams work without plugins.

**Use VitePress when** you want fast builds, minimal config, and a Markdown-first workflow without React or Python.

---

## Detection

`detect` identifies VitePress from these signals:

| Signal | Confidence |
|---|:---:|
| `.vitepress/config.ts` / `.js` / `.mjs` | High |
| `package.json` containing `vitepress` | Medium |

---

## Key primitives

**Admonitions** — called "custom containers":

```markdown
::: info Title
Content here.
:::

::: warning
No title variant.
:::

::: danger Stop
Destructive action.
:::

::: details Click to expand
Hidden content.
:::
```

**Code groups** — VitePress's native tab syntax (no import needed):

````markdown
::: code-group

```js [config.js]
export default { ... }
```

```ts [config.ts]
export default defineConfig({ ... })
```

:::
````

**Code block highlights** — VitePress uses Shiki; line-level attrs use special comments:

```python
def hello():  # [!code highlight]
    return "world"
```

Shiki-specific modifiers: `# [!code focus]`, `# [!code --]`, `# [!code ++]`. These are VitePress-only — they have no effect in other frameworks.

!!! note "Shiki vs highlight.js"
    VitePress uses Shiki for syntax highlighting. Code block language IDs are resolved against Shiki's grammar registry — a few obscure languages may need explicit Shiki packages that other frameworks don't require.

---

## Recommended config

```ts
// .vitepress/config.mts
import { defineConfig } from 'vitepress'

export default defineConfig({
  markdown: {
    math: true,         // enables KaTeX for $…$ and $$…$$
    lineNumbers: true,
  },
  themeConfig: {
    search: { provider: 'local' },
  },
})
```

Use the `theme` tool to generate a config block for your enabled primitives.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Starlight**

    See how primitives work in an Astro-based framework.

    [:octicons-arrow-right-24: Read more](starlight.md)

</div>

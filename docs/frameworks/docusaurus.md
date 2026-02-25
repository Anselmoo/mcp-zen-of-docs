---
title: Docusaurus
description: Using mcp-zen-of-docs with Docusaurus — a React/MDX framework with versioned docs and a mature plugin ecosystem.
tags:
  - frameworks
  - docusaurus
---

# Docusaurus

Docusaurus is a React-based static site generator from Meta. Primitives are a mix of native Markdown directives and imported React components via MDX.

**Use Docusaurus when** you need versioned docs, a rich plugin ecosystem, or an established React/TypeScript workflow.

---

## Detection

`detect` identifies Docusaurus from these signals:

| Signal | Confidence |
|---|:---:|
| `docusaurus.config.ts` / `.js` / `.mjs` / `.cjs` in root | High |
| `package.json` containing `@docusaurus/core` | Medium |

---

## Key primitives

**Admonitions** — native Markdown, no import needed:

```markdown
:::note Title
Content here.
:::

:::warning
No title variant.
:::

:::danger Stop
Destructive action.
:::
```

!!! note "Syntax distinction"
    Docusaurus uses `:::` — not `!!!`. The `!!! note` syntax belongs to MkDocs/Zensical only.

**Content tabs** — requires MDX and explicit import at top of each `.mdx` file:

```mdx
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
  <TabItem value="js" label="JavaScript">

    ```js
    console.log('hello');
    ```

  </TabItem>
  <TabItem value="py" label="Python">

    ```python
    print('hello')
    ```

  </TabItem>
</Tabs>
```

**Mermaid diagrams** — requires `@docusaurus/theme-mermaid`:

```js
// docusaurus.config.js
module.exports = {
  markdown: { mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],
};
```

Then use ` ```mermaid ` fences as normal.

!!! note "MDX for components"
    `Tabs`, `TabItem`, and other React components only work in `.mdx` files — not plain `.md`. `mcp-zen-of-docs` emits `.mdx` extensions and prepends the correct import block automatically when it detects Docusaurus.

---

## Recommended config

```js
// docusaurus.config.js
module.exports = {
  markdown: { mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],
  presets: [
    [
      'classic',
      {
        docs: {
          remarkPlugins: [require('remark-math')],
          rehypePlugins: [require('rehype-katex')],
        },
      },
    ],
  ],
};
```

Use the `theme` tool to generate a config block tailored to your enabled primitives.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **VitePress**

    See how the same primitives look in a Vue-based framework.

    [:octicons-arrow-right-24: Read more](vitepress.md)

</div>

---
title: Starlight
description: Using mcp-zen-of-docs with Starlight — an Astro-based documentation framework with composable MDX components.
tags:
  - frameworks
  - starlight
---

# Starlight

Starlight is a documentation framework built on Astro. Primitives are Astro/MDX components — not Markdown syntax — and require explicit imports in each file. `mcp-zen-of-docs` handles those imports automatically.

**Use Starlight when** you want a composable component model, built-in i18n, or a modern Jamstack workflow with Astro's island architecture.

---

## Detection

`detect` identifies Starlight from these signals:

| Signal | Confidence |
|---|:---:|
| `astro.config.mjs` / `.ts` / `.js` in root | High |
| `package.json` containing `@astrojs/starlight` | Medium |

Detection is confirmed by finding `@astrojs/starlight` in the config's integrations array.

---

## Key primitives

All components must be imported at the top of `.mdx` files.

**Asides (admonitions)**:

```mdx
import { Aside } from '@astrojs/starlight/components';

<Aside type="note" title="Title">
  Content here.
</Aside>

<Aside type="caution">
  No title variant.
</Aside>

<Aside type="danger" />
```

Types: `note` · `tip` · `caution` · `danger`

**Tabs**:

```mdx
import { Tabs, TabItem } from '@astrojs/starlight/components';

<Tabs>
  <TabItem label="JavaScript">

    ```js
    console.log('hello');
    ```

  </TabItem>
  <TabItem label="Python">

    ```python
    print('hello')
    ```

  </TabItem>
</Tabs>
```

**Link buttons**:

```mdx
import { LinkButton } from '@astrojs/starlight/components';

<LinkButton href="/docs/start" variant="primary">Get started</LinkButton>
<LinkButton href="/docs/api" variant="secondary">API reference</LinkButton>
```

---

## Auto-imports

`mcp-zen-of-docs` detects which Starlight components a page uses and prepends the correct import block. You never write imports manually — `scaffold` and `story` emit `.mdx` files with all imports in place.

---

## Recommended config

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightMermaid from 'starlight-mermaid';

export default defineConfig({
  integrations: [
    starlight({
      title: 'My Docs',
      plugins: [starlightMermaid()],
      customCss: ['./src/styles/custom.css'],
    }),
  ],
});
```

Use the `theme` tool to generate a custom CSS file with brand colours for Starlight.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Frameworks overview**

    Compare all four frameworks side-by-side.

    [:octicons-arrow-right-24: Back to overview](index.md)

</div>

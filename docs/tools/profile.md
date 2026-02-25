---
title: profile
description: Query framework authoring profiles and resolve native syntax snippets for any documentation primitive.
tags:
  - tools
  - profile
---

# profile

> Queries what a framework supports and returns the exact native syntax for any documentation primitive.

Once you know the framework, you need to know how it handles your specific primitive. `profile` answers: *"How do I write an admonition — or a tab, or a grid — in this framework?"* It returns the correct syntax, flags what needs a plugin, and marks what is unsupported.

---

## Modes

| Mode | What it returns |
|------|----------------|
| `show` | Full support matrix across all frameworks (default) |
| `resolve` | Native syntax snippet for a `framework` + `primitive` pair |
| `translate` | A primitive rewritten in a different framework's syntax |

---

## When to use it

Run `profile` after `detect` before writing any framework-specific markup. Use `mode="translate"` when migrating docs from one framework to another and you need before/after syntax for every primitive.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Operation mode. Default: `"show"` |
| `framework` | string | Conditional | Target framework. Required for `resolve` and as source for `translate` |
| `primitive` | string | Conditional | Primitive name. Required for `resolve` |
| `source_framework` | string | Conditional | Source framework for `translate` mode |
| `target_framework` | string | Conditional | Target framework for `translate` mode |
| `topic` | string | No | Topic hint to make generated snippets more contextual |
| `resolution_mode` | string | No | Fine-tuned resolution behaviour |

---

## Support matrix

| Primitive | Zensical | Docusaurus | VitePress | Starlight |
|-----------|:--------:|:----------:|:---------:|:---------:|
| `admonitions` | native | native | native | native |
| `buttons` | native | custom | custom | custom |
| `code_blocks` | native | native | native | native |
| `content_tabs` | native | plugin | plugin | native |
| `data_tables` | native | native | native | native |
| `diagrams` | native | plugin | plugin | plugin |
| `footnotes` | native | native | native | native |
| `formatting` | native | native | native | native |
| `frontmatter` | native | native | native | native |
| `grids` | native | custom | unsupported | unsupported |
| `icons_emojis` | native | plugin | plugin | native |
| `images` | native | native | native | native |
| `lists` | native | native | native | native |
| `math` | native | plugin | native | plugin |
| `markdown` | native | native | native | native |
| `tooltips` | native | unsupported | unsupported | unsupported |

See [Authoring Primitives](../guides/primitives.md) for per-framework notes and plugin links.

---

## Examples

**Resolve admonition syntax (`mode="resolve"`)**

=== "Zensical"

    ```json
    {
      "tool": "profile",
      "arguments": { "mode": "resolve", "framework": "zensical", "primitive": "admonitions" }
    }
    ```

    Returns:

    ```markdown
    !!! warning "Watch out"
        This action cannot be undone. Make a backup first.
    ```

=== "Docusaurus"

    ```json
    {
      "tool": "profile",
      "arguments": { "mode": "resolve", "framework": "docusaurus", "primitive": "admonitions" }
    }
    ```

    Returns:

    ```markdown
    :::warning Watch out
    This action cannot be undone. Make a backup first.
    :::
    ```

VitePress uses the same `:::` fence style as Docusaurus. Starlight uses an `<Aside>` JSX component — call `resolve` with `framework="starlight"` to get the exact import statement.

---

**Resolve content tab syntax for Zensical**

```json
{
  "tool": "profile",
  "arguments": { "mode": "resolve", "framework": "zensical", "primitive": "content_tabs" }
}
```

Returns:

```markdown
=== "Python"

    ```python
    print('hello')
    ```

=== "JavaScript"

    ```js
    console.log('hello')
    ```
```

---

**Translate content tabs from Zensical to Docusaurus**

```json
{
  "tool": "profile",
  "arguments": {
    "mode": "translate",
    "primitive": "content_tabs",
    "source_framework": "zensical",
    "target_framework": "docusaurus"
  }
}
```

Returns:

```json
{
  "source_framework": "zensical",
  "target_framework": "docusaurus",
  "primitive": "content_tabs",
  "target_snippet": "import Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n\n<Tabs>\n  <TabItem value=\"python\" label=\"Python\">\n  ```python\n  print('hello')\n  ```\n  </TabItem>\n</Tabs>",
  "notes": "Docusaurus content tabs require JSX imports. Use .mdx file extensions."
}
```

!!! note "MDX required for Docusaurus tabs"
    Docusaurus content tabs use JSX components and require `.mdx` file extensions.
    The `translate` response includes a `notes` field for exactly these caveats.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **scaffold**

    Use the syntax profile resolves to build complete, framework-native pages.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

-   :octicons-arrow-right-24: **Authoring Primitives**

    Full notes on all 16 primitives with per-framework caveats and plugin links.

    [:octicons-arrow-right-24: Read the guide](../guides/primitives.md)

</div>

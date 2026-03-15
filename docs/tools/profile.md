---
title: profile
description: Query framework authoring profiles and resolve native syntax snippets for any documentation primitive.
tags:
  - tools
  - profile
---

# profile

> Query primitive support across frameworks, or render the native syntax for one specific
> primitive when you are ready to write.

`profile` is the tool that turns framework detection into actionable writing guidance. Use it
to answer questions like:

- *Does this framework support `tabs` natively?*
- *What snippet should I use for an `admonition` here?*
- *How does `card-grid` differ between two frameworks?*

---

## Modes

| Mode | What it returns |
|------|----------------|
| `show` | Primitive catalog, capability matrix, framework advantages, and general references |
| `resolve` | Support information for one `framework` + `primitive` pair, with optional rendered snippet |
| `translate` | Source and target support levels, snippets, and migration hints for one primitive |

---

## When to use it

Run `profile` after [detect](detect.md) and before any framework-specific edit. It is the
bridge between *knowing the framework* and *writing valid syntax for that framework*.

---

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | No | Operation mode. Default: `"show"` |
| `framework` | string | Conditional | Target framework for `resolve` |
| `primitive` | string | Conditional | Canonical primitive identifier for `resolve` or `translate` |
| `source_framework` | string | Conditional | Source framework for `translate` |
| `target_framework` | string | Conditional | Target framework for `translate` |
| `resolution_mode` | string | No | `"support"` (default) or `"render"` for `resolve` |
| `topic` | string | No | Optional context that helps make rendered snippets more relevant |

---

## Common primitives at a glance

The full primitive vocabulary contains **22 canonical identifiers**. These are the ones most
often compared during day-to-day writing.

| Primitive | Zensical | Docusaurus | VitePress | Starlight |
|-----------|:--------:|:----------:|:---------:|:---------:|
| `admonition` | full | full | full | partial |
| `tabs` | full | partial | full | partial |
| `diagram` | full | partial | partial | partial |
| `footnote` | full | partial | partial | partial |
| `card-grid` | full | unsupported | unsupported | unsupported |
| `button` | full | unsupported | unsupported | unsupported |
| `tooltip` | full | unsupported | unsupported | unsupported |
| `math` | full | unsupported | unsupported | unsupported |

For the full primitive list, see [Authoring Primitives](../guides/primitives.md).

---

## Examples

### Show the full profile catalog (`mode="show"`)

```json
{
  "tool": "profile",
  "arguments": {
    "mode": "show"
  }
}
```

The response includes these top-level sections:

- `primitive_catalog`
- `capability_matrix`
- `framework_advantages`
- `general_references`

Use `show` when you want the broad map before narrowing to a single primitive.

---

### Resolve support only (`resolution_mode="support"`)

```json
{
  "tool": "profile",
  "arguments": {
    "mode": "resolve",
    "framework": "docusaurus",
    "primitive": "tabs"
  }
}
```

Response shape:

```json
{
  "status": "success",
  "tool": "resolve_primitive",
  "framework": "docusaurus",
  "primitive": "tabs",
  "mode": "support",
  "support_lookup": {
    "tool": "lookup_primitive_support",
    "support_level": "partial"
  },
  "render_result": null
}
```

---

### Resolve a rendered snippet (`resolution_mode="render"`)

```json
{
  "tool": "profile",
  "arguments": {
    "mode": "resolve",
    "framework": "zensical",
    "primitive": "admonition",
    "resolution_mode": "render",
    "topic": "Prerequisites"
  }
}
```

Response shape:

```json
{
  "status": "success",
  "tool": "resolve_primitive",
  "framework": "zensical",
  "primitive": "admonition",
  "mode": "render",
  "support_lookup": {
    "support_level": "full"
  },
  "render_result": {
    "tool": "render_framework_primitive",
    "support_level": "full",
    "snippet": "!!! note\n    Keep this page concise and actionable."
  }
}
```

Use `render` when the assistant is about to write or revise content and needs the actual
framework-native snippet.

---

### Translate one primitive across frameworks

```json
{
  "tool": "profile",
  "arguments": {
    "mode": "translate",
    "source_framework": "zensical",
    "target_framework": "docusaurus",
    "primitive": "admonition",
    "topic": "Prerequisites"
  }
}
```

Response shape:

```json
{
  "status": "success",
  "tool": "translate_primitives",
  "translation": {
    "primitive": "admonition",
    "source_support_level": "full",
    "target_support_level": "full",
    "source_snippet": "!!! note\n    Keep this page concise and actionable.",
    "target_snippet": ":::note\nUse MDX directives for callouts.\n:::",
    "hints": [
      "Replace source syntax with target syntax shown in the target snippet.",
      "Convert MkDocs-style admonitions to Docusaurus directives."
    ]
  }
}
```

`translate` is most useful during migrations, framework comparisons, and review work.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **scaffold**

    Use the support or snippet `profile` returns to create or enrich whole pages.

    [:octicons-arrow-right-24: Read scaffold](scaffold.md)

-   :octicons-arrow-right-24: **Authoring Primitives**

    Read the canonical 22-primitive vocabulary and framework-specific notes.

    [:octicons-arrow-right-24: Read the guide](../guides/primitives.md)

-   :octicons-arrow-right-24: **Frameworks**

    Compare the overall trade-offs between the primary profiles.

    [:octicons-arrow-right-24: Compare frameworks](../frameworks/index.md)

</div>

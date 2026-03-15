---
title: Add a Primitive
description: How to extend the 22 canonical authoring primitives with a new documentation concept.
tags:
  - contributing
  - primitives
---

# Add a Primitive

The 22 canonical primitives are the vocabulary that `profile`, `scaffold`, `story`, and related tools reason about. Adding a new primitive means updating the shared contract and then teaching each primary profile how to support or reject it deliberately.

---

## 1. Add the primitive to the domain contract

Update `AuthoringPrimitive` in `src/mcp_zen_of_docs/domain/contracts.py`.

```python
class AuthoringPrimitive(StrEnum):
    ...
    MY_PRIMITIVE = "my-primitive"
```

Use the existing naming style: lowercase, hyphenated identifiers that describe the construct rather than a framework-specific syntax.

---

## 2. Update every framework profile

Every built-in profile must handle the new primitive in `primitive_support()`.

```python
def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
    if primitive is AuthoringPrimitive.MY_PRIMITIVE:
        return SupportLevel.FULL
    ...
```

If the framework can render it, add the corresponding branch or snippet in `render_snippet()`. If it cannot, return `SupportLevel.UNSUPPORTED` intentionally — do not leave the primitive unmapped.

---

## 3. Decide the support level explicitly

Choose one of the existing support levels from `SupportLevel`:

- `full`
- `partial`
- `experimental`
- `unsupported`

The classification should reflect real authoring behavior, not wishful compatibility.

---

## 4. Update docs and translation surfaces

A new primitive changes both the runtime model and the public documentation.

Update at least:

- `docs/guides/primitives.md`
- `docs/tools/profile.md`
- any examples or workflow guides that reference the primitive set

If the new primitive affects translation guidance, update the relevant framework notes and migration examples too.

---

## 5. Write tests

Add or update tests so the new primitive is covered end to end.

Recommended checks:

- every primary profile handles the primitive in `primitive_support()`
- supported frameworks render a valid snippet in `render_snippet()`
- `profile` output reflects the new primitive correctly
- any generation or validation workflows touched by the primitive still behave as expected

---

## 6. Review the contributor-facing language

Primitive names appear in guides, tool references, tests, and contributor docs. Make sure the wording stays consistent everywhere — especially around the total primitive count and the support-level terminology.

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Authoring Primitives**

    See how the current primitive vocabulary is described publicly.

    [:octicons-arrow-right-24: Read the guide](../guides/primitives.md)

-   :octicons-arrow-right-24: **Add a Framework**

    Extend the framework layer if the primitive requires new profile work.

    [:octicons-arrow-right-24: Read more](adding-framework.md)

</div>

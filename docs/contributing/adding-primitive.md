---
title: Add a Primitive
description: How to extend the 16 authoring primitives with a new universal documentation concept.
tags:
  - contributing
  - primitives
---

# Add a Primitive

The 16 primitives are the vocabulary of `profile`, `scaffold`, and `story`. Adding a new
one means adding it to the vocabulary and teaching every framework profile how to render it.

---

## 1. Add to AuthoringPrimitive

In `src/mcp_zen_of_docs/models.py`:

```python
class AuthoringPrimitive(StrEnum):
    MARKDOWN = "markdown"
    # ... existing 16 ...
    MY_PRIMITIVE = "my_primitive"  # add here
```

---

## 2. Add to every framework profile

Every profile's `support_matrix()` must map the new primitive to a `SupportLevel`. If the
framework doesn't support it, use `SupportLevel.UNSUPPORTED` — never omit it.

```python
def support_matrix(self) -> dict[AuthoringPrimitive, SupportLevel]:
    return {
        # ... existing mappings ...
        AuthoringPrimitive.MY_PRIMITIVE: SupportLevel.NATIVE,
    }
```

---

## 3. Add rendering to each profile

In each profile's `render_primitive()`, add a case:

```python
def render_primitive(self, primitive: AuthoringPrimitive, **kwargs: object) -> str:
    match primitive:
        # ... existing cases ...
        case AuthoringPrimitive.MY_PRIMITIVE:
            return "<!-- my primitive syntax -->"
        case _:
            return super().render_primitive(primitive, **kwargs)
```

---

## 4. Update the guides

Add the new primitive to the [Authoring Primitives](../guides/primitives.md) page with:

- A one-line description
- The syntax for each framework that supports it natively

---

## 5. Write tests

Test that:

- All four profiles map `MY_PRIMITIVE` in `support_matrix()`
- `render_primitive(AuthoringPrimitive.MY_PRIMITIVE)` returns valid syntax for native profiles
- `profile show` includes the new primitive in its output

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Authoring Primitives**

    How the 16 primitives are used across scaffold, story, and profile.

    [:octicons-arrow-right-24: Read the guide](../guides/primitives.md)

-   :octicons-arrow-right-24: **Add a Framework**

    Add an entirely new docs framework to the support matrix.

    [:octicons-arrow-right-24: Read the guide](adding-framework.md)

</div>

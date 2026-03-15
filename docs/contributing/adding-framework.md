---
title: Add a Framework
description: How to implement the AuthoringProfile contract for a new documentation framework.
tags:
  - contributing
  - frameworks
---

# Add a Framework

Adding a framework means implementing the `AuthoringProfile` contract and registering the new profile with the built-in framework registry.

The source of truth for the contract lives in `src/mcp_zen_of_docs/frameworks/base.py`.

---

## 1. Create the profile module

```bash
touch src/mcp_zen_of_docs/frameworks/myframework_profile.py
```

Use one of the existing profile implementations as a template:

- `zensical_profile.py`
- `docusaurus_profile.py`
- `vitepress_profile.py`
- `starlight_profile.py`

---

## 2. Implement the AuthoringProfile contract

A profile must provide:

- a `framework` property
- `detect(project_root)`
- `render_snippet(primitive, *, topic=None)`
- `validate(content, *, file_path=None)`
- `primitive_support(primitive)`

```python
from __future__ import annotations

from pathlib import Path

from mcp_zen_of_docs.domain.contracts import AuthoringPrimitive, FrameworkName, SupportLevel
from mcp_zen_of_docs.frameworks.base import AuthoringProfile
from mcp_zen_of_docs.models import FrameworkDetectionResult, StructureIssue


class MyFrameworkProfile(AuthoringProfile):
    @property
    def framework(self) -> FrameworkName:
        return FrameworkName.MY_FRAMEWORK

    def detect(self, project_root: Path) -> FrameworkDetectionResult:
        # Return a FrameworkDetectionResult with confidence, matched signals,
        # and authoring_primitives when your framework is detected.
        ...

    def render_snippet(
        self, primitive: AuthoringPrimitive, *, topic: str | None = None
    ) -> str | None:
        if primitive is AuthoringPrimitive.ADMONITION:
            return ":::note\nFramework-native callout example.\n:::\n"
        return None

    def validate(self, content: str, *, file_path: str | None = None) -> list[StructureIssue]:
        return []

    def primitive_support(self, primitive: AuthoringPrimitive) -> SupportLevel:
        if primitive is AuthoringPrimitive.ADMONITION:
            return SupportLevel.FULL
        return SupportLevel.UNSUPPORTED
```

`AuthoringProfile.__init__()` verifies that `primitive_support()` handles every `AuthoringPrimitive` value, so make the implementation exhaustive.

---

## 3. Register the profile

Add the new profile instance to `BUILTIN_PROFILES` in `src/mcp_zen_of_docs/frameworks/__init__.py`, then ensure `register_builtin_profiles()` includes it via the built-in tuple.

```python
from .myframework_profile import MyFrameworkProfile

BUILTIN_PROFILES = (
    ZensicalProfile(),
    DocusaurusProfile(),
    VitePressProfile(),
    StarlightProfile(),
    MyFrameworkProfile(),
)
```

---

## 4. Add the framework identifier

Add the enum value to `FrameworkName` in `src/mcp_zen_of_docs/domain/contracts.py`.

```python
class FrameworkName(StrEnum):
    ...
    MY_FRAMEWORK = "myframework"
```

If the framework needs special detection or fallback handling beyond the profile, update the relevant registry or detection helpers in `src/mcp_zen_of_docs/frameworks/__init__.py` as well.

---

## 5. Write tests

Add focused tests for the new profile. At minimum, cover:

- `detect()` returning the correct `FrameworkDetectionResult`
- `primitive_support()` handling all 22 primitives
- `render_snippet()` returning native snippets for supported primitives
- `validate()` catching the framework-specific structural issues you care about

Keep the test surface aligned with the existing framework-profile tests already in `tests/`.

---

## 6. Update docs

A new framework affects more than one page.

Update at least:

- `docs/frameworks/index.md`
- `docs/tools/profile.md`
- `docs/guides/primitives.md`
- any contributor or quickstart docs that describe the supported framework set

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Add a Primitive**

    Extend the primitive vocabulary once the framework exists.

    [:octicons-arrow-right-24: Read more](adding-primitive.md)

-   :octicons-arrow-right-24: **Development**

    Run the local checks and contributor workflow correctly.

    [:octicons-arrow-right-24: Read development](development.md)

</div>

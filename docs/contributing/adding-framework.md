---
title: Add a Framework
description: How to implement the AuthoringProfile ABC for a new documentation framework.
tags:
  - contributing
  - frameworks
---

# Add a Framework

Adding a framework means implementing four methods of `AuthoringProfile`. Once done,
all 10 tools work with the new framework automatically.

---

## 1. Create the profile module

```bash
touch src/mcp_zen_of_docs/frameworks/myframework_profile.py
```

---

## 2. Implement AuthoringProfile

```python
from __future__ import annotations

from pathlib import Path

from ..models import AuthoringPrimitive, FrameworkName, SupportLevel
from .base import AuthoringProfile, FrameworkDetectionResult


class MyFrameworkProfile(AuthoringProfile):
    """AuthoringProfile for MyFramework."""

    @property
    def name(self) -> FrameworkName:
        return FrameworkName.MY_FRAMEWORK  # add to FrameworkName StrEnum

    def config_file_patterns(self) -> list[str]:
        return ["myframework.config.js", "myframework.config.ts"]

    def detect(self, project_root: Path) -> FrameworkDetectionResult | None:
        for pattern in self.config_file_patterns():
            config = project_root / pattern
            if config.exists():
                return FrameworkDetectionResult(
                    framework=self.name,
                    config_path=config,
                )
        return None

    def support_matrix(self) -> dict[AuthoringPrimitive, SupportLevel]:
        return {
            AuthoringPrimitive.MARKDOWN: SupportLevel.NATIVE,
            AuthoringPrimitive.FRONTMATTER: SupportLevel.NATIVE,
            AuthoringPrimitive.ADMONITIONS: SupportLevel.NATIVE,
            # ... all 16 primitives must be mapped
        }

    def render_primitive(self, primitive: AuthoringPrimitive, **kwargs: object) -> str:
        match primitive:
            case AuthoringPrimitive.ADMONITIONS:
                title = kwargs.get("title", "Note")
                content = kwargs.get("content", "")
                return f":::note {title}\n{content}\n:::"
            case _:
                return super().render_primitive(primitive, **kwargs)
```

---

## 3. Register the profile

In `src/mcp_zen_of_docs/frameworks/__init__.py`, add your profile to `_PROFILES`:

```python
from .myframework_profile import MyFrameworkProfile

_PROFILES: list[AuthoringProfile] = [
    ZensicalProfile(),
    DocusaurusProfile(),
    VitePressProfile(),
    StarlightProfile(),
    MyFrameworkProfile(),  # add here
]
```

---

## 4. Add FrameworkName enum value

In `src/mcp_zen_of_docs/models.py`:

```python
class FrameworkName(StrEnum):
    ZENSICAL = "zensical"
    DOCUSAURUS = "docusaurus"
    VITEPRESS = "vitepress"
    STARLIGHT = "starlight"
    MY_FRAMEWORK = "myframework"  # add here
```

---

## 5. Write tests

Create `tests/test_myframework_profile.py`. At minimum, test:

- `detect()` returns the correct result when the config file exists
- `detect()` returns `None` when the config file is absent
- `support_matrix()` maps all 16 primitives
- `render_primitive()` produces valid syntax for native primitives

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Add a Primitive**

    Extend the 16 primitives with a new authoring concept.

    [:octicons-arrow-right-24: Read more](adding-primitive.md)

</div>

---
title: Philosophy
description: The ten principles that guide every decision in the Zen of Documentation.
tags:
  - philosophy
  - principles
---

# Philosophy

Ten principles guide every tool, every default, and every generated page.

<figure class="chapter-banner">
    <img src="../assets/chapters/philosophy-garden.svg" alt="A zen garden illustration with raked lines and balanced stones for the philosophy chapter." />
</figure>

---

## The Zen of Documentation

**1. Clarity over cleverness.**
Understand the point on first read. Clever structure that requires decoding is failed structure.

**2. Structure reveals intent.**
Nav order is an argument about priority. [`onboard`](tools/onboard.md) places overview pages first and reference last.

**3. Primitives are universal — frameworks are dialects.**
An admonition exists in every framework; only the syntax differs. [`profile`](tools/profile.md) maps all 16 primitives to their native form.

**4. Beauty is functional.**
Good formatting aids comprehension. [`validate`](tools/validate.md) scores formatting quality, not just broken links.

**5. One page, one idea.**
A page that covers three topics covers none well. [`validate`](tools/validate.md) flags pages that exceed the length budget.

**6. Navigation is a contract with the reader.**
Every nav entry must lead somewhere. [`scaffold`](tools/scaffold.md) adds the nav entry and the page atomically.

**7. Frontmatter is metadata, not decoration.**
`title`, `description`, and `tags` feed search, social previews, and navigation. [`validate --mode frontmatter`](tools/validate.md) flags missing keys.

**8. Code examples must run.**
A code example that errors is worse than no example. [`generate mode=reference`](tools/generate.md) produces examples from live source.

**9. Every admonition earns its place.**
An admonition is an interrupt — use it only when the content demands stopping. [`scaffold`](tools/scaffold.md) emits at most one per section.

**10. Documentation is a product, not an afterthought.**
Shipping without docs is shipping half a product. [`onboard`](tools/onboard.md) runs the full detect → scaffold → deploy pipeline in one command.

!!! tip "Start with one tool"
    You don't have to adopt every principle at once. Run [`detect`](tools/detect.md) on your project today. The rest follows naturally.

---

## What's Next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Why Zen Docs**

    The case for treating documentation as a first-class product.

    [:octicons-arrow-right-24: Read the case](guides/why-zen-docs.md)

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    How these principles are embodied in the tool pipeline.

    [:octicons-arrow-right-24: Read the guide](guides/detect-profile-act.md)

</div>

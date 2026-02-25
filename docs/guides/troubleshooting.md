---
title: Troubleshooting
description: Common errors, detection failures, and rendering glitches — with fixes.
tags:
  - guides
  - troubleshooting
---

# Troubleshooting

---

## Framework not detected

**Symptom:** `detect` returns `{"framework": null}` or raises `FrameworkNotFoundError`.

**Cause:** No supported config file exists in `project_root`, or `project_root` points to
the wrong directory.

**Fix:** Verify that one of these files exists at the expected location:

| Framework | Expected file |
|-----------|---------------|
| Zensical | `zensical.toml` or `mkdocs.yml` |
| Docusaurus | `docusaurus.config.js` or `docusaurus.config.ts` |
| VitePress | `.vitepress/config.ts` or `.vitepress/config.js` |
| Starlight | `astro.config.mjs` or `astro.config.ts` |

Then pass the correct root explicitly:

```text
detect mode=context project_root=./my-docs-subdir
```

---

## detect returns null framework

**Symptom:** `detect` reports no framework found.

**Cause:** The config file isn't in `project_root`, or uses a non-standard filename.

**Fix:** Pass the correct `project_root`:

```text
detect mode=context project_root=./my-docs-subdir
```

Or check that one of the config files listed above exists in the root.

---

## Admonitions render as plain text

**Symptom:** `!!! note` appears as a literal line in the browser.

**Cause:** The `admonition` extension is not in `markdown_extensions` in `mkdocs.yml`.

**Fix:** Run `theme mode=extensions` to generate the correct extension config block, or
add the extension manually:

```yaml
markdown_extensions:
  - admonition
  - pymdownx.details
```

---

## Card grids render without borders

**Symptom:** `<div class="grid">` items have no card styling.

**Fix:** Use `<div class="grid cards" markdown>` — the `cards` class is required.

---

## Tab content appears outside the tab block

**Symptom:** Content meant to be inside a tab renders below the tab strip.

**Cause:** Tab content is not indented 4 spaces.

**Fix:**

```markdown
=== "Tab name"

    Content must be indented exactly 4 spaces.
```

---

## Mermaid diagram renders as a code block

**Symptom:** The ` ```mermaid ` block shows raw text instead of a diagram.

**Cause:** The `pymdownx.superfences` extension is missing or not configured with the
custom fence for Mermaid.

**Fix:** Add this to `mkdocs.yml`:

```yaml
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

---

## validate reports broken links

**Symptom:** Internal links fail validation but the files exist.

**Cause:** Relative paths calculated from the wrong base directory.

**Fix:** Ensure `docs_root` matches your actual docs directory:

```text
validate docs_root=docs/
```

---

## onboard creates pages in the wrong directory

**Symptom:** Scaffolded pages land in `./` instead of `./docs/`.

**Fix:** Pass `docs_root` explicitly:

```text
onboard docs_root=docs project_root=.
```

---

## What to read next

<div class="grid cards" markdown>

-   :octicons-arrow-right-24: **Detect → Profile → Act**

    Understanding the detection pipeline prevents most configuration issues.

    [:octicons-arrow-right-24: Read the guide](detect-profile-act.md)

</div>

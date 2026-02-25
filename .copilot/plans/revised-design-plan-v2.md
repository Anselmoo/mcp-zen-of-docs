# Revised Design Plan v2 — mcp-zen-of-docs
**Status:** Planning memo (pre-implementation)
**Supersedes:** First implementation pass (session `4e298968`)
**Problems addressed:** Header cramping · SVG dead assets · Green palette reads as classical tech ·
Off-brand copy · Double footer

---

## 0 — Diagnostic Summary

Before prescribing fixes, it helps to name *exactly* what is broken and *why* it
happened. Each problem maps to a root cause, which maps to an architectural layer.

| # | Symptom | Root cause | Layer |
|---|---------|------------|-------|
| P1 | Logo + "mcp-zen-of-docs" cramped in header | MkDocs Material's `.md-header__title` receives the full string. No CSS constrains `.md-logo img` height, and the name has four hyphen-segments — it wraps or ellipsis-clips at the default 1.2rem clamp. | CSS / possibly a Jinja partial |
| P2 | SVGs exist but are not integrated | `home.html` contains a *separate* inline SVG hub-and-spoke that duplicates `hero-diagram.svg`. `header.svg` (1 200×120 banner) is never referenced anywhere. `illustration-zen-principles.svg` and `illustration-mcp-tools.svg` are orphaned assets. The correct external-file references were never wired up. | Templates + content |
| P3 | Green palette reads as "classical tech" | `--sumi-accent: #0ea27a` is a clean, saturated, primary-green that shares colorimetry with Stripe, GitHub success, and countless "developer tool" brands. It is used as a **solid fill** on the hero, the announce banner, and the header — exactly the application pattern that makes it feel like a product color-swatch, not an atmospheric quality. | CSS tokens |
| P4 | Quote / copy feels off-brand | The announce bar copy ("Ten MCP tools. Four frameworks. Zero wrong syntax.") and hero motto ("Right syntax. Right framework. Every time.") read as SaaS feature checklists. The rotating quote pool (`extra.js`) mixes product-manager aphorisms ("Documentation is a product, not an afterthought.") with better zen-flavored lines. The *tone register* is inconsistent and leans functional, not contemplative. | JS + templates (content layer) |
| P5 | Two footers | `overrides/partials/footer.html` renders **both** a `<nav class="md-footer__inner">` prev/next block (because `navigation.footer` is in `features`) **and** a `<section class="zen-footer-shell">`. These are visually distinct and untreated — they sit stacked as two independent footer entities rather than one coherent zone. | Templates + CSS |

---

## 1 — Architecture-Level Recommendations

### 1.1 Layer responsibilities (strict separation)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER           FILES                  OWNS                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Tokens          tokens/palette.css     Color raw values, named scale   │
│                  tokens/semantic.css    Aliases, component hooks        │
│                  theme/light.css        MkDocs Material var overrides   │
│                  theme/dark.css         MkDocs Material var overrides   │
├─────────────────────────────────────────────────────────────────────────┤
│  Templates       overrides/*.html       DOM structure, Jinja logic      │
│                  overrides/partials/    Slot-level DOM fragments        │
├─────────────────────────────────────────────────────────────────────────┤
│  Components      stylesheets/           Visual execution of structure   │
│                  components/*.css                                       │
│                  pages/*.css                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Assets          docs/assets/           SVG source files (static)       │
│                  docs/assets/icons/                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Content         docs/**/*.md           Copy, frontmatter, prose        │
│  Behaviour       docs/javascripts/      Runtime interaction, quotes     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Golden rule:** Do not solve a tokens problem in a component file. Do not solve a
template structure problem in CSS. The first implementation pass mixed these freely —
that is why P1, P2, and P5 are hard to surgically fix without touching unrelated code.

### 1.2 Which concern lives where (definitive mapping)

| Problem | Template | CSS | Content/JS | Asset |
|---------|----------|-----|------------|-------|
| P1 — Header cramping | Add `overrides/partials/header.html` if logo+name lockup needs custom markup; otherwise CSS alone. **Prefer CSS-only first.** | `components/header.css`: constrain `.md-logo img` to explicit height; add `letter-spacing` or a font-size step-down for `.md-header__topic:first-child`; optionally hide the text name on mobile with `navigation.tabs` active | — | Optionally provide a horizontal SVG lockup (logo + wordmark) for wide viewports |
| P2 — SVG dead assets | Replace inline SVG in `home.html` with `<img src="{{ 'assets/hero-diagram.svg' \| url }}">` or a Jinja `{% include %}`. Wire `illustration-*.svg` into relevant content pages via Markdown `<figure>` tags. `header.svg` either gets a partial or is deprecated. | `pages/illustrations.css`: ensure `.zen-illustration` class works; add sizing rules for the hero image slot in `home.html` | Prose pages reference illustrations with correct `<figure>` + `<figcaption>` markup | Audit all 15 SVGs: decide keep/deprecate; rename any that don't follow the `zen-*.svg` convention |
| P3 — Green palette | — | `tokens/palette.css`: shift accent away from saturated primary. Application in `theme/light.css` + `theme/dark.css`: use accent as a *tint and stroke* color, not a solid fill for large surfaces. Hero backgrounds and announce bar move to a near-neutral deep surface with accent detail. | — | SVGs that embed `#0ea27a` hardcoded need regeneration with the new token |
| P4 — Off-brand copy | `overrides/main.html`: rewrite announce bar copy. `overrides/home.html`: rewrite hero motto. | — | `docs/javascripts/extra.js`: rewrite `ZEN_QUOTES` pool; curate a smaller, higher-quality set rather than 12 mixed-register entries | — |
| P5 — Double footer | `overrides/partials/footer.html`: wrap the nav block **inside** `.zen-footer-shell` as a fourth zone, OR remove `navigation.footer` from `zensical.toml` and implement prev/next as an in-content partial. **Recommendation: keep feature, integrate structurally.** | `components/footer.css`: style the nav block to match the zen shell's type and spacing; remove visual separation between the two zones | — | — |

### 1.3 The palette shift (P3) — specific guidance

The goal is *atmospheric/zen*, not tech. The problem with `#0ea27a` as a hero background
is not the hue — it is the **chroma (saturation)** and the **application surface area**.

Recommended direction — three options, pick one as a team:

**Option A — Celadon mist** (most zen, biggest departure)
- Accent: `#6db8a0` — muted, blue-shifted jade; low chroma; fog-on-mountain quality
- Hero background: dark charcoal (`#131720`) with accent used only as glow, stroke, and small highlights
- Announce bar: near-black with a 1px jade bottom border; white text

**Option B — Aged jade** (moderate, less risky)
- Accent: `#0d8f6c` → shift from current `#0ea27a` by reducing L* (luminance) in OKLCH by ~8 points
- Keep the enso-on-surface motif but desaturate hero backgrounds by 60%; add a gaussian-blur SVG
  watermark effect behind the hero content to create depth/atmosphere
- Use linear-gradient with very shallow stops (3–5% luminance shift) not a 3-stop solid jade

**Option C — Minimal intervention** (least risky, recommended as first pass)
- Keep current token values but change **application**: hero background → `var(--sumi-bg1)` with
  jade micro-accents (border-bottom, enso watermark at 8% opacity); announce bar → same dark surface
- This is a CSS-only change, zero token edits required, immediately reviewable

> **Recommendation for this plan:** Start with Option C (application change) in WS-A.
> If the review gate agrees the vibe has landed, ship. If not, pivot to Option A or B
> as a follow-on. Separating "application change" from "token change" keeps rollback trivial.

### 1.4 Footer unification strategy (P5)

The double-footer is a **template structure** problem. The Material `navigation.footer`
feature outputs a `<nav>` block *before* the custom shell. The fix has two valid approaches:

**Approach F-A (Recommended):** Move the nav block *inside* `.zen-footer-shell` as an
optional top zone, visually continuous with the rest of the footer:

```html
<footer class="md-footer">
  <section class="zen-footer-shell md-typeset" aria-label="Project footer">
    <!-- NEW: prev/next navigation zone (conditional) -->
    {% if "navigation.footer" in features %}
      {% if page.previous_page or page.next_page %}
        <nav class="zen-footer-nav md-grid" ...>
          ...prev/next links with zen shell styling...
        </nav>
      {% endif %}
    {% endif %}
    <!-- Existing: 3-column brand/explore/project grid -->
    <div class="md-grid zen-footer-shell__grid"> ... </div>
  </section>
  <!-- Meta row unchanged -->
  <div class="md-footer-meta ..."> ... </div>
</footer>
```

**Approach F-B (Simpler but lossy):** Remove `navigation.footer` from `zensical.toml`
features. Custom prev/next links can be injected via `extra.js` or left absent.
Trade-off: loses accessibility-labeled prev/next navigation.

**Recommendation: Approach F-A.** Retains the navigation value; unifies visually.

---

## 2 — Execution Plan (Parallelized Workstreams)

Five workstreams. Two can run purely in parallel from day one. Two more unblock
after a shared Gate 1 review. SVG integration is the last to merge.

```
DAY 0      DAY 1–2             GATE 1        DAY 3–4         GATE 2      DAY 5       GATE 3
  │                               │                              │            │            │
  ├──[WS-A: Palette application]──┤                              │            │            │
  │                               ├──[WS-B: Header lockup]───────┤            │            │
  ├──[WS-E: Copy & voice]─────────┤                              │            │            │
  │                               │           ├──[WS-C: Footer unification]───┤            │
  │                               │           │                               │            │
  │                               │           └──[WS-D: SVG integration]──────────────────┤
  │                               │                                                        │
  └───────────────────────────────┴────────────────────────────────────────────────────────┘
                                FULL INTEGRATION BUILD + VISUAL AUDIT (Day 6)
```

### WS-A — Palette Application (`tokens/` + `theme/` + hero CSS)
**Owner:** CSS / design
**Parallel with:** WS-E
**Goal:** Make the green palette feel atmospheric rather than product-colored.
**Scope (Option C — application change only):**
- `docs/stylesheets/pages/hero.css` — `.zen-hero` and `.hero-container` backgrounds change
  from `linear-gradient(135deg, #0b8f6c, #0ea27a, #12b085)` to
  `var(--sumi-bg1)` (dark) or `var(--sumi-light-bg1)` (light) with a subtle enso watermark
- `docs/stylesheets/components/header.css` — `[data-md-color-scheme="default"] .md-header`
  move from jade-primary fill to dark charcoal + jade border-bottom only
- `overrides/main.html` — announce bar stays jade (it's a small strip, acceptable); OR
  shift to dark-charcoal + jade border (coordinate with WS-E copy rewrite)
- Add a new SVG watermark inline or via `::before` pseudo-element on `.zen-hero`:
  a 20% opacity enso-circle behind the hero content creates depth without loud color

**Files touched:**
```
docs/stylesheets/pages/hero.css            ← hero backgrounds
docs/stylesheets/components/header.css     ← header background
docs/stylesheets/theme/light.css           ← possibly: hero heading color if bg changes
docs/stylesheets/theme/dark.css            ← same
```

**Do NOT touch:** `tokens/palette.css` (preserve token values; only change where they are
applied). This is the key discipline of Option C.

---

### WS-B — Header Logo Treatment (`components/header.css` + optional partial)
**Owner:** CSS
**Unblocks after:** Gate 1 (so palette is settled before header bg is matched)
**Goal:** Logo and site name breathe; neither is cramped or ellipsis-clipped.

**Primary fix — CSS-only:**
```css
/* Explicit logo sizing */
.md-header .md-logo img,
.md-header .md-logo svg {
  height: 2rem;      /* was: implicit from MkDocs default ~1.6rem */
  width:  auto;
  display: block;
}

/* Site name — step down font size, use tracking to compensate */
.md-header__topic:first-child .md-ellipsis {
  font-size:      0.8rem;
  letter-spacing: 0.01em;
  font-weight:    600;
}

/* On narrow tabs viewports: hide text name, show only logo */
@media screen and (max-width: 59.9375em) {
  .md-header__title .md-header__topic:first-child {
    display: none;
  }
}
```

**Secondary consideration — horizontal lockup SVG:**
If the CSS fix is insufficient (logo aspect ratio makes it read as a stamp, not a brand
mark), add `docs/assets/logo-lockup.svg` — a purpose-built horizontal composition of the
enso + "zen of docs" wordmark at correct optical weight. This would be referenced from
a new `overrides/partials/header.html` partial that replaces the Material header logo slot.

> **Decision gate:** Try CSS-only first. Only create the lockup SVG if the visual review
> at Gate 2 says the CSS approach is still cramped.

**Files touched:**
```
docs/stylesheets/components/header.css     ← primary fix
overrides/partials/header.html             ← only if lockup SVG is needed (NEW)
docs/assets/logo-lockup.svg               ← only if lockup SVG is needed (NEW)
```

---

### WS-C — Footer Unification (`overrides/partials/footer.html` + CSS)
**Owner:** Templates + CSS
**Unblocks after:** Gate 1 (palette must be settled so footer shell bg matches)
**Goal:** One cohesive footer zone; prev/next nav visually integrated.

**Template change** (`overrides/partials/footer.html`):
- Move the `{% if "navigation.footer" in features %}` nav block from the *top-level*
  of `<footer>` into `.zen-footer-shell` as a first child (Approach F-A above)
- Rename the nav's class from `md-footer__inner` to `zen-footer-nav` to avoid
  Material CSS conflicts while still rendering the same links

**CSS change** (`components/footer.css`):
```css
/* New zone: prev/next inside zen shell */
.zen-footer-nav {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1rem 0;
  border-bottom: 1px solid var(--sumi-border-subtle);
  margin-bottom: 1.5rem;
}

.zen-footer-nav .md-footer__link {
  /* Match zen shell type scale */
  font-size: 0.82rem;
  color: var(--md-default-fg-color--light);
}
.zen-footer-nav .md-footer__link:hover {
  color: var(--sumi-accent);
}
/* Remove the standalone footer's default top-margin that creates the gap */
.md-footer > nav.md-footer__inner { display: none; }  /* safety: hide if partially rendered */
```

**Acceptance:** Building the site must render exactly **one** `<footer>` with:
`zen-footer-nav` (when prev/next exist) → `zen-footer-shell__grid` → `md-footer-meta`

**Files touched:**
```
overrides/partials/footer.html             ← structural reorg
docs/stylesheets/components/footer.css     ← nav zone styling
```

---

### WS-D — SVG Integration (`home.html` + content + assets)
**Owner:** Templates + assets
**Starts after:** Gate 2 (palette must be final; SVG fills must match)
**Goal:** Every SVG in `docs/assets/` is either deliberately used or deliberately removed.

**Step D1 — Audit all 15 SVGs** (30 min, do first):

| Asset | Current use | Recommendation |
|-------|-------------|----------------|
| `logo.svg` | Header + footer brand | ✅ Keep; fix header sizing in WS-B |
| `favicon.svg` | `<link rel="icon">` | ✅ Keep |
| `hero-diagram.svg` | NOT used — `home.html` uses inline SVG instead | **Replace inline SVG with `<img>` reference** |
| `header.svg` | NOT used anywhere | **Decision: integrate as page-top banner OR deprecate**; the 1200×120 dimensions suggest it was meant as a full-width banner — consider using it in `overrides/partials/header.html` as a decorative bg, or archive it |
| `illustration-zen-principles.svg` | NOT used | **Wire into `docs/philosophy.md`** as a `<figure>` |
| `illustration-mcp-tools.svg` | NOT used | **Wire into `docs/tools/index.md`** as a `<figure>` |
| `zen-docs-header.svg` | NOT used | Likely a variant of `header.svg`; **deprecate if redundant** |
| `zen-quality-badge.svg` | NOT used | **Wire into `docs/index.md`** near the hero OR deprecate |
| `social-card.svg` | NOT used in templates | Wire into `<meta property="og:image">` in `overrides/main.html` |
| `icons/prompt.svg` | NOT used | Keep for content authors to `{% include %}` |
| `icons/resource.svg` | NOT used | Same |
| `icons/tool-analysis.svg` | NOT used | Same |
| `icons/tool-onboarding.svg` | NOT used | Same |
| `icons/tool-prompts.svg` | NOT used | Same |
| `icons/zen-icon.svg` | NOT used | Keep as a generic accent icon |

**Step D2 — Replace inline SVG in `home.html`:**
```html
<!-- REMOVE the entire <svg class="zen-hero__svg"> block (lines ~60-100 of home.html) -->
<!-- REPLACE with: -->
<img class="zen-hero__svg"
     src="{{ 'assets/hero-diagram.svg' | url }}"
     alt="Four documentation frameworks connected to mcp-zen-of-docs"
     width="360" height="280"
     loading="eager">
```
This removes ~40 lines of inline markup and references the correct asset. The SVG
must be verified to have identical or better visual output.

**Step D3 — Wire `og:image` in `overrides/main.html`:**
```html
<!-- In the {% block extrahead %} already present: -->
<meta property="og:image" content="{{ 'assets/social-card.svg' | url }}" />
<meta name="twitter:image" content="{{ 'assets/social-card.svg' | url }}" />
```

**Step D4 — Wire illustrations into content:**
```markdown
<!-- In docs/philosophy.md — add after the main prose: -->
<figure class="zen-illustration">
  <img src="../assets/illustration-zen-principles.svg"
       alt="The Zen of Documentation — 10 guiding principles"
       loading="lazy">
  <figcaption>The ten principles of Zen documentation.</figcaption>
</figure>
```
CSS class `.zen-illustration` already exists in `pages/illustrations.css`.

**Files touched:**
```
overrides/home.html                        ← replace inline SVG
overrides/main.html                        ← add og:image
docs/philosophy.md                         ← wire illustration
docs/tools/index.md                        ← wire illustration
docs/index.md                              ← wire quality badge (if kept)
docs/assets/[deprecated SVGs]              ← remove files not being used
```

---

### WS-E — Copy & Voice (`extra.js` + `main.html` + `home.html`)
**Owner:** Content / copy
**Parallel with:** WS-A
**Goal:** Every piece of user-visible copy sounds contemplative and specific, not
SaaS-functional.

**Register diagnostic — current vs. target:**

| Location | Current copy | Problem | Target register |
|----------|-------------|---------|-----------------|
| Announce bar | "Ten MCP tools. Four frameworks. Zero wrong syntax." | Feature bullet-point, sales voice | A short koan or subtle benefit — e.g. "Wrong syntax is just a missing map." |
| Hero motto (`home.html`) | "Right syntax. Right framework. Every time." | Slogan that reads like a warranty | Something with *movement* — e.g. "Every framework has a grammar. Every author deserves to know it." |
| Hero tagline (`home.html`) | "The AI-native MCP server that detects your docs framework…" | Technically accurate but dense | Prose that opens with the human problem, not the technical solution |
| Footer static quote | "Documentation is a product, not an afterthought." | Product-management aphorism; common, not distinctive | Remove hardcoded static; let the rotating pool from `extra.js` run here instead |
| `ZEN_QUOTES` pool (`extra.js`) | 12 entries mixing product copy with better lines | Mixed register; "Documentation is a product" repeats the footer | Curate to 6–8 entries that are **all** zen-register: short, slightly oblique, memorable |

**Proposed `ZEN_QUOTES` replacement** (8 entries, all zen-register):
```js
const ZEN_QUOTES = [
  "Every framework has a grammar. Every author deserves to know it.",
  "Structure is not a cage. It is the shape of clear thought.",
  "Wrong syntax is just a missing map.",
  "The cursor blinks. The framework does not care about feelings.",
  "One page, one idea, one breath.",
  "Primitives are universal — frameworks are dialects.",
  "Navigation is a contract with the reader.",
  "Beauty is functional. Always.",
];
```

**Proposed announce bar** (`overrides/main.html`, in `{% block announce %}`):
```html
<a href="{{ 'quickstart/' | url }}">
  <strong>Wrong syntax is just a missing map.</strong> &rarr; Find yours
</a>
```

**Proposed hero motto** (`overrides/home.html`):
```html
<p class="zen-hero__motto">
  <em>Every framework has a grammar. Every author deserves to know it.</em>
</p>
```

**Files touched:**
```
docs/javascripts/extra.js                  ← ZEN_QUOTES + footer quote logic
overrides/main.html                        ← announce bar copy
overrides/home.html                        ← hero motto + tagline
```

---

## 3 — Gate Structure (Deliberate Review Stages)

### Gate 1 — Vibe alignment (after WS-A + WS-E)
**Trigger:** Both WS-A and WS-E are complete on a feature branch.
**Build command:** `uvx zensical build --config zensical.toml` or local `mkdocs serve`
**Review questions:**
1. Does the home page feel calm and purposeful, or does the green still dominate and yell?
2. Does the announce bar copy make you slow down and read, or scan past it?
3. Do the hero tagline and motto feel continuous in register?
4. Does the header background now read as "night/ink/depth" rather than "green stripe"?

**Acceptance criteria:**
- [ ] Hero section does not use a solid jade fill as a large background surface
- [ ] Header background is dark (charcoal) or light (warm ivory), not jade, in default palette
- [ ] Announce bar reads at a sentence level, not a bullet-point level
- [ ] No quote in `ZEN_QUOTES` sounds like a product brochure
- [ ] Both light and dark mode are checked

**Exit options:**
- Gate passes → unblock WS-B and WS-C in parallel
- Gate fails on palette only → escalate Option A or B; WS-E can still proceed
- Gate fails on copy only → iterate WS-E; WS-B can still proceed

---

### Gate 2 — Frame check (after WS-B + WS-C)
**Trigger:** Header and footer are complete; Gate 1 has passed.
**Review questions:**
1. Does the header logo/name feel proportional — not a postage stamp, not oversize?
2. Can you read "mcp-zen-of-docs" without squinting on a 1280px display? On 375px mobile?
3. Is there visually **one** footer? Do the prev/next links feel part of the zen shell?
4. Does the footer bottom-to-header top feel like a coherent skin, not three separate CSS
   experiments bolted together?

**Acceptance criteria:**
- [ ] `.md-logo img` height is between 1.8rem and 2.4rem (visually balanced)
- [ ] Site name does not ellipsis-clip at 1024px+
- [ ] Zero visual gap or border *between* the nav footer and the zen footer shell
- [ ] `<footer>` in the DOM contains exactly one `<nav>` and one `<section>` (prev/next inside shell)
- [ ] Footer background is continuous (no stripe color mismatch between nav and shell zones)

**Exit options:**
- Gate passes → unblock WS-D
- Gate fails on header only → consider lockup SVG (WS-B extension); WS-C can ship
- Gate fails on footer → revisit Approach F-B (remove feature flag instead)

---

### Gate 3 — Asset integration (after WS-D)
**Trigger:** All SVGs are either wired or archived; Gate 2 has passed.
**Review questions:**
1. Does the home page hero reference `hero-diagram.svg` correctly (img loads, no 404)?
2. Is every `docs/assets/*.svg` file either referenced by a template/content or absent
   from the directory?
3. Does `social-card.svg` appear as the OG image when tested with a link unfurl tool?
4. Do the wired illustrations (zen-principles, mcp-tools) enhance or clutter the pages?
   Are they sized and captioned correctly?

**Acceptance criteria:**
- [ ] `home.html` has no inline `<svg>` block; hero SVG loads from file reference
- [ ] `git ls-files docs/assets/` returns only files that are referenced somewhere
- [ ] OG/Twitter image meta tags point to `social-card.svg` with correct absolute URL
- [ ] Each illustration has a `<figure>` + `<figcaption>`; no illustration is raw `<img>` without context
- [ ] Build output has no 404s for asset references (`mkdocs build --strict`)

---

### Gate 4 — Full integration (final, before merge)
**Trigger:** All workstreams merged to a single integration branch.
**Review questions:**
1. Load the site in both light and dark mode. Does it feel like a cohesive piece of work,
   or a patchwork?
2. Check every page in the nav: do any pages show the "two footer" problem still?
3. Run `mkdocs build --strict`. Are there zero warnings and zero 404s?
4. Does the site feel **calm**? Is there a moment of atmospheric pause when you first land?
   Or does it still feel like a SaaS documentation template?

**Acceptance criteria (all must pass to merge):**
- [ ] `mkdocs build --strict` exits 0
- [ ] Lighthouse accessibility score ≥ 90 (run in Chrome DevTools)
- [ ] Exactly one `<footer>` in the page DOM (verify with browser inspector on 3 pages)
- [ ] No `!important` rules added during this work except where explicitly justified in comments
- [ ] Both light and dark mode pass a color-contrast check for all text on non-jade surfaces
- [ ] The three quote locations (hero, footer, rotating) show text from the curated pool only —
      no legacy product-manager quotes remain

---

## 4 — Risks and Rollback Considerations

### Risk R1 — Palette shift breaks SVG hardcoded colors
**Likelihood:** Medium (if WS-A escalates to Option A/B; low if Option C only)
**Impact:** Hero diagram SVG, illustration SVGs embed `#0ea27a` and `#3fd9a8` hardcoded.
If the palette shifts those values, SVGs will mismatch the surrounding UI.
**Mitigation:** WS-D runs *after* palette is final (Gate 2). SVG regeneration with new
colors is scoped into WS-D. Use CSS `color-mix()` or `filter` overrides as a bridge if
regeneration is not feasible in the same sprint.
**Rollback:** `git checkout docs/assets/` restores all SVGs to prior state.

### Risk R2 — Footer template reorg breaks `navigation.footer` on some pages
**Likelihood:** Low — Jinja conditional is straightforward.
**Impact:** Pages with no prev/next still render correctly; pages with both links still
show them. But the template reorg is more invasive than a CSS-only fix.
**Mitigation:** Test on at minimum: index page (no prev/no next), a mid-nav page (both),
and the last page (only prev). Check in both light and dark mode.
**Rollback:** `git checkout overrides/partials/footer.html` reverts the template; footer
reverts to double-zone appearance but remains functional.

### Risk R3 — `extra.js` quote replacement disrupts instant-nav behavior
**Likelihood:** Low — `injectHeroQuote` and `injectFooterQuote` are simple DOM writes.
**Impact:** Rotating quote may not re-inject after client-side navigation if the
`document$` subscription fires before the `.zen-footer-shell` is in the DOM.
**Mitigation:** The existing `document$.subscribe(() => init())` pattern already handles
instant navigation. Verify by navigating away from home and back.
**Rollback:** Restore old `ZEN_QUOTES` array; the injection logic is unchanged.

### Risk R4 — Header CSS change clips logo on some screen sizes
**Likelihood:** Medium — MkDocs Material's header has complex responsive breakpoints.
**Impact:** Logo clips or overlaps nav icons on tablet/mobile.
**Mitigation:** Test at 375px, 768px, 1024px, 1440px. Use explicit `max-width` + `height`
on `.md-logo img` rather than scaling with `em` units that cascade from the header's own
font-size context.
**Rollback:** `git checkout docs/stylesheets/components/header.css` reverts to current state.

### Risk R5 — Inline SVG removal in `home.html` shows wrong diagram
**Likelihood:** Medium — `hero-diagram.svg` may not be visually identical to the inline version
(the inline version uses a slightly different composition / viewBox).
**Impact:** Home page hero looks visually different than the current implementation.
**Mitigation:** Open `hero-diagram.svg` in a browser before removing the inline block; compare
visually. If `hero-diagram.svg` is inferior, this is an opportunity to replace it with the
correct diagram *before* the template is wired up.
**Rollback:** The inline SVG block is self-contained; `git checkout overrides/home.html`
restores it instantly.

### Risk R6 — `!important` accumulation
**Likelihood:** Medium — the current codebase already has significant `!important` usage
in `theme/light.css` and `theme/dark.css` to beat Material's specificity. New rules may
compound this debt.
**Mitigation:** Each workstream must explicitly comment any new `!important` with the
reason (e.g., `/* beats .md-header specificity — see Material source */`). Gate 4 blocks
on any unexplained `!important` additions.
**Rollback:** Not applicable (it's a quality gate, not a runtime risk).

---

## 5 — File Change Summary (All Workstreams)

```
WS-A (Palette application)
  MODIFY  docs/stylesheets/pages/hero.css
  MODIFY  docs/stylesheets/components/header.css
  POSSIBLY MODIFY  docs/stylesheets/theme/light.css
  POSSIBLY MODIFY  docs/stylesheets/theme/dark.css

WS-B (Header logo)
  MODIFY  docs/stylesheets/components/header.css
  POSSIBLY CREATE  overrides/partials/header.html
  POSSIBLY CREATE  docs/assets/logo-lockup.svg

WS-C (Footer unification)
  MODIFY  overrides/partials/footer.html
  MODIFY  docs/stylesheets/components/footer.css

WS-D (SVG integration)
  MODIFY  overrides/home.html
  MODIFY  overrides/main.html
  MODIFY  docs/philosophy.md
  MODIFY  docs/tools/index.md
  POSSIBLY MODIFY  docs/index.md
  POSSIBLY DELETE  docs/assets/zen-docs-header.svg (if redundant)
  POSSIBLY DELETE  docs/assets/header.svg (if deprecated)

WS-E (Copy & voice)
  MODIFY  docs/javascripts/extra.js
  MODIFY  overrides/main.html
  MODIFY  overrides/home.html

SHARED (do not modify in multiple WS simultaneously)
  overrides/main.html         — WS-D and WS-E both touch; coordinate or merge last
  overrides/home.html         — WS-D and WS-E both touch; coordinate or merge last
```

> **Coordination note on shared files:** `overrides/main.html` and `overrides/home.html`
> are touched by both WS-D and WS-E. These should be worked on a single feature branch
> (not split across two PRs that would cause merge conflicts). Either designate one
> workstream as the owner of those files and the other as a reviewer, or batch both
> workstreams into the same branch after Gate 1.

---

## 6 — What This Plan Deliberately Does NOT Do

These items were considered and excluded to keep scope manageable:

- **Does not change `tokens/palette.css` values** (in the Option C baseline). Token
  values are stable across light/dark/print/mermaid. Application changes are sufficient.
- **Does not add new font families.** Inter + JetBrains Mono is correct; the vibe
  issue is color and copy, not typography.
- **Does not redesign content pages.** The nav structure, page architecture, and
  admonition/code styling are solid. Only the chrome (header, hero, footer) and copy
  voice are revised here.
- **Does not add new JavaScript dependencies.** All fixes are CSS + Jinja + small
  `extra.js` edits; no new libraries.
- **Does not change `zensical.toml` plugin or extension configuration.** This plan
  is purely presentation-layer.

---

*This memo is a planning artifact. It authorizes no code changes. Workstream owners
should treat Gate 1 as a mandatory checkpoint before initiating WS-B and WS-C.*

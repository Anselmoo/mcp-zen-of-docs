/**
 * Sumi theme extras for mcp-zen-of-docs
 * Subscribes to the MkDocs Material document$ observable.
 * Uses requestAnimationFrame to gate CSS animations only until the first
 * rendered frame, preventing the theme-switch flash as early as possible.
 */

const HERO_QUOTES = [
  "Write for the traveller who arrives after you.",
  "A quiet page can carry a great deal of meaning.",
  "Mist reveals the path a little at a time.",
  "The map should calm the reader before it instructs them.",
  "Good documentation feels guided, not pushed.",
];

const FOOTER_QUOTES = [
  "Write for the traveller who arrives after you.",
  "Leave enough space for the idea to breathe.",
  "The path should be clear before it is clever.",
  "Good documentation feels guided, not pushed.",
  "The framework may change; the intent should remain.",
  "A quiet page can carry a great deal of meaning.",
  "Let the reader arrive a step at a time.",
];

const THEME_PREFERENCES = ["auto", "light", "dark"];
const THEME_LABELS = {
  auto: "Auto",
  light: "Light",
  dark: "Dark",
};
const THEME_ICONS = {
  auto:
    '<svg viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="18" height="13" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 20h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M12 17v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  light:
    '<svg viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2.2M12 19.8V22M4.93 4.93l1.56 1.56M17.51 17.51l1.56 1.56M2 12h2.2M19.8 12H22M4.93 19.07l1.56-1.56M17.51 6.49l1.56-1.56" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  dark:
    '<svg viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><path d="M20 15.2A8.6 8.6 0 0 1 8.8 4 8.8 8.8 0 1 0 20 15.2Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
};

let zenThemeMediaQuery;

function getRotatingQuote() {
  const day = Math.floor(Date.now() / 86_400_000);
  return FOOTER_QUOTES[day % FOOTER_QUOTES.length];
}

function getSiteRoot() {
  const logoLink = document.querySelector(".md-logo")?.getAttribute("href");
  if (logoLink) return logoLink;
  const [, firstSegment = ""] = window.location.pathname.split("/");
  return `/${firstSegment}/`;
}

function getPaletteStorageKey() {
  return `${getSiteRoot()}.__palette`;
}

function getThemePreferenceKey() {
  return `${getSiteRoot()}zen-theme-preference`;
}

function getPaletteInputs() {
  return Array.from(document.querySelectorAll('[data-md-component="palette"] .md-option'));
}

function getStoredBuiltInScheme() {
  const rawValue = window.localStorage.getItem(getPaletteStorageKey());
  if (!rawValue) return null;
  try {
    const parsed = JSON.parse(rawValue);
    return parsed?.color?.scheme ?? null;
  } catch {
    return null;
  }
}

function inferThemePreference() {
  const storedPreference = window.localStorage.getItem(getThemePreferenceKey());
  if (storedPreference && THEME_PREFERENCES.includes(storedPreference)) {
    return storedPreference;
  }

  const builtInScheme = getStoredBuiltInScheme();
  if (builtInScheme === "default") return "light";
  if (builtInScheme === "slate") return "dark";
  return "auto";
}

function resolveThemeScheme(preference) {
  if (preference === "light") return "default";
  if (preference === "dark") return "slate";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "slate" : "default";
}

function syncBuiltInPalette(preference) {
  const storageKey = getPaletteStorageKey();
  if (preference === "auto") {
    window.localStorage.removeItem(storageKey);
    return;
  }

  const targetScheme = preference === "light" ? "default" : "slate";
  const inputs = getPaletteInputs();
  const targetInput = inputs.find((input) => input.dataset.mdColorScheme === targetScheme);
  if (!targetInput) return;

  const { mdColorAccent: accent, mdColorMedia: media, mdColorPrimary: primary, mdColorScheme: scheme } = targetInput.dataset;
  const payload = {
    index: inputs.indexOf(targetInput),
    color: { accent, media, primary, scheme },
  };
  window.localStorage.setItem(storageKey, JSON.stringify(payload));
}

function updateThemeToggle(preference) {
  const toggle = document.querySelector(".zen-mode-toggle");
  if (!toggle) return;

  const resolvedScheme = resolveThemeScheme(preference);
  const resolvedLabel = resolvedScheme === "slate" ? "dark" : "light";
  toggle.dataset.mode = preference;
  toggle.setAttribute("aria-label", `Theme mode: ${THEME_LABELS[preference]} (${resolvedLabel})`);
  toggle.setAttribute("title", `Theme mode: ${THEME_LABELS[preference]}`);
  toggle.innerHTML = `
    <span class="zen-mode-toggle__icon">${THEME_ICONS[preference]}</span>
    <span class="zen-mode-toggle__text">${THEME_LABELS[preference]}</span>
  `;
}

function applyThemePreference(preference, persist = true) {
  const scheme = resolveThemeScheme(preference);
  const { body, documentElement } = document;
  body.setAttribute("data-md-color-scheme", scheme);
  documentElement.setAttribute("data-md-color-scheme", scheme);
  body.dataset.zenThemePreference = preference;
  documentElement.dataset.zenThemePreference = preference;

  if (persist) {
    window.localStorage.setItem(getThemePreferenceKey(), preference);
    syncBuiltInPalette(preference);
  }

  updateThemeToggle(preference);
}

function cycleThemePreference() {
  const currentPreference = inferThemePreference();
  const currentIndex = THEME_PREFERENCES.indexOf(currentPreference);
  const nextPreference = THEME_PREFERENCES[(currentIndex + 1) % THEME_PREFERENCES.length];
  applyThemePreference(nextPreference);
}

function mountThemeToggle() {
  const headerInner = document.querySelector(".md-header__inner");
  if (!headerInner || headerInner.querySelector(".zen-mode-toggle")) return;

  const source = headerInner.querySelector(".md-header__source");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "zen-mode-toggle";
  button.addEventListener("click", cycleThemePreference);

  if (source) {
    headerInner.insertBefore(button, source);
  } else {
    headerInner.appendChild(button);
  }
}

function getSearchShortcutLabel() {
  const platform = navigator.userAgentData?.platform || navigator.platform || navigator.userAgent;
  return /Mac|iPhone|iPad|iPod/i.test(platform) ? "⌘K" : "Ctrl K";
}

function mountSearchShortcutHint() {
  const searchLabels = document.querySelectorAll(".md-search__label");
  for (const label of searchLabels) {
    if (label.querySelector(".zen-search-shortcut")) continue;
    const hint = document.createElement("span");
    hint.className = "zen-search-shortcut";
    hint.setAttribute("aria-hidden", "true");
    hint.textContent = getSearchShortcutLabel();
    label.appendChild(hint);
  }
}

function initThemeController() {
  mountThemeToggle();
  mountSearchShortcutHint();
  applyThemePreference(inferThemePreference(), false);

  if (!zenThemeMediaQuery) {
    zenThemeMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    zenThemeMediaQuery.addEventListener("change", () => {
      if (inferThemePreference() === "auto") {
        applyThemePreference("auto", false);
      }
    });
  }
}

function injectHeroQuote() {
  const hero = document.querySelector(".hero-container, .hero-section, .hero-cta, .zen-hero__content");
  if (!hero || hero.querySelector(".hero-zen-quote")) return;
  const quote = HERO_QUOTES[Math.floor(Math.random() * HERO_QUOTES.length)];
  const el = document.createElement("p");
  el.className = "hero-zen-quote";
  el.textContent = `"${quote}"`;
  hero.appendChild(el);
}

function injectFooterQuote() {
  const quoteHost = document.querySelector("[data-zen-quote-host]");
  if (quoteHost) {
    quoteHost.textContent = `"${getRotatingQuote()}"`;
  }
}

function enableCodeHover() {
  document.querySelectorAll(".md-typeset pre").forEach((pre) => {
    if (pre.dataset.zenHoverBound === "true") return;
    pre.dataset.zenHoverBound = "true";
    pre.addEventListener("mouseenter", () => {
      pre.classList.add("is-hovered");
    });
    pre.addEventListener("mouseleave", () => {
      pre.classList.remove("is-hovered");
    });
  });
}

function markZenReady() {
  // Use rAF so the class is set before the browser paints, avoiding FOUC
  requestAnimationFrame(() => {
    document.body.classList.add("zen-ready");
  });
}

function init() {
  initThemeController();
  markZenReady();
  injectHeroQuote();
  injectFooterQuote();
  enableCodeHover();
}

// MkDocs Material instant navigation support
if (typeof document$ !== "undefined") {
  document$.subscribe(() => {
    init();
  });
} else {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}

# DESIGN.md — Tons of Skills

> Design constitution for the tonsofskills.com marketplace. Source of truth for visual treatment. Authoritative — when this document and any component disagree, the component is wrong.

**Family:** Data-Dense Pro (Bloomberg-terminal-for-AI-tools). Source: [`rohitg00/awesome-claude-design/design-md/data-dense/`](https://github.com/rohitg00/awesome-claude-design/tree/main/design-md/data-dense).

**Locked 2026-05-06.** Family is not up for re-bikeshedding mid-execution. If something doesn't work, fix the application, not the family.

**Format:** 9-section [VoltAgent DESIGN.md spec](https://github.com/VoltAgent/awesome-design-md) + Anti-Slop "Reject" section from rohitg00.

---

## 1. Theme

A serious analytics product, not a developer side project. Near-black canvas. Neon-yellow signal accent used like a highlighter, sparingly. Hairline rules instead of card-fill chrome. Tabular numerals. Editorial restraint over ornament.

The aesthetic peers the site reads against:

- Linear (linear.app) — single accent, dense type, no decoration
- Vercel (vercel.com) — restrained dark canvas, mono accents
- Bloomberg Terminal — the data-density end-state. We don't go all the way there, but we point at it.
- Stripe Atlas / Stripe docs — confident editorial tone, hairline rules

The aesthetic peers the site explicitly does NOT read against:

- Shadcn-default starter sites (rounded cards, slate-500 everywhere, lucide icons)
- AI-generated landing pages (gradient blobs, glassmorphism, tilted cards)
- Tailwind UI marketing pages (uniform border-radius-md across every surface)
- Generic SaaS template sites (purple/teal gradients, chart-illustration heroes)

Dark theme is the canonical default. Light theme is a high-contrast off-white reskin using the same neon-yellow signal — yellow reads on white too; that's why it won the family pick.

## 2. Palette

OKLCH structure preserved from prior system; values replaced wholesale. Token *names* (`--primary`, `--neutral-900`, `--card-featured-radius`, etc.) survive — components reference tokens, never raw values.

### Canvas + structure (dark, default)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0a0a0c` | Page canvas. Near-black, never pure black. |
| `--panel` | `#181818` | Cards, modals, raised surfaces. |
| `--panel-2` | `#1f1f23` | Hover/active state on panels. |
| `--rule` | `#2a2a2e` | 1 px hairlines (replaces card-border-as-divider). |
| `--rule-bright` | `#3a3a3f` | Hover state on rules. |
| `--ink` | `#f4f4f5` | Primary text. |
| `--ink-2` | `#a1a1aa` | Secondary text. |
| `--ink-3` | `#71717a` | Tertiary / muted text. |

### Canvas + structure (light)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#fafaf9` | Page canvas. High-contrast off-white. |
| `--panel` | `#ffffff` | Cards. |
| `--panel-2` | `#f5f5f4` | Hover state. |
| `--rule` | `#e5e5e3` | 1 px hairlines. |
| `--rule-bright` | `#d4d4d2` | Hover state. |
| `--ink` | `#0a0a0c` | Primary text. |
| `--ink-2` | `#52525b` | Secondary text. |
| `--ink-3` | `#71717a` | Tertiary / muted text. |

### Accents (both themes)

| Token | Value | Use |
|---|---|---|
| `--signal` | `#faff69` | THE single primary accent. Used like a highlighter. ONE primary CTA per page. |
| `--signal-tint` | `#faff6914` | 8 % opacity wash for subtle backgrounds. |
| `--signal-edge` | `#faff6940` | 25 % opacity for hover borders. |
| `--alert` | `#ff3d6e` | Negative-space accent. Errors, destructive actions. Used sparingly. |
| `--positive` | `#6dffa1` | Success states. Used sparingly. |
| `--ink-link` | `#7dd3fc` (dark) / `#0284c7` (light) | Inline-link underline color. Distinct from `--signal`. |

### Contrast budget

- `#faff69` on `#0a0a0c` — measured 17.4:1. Passes WCAG AAA for normal + large text.
- `#f4f4f5` on `#0a0a0c` — 15.8:1. AAA.
- `#a1a1aa` on `#0a0a0c` — 7.4:1. AAA for normal text.
- `#7dd3fc` on `#0a0a0c` — 9.6:1. AAA. Passes 4.5:1 AA at 14 px.
- `#faff69` on `#fafaf9` — 1.6:1. **Fails AA for text.** Light-theme rule: `#faff69` is decorative-only on light bg; ANY signal-on-light text uses `#a3a302` or higher.

## 3. Typography

| Role | Font | Weights loaded | Notes |
|---|---|---|---|
| Display | **Inter Tight** | 500, 600, 700 | h1, h2, hero. Tight letter-spacing (-0.02 em). |
| Body | **Inter** | 400, 500, 600 | All running text. `font-feature-settings: 'tnum' 1, 'cv11' 1` — tabular numerals always on, stylistic alt for single-story `a`. |
| Mono | **JetBrains Mono** | 400, 500 | Code, labels, stats, badges. Tabular by default. |

Loaded as a single Google Fonts request:

```
https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap
```

`font-feature-settings: 'tnum' 1` is set globally on `body`. Numbers in tables, stat readouts, and price/count displays will line up across rows without manual `tabular-nums` classes.

### Type scale (fluid, `clamp()`)

| Token | Min | Max | Notes |
|---|---|---|---|
| `--text-xs` | 12 px | 12.8 px | Labels, badges. |
| `--text-sm` | 13 px | 14 px | Card meta. |
| `--text-base` | 15 px | 16.8 px | Body. |
| `--text-lg` | 18 px | 21.6 px | Card titles. |
| `--text-xl` | 24 px | 32 px | Section h2. |
| `--text-2xl` | 32 px | 48 px | Page h1. |
| `--text-3xl` | 40 px | 64 px | Hero h1. |
| `--text-4xl` | 48 px | 80 px | Marketing hero only. |

Body line-height is `1.55` (Inter at 16 px ideal). Display line-height is `1.05` (Inter Tight tight). Mono line-height is `1.45`.

## 4. Components

### Buttons (primary, secondary, ghost, link)

| Tier | Background | Border | Text | When |
|---|---|---|---|---|
| **Primary** | `--signal` (`#faff69`) | none | `#0a0a0c` | ONE per page. The single conversion action. |
| **Secondary** | transparent | `1 px solid --rule` | `--ink` | All other actions. Hover: border becomes `--rule-bright`. |
| **Ghost** | transparent | none | `--ink-2` | Tertiary, in-context actions. Hover: text becomes `--ink`. |
| **Link** | n/a | n/a | `--ink-link` | Inline links in body copy. Underline default; offset 2 px. |

Buttons are **never** `box-shadow`'d. Never gradient-filled. Never have a colored hover-background that isn't `--signal-tint` or `--rule`.

### Cards (3 tiers — preserved from prior system)

| Tier | Padding | Radius | Border | Use |
|---|---|---|---|---|
| **Compact** | 16 px | 6 px | `1 px solid --rule` on hover only | Search results, dense grids. |
| **Standard** | 24 px | 8 px | `1 px solid --rule` always | Plugin/skill detail cards. |
| **Featured** | 32 px | 12 px | `1 px solid --rule` always; `--signal-edge` on hover | Hall of fame, killer-skill spotlight. |

Cards are panels (`--panel`), not gradients. Hover state: `transform: translateY(-1 px)` (subtle), border tints to `--signal-edge` if it's a clickable hero card; otherwise border stays `--rule`. NEVER `box-shadow` lift on hover — that's the tell of an AI-generated layout.

### Tables

Hairline rules only. No alternating row stripes. Header-separator + bottom rule, nothing else. Tabular numerals (already global). Right-align numeric columns.

### Inputs

Bottom-rule input style: 1 px `--rule` bottom-border, transparent bg, no rounded corners, focus state turns the bottom rule `--signal`. Never the boxed-input shadow + border-radius treatment.

### Badges + tags

Mono font. 11 px. Border `1 px solid --rule`. Padding `2 px 8 px`. No background fill in the default state. Active/selected: bg `--signal-tint`, border `--signal-edge`, text `--ink`.

### Partner bar

Static row, no marquee. Hosts a `partners.json` config; renders 3-up at desktop, 2-up at mobile. When fewer than 5 entries, **never** loop on infinite scroll. Each partner: just the wordmark or logo lockup, no badge chrome around it. Hover: opacity 100 → 70.

## 5. Layout

### Breakpoint scale

| Token | Min width | Use |
|---|---|---|
| `--breakpoint-mobile` | 0 px | 1-column. |
| `--breakpoint-tablet` | 1024 px | 2-column. **Newly introduced.** Was missing before; 768 px → 1280 px jumped from 1-column to 3-column. |
| `--breakpoint-desktop` | 1280 px | 3-column. |
| `--breakpoint-wide` | 1536 px | 4-column for explore-page result grid only. |

### Spacing — 4 px grid (preserved)

`--space-1` (4 px) through `--space-12` (96 px). Padding pairs: hero `5 rem / 3.5 rem / 2 rem` (desktop / tablet / mobile). Section vertical: `var(--space-10)` desktop, `var(--space-6)` mobile.

### Container

Single canonical container `max-width: 1280 px; margin: 0 auto; padding: 0 var(--space-5);`. Hero may bleed full-bleed; everything else respects the container.

### Grid

Result grids use `grid-template-columns: repeat(auto-fill, minmax(320 px, 1 fr));` at desktop. At 1024 px (tablet): forced 2-column. At 768 px and below: forced 1-column.

## 6. Depth + motion

**Depth ladder is rule-based, not shadow-based.**

- Level 0: `--bg`
- Level 1: `--panel` on `--bg` (single 1 px `--rule` border)
- Level 2: `--panel-2` on `--panel` (modal-on-card, dropdown menus)
- Level 3 (rare): `box-shadow: 0 8 px 24 px #00000040` for true overlays (modals over the whole page)

Cards do NOT use `box-shadow`. Hover lift is `transform: translateY(-1 px)` only.

### Motion

| Duration | When |
|---|---|
| 100 ms | Hover state, button press feedback. |
| 200 ms | Card expand, accordion. |
| 300 ms | Modal open / close. |
| 0 ms | When `prefers-reduced-motion: reduce`. Already wired in `tokens.css`. |

Easing: `cubic-bezier(0.25, 1, 0.5, 1)` (`--ease-out`) for almost everything. `cubic-bezier(0.65, 0, 0.35, 1)` (`--ease-in-out`) for two-way animations.

No bouncy springs. No scale-up-on-hover on whole cards.

## 7. Do

- **One signal accent per page.** `#faff69` highlights the single primary CTA + the page's hero stat. That's it.
- **Hairlines do the work shadows used to do.** A 1 px `--rule` border separates panels; it doesn't need a drop-shadow to feel detached.
- **Tabular numerals always.** Set on `body`. Never override.
- **Mono for stats, codes, IDs, version numbers.** Never mono for body copy.
- **Card titles are display font, not body font.** Inter Tight 600.
- **Section headings have hairline rules under them.** Single 1 px `--rule` under h2 with `--space-3` margin-bottom.
- **Stat readouts use mono + tabular.** "1,537 skills" reads as `1,537` in JetBrains Mono.
- **Light theme is high-contrast off-white, not pure white.** `#fafaf9` canvas. Pure white is gallery-print; we're a terminal.
- **Test every change at 3 viewports.** 1440 / 1024 / 375 px.

## 8. Don't (Anti-Slop Reject Table)

These are the AI-generated-layout fingerprints. Reject on sight.

| Reject | Why |
|---|---|
| Gradient backgrounds (`linear-gradient(...)` on cards or sections) | Tell of a generic Tailwind starter. Use solid `--panel`. |
| Glassmorphism (`backdrop-filter: blur()` on cards or modals) | Default-aesthetic AI sludge. Solid panels with hairline rules. |
| Border-radius `md` (6–8 px) on every surface uniformly | Default Tailwind. Use the radius scale: 6 / 8 / 12 px deliberately by tier. |
| Drop-shadow stacks (`shadow-lg`, `shadow-xl`, `shadow-2xl`) | Replace with hairline rules + tonal `--panel-2` for hover. |
| Lucide / Heroicons next to every label | Decorative noise. Use icons only when they replace a word, not when they decorate one. |
| Slate-500 (or any gray) as body text on slate-900 bg | Low contrast. Use the OKLCH ink scale (`--ink`, `--ink-2`, `--ink-3`). |
| Multiple accent colors (purple + teal + orange "from the brand palette") | We have ONE accent: `#faff69`. Plus `--alert` and `--positive` for semantic states only. |
| Hover state = scale-up on whole card (`hover:scale-105`) | Mobile-touch breaks it; on desktop it reads as cheap. Use `translateY(-1 px)`. |
| Decorative gradient blobs / SVG ornament behind hero | The data IS the hero. Show the data. |
| Center-aligned body copy in long-form sections | Editorial copy reads left-aligned. Center-align is for marketing-page heroes only. |
| Font-weight 300 anywhere | Inter at 300 looks washed out on dark backgrounds. Minimum body weight: 400. |
| `text-gray-400 dark:text-gray-300` style theming | Use semantic tokens (`--ink-2`), not raw gray. |
| Different border-radius on every component within a single section | Pick one of the three tiers (compact/standard/featured) per section. |
| `border-2` or thicker on cards | Default-aesthetic. We use `1 px` everywhere. |
| Generic stock illustrations (undraw.co, illlustrations.co) | We don't ship illustrations. Type and tabular data ARE the illustration. |
| Soft pastel "AI" gradient on hero text (`bg-gradient-to-r from-purple-500 to-pink-500`) | The single most identifying mark of AI-generated landing pages. Hero text is solid `--ink` with `--signal` underline accent. |

## 9. Mobile

Mobile is a first-class workstream, not a desktop afterthought.

### Breakpoints (re-stated for emphasis)

- 0 → 768 px: 1-column. Hero padding 2 rem. Card grid forced 1-column.
- 768 → 1024 px: 1-column with wider hero. **NOT** the cramped mobile layout — paddings step up here.
- 1024 → 1280 px: 2-column. Hero padding 3.5 rem. **Newly introduced; was previously absent.**
- 1280 + : 3-column desktop.

### Touch targets

Every interactive element ≥ 44 × 44 px on mobile. This is the Apple HIG floor; Material says 48, we're meeting Apple's cutoff. Audit list the Mobile Specialist owns:

- `.partner-link` — must hit 44 × 44 even when wordmark is shorter
- `.nav-cta` — already pad-button-size, verify
- `.copy-btn` (install command) — currently undersized, fix
- `.filter-chip` — currently 32 × 28, must grow to 44 × 32 minimum
- `.sort-select` — verify dropdown trigger surface

### Filter rail (the explore-page sticky-bar problem)

The current `position: sticky; top: 80 px` filter rail consumes ~25 % of vertical viewport on phones. **Fix**: at viewports < 768 px, collapse the filter rail into a chip-row sheet. Tap a "Filters" chip to open a bottom sheet (or full-screen modal). On scroll, the sticky un-sticks below 100 px (filter goes away after first scroll, returns when user scrolls back up).

### Mobile performance budget (separate from desktop)

- First-load transferred bytes (HTML + render-blocking assets, gzipped) ≤ 250 KB on `/explore` and `/skills`
- Largest Contentful Paint ≤ 2.5 s on Slow 3G (1.6 Mbps simulated)
- Lighthouse mobile-performance score ≥ 80

Enforced by `node scripts/check-performance.mjs --mobile`.

### Mobile search input UX

- `inputmode="search"` and `enterkeyhint="search"` so iOS shows the search-key label.
- Sticky search bar on scroll-up only — not always-on. (Always-on fights thumb reach.)

### Card reflow on mobile

Each card on mobile shows: title + grade + 1-line description. Remaining metadata (author, version, install command, last-updated) collapses behind a tap-to-expand row. No horizontal scroll. No font-size reduction below `--text-sm` on body copy.

---

## Agent prompt guide

When using AI to generate or edit components for this site:

```
Use the design system in marketplace/DESIGN.md. Specifically:
- Single accent #faff69 used sparingly (one primary CTA per page).
- Solid panel #181818 on dark / #ffffff on light, separated by 1px hairline rules in #2a2a2e (dark) / #e5e5e3 (light).
- Inter Tight (display), Inter (body, with font-feature-settings: 'tnum'), JetBrains Mono (mono).
- No gradients. No glassmorphism. No drop-shadows on cards (hover is translateY(-1px)).
- Hairline rules instead of card-bg fills.
- Single signal accent #faff69 — never multi-accent.
- Reject the Anti-Slop fingerprints in DESIGN.md § 8.
- Reference design tokens via var(--token-name); never raw hex.
```

Paste that block into any prompt that asks AI to render UI for this codebase.

---

## Changelog

- **2026-06-03** — VibeCheck PR 1 follow-up. The 2026-05-31 pass flattened radii, removed gradients/blur, and added `lint-design-tells.mjs`. This pass targets the residual AI-tell layouts on the highest-visibility page (homepage `/`):
  1. **Rules over boxes — operative on the homepage feature list.** The 6-tile 3-column emoji-icon `.feature-card` grid (Signals 1, 6, 7 from the VibeCheck audit: card chrome + icon-in-colored-box + equal-column grid) is replaced with a numbered horizontal-rule list (`<ol class="features-list">`). Each row: mono numeric kicker (`01`–`06`), title, single-line description. No box wrappers, no decorative icons, no equal-column grid. Hairline rules carry the structure.
  2. **Dead `--purple` token removed from `pages/tools.astro`.** The 2026-05-06 redesign left an unused `--purple: #8b5cf6` declaration. The accent palette is intentionally yellow-only (`--signal`); secondary `--blue` and `--orange` remain because they're actually referenced.
  3. Existing `lint-design-tells.mjs` gates continue to pass (em-dash density in visible chrome: 1 / threshold 12). Mass em-dash hand-editing across `pages/` (346 raw hits) deferred — the lint's narrow scope already catches the ones that affect render.
  4. **Follow-up PR scope:** 31 vendor `/learn/<vendor>/` templates and ~20 secondary pages still carry card-chrome wrappers. They're already gradient-stripped from the 2026-05-31 pass, so the residual is structural (not visual) and can land incrementally without breaking the visual constitution.

- **2026-05-31** — VibeCheck audit (vibecheck.fail) returned 25/100 on the deployed site. Investigation found constitution drift: ~190 `linear-gradient` declarations and ~230 large-radius card chrome surfaces across components and pages, in direct contradiction of §1 and §8. Enforcement actions:
  1. Border-radius scale flattened to 2 px across all tiers (`--radius-sm/md/lg/xl`). Square corners are the anti-default; pills and tags still get the small radius. Circles (`50%`) and 1 px hairlines untouched.
  2. All chrome `linear-gradient` declarations replaced with solid tokens. Allowlist: `mask-image: linear-gradient(...)` for progressive scroll fades.
  3. `backdrop-filter: blur()` removed from `BaseLayout` nav and elsewhere; nav now sits on solid `--bg` with `border-bottom: 1px solid var(--rule)`.
  4. Vendor `/learn/<vendor>/` template (31 pages) had its orange-gradient hero and four metallic tier-badge gradients replaced with solid tokens.
  5. **New CI gate**: `scripts/lint-design-tells.mjs` runs every build. Blocks on any `linear-gradient` in chrome paths, any `backdrop-blur|backdrop-filter` (except explicit `: none` resets), any `(bg|from|via|to|text|border)-(purple|indigo|violet)-N` utility, and em-dash density >12 in visible-chrome files (Hero / components / index / explore / getting-started). Run `--strict` to tighten thresholds.
  6. Hero copy stripped of "Production-Ready / definitive / Supercharge / battle-tested" — that vocabulary is the linguistic equivalent of glassmorphism.

  Rule reinforced: **Rules over boxes.** A 1 px hairline above a section heading is the canonical separator. A rounded panel is the anti-pattern, not the default. The 2026-05-06 design family was correct; the components had drifted from it.

- **2026-05-06** — Constitution authored. Family locked to Data-Dense Pro. Warm-terracotta + Instrument Sans / Source Sans 3 / DM Mono retired. Token *names* preserved (downstream-compatible swap); values replaced wholesale.

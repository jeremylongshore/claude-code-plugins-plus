---
name: form-tokens
description: |
  Use when asked to define a design token system, create tokens, document tokens, set up CSS custom properties, build a Tailwind token config, establish a spacing scale, define color semantics, or bridge design decisions to code. Examples: "set up design tokens", "define our token system", "create CSS variables for the design system", "document our color tokens", "establish a spacing scale".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Form Tokens

You are Form — the visual designer on the Product Team.

Design tokens are the contract between design and code. They are not a deliverable — they are infrastructure. Every color, spacing value, and type size in the product should reference a token. This skill has 5 phases. Move through them in order. Do not skip phases.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

---

## Phase 1: Discovery

Before producing any tokens, you need to understand what already exists and what constraints apply. Ask these questions. Group them naturally — do not fire them as a list.

### Brand foundation

- Has `form-brand` been run? Is there a brand brief with a defined palette, type system, and visual language?
- If no brand brief exists, **stop here**. Run `form-brand` first. Tokens are downstream of brand decisions — defining tokens without a brand is building on sand.

### Tech stack

- What is the target stack? (CSS custom properties, Tailwind CSS, Style Dictionary, a design tool like Figma variables?)
- Is there an existing token file or partial system to audit, or are we starting from zero?
- Do tokens need to be exported to multiple formats (JSON, SCSS, Tailwind config, iOS Swift, Android XML)?

### Platform targets

- Which platforms need tokens? (Web, iOS, Android, email, print?)
- Multi-platform targets require Style Dictionary or an equivalent build step — flag this early if relevant.

### Existing constraints

- Are there hardcoded hex values, magic numbers, or inline styles in the codebase right now? (These are the things tokens will replace.)
- Is there a dark mode requirement today, or is it planned for the future? (The answer changes how semantic tokens are structured from day one.)

**Done when:** You know the brand state, the stack, the platforms, and whether dark mode is in scope.

---

## Phase 2: Token Architecture

Before producing a single token, explain the two-tier model. Do not skip this explanation — it is why the system works, and teams who skip it break it later.

### The two-tier model

**Primitive tokens** are raw values with no semantic meaning. They name a value, not a purpose.

```css
--color-blue-100: #e6eeff;
--color-blue-200: #b3caff;
--color-blue-300: #80a8ff;
--color-blue-400: #4d85ff;
--color-blue-500: #0057ff;
--color-blue-600: #0047d6;
--color-blue-700: #0038ad;
--color-blue-800: #002884;
--color-blue-900: #001a5c;

--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;
```

Primitives live in one place. They are never referenced directly in components.

**Semantic tokens** are meaning-bearing aliases that point to primitives. They name a purpose, not a value.

```css
--color-action-primary: var(--color-blue-500);
--color-action-primary-hover: var(--color-blue-600);
--color-action-primary-active: var(--color-blue-700);
--color-text-default: var(--color-gray-900);
--color-text-muted: var(--color-gray-500);
--color-surface-default: var(--color-gray-50);
```

Semantic tokens are what components reference. Always.

### The rule

```
Component → semantic token → primitive token → raw value
```

A button never references `--color-blue-500` directly. It references `--color-action-primary`, which happens to point to `--color-blue-500` today. When the brand color changes, one primitive changes, one semantic alias updates, and every component that references `--color-action-primary` updates automatically — with zero component changes.

This is the whole point of the system.

### Confirm understanding before proceeding

Ask the team to confirm they understand the two-tier model and the rule above. If there is any hesitation, work through a concrete example from their existing UI before continuing.

---

## Design Intelligence (via uiux)

After confirming token architecture (Phase 2), use the design system generator to seed initial token values:

```bash
python3 -m form_agent.uiux design-system --product-type "{product_type}"
```

Use the generated design system output to:

- Seed primitive color tokens from the industry-matched palette
- Seed typography tokens from the recommended font pairing
- Validate spacing and effect choices against the style recommendation

---

## Phase 3: Token Categories

Define tokens in this order. Each category builds on the previous.

---

### 3.1 Color Primitives

Full palette scales for each hue in the brand. Use 50–900 steps. 500 is the base hue — not necessarily the one used most, but the reference point for the scale.

Derive values systematically from the brand's primary, secondary, neutral, and any accent colors. Do not invent hues that were not established in the brand brief.

```css
/* ── Color Primitives ────────────────────────────────────── */

/* Brand primary */
--color-indigo-50: #eef2ff;
--color-indigo-100: #e0e7ff;
--color-indigo-200: #c7d2fe;
--color-indigo-300: #a5b4fc;
--color-indigo-400: #818cf8;
--color-indigo-500: #6366f1;
--color-indigo-600: #4f46e5;
--color-indigo-700: #4338ca;
--color-indigo-800: #3730a3;
--color-indigo-900: #312e81;

/* Neutral */
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;

/* Feedback palettes */
--color-green-50: #f0fdf4;
--color-green-500: #22c55e;
--color-green-700: #15803d;
--color-green-900: #14532d;

--color-yellow-50: #fefce8;
--color-yellow-500: #eab308;
--color-yellow-700: #a16207;
--color-yellow-900: #713f12;

--color-red-50: #fff1f2;
--color-red-500: #f43f5e;
--color-red-700: #be123c;
--color-red-900: #881337;

--color-blue-50: #eff6ff;
--color-blue-500: #3b82f6;
--color-blue-700: #1d4ed8;
--color-blue-900: #1e3a8a;

/* Absolute */
--color-white: #ffffff;
--color-black: #000000;
```

---

### 3.2 Color Semantic

Group semantic tokens by role. Name them by purpose, never by value.

Document use rules with every group: where each token appears, and where it must not.

```css
/* ── Color Semantic: Surface ─────────────────────────────── */
/* Surfaces are backgrounds — page, panel, card, input, overlay */

--color-surface-page: var(--color-gray-50); /* Root page background */
--color-surface-default: var(--color-white); /* Cards, panels, modals */
--color-surface-raised: var(
  --color-white
); /* Elevated surfaces — use with shadow tokens */
--color-surface-sunken: var(
  --color-gray-100
); /* Input fields, well backgrounds */
--color-surface-overlay: var(--color-white); /* Dropdown menus, popovers */
--color-surface-subtle: var(
  --color-gray-100
); /* Hover states on non-interactive areas */

/* DO NOT use surface tokens for text, borders, or icons */

/* ── Color Semantic: Text ────────────────────────────────── */
/* Text tokens govern all typographic content */

--color-text-default: var(
  --color-gray-900
); /* Body copy, headings — default readable text */
--color-text-muted: var(
  --color-gray-500
); /* Secondary text, captions, placeholders */
--color-text-subtle: var(
  --color-gray-400
); /* Disabled text, decorative labels */
--color-text-inverse: var(--color-white); /* Text on dark/colored backgrounds */
--color-text-link: var(--color-indigo-600); /* Inline links */
--color-text-link-hover: var(--color-indigo-700); /* Inline links on hover */

/* DO NOT use --color-text-muted for interactive elements — use action tokens */

/* ── Color Semantic: Border ──────────────────────────────── */
/* Borders define structure — dividers, outlines, rings */

--color-border-default: var(
  --color-gray-200
); /* Default dividers, card edges */
--color-border-strong: var(
  --color-gray-300
); /* Emphasized dividers, section breaks */
--color-border-focus: var(
  --color-indigo-500
); /* Focus rings on interactive elements */
--color-border-error: var(--color-red-500); /* Error state borders on inputs */

/* DO NOT use --color-border-default for focus rings — always use --color-border-focus */

/* ── Color Semantic: Action ──────────────────────────────── */
/* Actions drive user intent — buttons, links, triggers */

--color-action-primary: var(--color-indigo-600);
--color-action-primary-hover: var(--color-indigo-700);
--color-action-primary-active: var(--color-indigo-800);
--color-action-primary-text: var(--color-white);

--color-action-secondary: var(--color-gray-100);
--color-action-secondary-hover: var(--color-gray-200);
--color-action-secondary-active: var(--color-gray-300);
--color-action-secondary-text: var(--color-gray-900);

--color-action-destructive: var(--color-red-600);
--color-action-destructive-hover: var(--color-red-700);
--color-action-destructive-text: var(--color-white);

--color-action-disabled-bg: var(--color-gray-100);
--color-action-disabled-text: var(--color-gray-400);

/* DO NOT hardcode hover/active states in component code — use action tokens */

/* ── Color Semantic: Feedback ────────────────────────────── */
/* Feedback communicates system status — alerts, banners, badges, toasts */

--color-feedback-success-bg: var(--color-green-50);
--color-feedback-success-border: var(--color-green-500);
--color-feedback-success-text: var(--color-green-700);
--color-feedback-success-icon: var(--color-green-500);

--color-feedback-warning-bg: var(--color-yellow-50);
--color-feedback-warning-border: var(--color-yellow-500);
--color-feedback-warning-text: var(--color-yellow-700);
--color-feedback-warning-icon: var(--color-yellow-500);

--color-feedback-error-bg: var(--color-red-50);
--color-feedback-error-border: var(--color-red-500);
--color-feedback-error-text: var(--color-red-700);
--color-feedback-error-icon: var(--color-red-500);

--color-feedback-info-bg: var(--color-blue-50);
--color-feedback-info-border: var(--color-blue-500);
--color-feedback-info-text: var(--color-blue-700);
--color-feedback-info-icon: var(--color-blue-500);

/* DO NOT use raw primitive colors in alert/toast components — always use feedback tokens */
```

---

### 3.3 Spacing Scale

All spacing derives from a single base unit: **8px**. No arbitrary values.

```css
/* ── Spacing ─────────────────────────────────────────────── */
/* Base unit: 8px. Every value is a multiple or half-multiple of 8. */

--space-1: 4px; /* 0.5× — tight internal padding, icon gaps */
--space-2: 8px; /* 1×  — default small gap, icon padding */
--space-3: 12px; /* 1.5× — compact list item padding */
--space-4: 16px; /* 2×  — default component padding */
--space-6: 24px; /* 3×  — section internal spacing */
--space-8: 32px; /* 4×  — card padding, form field gap */
--space-12: 48px; /* 6×  — section padding, large gap */
--space-16: 64px; /* 8×  — page section rhythm */
--space-24: 96px; /* 12× — hero spacing, major breakpoints */
```

Token names map to the multiplier (--space-4 = 4px × the multiplier naming convention tracks with Tailwind's default scale). Adjust naming to match your stack — what matters is the math, not the names.

Rule: if a spacing value is not on this scale, it does not go in the code. Raise a design question first.

---

### 3.4 Typography

Define font family, size scale, weight scale, and line-height scale as separate token groups.

```css
/* ── Typography: Font Family ─────────────────────────────── */

--font-sans: "Inter", "Helvetica Neue", Arial, sans-serif;
--font-serif: "Merriweather", Georgia, serif; /* editorial use only */
--font-mono: "JetBrains Mono", "Fira Code", monospace; /* code, data */

/* ── Typography: Size Scale ──────────────────────────────── */
/* Modular scale — each step ×1.25 (major third) from 16px base */

--text-xs: 12px; /* Labels, captions, badges */
--text-sm: 14px; /* Secondary body, input fields */
--text-base: 16px; /* Primary body copy */
--text-lg: 18px; /* Large body, lead paragraphs */
--text-xl: 20px; /* Small headings */
--text-2xl: 24px; /* Section headings */
--text-3xl: 30px; /* Page headings */
--text-4xl: 36px; /* Hero subheadings */
--text-5xl: 48px; /* Hero headings */
--text-6xl: 60px; /* Display / marketing */

/* ── Typography: Weight Scale ────────────────────────────── */

--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* ── Typography: Line Height ─────────────────────────────── */

--leading-none: 1; /* Display type only — no space between lines */
--leading-tight: 1.25; /* Headings */
--leading-snug: 1.375; /* Subheadings, callouts */
--leading-normal: 1.5; /* Body copy — default */
--leading-relaxed: 1.625; /* Long-form reading */
--leading-loose: 2; /* Captions, labels with extra air */

/* ── Typography: Letter Spacing ──────────────────────────── */

--tracking-tight: -0.025em; /* Large headings */
--tracking-normal: 0; /* Default */
--tracking-wide: 0.025em; /* UI labels, buttons */
--tracking-wider: 0.05em; /* Caps labels, badges */
--tracking-widest: 0.1em; /* Overlines, legal text */
```

---

### 3.5 Border Radius

```css
/* ── Border Radius ───────────────────────────────────────── */

--radius-none: 0; /* Sharp — tables, data-dense UIs */
--radius-sm: 2px; /* Subtle rounding — badges, tags */
--radius-base: 4px; /* Default — inputs, buttons */
--radius-md: 6px; /* Cards, panels */
--radius-lg: 8px; /* Modals, drawers */
--radius-xl: 12px; /* Feature cards, image containers */
--radius-2xl: 16px; /* Large surface rounding */
--radius-full: 9999px; /* Pill — tags, avatars, toggle thumbs */
```

---

### 3.6 Shadow / Elevation

Elevation communicates layer height. Use consistently — don't reach for a deeper shadow for emphasis when border or color is the right tool.

```css
/* ── Shadow / Elevation ──────────────────────────────────── */
/* Level 0: flat — no shadow. Used for page and panel backgrounds. */

--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
/* Level 1 — Buttons, inputs, subtle surface lift */

--shadow-base: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
/* Level 2 — Cards, dropdowns, date pickers */

--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
/* Level 3 — Floating panels, contextual menus */

--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
/* Level 4 — Modals, dialogs */

--shadow-xl:
  0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
/* Level 5 — Full-screen overlays, toast notifications */
```

---

### 3.7 Z-Index (Named Layers)

Z-index wars happen when values are chosen arbitrarily. Named layers end them.

```css
/* ── Z-Index ─────────────────────────────────────────────── */

--z-base: 0; /* Normal document flow */
--z-raised: 10; /* Sticky headers, floating action buttons */
--z-dropdown: 100; /* Dropdown menus, autocomplete lists */
--z-sticky: 200; /* Sticky navigation */
--z-overlay: 300; /* Backdrop overlays (behind modals) */
--z-modal: 400; /* Modals, dialogs, drawers */
--z-toast: 500; /* Toast notifications (above modals) */
--z-tooltip: 600; /* Tooltips (above everything interactive) */
```

Rule: never use a raw integer for z-index in component code. Always reference a named layer. If the existing layers do not fit the need, add a named layer here — do not hardcode 9999.

---

### 3.8 Motion

```css
/* ── Motion: Duration ────────────────────────────────────── */

--duration-instant: 0ms; /* Immediate — no animation (reduced-motion fallback) */
--duration-fast: 100ms; /* Micro-interactions — button press, toggle */
--duration-normal: 200ms; /* Standard — state transitions, hover */
--duration-slow: 300ms; /* Deliberate — panel open, modal enter */
--duration-slower: 500ms; /* Narrative — page transitions, hero animations */

/* ── Motion: Easing ──────────────────────────────────────── */

--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1); /* Exits — elements leaving the screen */
--ease-out: cubic-bezier(0, 0, 0.2, 1); /* Entrances — elements arriving */
--ease-in-out: cubic-bezier(
  0.4,
  0,
  0.2,
  1
); /* State changes — two-way transitions */
--ease-spring: cubic-bezier(
  0.34,
  1.56,
  0.64,
  1
); /* Playful spring — toggles, thumbs */
```

Use `--ease-out` for entrances (user is waiting for something to appear — make it feel immediate). Use `--ease-in` for exits (user triggered the dismissal — don't slow them down). Use `--ease-in-out` for transitions where direction is ambiguous.

Always implement `@media (prefers-reduced-motion: reduce)` — swap durations to `--duration-instant` and easing to `--ease-linear`.

---

## Phase 4: Output Format

### CSS custom properties block

Deliver all tokens in a single `:root` block (light mode defaults), organized by category with clear section comments. The order from Phase 3 is the output order.

```css
:root {
  /* Color Primitives */
  /* ... */

  /* Color Semantic: Surface */
  /* ... */

  /* Color Semantic: Text */
  /* ... */

  /* Color Semantic: Border */
  /* ... */

  /* Color Semantic: Action */
  /* ... */

  /* Color Semantic: Feedback */
  /* ... */

  /* Spacing */
  /* ... */

  /* Typography */
  /* ... */

  /* Border Radius */
  /* ... */

  /* Shadow */
  /* ... */

  /* Z-Index */
  /* ... */

  /* Motion */
  /* ... */
}
```

### Tailwind config mapping (if applicable)

If the project uses Tailwind CSS, produce a `tailwind.config.js` that maps tokens to Tailwind's `theme.extend` using `var()` references. Do not duplicate raw values — Tailwind reads from the custom properties defined in `:root`.

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        "action-primary": "var(--color-action-primary)",
        "action-primary-hover": "var(--color-action-primary-hover)",
        "action-secondary": "var(--color-action-secondary)",
        "text-default": "var(--color-text-default)",
        "text-muted": "var(--color-text-muted)",
        "surface-page": "var(--color-surface-page)",
        "surface-default": "var(--color-surface-default)",
        "border-default": "var(--color-border-default)",
        "border-focus": "var(--color-border-focus)",
        "feedback-success-bg": "var(--color-feedback-success-bg)",
        "feedback-error-bg": "var(--color-feedback-error-bg)",
        // ... complete the mapping
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        12: "var(--space-12)",
        16: "var(--space-16)",
        24: "var(--space-24)",
      },
      fontFamily: {
        sans: "var(--font-sans)",
        serif: "var(--font-serif)",
        mono: "var(--font-mono)",
      },
      fontSize: {
        xs: "var(--text-xs)",
        sm: "var(--text-sm)",
        base: "var(--text-base)",
        lg: "var(--text-lg)",
        xl: "var(--text-xl)",
        "2xl": "var(--text-2xl)",
        "3xl": "var(--text-3xl)",
        "4xl": "var(--text-4xl)",
        "5xl": "var(--text-5xl)",
        "6xl": "var(--text-6xl)",
      },
      borderRadius: {
        none: "var(--radius-none)",
        sm: "var(--radius-sm)",
        DEFAULT: "var(--radius-base)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        DEFAULT: "var(--shadow-base)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
      },
      zIndex: {
        base: "var(--z-base)",
        raised: "var(--z-raised)",
        dropdown: "var(--z-dropdown)",
        sticky: "var(--z-sticky)",
        overlay: "var(--z-overlay)",
        modal: "var(--z-modal)",
        toast: "var(--z-toast)",
        tooltip: "var(--z-tooltip)",
      },
      transitionDuration: {
        instant: "var(--duration-instant)",
        fast: "var(--duration-fast)",
        normal: "var(--duration-normal)",
        slow: "var(--duration-slow)",
        slower: "var(--duration-slower)",
      },
    },
  },
};
```

### Style Dictionary (if multi-platform)

If tokens need to reach iOS or Android, recommend Style Dictionary as the build step. Produce the source JSON token file and a `config.json`. The CSS custom properties block above becomes one of the output formats — not the source of truth. Style Dictionary JSON is the source.

---

## Phase 5: Dark Mode

Dark mode is not light mode inverted. Every semantic token needs an explicit value for dark mode. Explain this before proceeding.

### The wrong approach

```css
/* WRONG — DO NOT DO THIS */
html[data-theme="dark"] {
  filter: invert(1) hue-rotate(180deg);
}
```

This inverts images, photos, and icons. It produces incorrect colors for feedback states. It is a hack, not a system.

### The right approach

Redefine every semantic token under a `[data-theme="dark"]` selector (or `@media (prefers-color-scheme: dark)` — choose one strategy and stay consistent). Primitives do not change. Semantic tokens point to different primitives.

```css
[data-theme="dark"] {
  /* Surface */
  --color-surface-page: var(--color-gray-900);
  --color-surface-default: var(--color-gray-800);
  --color-surface-raised: var(--color-gray-800);
  --color-surface-sunken: var(--color-gray-900);
  --color-surface-overlay: var(--color-gray-800);
  --color-surface-subtle: var(--color-gray-700);

  /* Text */
  --color-text-default: var(--color-gray-50);
  --color-text-muted: var(--color-gray-400);
  --color-text-subtle: var(--color-gray-600);
  --color-text-inverse: var(--color-gray-900);
  --color-text-link: var(--color-indigo-400);
  --color-text-link-hover: var(--color-indigo-300);

  /* Border */
  --color-border-default: var(--color-gray-700);
  --color-border-strong: var(--color-gray-600);
  --color-border-focus: var(--color-indigo-400);
  --color-border-error: var(--color-red-400);

  /* Action */
  --color-action-primary: var(--color-indigo-500);
  --color-action-primary-hover: var(--color-indigo-400);
  --color-action-primary-active: var(--color-indigo-300);
  --color-action-primary-text: var(--color-white);

  --color-action-secondary: var(--color-gray-700);
  --color-action-secondary-hover: var(--color-gray-600);
  --color-action-secondary-active: var(--color-gray-500);
  --color-action-secondary-text: var(--color-gray-100);

  --color-action-destructive: var(--color-red-500);
  --color-action-destructive-hover: var(--color-red-400);
  --color-action-destructive-text: var(--color-white);

  --color-action-disabled-bg: var(--color-gray-800);
  --color-action-disabled-text: var(--color-gray-600);

  /* Feedback */
  --color-feedback-success-bg: var(--color-green-900);
  --color-feedback-success-border: var(--color-green-500);
  --color-feedback-success-text: var(--color-green-50);
  --color-feedback-success-icon: var(--color-green-500);

  --color-feedback-warning-bg: var(--color-yellow-900);
  --color-feedback-warning-border: var(--color-yellow-500);
  --color-feedback-warning-text: var(--color-yellow-50);
  --color-feedback-warning-icon: var(--color-yellow-500);

  --color-feedback-error-bg: var(--color-red-900);
  --color-feedback-error-border: var(--color-red-500);
  --color-feedback-error-text: var(--color-red-50);
  --color-feedback-error-icon: var(--color-red-500);

  --color-feedback-info-bg: var(--color-blue-900);
  --color-feedback-info-border: var(--color-blue-500);
  --color-feedback-info-text: var(--color-blue-50);
  --color-feedback-info-icon: var(--color-blue-500);
}
```

Notice: dark mode feedback tokens do NOT use `-50` background primitives (which are near-white). They use `-900` primitives (deep, desaturated). Dark mode is not a mirror — it is a separate set of decisions.

### Dark mode checklist

```
[ ] Every semantic token has an explicit dark value
[ ] Feedback backgrounds use deep palette values, not inverted light values
[ ] Text muted color passes 3:1 contrast on dark surface
[ ] Primary action color passes 4.5:1 contrast on dark surface
[ ] Focus ring is visible on all dark surfaces
[ ] No filter: invert() anywhere in the codebase
[ ] prefers-color-scheme and data-theme strategies are consistent — pick one
```

---

## Anti-Patterns

- **Semantic tokens that describe values, not purpose** — `--color-blue` instead of `--color-action-primary`. When the brand color changes from blue to teal, `--color-blue` breaks. `--color-action-primary` does not.
- **Components that hardcode hex values** — any `#hex` in a component file is a token debt. Every hex in a component is a future theming bug.
- **Dark mode as `filter: invert()`** — inverts photos, corrupts feedback colors, and signals the team has no token system.
- **Dark mode as "just swap light and dark"** — naive inversion produces incorrect contrast ratios and broken feedback states. Dark mode requires explicit decisions.
- **Spacing values that aren't on the scale** — `margin: 13px` is a design decision that never got made. Surface it, snap it to the scale.
- **No z-index system** — `z-index: 9999` is a symptom. Named layers are the cure.
- **Semantic tokens that skip the primitive tier** — `--color-action-primary: #4F46E5` works, but it breaks the one-edit-propagates-everywhere guarantee. Always alias through a primitive.
- **Incomplete dark token sets** — a semantic token without a dark value defaults to its light value in dark mode. This is always wrong, rarely intentional, and hard to catch in review.

---

## Delivery Checklist

Before handing the token system to engineering, verify:

```
[ ] Brand brief confirmed — tokens derive from documented brand decisions
[ ] Two-tier model in place — primitives and semantic layers both exist
[ ] No component in the codebase references a primitive token directly
[ ] All 8 token categories defined: color primitives, color semantic, spacing,
    typography, border radius, shadow, z-index, motion
[ ] Spacing scale derives from 8px base — no arbitrary values
[ ] Every semantic token has documented use rules (where it appears, where it must not)
[ ] Dark mode: explicit values for every semantic token
[ ] Dark mode: feedback tokens use deep palette values, not inverted light values
[ ] Tailwind config (or equivalent) produced if applicable
[ ] Reduced-motion handled in motion tokens
[ ] Token file delivered as a single importable CSS file (or Style Dictionary source if multi-platform)
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.

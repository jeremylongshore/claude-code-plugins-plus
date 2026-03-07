# Theming & Dark Mode Design

Creating effective color themes and implementing dark mode correctly.

## Dark Mode Philosophy

Dark mode isn't just inverting colors—it requires deliberate design decisions to maintain usability, hierarchy, and aesthetics.

### Why Dark Mode Matters

- **User preference:** Many users prefer it
- **Eye strain:** Reduces strain in low-light environments
- **Battery life:** Saves power on OLED screens
- **Accessibility:** Some users have photosensitivity
- **Professional expectation:** Users expect modern apps to support it

---

## Dark Mode Color Principles

### Don't Just Invert

| Light Mode | Bad Dark Mode | Good Dark Mode |
|------------|---------------|----------------|
| White `#ffffff` | Black `#000000` | Dark gray `#18181b` |
| Black text `#000000` | White text `#ffffff` | Off-white `#fafafa` |
| Gray `#6b7280` | Gray `#6b7280` | Lighter gray `#a1a1aa` |

### Key Principles

**1. Use dark grays, not pure black**

Pure black (`#000000`) creates harsh contrast and "halation" (text appears to glow).

```css
/* Background scale for dark mode */
--bg-base: #09090b;      /* Deepest background */
--bg-subtle: #18181b;    /* Cards, elevated surfaces */
--bg-muted: #27272a;     /* Hover states, inputs */
--bg-emphasis: #3f3f46;  /* Active states */
```

**2. Reduce contrast slightly**

Max contrast in dark mode is harsher than in light mode.

```css
/* Text colors for dark mode */
--text-primary: #fafafa;   /* ~95% white, not 100% */
--text-secondary: #a1a1aa; /* Muted text */
--text-tertiary: #71717a;  /* Subtle text */
```

**3. Desaturate colors**

Bright saturated colors on dark backgrounds cause eye strain.

```css
/* Light mode brand color */
--primary-light: #3b82f6;  /* Bright blue */

/* Dark mode - slightly desaturated */
--primary-dark: #60a5fa;   /* Lighter, less saturated */
```

**4. Elevate with lightness, not shadow**

In dark mode, shadows are invisible. Show elevation with lighter surfaces.

```css
/* Light mode: shadow for depth */
.card-light {
  background: white;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Dark mode: lighter surface for depth */
.card-dark {
  background: #27272a;  /* Lighter than base */
  box-shadow: none;     /* Or very subtle */
}
```

---

## Building a Dark Mode Palette

### Step 1: Define Your Gray Scale

Create 9-10 shades from near-black to near-white:

```css
/* Dark mode gray scale (Zinc example) */
--gray-950: #09090b;  /* Deepest background */
--gray-900: #18181b;  /* Card backgrounds */
--gray-800: #27272a;  /* Elevated surfaces */
--gray-700: #3f3f46;  /* Borders, dividers */
--gray-600: #52525b;  /* Disabled states */
--gray-500: #71717a;  /* Placeholder text */
--gray-400: #a1a1aa;  /* Secondary text */
--gray-300: #d4d4d8;  /* Primary text (alt) */
--gray-200: #e4e4e7;  /* Headings */
--gray-100: #f4f4f5;  /* Emphasis text */
--gray-50:  #fafafa;  /* Primary text */
```

### Step 2: Adjust Accent Colors

```css
/* Primary color adjustments */
/* Light mode: use 500-600 range */
--primary-light: #2563eb;

/* Dark mode: use 400-500 range (lighter) */
--primary-dark: #3b82f6;

/* Same for semantic colors */
--success-light: #16a34a;
--success-dark: #22c55e;

--error-light: #dc2626;
--error-dark: #ef4444;
```

### Step 3: Define Semantic Tokens

```css
/* Semantic tokens that switch based on mode */
:root {
  --color-bg: var(--gray-50);
  --color-bg-subtle: var(--gray-100);
  --color-text: var(--gray-900);
  --color-text-muted: var(--gray-600);
  --color-border: var(--gray-200);
  --color-primary: var(--blue-600);
}

[data-theme="dark"] {
  --color-bg: var(--gray-950);
  --color-bg-subtle: var(--gray-900);
  --color-text: var(--gray-50);
  --color-text-muted: var(--gray-400);
  --color-border: var(--gray-800);
  --color-primary: var(--blue-400);
}
```

---

## Implementation Strategies

### Strategy 1: CSS Custom Properties

```css
:root {
  --bg: #ffffff;
  --text: #18181b;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #18181b;
    --text: #fafafa;
  }
}

body {
  background: var(--bg);
  color: var(--text);
}
```

### Strategy 2: Data Attribute + Class

```html
<html data-theme="dark">
```

```css
[data-theme="light"] {
  --bg: #ffffff;
}
[data-theme="dark"] {
  --bg: #18181b;
}
```

```javascript
// Toggle theme
function toggleTheme() {
  const current = document.documentElement.dataset.theme;
  document.documentElement.dataset.theme = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', document.documentElement.dataset.theme);
}

// Initialize from preference
function initTheme() {
  const saved = localStorage.getItem('theme');
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  document.documentElement.dataset.theme = saved || preferred;
}
```

### Strategy 3: Tailwind Dark Mode

```html
<!-- With class strategy -->
<html class="dark">
  <body class="bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50">
```

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // or 'media' for system preference only
}
```

---

## Component Considerations

### Cards and Surfaces

```css
/* Light: white with shadow */
.card {
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Dark: lighter surface, subtle or no shadow */
[data-theme="dark"] .card {
  background: var(--gray-900);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3); /* Darker shadow if any */
  /* Or: border: 1px solid var(--gray-800); */
}
```

### Form Inputs

```css
.input {
  background: white;
  border: 1px solid var(--gray-300);
}

[data-theme="dark"] .input {
  background: var(--gray-900);
  border: 1px solid var(--gray-700);
}
```

### Buttons

```css
/* Primary button */
.btn-primary {
  background: var(--primary);
  color: white;
}

[data-theme="dark"] .btn-primary {
  /* Often same or slightly adjusted */
  background: var(--primary-dark);
}

/* Secondary button */
.btn-secondary {
  background: var(--gray-100);
  color: var(--gray-900);
}

[data-theme="dark"] .btn-secondary {
  background: var(--gray-800);
  color: var(--gray-100);
}
```

### Images and Media

```css
/* Reduce brightness/contrast of images in dark mode */
[data-theme="dark"] img:not([data-no-dim]) {
  filter: brightness(0.9) contrast(1.1);
}

/* Invert diagrams/illustrations if needed */
[data-theme="dark"] .diagram {
  filter: invert(1) hue-rotate(180deg);
}
```

### Syntax Highlighting

Don't forget code blocks need dark mode variants:
- Use dark theme variants of syntax highlighters
- Or invert colors appropriately
- Popular: One Dark, Dracula, Night Owl

---

## Testing Dark Mode

### Checklist

- [ ] All text is readable (sufficient contrast)
- [ ] Hierarchy still clear (headings vs body)
- [ ] Focus states visible
- [ ] Images don't blow out
- [ ] Forms inputs clearly visible
- [ ] Error/success states distinct
- [ ] Loading states visible
- [ ] Shadows/elevation still work
- [ ] Icons visible (may need color swap)
- [ ] Brand colors still recognizable

### Contrast Ratios

Same WCAG requirements apply:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- UI components: 3:1 minimum

**Common dark mode fails:**
- Gray text on dark background
- Colored text on colored backgrounds
- Disabled states too subtle

---

## Theme Toggle UI

### Placement

- Header/navigation (most common)
- Settings page
- Footer (less common)

### Icon Patterns

```html
<!-- Sun/Moon toggle -->
<button aria-label="Toggle dark mode">
  <svg class="sun hidden dark:block">...</svg>
  <svg class="moon block dark:hidden">...</svg>
</button>
```

### State Options

1. **Light / Dark** - Simple toggle
2. **Light / Dark / System** - Respect OS preference option
3. **Auto only** - Always follow system (no toggle)

### Persistence

```javascript
// Save preference
localStorage.setItem('theme', 'dark');

// Load preference (with system fallback)
const theme = localStorage.getItem('theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
```

---

## Advanced: Multiple Themes

### Brand Themes

```css
[data-theme="brand-a"] {
  --primary: #ff6b6b;
  --primary-hover: #ee5a5a;
}

[data-theme="brand-b"] {
  --primary: #4ecdc4;
  --primary-hover: #3dbdb5;
}
```

### Theme Structure

```css
/* Base tokens (don't change) */
--spacing-4: 16px;
--radius-md: 8px;

/* Color tokens (change per theme) */
--color-primary: ...;
--color-bg: ...;

/* Component tokens (reference color tokens) */
--button-bg: var(--color-primary);
--card-bg: var(--color-bg);
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Pure black background | Harsh, looks flat | Use dark gray (#18181b) |
| Pure white text | Too much contrast | Use off-white (#fafafa) |
| Same saturated colors | Eye strain | Desaturate for dark mode |
| Shadows for elevation | Invisible in dark | Use lighter surfaces |
| Forgetting images | Can be too bright | Dim images slightly |
| One contrast check | Colors interact differently | Check all combinations |
| Forgetting focus states | Invisible borders | Ensure visible focus rings |

---

## Quick Reference

### Minimum Viable Dark Mode

```css
:root {
  --bg: #ffffff;
  --bg-subtle: #f4f4f5;
  --text: #18181b;
  --text-muted: #71717a;
  --border: #e4e4e7;
  --primary: #2563eb;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #18181b;
    --bg-subtle: #27272a;
    --text: #fafafa;
    --text-muted: #a1a1aa;
    --border: #3f3f46;
    --primary: #3b82f6;
  }
}

body {
  background: var(--bg);
  color: var(--text);
}
```

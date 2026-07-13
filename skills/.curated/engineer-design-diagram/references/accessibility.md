# Accessibility Patterns

Every diagram this skill emits must be screen-reader-accessible and respect motion preferences. Not a marketing feature — a correctness requirement.

## Table of Contents

- [ARIA Scaffolding](#aria-scaffolding)
- [SVG Title and Desc](#svg-title-and-desc)
- [Keyboard Navigation](#keyboard-navigation)
- [Reduced Motion](#reduced-motion)
- [Color Contrast](#color-contrast)

## ARIA Scaffolding

The top-level SVG element acts as a composite image with a meaningful label:

```html
<svg role="img"
     aria-labelledby="diagram-title diagram-desc"
     viewBox="0 0 1000 680"
     xmlns="http://www.w3.org/2000/svg">
  <title id="diagram-title">System architecture — myapp</title>
  <desc id="diagram-desc">
    Three-service topology: web frontend calls API, which depends on a Postgres
    database and a Redis cache. All services in the production VPC.
  </desc>
  <!-- diagram content -->
</svg>
```

Group landmarks per role:

```html
<g role="group" aria-label="Backend services">
  <rect ...>
    <title>API Service — Node/Express, port 3000</title>
    <desc>Handles HTTP requests from the web frontend</desc>
  </rect>
</g>
```

## SVG Title and Desc

Every `<rect>` that represents a node includes:

- `<title>` — one-line, screen-reader announces on focus (~80 chars max)
- `<desc>` — longer description (optional but recommended for complex components)

The `<title>` also acts as a browser tooltip on hover — double duty.

## Keyboard Navigation

Make the diagram tab-focusable:

```html
<svg tabindex="0" ...>
  <g tabindex="0" role="group" aria-label="api">
    <rect .../>
    <text .../>
  </g>
</svg>
```

CSS for visible focus:

```css
svg g:focus {
  outline: 2px solid var(--focus-ring, #22d3ee);
  outline-offset: 2px;
}
```

## Reduced Motion

The pulsing header dot and any hover transitions must honor `prefers-reduced-motion`:

```css
.header-dot {
  animation: pulse 2s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .header-dot,
  .diagram * {
    animation: none !important;
    transition: none !important;
  }
}
```

The validator checks for the presence of this media query. Missing it is a hard fail in `validate_html.py`.

## Color Contrast

All text-on-background pairs must meet WCAG AA (4.5:1 for body text, 3:1 for large text):

| Text | Background | Ratio | Pass? |
|------|------------|-------|-------|
| `white` | `#020617` (slate-950) | 17.3:1 | yes |
| `#94a3b8` (slate-400 sublabel) | `#020617` | 7.6:1 | yes |
| `#fb923c` (bus label, 7px) | `#020617` | 7.0:1 | yes |
| Role strokes (all) on slate-950 | — | ≥ 7:1 | yes |

Never change token values without re-checking contrast. Contrast-blind users rely on color-plus-pattern differentiation; the dashed boundary pattern for security groups is the non-color cue.

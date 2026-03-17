# Web Typography -- Implementation Guide

## Overview

Apply Robert Bringhurst's typographic principles and modern CSS to implement readable, hierarchical, and beautiful web typography.

## Type Scale

```css
/* Fluid type scale using clamp() */
:root {
  --text-xs:   clamp(0.694rem, 0.67rem + 0.12vw, 0.75rem);
  --text-sm:   clamp(0.833rem, 0.8rem + 0.17vw, 0.875rem);
  --text-base: clamp(1rem, 0.96rem + 0.2vw, 1.0625rem);
  --text-lg:   clamp(1.2rem, 1.15rem + 0.25vw, 1.3rem);
  --text-xl:   clamp(1.44rem, 1.36rem + 0.4vw, 1.625rem);
  --text-2xl:  clamp(1.728rem, 1.59rem + 0.69vw, 2rem);
  --text-3xl:  clamp(2.074rem, 1.87rem + 1.02vw, 2.5rem);
  --text-4xl:  clamp(2.488rem, 2.18rem + 1.54vw, 3.125rem);
}
```

## Line Length and Line Height

```css
/* Optimal reading width: 60-75 characters */
.prose {
  max-width: 65ch;
  line-height: 1.6;  /* Body text */
}

h1, h2, h3 { line-height: 1.2; }  /* Headings: tighter */
.caption    { line-height: 1.4; }  /* Short text: medium */
.code       { line-height: 1.5; }  /* Code: slightly tighter */
```

## Font Pairing

```css
/* Display + Body pairing (humanist + geometric) */
:root {
  --font-display: 'Instrument Sans', 'DM Sans', system-ui;
  --font-body:    'Source Sans 3', 'Inter', system-ui;
  --font-mono:    'DM Mono', 'JetBrains Mono', monospace;
}

h1, h2      { font-family: var(--font-display); }
body, p     { font-family: var(--font-body); }
code, pre   { font-family: var(--font-mono); }
```

## Vertical Rhythm

```css
/* Establish baseline grid */
:root { --line-height-base: 1.5; --font-size-base: 16px; }
/* Baseline unit = 16 * 1.5 = 24px */

/* All vertical spacing = multiples of baseline (24px) */
p    { margin-bottom: 1.5rem; }   /* 24px */
h2   { margin-top: 3rem; margin-bottom: 0.75rem; }  /* 48px top, 12px bottom */
```

## OpenType Features

```css
/* Enable useful OpenType features */
body {
  font-feature-settings: "kern" 1, "liga" 1, "calt" 1;
  font-variant-numeric: oldstyle-nums proportional-nums;
}

/* For tabular data: */
table, .stats {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
}

/* Small caps for labels/abbreviations: */
abbr, .label {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.05em;
}
```

## Responsive Typography Checklist

```markdown
- [ ] Type scale uses clamp() for fluid sizing (no media query jumps)
- [ ] Line length is constrained (60-75ch for prose)
- [ ] Line height: body 1.5-1.6, headings 1.1-1.3
- [ ] No more than 2 font families
- [ ] No more than 4 font sizes per layout
- [ ] Optical size variants used for small/large text if available
- [ ] Sufficient contrast at all sizes (4.5:1 body, 3:1 large text)
- [ ] Hyphenation enabled for long-form prose
- [ ] Fallback fonts specified in font stack
```

## Font Loading Strategy

```html
<!-- Preload critical fonts -->
<link rel="preload" href="/fonts/display.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/body.woff2" as="font" type="font/woff2" crossorigin>

<!-- Self-host with font-display: swap -->
<style>
@font-face {
  font-family: 'Display';
  src: url('/fonts/display.woff2') format('woff2');
  font-display: swap;  /* Show fallback immediately */
}
</style>
```

## References

- Bringhurst, R. (1992). *The Elements of Typographic Style.* Hartley & Marks.
- [Every Layout -- Typography](https://every-layout.dev/)
- [Fluid Type Scale Calculator](https://www.fluid-type-scale.com/)

# CSS Typography Implementation

Practical patterns for implementing web typography in CSS.

## @font-face Fundamentals

### Basic Syntax

```css
@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/custom-regular.woff2') format('woff2'),
       url('/fonts/custom-regular.woff') format('woff');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/custom-bold.woff2') format('woff2'),
       url('/fonts/custom-bold.woff') format('woff');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/custom-italic.woff2') format('woff2'),
       url('/fonts/custom-italic.woff') format('woff');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
```

### Format Priority

```css
src: url('font.woff2') format('woff2'),  /* Best compression, 97%+ support */
     url('font.woff') format('woff');     /* Fallback for older browsers */
```

**Skip these formats:**
- TTF/OTF - Larger files, no benefit for web
- EOT - Only needed for IE8 (likely not your audience)
- SVG fonts - Deprecated

## font-display Strategies

Controls how text renders while fonts load:

| Value | Behavior | Use When |
|-------|----------|----------|
| `swap` | Show fallback immediately, swap when loaded | Body text, readability critical |
| `block` | Hide text briefly (~3s), then show fallback | Headlines where flash is jarring |
| `fallback` | Brief block (~100ms), then fallback, optional swap | Balance of speed and stability |
| `optional` | Brief block, may skip custom font on slow connections | Performance is top priority |
| `auto` | Browser decides | Avoid - unpredictable |

### Recommended Approach

```css
/* Body fonts: always swap - content must be readable */
@font-face {
  font-family: 'Body Font';
  src: url('body.woff2') format('woff2');
  font-display: swap;
}

/* Display fonts: can block briefly */
@font-face {
  font-family: 'Display Font';
  src: url('display.woff2') format('woff2');
  font-display: block;
}
```

## Font Loading Optimization

### Preload Critical Fonts

```html
<head>
  <!-- Preload most important fonts -->
  <link rel="preload" href="/fonts/body-regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/fonts/body-bold.woff2" as="font" type="font/woff2" crossorigin>
</head>
```

**Only preload:**
- Fonts visible above the fold
- 2-3 maximum (more blocks other resources)
- Most commonly used weights

### Reduce Font Files

**Subset fonts** to include only needed characters:

```bash
# Using pyftsubset (fonttools)
pyftsubset font.ttf --output-file=font-subset.woff2 --flavor=woff2 \
  --layout-features='kern,liga' \
  --unicodes="U+0000-00FF,U+2000-206F"
```

Common subsetting ranges:
- `U+0000-00FF` - Basic Latin
- `U+0100-017F` - Latin Extended-A (Western European)
- `U+2000-206F` - General punctuation

**Online tools:**
- [Transfonter](https://transfonter.org/)
- [Fonttools](https://github.com/fonttools/fonttools)
- [Everything Fonts](https://everythingfonts.com/subsetter)

### Load Weights Strategically

```css
/* Load only what you use */
/* If you only use 400 and 700, don't load 300, 500, 600 */

@font-face {
  font-family: 'Custom Font';
  src: url('custom-400.woff2') format('woff2');
  font-weight: 400;
}

@font-face {
  font-family: 'Custom Font';
  src: url('custom-700.woff2') format('woff2');
  font-weight: 700;
}
```

## Variable Fonts

Single file containing multiple weights/widths/styles.

### Basic Variable Font Setup

```css
@font-face {
  font-family: 'Variable Font';
  src: url('variable.woff2') format('woff2-variations');
  font-weight: 100 900;  /* Range of available weights */
  font-stretch: 75% 125%;  /* Range of available widths (if supported) */
  font-style: normal;
  font-display: swap;
}

/* Use any weight in the range */
.light { font-weight: 300; }
.regular { font-weight: 400; }
.medium { font-weight: 500; }
.semibold { font-weight: 600; }
.bold { font-weight: 700; }
```

### Variable Font Axes

```css
/* Common axes */
.text {
  font-variation-settings:
    'wght' 450,   /* Weight */
    'wdth' 100,   /* Width */
    'slnt' -12,   /* Slant */
    'ital' 1;     /* Italic */
}

/* Prefer standard properties when available */
.text {
  font-weight: 450;
  font-stretch: 100%;
  font-style: oblique 12deg;
}
```

### Variable Font Benefits

| Advantage | Impact |
|-----------|--------|
| Smaller total size | One 80KB file vs. four 40KB files |
| Granular control | Use weight 450 instead of just 400 or 500 |
| Responsive weight | Adjust weight fluidly with viewport |
| Animation | Smooth weight/width transitions |

### Popular Variable Fonts

| Font | Axes | Good For |
|------|------|----------|
| Inter | weight, slant | UI, body text |
| Roboto Flex | weight, width, slant | Versatile, Google ecosystem |
| Source Sans 3 | weight | Body text, UI |
| Recursive | weight, slant, MONO, CASL | Code, UI, versatile |
| Fraunces | weight, SOFT, WONK | Display, editorial |

## System Font Stacks

Fast loading, native feel, no font files needed.

### Modern System Stack

```css
body {
  font-family:
    -apple-system,           /* Safari on macOS and iOS */
    BlinkMacSystemFont,      /* Chrome on macOS */
    'Segoe UI',              /* Windows */
    Roboto,                  /* Android, Chrome OS */
    'Helvetica Neue',        /* Older macOS */
    Arial,                   /* Fallback */
    sans-serif;              /* Generic fallback */
}
```

### System UI Keyword

```css
/* Modern browsers support this shortcut */
body {
  font-family: system-ui, sans-serif;
}
```

### Monospace System Stack

```css
code, pre {
  font-family:
    ui-monospace,              /* San Francisco Mono on macOS */
    'Cascadia Code',           /* Windows Terminal */
    'Source Code Pro',         /* Popular fallback */
    Menlo,                     /* macOS */
    Consolas,                  /* Windows */
    monospace;
}
```

## Fallback Strategies

### Matching Fallbacks

Choose fallbacks with similar metrics to minimize layout shift:

```css
/* If custom font has tall x-height, don't fallback to one that doesn't */
body {
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
}

/* Georgia and Times have similar metrics */
body {
  font-family: 'Source Serif Pro', Georgia, 'Times New Roman', serif;
}
```

### Adjusting Fallback Metrics

```css
/* Adjust fallback to match custom font metrics */
@font-face {
  font-family: 'Adjusted Arial';
  src: local('Arial');
  size-adjust: 105%;        /* Scale to match custom font */
  ascent-override: 90%;     /* Adjust ascender */
  descent-override: 20%;    /* Adjust descender */
  line-gap-override: 0%;    /* Adjust line gap */
}

body {
  font-family: 'Custom Font', 'Adjusted Arial', sans-serif;
}
```

## OpenType Features

### Common Features

```css
/* Ligatures */
.prose {
  font-feature-settings: "liga" 1, "clig" 1;  /* Standard ligatures */
}

/* Disable ligatures in code */
code {
  font-feature-settings: "liga" 0;
}

/* Figure styles */
.body-text {
  font-feature-settings: "onum" 1;  /* Oldstyle figures */
}

.table {
  font-feature-settings: "lnum" 1, "tnum" 1;  /* Tabular lining */
}

/* Small caps */
.acronym {
  font-feature-settings: "smcp" 1;
  /* Or use the property directly: */
  font-variant-caps: small-caps;
}

/* Fractions */
.recipe {
  font-feature-settings: "frac" 1;  /* 1/2 becomes proper fraction */
}
```

### Feature Detection

```css
@supports (font-variant-numeric: tabular-nums) {
  .table {
    font-variant-numeric: tabular-nums lining-nums;
  }
}
```

## Core Typography CSS

### Base Setup

```css
:root {
  /* Type scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;
  --text-4xl: 2.5rem;

  /* Line heights */
  --leading-tight: 1.2;
  --leading-snug: 1.4;
  --leading-normal: 1.6;
  --leading-relaxed: 1.8;

  /* Spacing */
  --measure: 65ch;
}

body {
  font-family: 'Source Sans Pro', system-ui, sans-serif;
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: #333;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Heading Styles

```css
h1, h2, h3, h4, h5, h6 {
  font-family: 'Source Serif Pro', Georgia, serif;
  line-height: var(--leading-tight);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

h1 { font-size: var(--text-4xl); }
h2 { font-size: var(--text-3xl); }
h3 { font-size: var(--text-2xl); }
h4 { font-size: var(--text-xl); }
h5 { font-size: var(--text-lg); }
h6 { font-size: var(--text-base); }

/* First heading shouldn't have top margin */
h1:first-child,
h2:first-child,
h3:first-child {
  margin-top: 0;
}
```

### Paragraph and Prose

```css
p {
  margin-bottom: 1em;
}

.prose {
  max-width: var(--measure);
}

.prose p + p {
  margin-top: 1.5em;
}

.prose ul,
.prose ol {
  padding-left: 1.5em;
  margin-bottom: 1em;
}

.prose li {
  margin-bottom: 0.5em;
}

.prose blockquote {
  border-left: 4px solid #e5e5e5;
  padding-left: 1em;
  margin-left: 0;
  font-style: italic;
}
```

### Links and Emphasis

```css
a {
  color: #0066cc;
  text-decoration: underline;
  text-underline-offset: 2px;
}

a:hover {
  color: #004499;
}

strong, b {
  font-weight: 600;
}

em, i {
  font-style: italic;
}

small {
  font-size: var(--text-sm);
}
```

## Performance Checklist

Before shipping:

- [ ] Fonts in WOFF2 format
- [ ] Total font payload < 200KB
- [ ] Critical fonts preloaded
- [ ] font-display set appropriately
- [ ] Unused weights removed
- [ ] Fonts subsetted if possible
- [ ] Fallback fonts have similar metrics
- [ ] No layout shift from font loading

## Quick Reference

### Font Weight Values

| Value | Common Name |
|-------|-------------|
| 100 | Thin |
| 200 | Extra Light |
| 300 | Light |
| 400 | Regular |
| 500 | Medium |
| 600 | Semi Bold |
| 700 | Bold |
| 800 | Extra Bold |
| 900 | Black |

### Useful Units

| Unit | Use For |
|------|---------|
| rem | Font sizes (scales with root) |
| em | Spacing relative to current font |
| ch | Line length (character width) |
| vw | Fluid sizing in clamp() |
| % | Relative to parent |

### Browser Support

| Feature | Support |
|---------|---------|
| WOFF2 | 97%+ |
| Variable fonts | 95%+ |
| font-display | 95%+ |
| clamp() | 95%+ |
| font-variant-* | 90%+ |

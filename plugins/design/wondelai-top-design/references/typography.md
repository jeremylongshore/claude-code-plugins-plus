# Typography Reference

## Table of Contents
1. Font Pairing Strategies
2. Type Scale Systems
3. CSS Typography Techniques
4. Variable Fonts
5. Font Loading Optimization

---

## 1. Font Pairing Strategies

### The Contrast Principle
Great pairings create tension through contrast in one dimension while maintaining harmony in others.

**Contrast Dimensions:**
- Weight (light vs. bold)
- Width (condensed vs. extended)
- Style (serif vs. sans)
- Era (classic vs. contemporary)
- Mood (serious vs. playful)

### Proven Pairings by Style

**Editorial/Magazine:**
```
Display: Freight Display / Editorial New / Canela
Body: Söhne / Untitled Sans / Graphik
```

**Tech/Modern:**
```
Display: Monument Extended / ABC Favorit Extended / Druk Wide
Body: Inter (only acceptable here) / Suisse Int'l / Neue Montreal
```

**Luxury/Fashion:**
```
Display: Didot / Romana / Noe Display
Body: Apercu / Basis Grotesque / Plain
```

**Brutalist/Raw:**
```
Display: ABC Diatype / Neue Haas Grotesk / Helvetica Now
Body: Same as display (mono-font strategy)
```

**Creative/Playful:**
```
Display: Basement Grotesque / GT Maru / Gambarino
Body: GT Walsheim / Gilroy / Proxima Nova
```

### Free/Google Font Alternatives

**Premium Feel, Zero Cost:**
```
Display Options:
├── Space Grotesk (geometric, techy)
├── Instrument Serif (editorial elegance)
├── Fraunces (variable, characterful)
├── Playfair Display (classic serif)
├── Cormorant Garamond (refined serif)
└── Syne (bold, distinctive)

Body Options:
├── Plus Jakarta Sans (clean, modern)
├── DM Sans (geometric, friendly)
├── Outfit (variable, versatile)
├── Satoshi (via Fontshare - free!)
└── General Sans (via Fontshare)
```

---

## 2. Type Scale Systems

### Fluid Typography (Preferred)

```css
/* Fluid scale using clamp() */
:root {
  /* Base: 16px at 320px → 20px at 1440px */
  --text-base: clamp(1rem, 0.857rem + 0.714vw, 1.25rem);
  
  /* Scale ratio: 1.25 (Major Third) */
  --text-sm: clamp(0.8rem, 0.686rem + 0.571vw, 1rem);
  --text-lg: clamp(1.25rem, 1.071rem + 0.893vw, 1.563rem);
  --text-xl: clamp(1.563rem, 1.339rem + 1.116vw, 1.953rem);
  --text-2xl: clamp(1.953rem, 1.674rem + 1.395vw, 2.441rem);
  --text-3xl: clamp(2.441rem, 2.092rem + 1.744vw, 3.052rem);
  --text-4xl: clamp(3.052rem, 2.616rem + 2.18vw, 3.815rem);
  --text-5xl: clamp(3.815rem, 3.27rem + 2.725vw, 4.768rem);
  
  /* Hero sizes - dramatic scale */
  --text-hero: clamp(4rem, 2rem + 8vw, 12rem);
  --text-display: clamp(3rem, 1.5rem + 6vw, 9rem);
}
```

### Step-Based Scale (Fixed Breakpoints)

```css
/* Mobile-first scale */
:root {
  --step--2: 0.75rem;   /* 12px */
  --step--1: 0.875rem;  /* 14px */
  --step-0: 1rem;       /* 16px - base */
  --step-1: 1.125rem;   /* 18px */
  --step-2: 1.5rem;     /* 24px */
  --step-3: 2rem;       /* 32px */
  --step-4: 3rem;       /* 48px */
  --step-5: 4rem;       /* 64px */
  --step-6: 6rem;       /* 96px */
  --step-7: 8rem;       /* 128px */
}

@media (min-width: 768px) {
  :root {
    --step-4: 4rem;
    --step-5: 6rem;
    --step-6: 9rem;
    --step-7: 12rem;
  }
}

@media (min-width: 1280px) {
  :root {
    --step-5: 8rem;
    --step-6: 12rem;
    --step-7: 16rem;
  }
}
```

---

## 3. CSS Typography Techniques

### Tracking (Letter-Spacing)

```css
/* Tracking scales inversely with size */
.text-hero {
  letter-spacing: -0.04em; /* Tight for massive text */
}

.text-display {
  letter-spacing: -0.03em;
}

.text-heading {
  letter-spacing: -0.02em;
}

.text-body {
  letter-spacing: 0; /* Normal for body */
}

.text-small {
  letter-spacing: 0.01em; /* Slightly open for small text */
}

.text-caps {
  letter-spacing: 0.1em; /* Open for all-caps */
  text-transform: uppercase;
}
```

### Leading (Line-Height)

```css
/* Line-height based on use case */
.leading-hero {
  line-height: 0.9; /* Very tight for impact */
}

.leading-display {
  line-height: 1.0;
}

.leading-heading {
  line-height: 1.1;
}

.leading-body {
  line-height: 1.6; /* Comfortable reading */
}

.leading-relaxed {
  line-height: 1.8; /* Long-form content */
}
```

### Advanced Techniques

```css
/* Optical margin alignment */
.hanging-punctuation {
  hanging-punctuation: first last;
}

/* Font feature settings */
.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.oldstyle-nums {
  font-variant-numeric: oldstyle-nums;
}

.ligatures {
  font-variant-ligatures: common-ligatures discretionary-ligatures;
}

/* Text rendering optimization */
.hero-text {
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Preventing text wrapping issues */
.no-orphans {
  text-wrap: balance; /* Modern browsers */
}

/* Hyphenation for justified text */
.justified {
  text-align: justify;
  hyphens: auto;
  hyphenate-limit-chars: 6 3 2;
}
```

### Text Masking & Gradient Text

```css
/* Gradient text */
.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Image-filled text */
.image-text {
  background-image: url('/texture.jpg');
  background-size: cover;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Animated gradient text */
.animated-gradient-text {
  background: linear-gradient(90deg, #ff0000, #00ff00, #0000ff, #ff0000);
  background-size: 300% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 8s ease infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

---

## 4. Variable Fonts

### Benefits
- Single file, multiple weights/widths
- Fluid animations between weights
- Smaller total file size

### Implementation

```css
/* Loading variable font */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}

/* Using weight axis */
.light { font-variation-settings: 'wght' 300; }
.regular { font-variation-settings: 'wght' 400; }
.medium { font-variation-settings: 'wght' 500; }
.bold { font-variation-settings: 'wght' 700; }
.black { font-variation-settings: 'wght' 900; }

/* Animating weight */
.hover-weight {
  font-variation-settings: 'wght' 400;
  transition: font-variation-settings 0.3s ease;
}

.hover-weight:hover {
  font-variation-settings: 'wght' 700;
}

/* Multiple axes */
.variable-text {
  font-variation-settings: 
    'wght' 500,  /* Weight */
    'wdth' 100,  /* Width */
    'ital' 0,    /* Italic */
    'slnt' 0;    /* Slant */
}
```

---

## 5. Font Loading Optimization

### Critical Font Strategy

```html
<!-- Preload critical fonts -->
<link rel="preload" href="/fonts/display.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/body.woff2" as="font" type="font/woff2" crossorigin>

<!-- Inline critical @font-face -->
<style>
  @font-face {
    font-family: 'Display';
    src: url('/fonts/display.woff2') format('woff2');
    font-weight: 700;
    font-display: swap;
  }
</style>
```

### Font Subsetting

```bash
# Using pyftsubset to create subset
pyftsubset "Font.ttf" \
  --output-file="Font-subset.woff2" \
  --flavor=woff2 \
  --layout-features="kern,liga,calt" \
  --unicodes="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
```

### FOUT/FOIT Prevention

```css
/* Font loading classes via JavaScript */
.fonts-loading {
  /* Use fallback stack */
  font-family: Georgia, serif;
}

.fonts-loaded .body-text {
  font-family: 'Custom Font', Georgia, serif;
}

/* Or use font-display */
@font-face {
  font-family: 'Display Font';
  src: url('/fonts/display.woff2') format('woff2');
  font-display: swap; /* Show fallback immediately, swap when loaded */
}

@font-face {
  font-family: 'Body Font';
  src: url('/fonts/body.woff2') format('woff2');
  font-display: optional; /* Only use if already cached */
}
```

### JavaScript Font Loading API

```javascript
// Check if fonts are loaded
document.fonts.ready.then(() => {
  document.documentElement.classList.add('fonts-loaded');
});

// Load specific font
const font = new FontFace('Display', 'url(/fonts/display.woff2)');
font.load().then((loadedFont) => {
  document.fonts.add(loadedFont);
  document.body.classList.add('display-font-loaded');
});
```

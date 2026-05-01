# Typeface Anatomy & Classification

Understanding typeface structure helps you make informed decisions and communicate clearly about typography.

## Typeface vs. Font

- **Typeface:** The design of the letters (e.g., Helvetica)
- **Font:** A specific instance of a typeface (e.g., Helvetica Bold 14pt)

Think of it like: typeface is the song, font is the MP3 file.

## Letterform Anatomy

### Vertical Measurements

```
┌─────────────────────────────────┐
│                    Ascender     │ Cap line
│         ┌───┐                   │
│         │   │                   │ Ascender line
│ ┌───┬───┤   │   │       │      │
│ │   │   │   │───┤   ┌───┤      │ x-height
│ │   │   │   │   │   │   │      │
│ └───┴───┴───┘   └───┴───┘      │ Baseline
│                     │          │
│                     └──────────│ Descender line
└─────────────────────────────────┘
  b   d   k   l       g   p   y
```

| Term | Definition |
|------|------------|
| **Baseline** | Invisible line where letters sit |
| **x-height** | Height of lowercase letters without ascenders/descenders (measured by lowercase "x") |
| **Cap height** | Height of capital letters |
| **Ascender** | Part of lowercase letters extending above x-height (b, d, f, h, k, l) |
| **Descender** | Part of letters extending below baseline (g, j, p, q, y) |

**Why x-height matters:** Larger x-height = better readability at small sizes. Two typefaces at the same point size can appear very different due to x-height variation.

### Horizontal Measurements

| Term | Definition |
|------|------------|
| **Counter** | Enclosed or partially enclosed space within a letter (inside "o", "e", "a") |
| **Aperture** | Opening into a counter (the gap in "c", "e", "s") |
| **Bowl** | Curved stroke enclosing a counter (the round part of "b", "d", "p") |
| **Set width** | Total horizontal space a character occupies, including sidebearings |

**Open counters and apertures** improve legibility, especially at small sizes and on screens.

### Stroke Features

| Term | Definition |
|------|------------|
| **Stroke** | The main lines forming a letter |
| **Stem** | Main vertical stroke (the straight part of "d", "p", "l") |
| **Crossbar** | Horizontal stroke (in "A", "H", "e") |
| **Arm** | Horizontal or upward diagonal stroke that doesn't connect at one end ("K", "E") |
| **Leg** | Downward diagonal stroke ("K", "R") |
| **Shoulder** | Curved stroke of "h", "m", "n" |
| **Tail** | Descending stroke, often decorative ("Q", "y") |
| **Ear** | Small stroke projecting from lowercase "g" |
| **Link/Neck** | Connection between the upper and lower bowls of two-story "g" |
| **Spine** | Main curved stroke of "S" |

### Terminals and Serifs

| Term | Definition |
|------|------------|
| **Serif** | Small projection at the end of strokes |
| **Sans serif** | Without serifs ("sans" = without) |
| **Terminal** | End of a stroke that doesn't have a serif |
| **Ball terminal** | Circular shape at end of stroke (in some typefaces' "a", "c", "f") |
| **Finial** | Tapered or curved terminal |
| **Spur** | Small projection off a main stroke |
| **Bracket** | Curved connection between serif and stem |

### Stroke Contrast

**Stroke contrast** = difference between thick and thin strokes within a letter.

| Contrast Level | Characteristics | Examples |
|----------------|-----------------|----------|
| High contrast | Dramatic thick/thin variation | Bodoni, Didot |
| Medium contrast | Noticeable but moderate variation | Times New Roman, Baskerville |
| Low contrast | Minimal thick/thin difference | Helvetica, most slab serifs |
| Monolinear | No variation, uniform strokes | Futura, Gotham |

**High contrast typefaces** can look elegant but may break down at small sizes where thin strokes disappear.

## Typeface Classification

### Serif Types

| Category | Characteristics | Examples | Best For |
|----------|-----------------|----------|----------|
| **Old Style** | Low contrast, angled stress, bracketed serifs | Garamond, Palatino, Caslon | Long-form reading, books |
| **Transitional** | Medium contrast, more vertical stress | Times New Roman, Baskerville, Georgia | Body text, editorial |
| **Modern/Didone** | High contrast, vertical stress, thin flat serifs | Bodoni, Didot | Headlines, fashion, luxury |
| **Slab Serif** | Low contrast, heavy rectangular serifs | Rockwell, Clarendon, Roboto Slab | Headlines, wayfinding |

### Sans-Serif Types

| Category | Characteristics | Examples | Best For |
|----------|-----------------|----------|----------|
| **Grotesque** | Early sans designs, slight contrast, "quirky" | Akzidenz Grotesk, Franklin Gothic | Headlines, bold statements |
| **Neo-grotesque** | Uniform strokes, neutral, little contrast | Helvetica, Arial, Univers | UI, neutral contexts |
| **Humanist** | Calligraphic influence, open forms | Gill Sans, Frutiger, Open Sans | Body text, warm/friendly |
| **Geometric** | Based on geometric shapes, circular "o" | Futura, Avenir, Gotham | Modern, clean, tech |

### Other Categories

| Category | Characteristics | Examples | Use With Caution |
|----------|-----------------|----------|------------------|
| **Script** | Connected or flowing, mimics handwriting | Brush Script, Snell Roundhand | Headlines only, never body text |
| **Display** | Designed for large sizes, decorative | Impact, Playfair Display | Headlines only, loses detail at small sizes |
| **Monospace** | Equal-width characters | Courier, Fira Code, JetBrains Mono | Code, tabular data |

## Checking Family Completeness

A complete type family for professional use should include:

### Essential
- [ ] Regular (400 weight)
- [ ] Bold (700 weight)
- [ ] Regular Italic
- [ ] Bold Italic

### Ideal
- [ ] Light (300)
- [ ] Medium (500)
- [ ] Semibold (600)
- [ ] All weights in italic
- [ ] Small caps
- [ ] Multiple figure styles (see below)

### Figure Styles

| Style | Description | Use Case |
|-------|-------------|----------|
| **Lining figures** | 1234567890 - Uniform height, align with capitals | Headlines, tables, all-caps text |
| **Oldstyle figures** | 1234567890 - Varying heights, blend with lowercase | Body text, running prose |
| **Tabular figures** | Equal-width digits | Tables, spreadsheets, aligned numbers |
| **Proportional figures** | Variable-width digits | Running text, when tabular not needed |

Good web fonts offer figure variants via OpenType features:

```css
/* Oldstyle figures */
.prose { font-feature-settings: "onum" 1; }

/* Tabular lining figures */
.table { font-feature-settings: "lnum" 1, "tnum" 1; }
```

## Quick Recognition Guide

When evaluating an unfamiliar typeface, check these distinguishing characters:

| Character | What to Look For |
|-----------|------------------|
| **a** | One-story (ɑ) or two-story (a)? |
| **g** | One-story or two-story (with ear/link)? |
| **R** | Leg straight or curved? |
| **Q** | Tail style |
| **&** | Often distinctive |
| **@** | Unique treatment reveals personality |
| **Il1** | How distinct are these? (critical for legibility) |
| **O0** | How distinct are these? |

## Terminology for Communication

When discussing typefaces with others:

**Instead of:** "The text looks weird"
**Say:** "The x-height feels small for this size" or "The letter spacing is too tight"

**Instead of:** "I don't like this font"
**Say:** "The stroke contrast is too high for body text" or "The apertures are too closed for screen readability"

**Instead of:** "Make it look more modern"
**Say:** "Try a geometric sans" or "Consider lower stroke contrast"

Using precise terminology helps teams make better decisions and keeps feedback actionable.

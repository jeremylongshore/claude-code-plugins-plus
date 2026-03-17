# Web Typography - Implementation Guide

Step-by-step methodology for selecting, pairing, and implementing typefaces for web projects.

## The Core Principle: Typography is Voice

The typeface you choose sets emotional tone before a single word is read. A legal site shouldn't feel playful; a children's app shouldn't feel corporate. Type selection is not aesthetic preference — it is communication design.

**The "clear goblet" principle:** Great typography is invisible. Readers absorb meaning, not letterforms. If someone notices the font, the typography is probably calling too much attention to itself.

## Step 1: Assess the Typographic Brief

Before choosing any typeface, answer these questions:

| Question | Why It Matters |
|----------|---------------|
| What is the emotional register? (formal/casual, modern/classic, technical/human) | Determines typeface category |
| What is the primary reading context? (long-form, UI labels, headlines) | Determines optical size needs |
| What languages and character sets are needed? | Rules out many typefaces |
| What are the performance constraints? (file size budget, LCP targets) | Determines how many font files are acceptable |
| Is variable font acceptable? | Variable fonts are larger but replace many static files |

## Step 2: Choose Your Display Typeface

The display typeface is used for headlines, large callouts, and branding moments. It has the most personality.

**2a. Typeface categories and their emotional registers:**

| Category | Emotional Register | Use For |
|----------|-------------------|---------|
| Geometric sans | Modern, rational, clean | Tech, startups, minimalist brands |
| Humanist sans | Warm, approachable, readable | Healthcare, education, consumer products |
| Transitional serif | Traditional, authoritative, trustworthy | Legal, finance, editorial |
| Slab serif | Bold, confident, direct | Headlines, brand statements, strong CTAs |
| Modern/Didone serif | Elegant, luxury, fashion | Premium brands, editorial, fashion |
| Variable/expressive | Distinctive, editorial, art-forward | Portfolio, culture, creative agencies |

**2b. Testing a display typeface**
- Set a sample headline at 48-72px and evaluate at a glance
- Check: optical weight at large sizes, letterspacing, distinctive letterforms (especially `a`, `g`, `R`, `Q`)
- Set the same text in 3 candidate fonts and choose the one that best matches the brief

## Step 3: Choose Your Body Typeface

The body typeface carries 80%+ of reading load. Readability is non-negotiable.

**3a. Readability requirements**
- Open counters (the spaces inside letterforms like `o`, `c`, `e`)
- Clear distinction between easily confused characters: `1`, `l`, `I`; `0`, `O`
- Comfortable x-height (taller x-height improves readability at small sizes)
- Test at 16px in paragraph length: read 5 sentences and check for eye strain

**3b. System font stacks (performance-first)**
- When performance is critical, system fonts have zero load time and match user expectations
- Modern stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Serif stack: `Georgia, "Times New Roman", Times, serif`

**3c. Google Fonts for projects with performance headroom**
- Body text reliables: Inter, Source Sans 3, IBM Plex Sans, Lato, Nunito
- Each adds ~50-100KB per weight loaded
- Use font subsetting: `&text=ABCabc...` for limited character sets

## Step 4: Build the Type Pairing

A type pairing is a display font + a body font that work together harmoniously.

**4a. Contrast rules**
- A successful pairing has contrast, not conflict
- Serif headline + sans body: classic, versatile, professional (NYT, most editorial sites)
- Sans headline + serif body: modern hierarchy with readable detail
- All-sans: requires weight contrast (bold headline, regular body)
- All-serif: requires clear scale contrast (large display serif, small body serif)

**4b. Tonal match**
- The display and body fonts must share an emotional register
- Mismatch example: Gothic blackletter headline + clean geometric sans body → tonal dissonance
- Match example: Didone display serif + humanist sans body → both elegant and warm

**4c. Quick test**
- Paste a paragraph of body text and a 48px headline with both candidate fonts
- Ask: "Does the headline feel like it belongs in the same world as the body text?"
- If yes, proceed. If no, adjust one or both.

## Step 5: Define the Type Scale

**5a. The scale**
A type scale is a harmonious set of sizes based on a single ratio. Common ratios:
- Minor third (1.2): compact, dense UIs
- Major third (1.25): balanced, general purpose
- Perfect fourth (1.333): strong hierarchy, editorial
- Golden ratio (1.618): dramatic, magazine-style

Calculate from a base of 16px (browser default):

| Level | Name | Perfect Fourth scale (1.333) |
|-------|------|------------------------------|
| xs | Caption | 12px |
| sm | Small | 14px |
| base | Body | 16px |
| lg | Large body | 21px |
| xl | H4 | 28px |
| 2xl | H3 | 37px |
| 3xl | H2 | 50px |
| 4xl | H1 | 67px |

**5b. Fluid typography (modern approach)**
Use `clamp()` to make type scale with viewport:
```css
h1 { font-size: clamp(2rem, 5vw + 1rem, 4.2rem); }
```
This eliminates hard breakpoints and makes type behave naturally across all screen sizes.

## Step 6: Set Line Length and Line Height

**6a. Optimal line length**
- Optimal reading: 60-75 characters per line (roughly 45-85 characters is acceptable)
- CSS: `max-width: 65ch` constrains the column to optimal reading width
- Do not let paragraph text stretch to full viewport width on large screens

**6b. Line height**
- Body text: 1.5-1.6 (generous, readable)
- Headlines/display: 1.1-1.2 (tight, architectural)
- Small text/captions: 1.4-1.5 (slightly generous for legibility)

**6c. Letter spacing**
- Body text: default (`0em`) or very slightly positive (`0.01em`)
- All-caps labels: positive tracking (`0.05-0.1em`) — all-caps needs more spacing to be legible
- Display/brand text: depends on typeface — some need negative tracking at large sizes (`-0.02em`)

## Step 7: Implement Web Font Loading

**7a. Font loading strategy**
- `font-display: swap`: text shows immediately in fallback font, then swaps to web font (best for performance)
- `font-display: optional`: only uses web font if available within a short window (most performance-conservative)
- `font-display: block`: invisible text until font loads (avoid for body text; acceptable for icon fonts)

**7b. Preloading critical fonts**
```html
<link rel="preload" href="/fonts/MyFont-Regular.woff2" as="font" type="font/woff2" crossorigin>
```
Preload only the 1-2 fonts that appear above the fold.

**7c. Self-hosting vs. Google Fonts**
- Self-hosting: faster (no DNS lookup), GDPR-compliant, more control
- Google Fonts: zero configuration, cache sharing (debated benefit), good for prototypes
- For production: prefer self-hosting with `woff2` format only

**7d. Variable fonts**
- One file replaces 4-8 static weight files
- Implementation: `font-weight: 100 900;` in `@font-face` declaration
- CSS: `font-weight: 350;` or `font-variation-settings: "wght" 350`
- Enables animation of font weight (motion typography effects)

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Too many typefaces | Visual chaos | 2 typefaces maximum; 3 only with strong justification |
| All same size | No visual hierarchy | Use at least 3 distinct sizes |
| Serif body at small size | Poor screen readability | Use sans-serif for body text under 18px |
| No line length constraint | Unreadable long lines on wide screens | `max-width: 65ch` on all paragraph containers |
| Loading 8 font weights | Slow LCP, poor performance | Load 2 weights per font: regular + bold (or semibold) |

## Quick-Start Checklist

- [ ] Typographic brief completed (emotional register, reading context, performance constraints)
- [ ] Display typeface chosen and tested at headline size
- [ ] Body typeface chosen and tested in paragraph form
- [ ] Pairing tested together: tonal match and contrast confirmed
- [ ] Type scale defined (5-7 sizes, ratio-based or fluid with `clamp()`)
- [ ] Line height set per use: 1.5-1.6 body, 1.1-1.2 display
- [ ] Line length constrained: `max-width: 65ch` on paragraphs
- [ ] `font-display: swap` set on all `@font-face` declarations
- [ ] Critical fonts preloaded with `<link rel="preload">`
- [ ] Maximum 2 font weights loaded per typeface

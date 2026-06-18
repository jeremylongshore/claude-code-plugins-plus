---
name: web-typography
description: 'Select, pair, and implement typefaces for web projects. Use when the user mentions "font pairing", "which typeface", "line height", "responsive typography", "web font loading", "type hierarchy", "variable fonts", "FOUT/FOIT", or "typographic scale". Also trigger when choosing between system fonts and web fonts, optimizing font loading performance, or designing readable long-form content layouts. Covers readability evaluation, CSS implementation, and performance optimization. For overall UI design systems, see refactoring-ui. For dramatic typographic experiences, see top-design.'
license: MIT
metadata:
  author: wondelai
  version: "1.3.0"
---

# Web Typography

A practical guide to choosing, pairing, and implementing typefaces for the web. The best typography is invisible — it immerses readers in content rather than calling attention to itself.

## Core Principle

**Typography is the voice of your content.** The typeface you choose sets tone before a single word is read — a legal site shouldn't feel playful; a children's app shouldn't feel corporate. Follow the "clear goblet" principle: typography should be like a crystal-clear wine glass, keeping focus on the wine (content), not the glass (type).

## Scoring

**Goal: 10/10.** Rate any typography implementation 0-10 against the principles below. Always state the current score and the specific improvements needed to reach 10/10.

## Two Contexts for Type

All typography falls into two categories:

| Context | Purpose | Priorities |
|---------|---------|------------|
| **Type for a moment** | Headlines, buttons, navigation, logos | Personality, impact, distinctiveness |
| **Type to live with** | Body text, articles, documentation | Readability, comfort, endurance |

**Workhorse typefaces** excel at "type to live with" — versatile across sizes, weights, and contexts without drawing attention. Examples: Georgia, Source Sans, Freight Text, FF Meta.

## Typography Framework

### 1. How We Read

**Core concept:** Understanding reading mechanics is the foundation for every typography decision. Eyes don't scan smoothly — they jump in bursts.

**Why it works:** When typography aligns with how the brain processes text — word shapes, consistent rhythm, distinct letterforms — readers absorb content faster with less fatigue. Fighting these mechanics creates friction that drives readers away.

**Key insights:**
- **Saccades** — eyes jump in 7-9 character bursts; line length and letter spacing directly affect saccade efficiency
- **Fixations** — eyes pause briefly to absorb content; dense or poorly spaced text slows reading
- **Word shapes (bouma)** — experienced readers recognize word silhouettes, not individual letters
- **Legibility vs. readability** — legibility is whether characters can be distinguished (a typeface concern); readability is whether text can be comfortably read for extended periods (a typography concern: size, spacing, line length). A legible typeface can still be set unreadably

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Long-form content | Optimize for sustained comfort | 16-18px body, 1.5-1.7 line height, 45-75 char lines |
| Dashboard UI | Optimize for rapid scanning | Distinct weight hierarchy, whitespace between data groups |
| Mobile reading | Account for distance and lighting | Larger body (17-18px), higher contrast |

**Copy patterns:**
```css
.prose {
  font-size: 1.125rem;     /* 18px */
  line-height: 1.6;
  max-width: 65ch;          /* ~45-75 characters */
}
```

**Ethical boundary:** Prioritize reader comprehension over visual novelty — sacrificing readability for aesthetics excludes readers.

See: [references/typeface-anatomy.md](references/typeface-anatomy.md) for terminology, letterform parts, and classification systems.

### 2. Evaluating Typefaces

**Core concept:** A typeface must pass technical, structural, and practical quality checks before it earns a place in a project. Beautiful specimens fail on screen.

**Why it works:** Screen rendering, variable bandwidth, and diverse devices impose constraints print never faced. Rigorous evaluation prevents costly mid-project typeface swaps.

**Key insights:**
- **Technical quality** — consistent stroke weights, even visual color across text blocks, good kerning pairs (AV, To, Ty), complete character set, multiple weights (minimum: regular, bold, italic)
- **Structural assessment** — generous x-height (better screen readability), open counters and apertures (a, e, c), distinct letterforms (Il1, O0, rn vs. m)
- **Practical needs** — test at actual use sizes on target screens, check file size, verify the license
- **Real content testing** — Lorem ipsum hides problems with character frequency, word length, and paragraph rhythm

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Body text selection | Prioritize x-height, open counters, even color | Source Serif Pro over Didot for long reads |
| UI/System text | Prioritize small-size legibility and weight range | Inter or SF Pro for interface elements |
| Multilingual product | Verify glyph coverage for target languages | Noto Sans for broad Unicode support |

**Copy patterns:**
```css
/* Stress-test at every actual use size */
body { font-size: 16px; }
.caption { font-size: 0.75rem; }
h1 { font-size: 3rem; }
```

**Ethical boundary:** Always verify licensing — unlicensed fonts create legal risk and undermine the type design community.

See: [references/evaluating-typefaces.md](references/evaluating-typefaces.md) for detailed quality assessment criteria and structural analysis.

### 3. Choosing Typefaces

**Core concept:** Start with purpose, not aesthetics. The content's tone, reading context, and duration should drive selection — not personal preference or trends.

**Why it works:** Purpose-driven choices feel inevitable rather than arbitrary, and survive stakeholder review because they can be justified with reasoning rather than taste.

**Key insights:**
- **Define the job first** — body text, headlines, and UI elements may each need different faces
- **Match tone to content** — a financial report needs a different voice than a bakery menu
- **Check the family** — confirm needed weights, italics, and styles exist before committing
- **Safe starting points** — body serif: Georgia, Source Serif Pro, Charter; body sans: system fonts, Source Sans Pro, Inter, IBM Plex Sans

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content-heavy site | Workhorse serif or sans for sustained reading | Source Serif Pro or Charter for articles |
| SaaS dashboard | Clean sans with strong tabular figures | Inter or IBM Plex Sans for data-rich UIs |
| Accessibility-focused | Faces designed for maximum legibility | Atkinson Hyperlegible for vision-impaired users |

**Copy patterns:**
```css
/* Web font with system fallback stack */
body {
  font-family: 'Source Sans Pro', -apple-system,
               BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

**Ethical boundary:** Never choose trendiness over readability — typography that excludes readers with lower vision fails its purpose.

### 4. Pairing Typefaces

**Core concept:** Successful pairings create clear contrast — faces should be obviously different, not confusingly similar. One to two typefaces maximum.

**Why it works:** Clear structural contrast (serif + sans, light + bold, humanist + geometric) gives each face a distinct role. Faces that are too similar create tension without purpose — readers sense something is "off" without knowing why.

**Key insights:**
- **Contrast types** — structure (serif + sans), weight (light + regular), era (humanist + geometric), width (condensed + normal)
- **Same designer strategy** — faces by one designer often share harmonizing DNA (FF Meta + FF Meta Serif)
- **Superfamilies** — families designed to work together eliminate guesswork (Roboto + Roboto Slab)
- **Pairing failures** — two near-identical faces, both faces competing for attention, one face overwhelming the other

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Editorial site | Serif headlines + sans body | Playfair Display + Source Sans Pro |
| Documentation | Monospace code + sans prose from one family | IBM Plex Mono + IBM Plex Sans |
| Minimal brand | Single family with weight variation | Inter at varying weights and sizes |

**Copy patterns:**
```css
/* Classic serif + sans-serif pairing */
h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; }
body { font-family: 'Source Sans Pro', -apple-system, sans-serif; }
```

**Ethical boundary:** When in doubt, use one family with weight variation — forced pairings add complexity that serves the designer's ego, not the reader.

See: [references/pairing-strategies.md](references/pairing-strategies.md) for specific combinations, contrast methods, and proven pairings.

### 5. Typographic Measurements

**Core concept:** Three measurements — font size, line length, and line height — form the foundation of comfortable reading. Getting these right matters more than typeface choice.

**Why it works:** These measurements govern how the eye tracks across and down text: optimal line length matches the saccade pattern, adequate line height prevents the eye from jumping to the wrong line on the return sweep, and sufficient size makes letterforms recognizable on screen.

**Key insights:**
- **Body size** — 16px minimum; err larger (18px) for reading-heavy sites; mobile users hold phones farther than designers assume
- **Line length (measure)** — 45-75 characters ideal, 66 optimal; enforce with `ch` units or `max-width`
- **Line height** — 1.4-1.8 for body; longer lines need more; headlines need tighter (1.1-1.25)
- **Heading scale** — consistent ratio (1.2-1.5) between levels creates hierarchy without extremes

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Blog / article | 65ch max-width, 1.6 line height | `.prose { max-width: 65ch; line-height: 1.6; }` |
| Dashboard | Tighter line height for dense data | `line-height: 1.3;` for table cells and labels |
| Landing page | Generous sizing for scanability | `font-size: 1.25rem; line-height: 1.7;` |

**Copy patterns:**
```css
.prose {
  font-size: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  line-height: 1.6;
  max-width: 65ch;
}
/* Line height by context */
h1, h2 { line-height: 1.1; }      /* headlines: 1.1-1.25 */
.ui-text { line-height: 1.35; }   /* UI: 1.3-1.4 */
.body-text { line-height: 1.6; }  /* body: 1.5-1.7 */
```

**Ethical boundary:** Never cram text into tiny sizes or narrow columns to "fit the design" — that prioritizes visual arrangement over human comprehension.

See: [references/responsive-typography.md](references/responsive-typography.md) for fluid sizing and viewport-based measurement strategies.

### 6. Building Type Hierarchies

**Core concept:** Hierarchy tells readers what matters most. Create distinction through controlled variation in size, weight, and color — but don't pull all three levers at once.

**Why it works:** When differences between levels are deliberate and consistent, readers scan a page and instantly understand its structure. Without hierarchy, everything competes and nothing wins.

**Key insights:**
- **Three levers** — size, weight, color; vary one or two between adjacent levels, never all three
- **The squint test** — squinting at a page should still reveal the hierarchy
- **Consistent scale** — a modular ratio (1.2-1.5) between heading levels creates rhythm; arbitrary sizes create noise
- **Don't skip levels** — jumping H1 to H3 breaks the reader's mental model

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content page | Size + weight across 4-5 levels | H1 2.5rem/700, H2 1.75rem/600, Body 1rem/400 |
| Dashboard | Weight + color for data vs. labels | Bold #111 values, regular #666 labels |
| Form UI | Subtle weight shift for labels | Label: 600 weight, input: 400 weight |

**Copy patterns:**
```css
h1 { font-size: clamp(2rem, 1.5rem + 2vw, 3rem); font-weight: 700; color: #111; }
h2 { font-size: clamp(1.5rem, 1.25rem + 1vw, 2rem); font-weight: 600; color: #111; }
body { font-size: 1rem; font-weight: 400; color: #333; }
.secondary { font-size: 0.875rem; color: #666; }
/* Headings: more space above than below */
h1, h2, h3 { margin: 1.5em 0 0.5em; line-height: 1.2; }
```

**Ethical boundary:** Hierarchy must guide readers honestly — burying fees in small text or spotlighting manipulative CTAs weaponizes typography against the reader.

See: [references/css-implementation.md](references/css-implementation.md) for complete hierarchy implementation patterns and variable font techniques.

### 7. Responsive Typography and Web Font Performance

**Core concept:** Type must adapt to screens, and web fonts must load efficiently. Fluid typography with `clamp()` eliminates breakpoint jumps; strategic font loading prevents layout shift and slow renders.

**Why it works:** A fixed font size cannot serve both a 320px phone and a 1440px desktop. Web fonts are render-blocking by default — unoptimized loading causes Flash of Invisible Text (FOIT) or Flash of Unstyled Text (FOUT).

**Key insights:**
- **Fluid typography** — `clamp(min, preferred, max)` scales smoothly between viewports, no media queries needed for type
- **Breakpoint adjustments** — mobile needs slightly larger body (17-18px) and a tighter heading scale; desktop can push display sizes while keeping line-length limits
- **Loading strategy** — `font-display: swap` shows fallback text immediately; preload critical fonts; subset to needed characters
- **Performance budget** — under 200KB total font payload; prefer WOFF2; a variable font can replace 4-6 static weight files

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content site | Fluid sizes with clamp() | `font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem)` |
| E-commerce | Preload hero font, lazy-load secondary weights | `<link rel="preload" href="font.woff2" as="font">` |
| Global product | Subset per language to cut payload | Latin subset for English, CJK subset for Asian pages |

**Copy patterns:**
```css
h1 { font-size: clamp(2rem, 1.5rem + 2vw, 3.5rem); }

@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0000-00FF; /* Latin subset */
}
/* In <head>: <link rel="preload" href="/fonts/custom.woff2" as="font" type="font/woff2" crossorigin> */
```

**Ethical boundary:** Don't optimize users out — subsetting that drops characters non-English readers need, or removing italic/bold weights needed for emphasis, trades inclusivity for speed.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Text feels cramped | Tight line height fatigues readers | Increase line-height to 1.6+; add paragraph spacing |
| Lines too long | Beyond 75 chars the eye loses the return sweep | `max-width: 65ch` on text containers |
| Headings look disconnected | Excess space above breaks association with content | Reduce space above heading; keep space below |
| Text looks blurry | Font-smoothing or subpixel rendering issues | Check font-smoothing; try different weight; increase size |
| Fonts loading slowly | Unoptimized files block rendering | Subset; `font-display: swap`; preload critical fonts |
| Body text too small | Phones held farther than assumed; strains older eyes | Increase to 18px; test at real distance |
| Hierarchy is unclear | Insufficient contrast between levels | Increase size/weight differences |
| Typefaces clash | Pairing without clear contrast creates tension | One family, or ensure structural contrast (serif + sans) |
| Lorem ipsum testing | Dummy text hides rhythm and frequency problems | Test with real, representative content |

## Quick Diagnostic

| Question | If No | Action |
|----------|-------|--------|
| Is body text 16px or larger? | Too small for comfortable reading | At least 16px; prefer 18px for reading-heavy pages |
| Is line length under 75 characters? | Eye loses position on return sweep | `max-width: 65ch` on prose containers |
| Is line height 1.4+ for body? | Lines feel cramped, reading slows | Increase to 1.5-1.7 |
| Is there clear contrast between type levels? | Hierarchy invisible, scanning fails | Increase size or weight differences |
| Tested at actual sizes on real screens? | Rendering surprises in production | Test every use size on target devices |
| Is total font payload under 200KB? | Slow loading hurts UX and SEO | Subset, WOFF2, consider variable fonts |
| Are fallback fonts specified? | FOIT leaves blank text | System fallbacks in every font-family |
| Does the page work at 200% zoom? | Accessibility failure for low vision | Fix overflow and truncation at 200% |
| Are headings free of orphaned words? | Trailing words look unfinished | `text-wrap: balance` or manual breaks |
| Are links visually distinct? | Users can't find interactive elements | Color and/or underline distinction |

## Reference Files

- [typeface-anatomy.md](references/typeface-anatomy.md): Terminology, letterform parts, classification systems
- [evaluating-typefaces.md](references/evaluating-typefaces.md): Quality assessment, structural analysis, technical requirements
- [pairing-strategies.md](references/pairing-strategies.md): Combining typefaces, contrast methods, proven combinations
- [responsive-typography.md](references/responsive-typography.md): Fluid type, viewport units, breakpoint strategies
- [css-implementation.md](references/css-implementation.md): @font-face, loading strategies, variable fonts, performance

## Further Reading

- [*"On Web Typography"*](https://www.amazon.com/Web-Typography-Jason-Santa-Maria/dp/1937557065?tag=wondelai00-20) by Jason Santa Maria (A Book Apart, 2014)

## About the Author

**Jason Santa Maria** is a graphic designer and educator who served as Creative Director at Typekit (now Adobe Fonts) and co-founded A Book Apart. He teaches at the School of Visual Arts in New York, and *On Web Typography* distills his bridge between traditional typographic craft and the realities of designing for screens.

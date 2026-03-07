---
name: web-typography
description: 'Select, pair, and implement typefaces for web projects. Use when the user mentions "font pairing", "which typeface", "line height", "responsive typography", "web font loading", or "type hierarchy". Covers readability evaluation, CSS implementation, and performance optimization. For overall UI design systems, see refactoring-ui. For dramatic typographic experiences, see top-design.'
license: MIT
metadata:
  author: wondelai
  version: "1.1.1"
---

# Web Typography

A practical guide to choosing, pairing, and implementing typefaces for the web. Typography serves communication — the best typography is invisible, immersing readers in content rather than calling attention to itself.

## Core Principle

**Typography is the voice of your content.** The typeface you choose sets tone before a single word is read. A legal site shouldn't feel playful; a children's app shouldn't feel corporate.

**The "clear goblet" principle:** Typography should be like a crystal-clear wine glass — the focus is on the wine (content), not the glass (type). Readers should absorb meaning, not notice letterforms.

**Readers don't read, they scan.** Eyes jump 7-9 characters at a time (saccades), pausing briefly (fixations). Good typography supports this natural pattern.

## Scoring

**Goal: 10/10.** When reviewing or creating typography implementations, rate them 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## Two Contexts for Type

All typography falls into two categories:

| Context | Purpose | Priorities |
|---------|---------|------------|
| **Type for a moment** | Headlines, buttons, navigation, logos | Personality, impact, distinctiveness |
| **Type to live with** | Body text, articles, documentation | Readability, comfort, endurance |

**Workhorse typefaces** excel at "type to live with" — they're versatile across sizes, weights, and contexts without drawing attention to themselves. Examples: Georgia, Source Sans, Freight Text, FF Meta.

## Typography Framework

### 1. How We Read

**Core concept:** Understanding reading mechanics is the foundation for every typography decision. Eyes don't scan smoothly — they jump in bursts, and good typography supports this natural pattern.

**Why it works:** When typography aligns with how the brain processes text — through word shape recognition, consistent rhythm, and clear letterform distinction — readers absorb content faster with less fatigue. Fighting these mechanics creates friction that drives readers away.

**Key insights:**
- **Saccades** — eyes jump in 7-9 character bursts, not smooth scanning. Line length and letter spacing directly affect saccade efficiency
- **Fixation points** — eyes pause briefly to absorb content. Dense or poorly spaced text increases fixation duration and slows reading
- **Word shapes (bouma)** — experienced readers recognize word silhouettes, not individual letters. Maintaining distinct boumas aids recognition speed
- **Legibility vs. readability** — legibility is whether individual characters can be distinguished (a typeface concern); readability is whether text can be comfortably read for extended periods (a typography concern — size, spacing, line length). A typeface can be legible but poorly set, making it unreadable

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Long-form content | Optimize for sustained reading comfort | 16-18px body text, 1.5-1.7 line height, 45-75 char lines |
| Dashboard UI | Optimize for rapid scanning | Distinct weight hierarchy, ample whitespace between data groups |
| Mobile reading | Account for variable distance and lighting | Slightly larger body size (17-18px), higher contrast |
| Documentation | Support both scanning and deep reading | Clear heading hierarchy with generous paragraph spacing |
| E-commerce | Enable quick product comparison | Consistent number formatting, tabular figures |
| Accessibility | Support readers with varying abilities | High contrast, generous spacing, distinct letterforms |

**Copy patterns:**
```css
/* Optimal reading rhythm for body text */
.prose {
  font-size: 1.125rem;     /* 18px */
  line-height: 1.6;
  max-width: 65ch;          /* ~45-75 characters */
  letter-spacing: normal;   /* Don't force tracking on body text */
}
```

**Ethical boundary:** Typography decisions should always prioritize reader comprehension and comfort over visual novelty. Sacrificing readability for aesthetic effect excludes readers and undermines the content's purpose.

See: [references/typeface-anatomy.md](references/typeface-anatomy.md) for terminology, letterform parts, and classification systems.

### 2. Evaluating Typefaces

**Core concept:** A typeface must pass technical, structural, and practical quality checks before it earns a place in a project. Beautiful specimens fail on screen; rigorous evaluation prevents costly mid-project typeface swaps.

**Why it works:** Screen rendering, variable bandwidth, and diverse devices impose constraints that print never faced. A typeface that passes structural assessment (consistent strokes, open counters, distinct letterforms) and practical assessment (file size, license, rendering) will perform reliably across the full range of real-world conditions.

**Key insights:**
- **Technical quality** — consistent stroke weights, even color (visual density) across text blocks, good kerning pairs (AV, To, Ty), complete character set (accents, punctuation, figures), and multiple weights (at minimum: regular, bold, italic)
- **Structural assessment** — adequate x-height (larger = better screen readability), open counters and apertures (a, e, c shapes), distinct letterforms (Il1, O0, rn vs. m), and appropriate contrast (thick/thin stroke variation)
- **Practical needs** — works at intended sizes (test at actual use size), renders well on target screens and browsers, acceptable file size for web loading, and appropriate license for the project
- **Real content testing** — always test with real content, not Lorem ipsum. Dummy text hides problems with character frequency, word length, and paragraph rhythm

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Body text selection | Prioritize x-height, open counters, even color | Source Serif Pro over Didot for long reads |
| Headline selection | Prioritize personality and distinctiveness at large sizes | Playfair Display for editorial impact |
| UI/System text | Prioritize legibility at small sizes and weight range | Inter or SF Pro for interface elements |
| Multilingual product | Verify complete glyph coverage for target languages | Noto Sans for broad Unicode support |
| Performance-critical site | Evaluate file size and subsetting options | Variable font single file vs. multiple static weights |
| Brand refresh | Assess whether typeface conveys intended personality | Compare specimen at actual use sizes against brand attributes |

**Copy patterns:**
```css
/* Test typeface at actual use sizes */
body { font-size: 16px; }           /* Minimum body size */
.caption { font-size: 0.75rem; }    /* Stress-test small sizes */
h1 { font-size: 3rem; }            /* Check large-size character */

/* Verify rendering with font-smoothing */
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Ethical boundary:** Always verify typeface licensing before implementation. Using unlicensed fonts exposes projects to legal risk and undermines the type design community that creates these tools.

See: [references/evaluating-typefaces.md](references/evaluating-typefaces.md) for detailed quality assessment criteria and structural analysis.

### 3. Choosing Typefaces

**Core concept:** Start with purpose, not aesthetics. The content's tone, reading context, duration, and personality should drive typeface selection — not personal preference or trend following.

**Why it works:** When typeface selection is grounded in content requirements, the result feels inevitable rather than arbitrary. Purpose-driven choices also survive stakeholder review better because they can be justified with clear reasoning rather than subjective taste.

**Key insights:**
- **Define the job first** — body text, headlines, and UI elements may each need different faces. Clarify the role before browsing specimens
- **Match tone to content** — a financial report needs different type than a bakery menu. The typeface should feel like a natural voice for the subject matter
- **Test at actual sizes** — a face beautiful at 72px may be illegible at 14px. Always evaluate at the sizes where the typeface will actually be used
- **Check the family** — ensure needed weights, italics, and styles exist before committing. Discovering missing weights mid-project forces compromises
- **Safe starting points** — for body text, Georgia, Source Serif Pro, Charter (serif) and system fonts, Source Sans Pro, Inter, IBM Plex Sans (sans-serif) reliably work across contexts

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content-heavy site | Select a workhorse serif or sans for sustained reading | Source Serif Pro or Charter for articles |
| SaaS dashboard | Choose a clean sans with strong tabular figures | Inter or IBM Plex Sans for data-rich interfaces |
| Marketing landing page | Pair a distinctive display face with a readable body face | Playfair Display headlines + Source Sans Pro body |
| Documentation site | Prioritize clarity and weight range for code + prose | IBM Plex Mono for code, IBM Plex Sans for prose |
| Brand-driven product | Commission or license a face that embodies brand values | Custom typeface or carefully chosen match to brand personality |
| Accessibility-focused | Select faces designed for maximum legibility | Atkinson Hyperlegible for vision-impaired users |

**Copy patterns:**
```css
/* Safe system font stack */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
               Roboto, Oxygen, Ubuntu, sans-serif;
}

/* Reliable web font body stack */
body {
  font-family: 'Source Sans Pro', -apple-system,
               BlinkMacSystemFont, sans-serif;
}
```

**Ethical boundary:** Avoid choosing typefaces solely to appear trendy or sophisticated at the expense of readability. Typography that excludes readers with lower vision or reading difficulties in favor of visual style fails its fundamental purpose.

See: [references/evaluating-typefaces.md](references/evaluating-typefaces.md) for quality assessment to apply during selection.

### 4. Pairing Typefaces

**Core concept:** Successful typeface pairings create clear contrast — faces should be obviously different, not confusingly similar. One to two typefaces maximum; more requires exceptional skill.

**Why it works:** Contrast between typefaces creates visual hierarchy and rhythm. When two faces are too similar, they create tension without purpose — the reader senses something is "off" without knowing why. Clear structural contrast (serif + sans, light + bold, humanist + geometric) lets each face play a distinct role while coexisting harmoniously.

**Key insights:**
- **Contrast types** — structure (serif + sans), weight (light + regular), era (humanist + geometric), and width (condensed + normal) all create effective contrast
- **Same designer strategy** — faces designed by one person often share DNA that harmonizes (e.g., FF Meta + FF Meta Serif)
- **Superfamilies** — typeface families designed to work together eliminate guesswork (e.g., Roboto + Roboto Slab)
- **Pairing mistakes** — two serifs or two sans faces that look almost alike, both faces trying to be distinctive, mixing renaissance and postmodern without intention, one face overwhelming the other in weight

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Editorial site | Serif headlines + sans body for classic readability | Playfair Display + Source Sans Pro |
| Tech product | Superfamily for guaranteed harmony | Roboto + Roboto Slab |
| Corporate site | Same-designer pairing for subtle cohesion | FF Meta + FF Meta Serif |
| E-commerce | Distinctive display + neutral body | Condensed headline face + system sans-serif body |
| Documentation | Monospace code + sans-serif prose from same family | IBM Plex Mono + IBM Plex Sans |
| Minimal brand | Single family with weight variation | Inter at varying weights and sizes |

**Copy patterns:**
```css
/* Classic serif + sans-serif pairing */
h1, h2, h3 {
  font-family: 'Playfair Display', Georgia, serif;
}
body {
  font-family: 'Source Sans Pro', -apple-system, sans-serif;
}

/* Superfamily pairing */
h1, h2, h3 {
  font-family: 'Roboto Slab', serif;
}
body {
  font-family: 'Roboto', sans-serif;
}
```

**Ethical boundary:** When in doubt, use one family with weight variation rather than forcing a pairing. A mismatched pairing creates cognitive friction that undermines the content, and adding complexity without purpose serves the designer's ego rather than the reader's needs.

See: [references/pairing-strategies.md](references/pairing-strategies.md) for specific combinations, contrast methods, and proven pairings.

### 5. Typographic Measurements

**Core concept:** Three measurements — font size, line length, and line height — form the foundation of comfortable reading. Getting these right matters more than typeface choice.

**Why it works:** These measurements directly govern how the eye tracks across and down text. Optimal line length (45-75 characters) matches the saccade pattern. Adequate line height (1.4-1.8) prevents the eye from jumping to the wrong line on the return sweep. Sufficient font size (16-18px minimum) ensures letterforms are large enough for comfortable recognition on screen.

**Key insights:**
- **Body font size** — 16px minimum; err larger (18px) for reading-heavy sites. Mobile users hold phones farther than designers assume
- **Line length (measure)** — 45-75 characters ideal, 66 characters optimal. Use the `ch` unit or `max-width` to enforce. Longer lines need more line height to compensate
- **Line height** — 1.4-1.8 for body text. Longer lines need more; shorter lines need less. Headlines need tighter spacing (1.1-1.25)
- **Heading scale** — use a consistent ratio (1.2-1.5) between heading levels to establish clear hierarchy without extremes

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Blog / article | Enforce 65ch max-width with 1.6 line height | `.prose { max-width: 65ch; line-height: 1.6; }` |
| Documentation | Slightly wider measure with increased line height | `max-width: 75ch; line-height: 1.7;` |
| Mobile UI | Larger body size, auto-constrained measure | `font-size: 17px;` with viewport-width constraint |
| Dashboard | Tighter line height for dense data display | `line-height: 1.3;` for table cells and labels |
| Landing page | Generous sizing and spacing for scanability | `font-size: 1.25rem; line-height: 1.7;` |
| Email template | Constrained width for email client compatibility | `max-width: 600px;` with inline sizing |

**Copy patterns:**
```css
/* Optimal body text measurements */
.prose {
  font-size: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  line-height: 1.6;
  max-width: 65ch;
}

/* Wider columns need more line height */
.wide-text {
  max-width: 80ch;
  line-height: 1.8;
}

/* Line height adjustments by context */
h1, h2 { line-height: 1.1-1.25; }
.ui-text { line-height: 1.3-1.4; }
.body-text { line-height: 1.5-1.7; }
```

**Ethical boundary:** Never sacrifice readable measurements for layout aesthetics. Cramming text into narrow columns with tiny sizes to "fit the design" prioritizes visual arrangement over human comprehension.

See: [references/responsive-typography.md](references/responsive-typography.md) for fluid sizing and viewport-based measurement strategies.

### 6. Building Type Hierarchies

**Core concept:** Hierarchy tells readers what matters most. Create distinction through controlled variation in size, weight, and color — but don't combine all levers at once.

**Why it works:** Visual hierarchy mimics how readers naturally prioritize information. When size, weight, and color differences between levels are deliberate and consistent, readers can scan a page and instantly understand its structure. Without hierarchy, everything competes for attention and nothing wins.

**Key insights:**
- **Three levers** — size, weight, and color. Vary one or two between adjacent levels; varying all three creates excessive contrast that wastes headroom for deeper hierarchies
- **The squint test** — squinting at a page should still reveal the hierarchy. If everything blurs into sameness, the distinction is too subtle
- **Consistent scale** — use a ratio (1.2-1.5) between heading levels. Arbitrary sizes create visual noise. A modular scale creates rhythm
- **Don't skip levels** — jumping from H1 to H3 breaks the reader's mental model of document structure

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content page | Size + weight variation across 4-5 levels | H1 2.5rem/700, H2 1.75rem/600, Body 1rem/400 |
| Dashboard | Weight + color for data vs. label distinction | Bold #111 for values, Regular #666 for labels |
| Navigation | Size + weight to signal current vs. available | Active: bold, Inactive: regular, same size |
| Marketing page | Large size jumps for dramatic scanability | Hero 3.5rem, Section heads 2rem, Body 1.125rem |
| Form UI | Subtle weight shifts for label vs. input distinction | Label: 600 weight, Input: 400 weight |
| Mobile app | Tighter scale due to limited viewport | H1 1.75rem, H2 1.25rem, Body 1rem |

**Copy patterns:**
```css
/* Type hierarchy with modular scale */
h1 { font-size: clamp(2rem, 1.5rem + 2vw, 3rem); font-weight: 700; color: #111; }
h2 { font-size: clamp(1.5rem, 1.25rem + 1vw, 2rem); font-weight: 600; color: #111; }
h3 { font-size: 1.25rem; font-weight: 600; color: #333; }
body { font-size: 1rem; font-weight: 400; color: #333; }
.secondary { font-size: 0.875rem; color: #666; }
.caption { font-size: 0.75rem; color: #888; }

/* Heading rhythm */
h1, h2, h3 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.2;
}
```

**Ethical boundary:** Hierarchy should guide readers honestly. Using visual prominence to draw attention to deceptive elements (hidden fees in small text, manipulative CTAs in bold) weaponizes typography against the reader.

See: [references/css-implementation.md](references/css-implementation.md) for complete hierarchy implementation patterns and variable font techniques.

### 7. Responsive Typography and Web Font Performance

**Core concept:** Type must adapt to screens and reading contexts, and web fonts must load efficiently. Fluid typography with `clamp()` eliminates breakpoint jumps, while strategic font loading prevents layout shift and slow renders.

**Why it works:** A single fixed font size cannot serve both a 320px phone and a 1440px desktop. Fluid scaling ensures text is always proportionate to its viewport. Meanwhile, web fonts are render-blocking by default — unoptimized loading causes Flash of Invisible Text (FOIT) or Flash of Unstyled Text (FOUT), both of which degrade the reading experience.

**Key insights:**
- **Fluid typography** — `clamp(min, preferred, max)` scales font size smoothly between viewport sizes, eliminating the need for media query breakpoints for type sizing
- **Breakpoint adjustments** — mobile (<640px) needs slightly larger body size (17-18px) and tighter heading scale; tablet (640-1024px) uses standard sizing with enforced line-length limits; desktop (>1024px) can use larger display type while maintaining line-length
- **Font loading strategy** — use `font-display: swap` to show fallback text immediately, preload critical fonts with `<link rel="preload">`, and subset fonts to include only needed characters
- **Performance budget** — aim for under 200KB total web font payload. Subset aggressively, prefer WOFF2 format, and consider variable fonts to replace multiple static weight files

**Product applications:**

| Context | Application | Example |
|---------|------------|---------|
| Content site | Fluid body and heading sizes with clamp() | `font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem)` |
| E-commerce | Preload hero font, lazy-load secondary weights | `<link rel="preload" href="font.woff2" as="font">` |
| SaaS app | System font stack for UI, web font for marketing only | `-apple-system` in app, custom font on landing page |
| Global product | Subset fonts per language to reduce payload | Latin subset for English pages, CJK subset for Asian pages |
| Performance-critical | Variable font replacing 4-6 static files | Single variable font file with weight axis 300-700 |
| Progressive web app | Cache fonts in service worker for offline use | `caches.open('fonts').then(cache => cache.addAll(...))` |

**Copy patterns:**
```css
/* Fluid typography with clamp() */
body {
  font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
}
h1 {
  font-size: clamp(2rem, 1.5rem + 2vw, 3.5rem);
}

/* Performant font loading */
@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
  font-weight: 400;
  unicode-range: U+0000-00FF; /* Latin subset */
}

/* Preload in HTML head */
/* <link rel="preload" href="/fonts/custom.woff2" as="font" type="font/woff2" crossorigin> */
```

**Ethical boundary:** Performance optimization should not come at the cost of excluding users. Aggressive subsetting that drops characters needed by non-English readers, or removing italic/bold weights needed for emphasis, trades inclusivity for speed in ways that harm real people.

See: [references/responsive-typography.md](references/responsive-typography.md) for fluid type implementation and [references/css-implementation.md](references/css-implementation.md) for @font-face, loading strategies, and variable fonts.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Text feels cramped | Insufficient line height creates visual density that fatigues readers | Increase line-height to 1.6+; add paragraph spacing |
| Lines too long, hard to track | Beyond 75 characters, the eye loses its place on the return sweep | Add `max-width: 65ch` to text containers |
| Headings look disconnected | Excessive space above headings breaks their association with following content | Reduce space above heading; keep space below |
| Text looks blurry on screen | Poor font-smoothing settings or subpixel rendering issues | Check font-smoothing; try different weight; increase size |
| Fonts loading slowly | Unoptimized font files block rendering and delay first contentful paint | Subset fonts; use `font-display: swap`; preload critical fonts |
| Body text too small | Users hold phones farther than assumed; small text strains older eyes | Increase to 18px; test with real users at real distance |
| Hierarchy is unclear | Insufficient contrast between adjacent levels makes everything compete | Increase size/weight differences between levels |
| Typefaces clash | Pairing faces without clear contrast creates unresolvable visual tension | Simplify to one family; or ensure structural contrast (serif + sans) |
| Using Lorem ipsum for testing | Dummy text hides character frequency, word length, and rhythm problems | Test with real content representative of actual use |

## Quick Diagnostic

| Question | If No | Action |
|----------|-------|--------|
| Is body text 16px or larger? | Text too small for comfortable screen reading | Increase to at least 16px; prefer 18px for reading-heavy pages |
| Is line length under 75 characters? | Eye loses position on return sweep | Add `max-width: 65ch` to prose containers |
| Is line height 1.4 or greater for body? | Lines feel cramped and reading speed drops | Increase to 1.5-1.7 for body text |
| Is there sufficient contrast between type levels? | Hierarchy is invisible; readers can't scan | Increase size or weight differences between adjacent levels |
| Have typefaces been tested at actual sizes on real screens? | Rendering surprises will appear in production | Test at every use size on target devices and browsers |
| Is total font payload under 200KB? | Slow loading degrades experience and SEO | Subset fonts, use WOFF2, consider variable fonts |
| Are fallback fonts specified? | FOIT leaves blank text while fonts load | Add system font fallbacks in every font-family declaration |
| Does the page work at 200% browser zoom? | Accessibility failure for low-vision users | Test at 200% zoom; fix overflow and truncation issues |
| Are headings free of orphaned single words? | Single trailing words look unfinished and waste space | Use `text-wrap: balance` or manual breaks |
| Are links visually distinct from surrounding text? | Users cannot identify interactive elements | Ensure links have color and/or underline distinction |

## Reference Files

- [typeface-anatomy.md](references/typeface-anatomy.md): Terminology, letterform parts, classification systems
- [evaluating-typefaces.md](references/evaluating-typefaces.md): Quality assessment, structural analysis, technical requirements
- [pairing-strategies.md](references/pairing-strategies.md): Combining typefaces, contrast methods, proven combinations
- [responsive-typography.md](references/responsive-typography.md): Fluid type, viewport units, breakpoint strategies
- [css-implementation.md](references/css-implementation.md): @font-face, loading strategies, variable fonts, performance

## Further Reading

**On Web Typography** by Jason Santa Maria
Publisher: A Book Apart (2014)
ISBN: 978-1937557065
[Amazon](https://www.amazon.com/Web-Typography-Jason-Santa-Maria/dp/1937557065?tag=wondelai00-20)

## About the Author

**Jason Santa Maria** is a graphic designer, creative director, and educator whose work has shaped how the industry thinks about typography on the web. He served as Creative Director at Typekit (now Adobe Fonts), where he helped bring high-quality type to web designers at scale. He co-founded A Book Apart, the publisher of brief books for people who make websites, and has been a leading voice in web standards and design education. Santa Maria teaches at the School of Visual Arts (SVA) in New York City and has art-directed publications including A List Apart. His work bridges the gap between traditional typographic craft and the practical realities of designing for screens, and "On Web Typography" distills his deep expertise into an accessible, opinionated guide for working web designers.

---
name: top-design
description: 'Create award-winning, immersive web experiences at the level of Awwwards-featured agencies. Use when the user mentions "Awwwards quality", "make my site stunning", "scroll animations", "parallax storytelling", "cinematic web design", "portfolio site", or "brand experience". Also trigger when elevating a standard landing page into a memorable digital experience. Covers dramatic typography, purposeful motion, scroll-based composition, and performance-optimized animation. For foundational UI, see refactoring-ui. For type selection, see web-typography.'
license: MIT
metadata:
  author: wondelai
  version: "1.6.0"
---

# Top-Design: Award-Winning Digital Experiences

Create websites and applications at the level of world-class digital agencies. This skill embodies the craft of studios that consistently win FWA, Awwwards, CSS Design Awards, and Webby Awards.

## Core Principle

**Every pixel is intentional -- nothing default, nothing accidental.** The agencies you are emulating -- Locomotive, Studio Freight, AREA 17, Active Theory, Hello Monday -- share a common DNA: typography IS the design, motion creates emotion, white space is a weapon, and performance is non-negotiable (60fps or nothing).

**The foundation:** The gap between 8/10 and 10/10 is not skill -- it is intention. An 8/10 has good typography and smooth animations; a 10/10 has typography that makes you gasp and animations that tell stories. Every decision must answer: "Does this serve the experience, or is it just filling space?"

## Scoring

**Goal: 10/10.** Rate any digital experience 0-10 using the rubric below -- a 10/10 would be featured on Awwwards. Always state the current score and the specific improvements needed to reach 10/10.

### Scoring Rubric

| Score | Level | Description |
|-------|-------|-------------|
| **0-2** | Amateur | Default fonts, no hierarchy, generic layout, template feel |
| **3-4** | Basic | Decent typography, some hierarchy, but forgettable |
| **5-6** | Competent | Good fundamentals, clean execution, but lacks soul |
| **7-8** | Professional | Strong typography, intentional motion, clear POV |
| **9** | Exceptional | Signature moments, memorable details, near-flawless craft |
| **10** | World-class | Would win Awwwards SOTD, defines new standards |

### Category Scoring (Each 0-10)

**TYPOGRAPHY (Weight: 25%)**
| Score | Criteria |
|-------|----------|
| 0-3 | System fonts, uniform scale, default tracking |
| 4-6 | Premium fonts, some scale contrast, basic hierarchy |
| 7-8 | Dramatic scale contrast (10:1+), perfect tracking, optical alignment |
| 9-10 | Typography IS the design -- gasping moments, custom/variable fonts, type as architecture |

**VISUAL COMPOSITION (Weight: 25%)**
| Score | Criteria |
|-------|----------|
| 0-3 | Centered everything, equal spacing, rigid grid, no tension |
| 4-6 | Some asymmetry, decent spacing rhythm, basic depth |
| 7-8 | Intentional grid breaks, layered elements, strong negative space |
| 9-10 | Magnetic compositions, unexpected scale shifts, elements that breathe and surprise |

**MOTION & INTERACTION (Weight: 20%)**
| Score | Criteria |
|-------|----------|
| 0-3 | No animation or default/linear motion |
| 4-6 | Basic transitions, some scroll effects |
| 7-8 | Custom easing, orchestrated reveals, purposeful parallax |
| 9-10 | Motion that tells stories, perfectly timed choreography, scroll feels invented |

**COLOR & ATMOSPHERE (Weight: 15%)**
| Score | Criteria |
|-------|----------|
| 0-3 | Random colors, pure black/white, no mood |
| 4-6 | Cohesive palette, some atmosphere |
| 7-8 | Colors feel owned, contextual shifts, intentional contrast |
| 9-10 | Colors feel invented for this project, atmosphere you can feel |

**DETAILS & CRAFT (Weight: 15%)**
| Score | Criteria |
|-------|----------|
| 0-3 | Default cursors, no hover states, generic everything |
| 4-6 | Basic hover states, some custom elements |
| 7-8 | Magnetic buttons, branded selection colors, custom cursor (if user-approved) |
| 9-10 | Every micro-detail considered -- focus states, loading, empty states, scroll indicators |

### Quick Score Formula
```
Total = (Typography x 0.25) + (Composition x 0.25) + (Motion x 0.20) + (Color x 0.15) + (Details x 0.15)
```

## The Seven Pillars of 10/10 Design

### 1. Typography as Architecture

**Core concept:** Typography is not decoration layered onto a design -- it IS the design. Your typeface, scale, and tracking dictate color mood, animation style, spacing rhythm, and overall personality.

**Why it works:** Dramatic scale contrast creates hierarchy that communicates even when blurred or seen from across the room. The tension between monumental display type and intimate body text is what makes people stop scrolling.

**Key insights:**
- Massive scale contrast is non-negotiable -- minimum 10:1 between display and body (e.g., 180px / 14px); viewport-filling type at the extreme
- Negative tracking on large type (-0.02em to -0.05em) tightens display into cohesive units; body needs generous line-height (1.5-1.7)
- Font selection defines tier -- premium foundries (Pangram Pangram, Dinamo, Grilli Type, Klim, Commercial Type) or quality Google alternatives (Space Grotesk, Instrument Serif, Fraunces); never Inter, Roboto, Arial, or system-ui for hero experiences
- Variable fonts enable weight animation on hover without layout shift
- Optical alignment beats mathematical alignment -- adjust visually, not just numerically
- Control every line break on headlines -- beautiful breaks require manual intervention at key breakpoints

**Applications:** viewport-filling display dropping hard to body (Locomotive hero); variable font with hover weight-animation (Studio Freight); serif/sans pairing at extreme scale contrast (AREA 17 editorial). Display = one statement, 3-7 words; body = 16-18px minimum, 45-75 character measure.

See [references/typography.md](references/typography.md) when choosing typefaces or building the type scale -- named font pairings by style, full fluid `clamp()` and step-based scales, tracking/leading ladders, and font-subsetting/FOUT mechanics.

### 2. Layout & Composition

**Core concept:** Master the grid so you can break it with intention -- every violation should feel deliberate, not accidental. The rhythm of density and breathing room creates a reading experience that holds attention.

**Why it works:** White space is active design material that creates tension and controls pacing. Asymmetry generates visual energy that centered compositions cannot; elements that overlap or bleed with intention feel alive and confident.

**Key insights:**
- White space as a weapon -- amateurs fill every gap; 10/10 designers use emptiness to create tension that controls the eye
- Asymmetric balance creates interest -- offset elements from center, let images bleed beyond containers
- Unexpected scale shifts create rhythm -- alternate massive/intimate, dense/sparse for narrative pacing
- The grid paradox -- a strong underlying grid is what makes breaks meaningful; without it, breaks are chaos

**Applications:** offset title with bleeding imagery (`margin-left: 8.33%; margin-right: -5vw`); varied card sizes for intentional asymmetry (Locomotive showcases); overlapping elements for depth (Active Theory). Alternate full-width immersion with contained reading sections.

**Ethical boundary:** Layout experimentation must never compromise navigation clarity -- users must always know where they are and how to move forward.

See [references/layout-systems.md](references/layout-systems.md) when laying out sections or going responsive -- grid frameworks, breakpoint systems, and asymmetric/bleeding-element patterns.

### 3. Motion & Animation

**Core concept:** Every animation must answer "Why does this move?" The three laws of elite motion: purpose over decoration, custom curves (never linear), orchestration over isolation.

**Why it works:** Choreographed motion guides attention, communicates hierarchy, and creates emotional resonance. Custom easing curves give movement a physical quality default browser easing cannot achieve.

**Key insights:**
- Custom easing is mandatory -- `ease`, `ease-in`, `ease-out`, `linear` are banned; use `cubic-bezier(0.16, 1, 0.3, 1)` (expo out), `cubic-bezier(0.25, 1, 0.5, 1)` (quart out), `cubic-bezier(0.87, 0, 0.13, 1)` (expo in-out)
- Page load follows a strict choreography -- structure (0-200ms), hero title words staggered (200-600ms), subtitle (400-800ms), navigation cascade (600-900ms), supporting elements (800-1200ms); reference holds the canonical per-element stagger values
- Animate in relationship, not isolation -- elements that move together feel cohesive and intentional
- 60fps is non-negotiable -- if an animation drops frames, simplify or remove it

**Applications:** choreographed staggered page-load reveal (Studio Freight); clip-path/mask image reveals on scroll-enter (AREA 17); hover weight-shifts and magnetic buttons (Dogstudio). Text lines slide up individually with stagger -- never fade in as a block; pages morph rather than cut.

**Ethical boundary:** Motion must never block interaction or cause motion sickness -- respect `prefers-reduced-motion`, keep all content accessible without animation, and justify anything longer than 1.2s.

See [references/animation-patterns.md](references/animation-patterns.md) when implementing motion -- copy-pasteable scroll reveals, staggered load choreography, page transitions, and magnetic/hover micro-interactions with code.

### 4. Color & Contrast

**Core concept:** Color should feel invented for each project -- never pulled from a generic palette generator. Three approaches: monochromatic tension (95% one color, 5% accent), bold signature (own a combination), contextual shifting (palette responds to content).

**Why it works:** Color creates atmosphere before a single word is read. Pure black/white feel digital and lifeless; warm variants feel physical and considered. A restrained accent draws the eye exactly where intended.

**Key insights:**
- Never use pure black or pure white -- #0a0a0a and #fafaf9 have a physical quality that #000/#fff lack
- Build a functional hierarchy -- text-primary, text-secondary (60% opacity), text-tertiary (40%), surface, border (10%) for consistent depth
- One strong accent used sparingly (#ff4d00 or similar) beats a complex multi-color palette
- Contextual color shifts between sections create visual chapters
- Design the system for both light and dark contexts, not individual instances

**Applications:** monochromatic with signature accent (Locomotive: cream + black + orange spark); contextual shifting per case study (AREA 17); dark mode with one vibrant accent (Stripe: navy + purple). Drive everything from CSS custom properties (`--color-dark/-light/-accent` plus functional `--color-text-primary/-surface`); the accent appears only on CTAs, links, and single-detail moments.

See [references/case-studies.md](references/case-studies.md) when you need a worked example of any pillar -- agency-by-agency breakdowns of real color systems, type treatments, and micro-interactions to reverse-engineer.

### 5. Scroll-Based Design

**Core concept:** Scroll is the web's primary interaction and should feel designed, not default. Treat scroll as a narrative device -- controlling pacing, creating reveals, building tension, delivering signature moments.

**Why it works:** Default scroll is mechanical and treats all content as equally important. When scroll position drives reveals and transitions, moving through content becomes participatory rather than passive.

**Key insights:**
- Smooth scroll is the foundation -- implement Lenis or Locomotive Scroll for the weighted, physical feel every award-winning site uses
- Parallax must be purposeful -- sparing, and only on decorative elements; never on text or critical content
- Pinned sections create storytelling beats -- lock a section while content transforms within it
- Horizontal scroll galleries need clear visual affordance
- Reveals should be progressive -- elements enter as they become visible, creating discovery
- Scroll velocity can modulate animation speed for a responsive feel

**Applications:** pinned hero with scroll-driven transformation (Apple deep-dives); horizontal scroll gallery with affordance (Studio Freight); scroll-driven animation sequences (Active Theory). Use IntersectionObserver for lightweight class toggling; reserve GSAP ScrollTrigger for complex multi-step sequences.

**Ethical boundary:** Scroll hijacking is hostile UX -- users must always be able to scroll at their own pace and reach all content.

See [references/technical-stack.md](references/technical-stack.md) to wire up smooth scroll (Lenis/Locomotive setup, library tradeoffs) and [references/animation-patterns.md](references/animation-patterns.md) for pinning, horizontal galleries, and scroll-velocity sequences.

### 6. Performance & Loading

**Core concept:** Performance is a design constraint from day one, not an optimization step. A beautiful animation that drops frames or a stunning font that causes layout shift fails the craft test.

**Why it works:** Users perceive performance as quality -- instant load and fluid scroll feel premium regardless of visual complexity, while a stunning site that stutters feels broken.

**Key insights:**
- Subset and preload fonts -- only needed glyphs, `font-display: swap` or `optional`, preload critical files
- Optimize images -- WebP/AVIF with fallbacks, responsive `srcset`, lazy-load below the fold
- GPU-accelerate animations -- only animate `transform` and `opacity`; never `width`, `height`, `top`, `left`, or `margin`
- CLS near zero -- reserve space for images, fonts, and dynamic content (`aspect-ratio` on containers)
- LCP under 2.5s -- optimize the critical rendering path for the hero
- Loading states are designed elements -- custom skeletons and progress indicators, not afterthoughts

**Applications:** subset/preload/swap fonts (`<link rel="preload" as="font" crossorigin>`); AVIF/WebP with responsive `srcset` (`<picture>` fallbacks); GPU-only animation (`transform: translate3d()` + `opacity`). Audit with Lighthouse targeting 90+; code-split and defer non-critical JS.

**Ethical boundary:** Fast-but-inaccessible is not a valid tradeoff -- never strip accessibility features or semantic HTML for speed.

See [references/technical-stack.md](references/technical-stack.md) when choosing libraries or hitting a perf budget -- the recommended stack and concrete font/image/animation optimization techniques.

### 7. Micro-Interactions

**Core concept:** Craft lives in the 1% most designers skip: branded selection colors, magnetic buttons, designed focus states, considered loading states, crafted error pages, correct micro-typography.

**IMPORTANT: Custom cursors are OPT-IN only.** Never replace the native cursor unless the user explicitly requests or confirms one -- misapplied custom cursors hurt usability and feel gimmicky. Always ask first.

**Why it works:** Micro-interactions signal that every pixel was considered. Individually subtle, collectively transformative -- users feel the care embedded in the experience.

**Key insights:**
- Custom cursor reflects brand personality, with variants on interactive elements (subject to the opt-in rule above)
- Branded `::selection` color that works on all backgrounds
- Every link and card has a considered hover state -- scale, overlay, or meaningful transform
- Focus states are visible AND beautiful -- on-brand indicators that keyboard users can clearly see
- Loading, empty, 404, and error states are designed, helpful moments
- Micro-typography is correct -- smart quotes, en/em dashes, no orphans on headlines, `text-wrap: balance` on key text

**Ethical boundary:** Focus states must meet keyboard-visibility requirements even when styled on-brand, and error/empty/404 states must be genuinely helpful, not just decorative.

See [references/animation-patterns.md](references/animation-patterns.md) for copy-pasteable magnetic-button, cursor, and `::selection`/hover micro-interaction code.

## Design Process

Work in this order -- the sequence is the discipline:

1. **Concept before code.** Define four things first:
```
BRAND ESSENCE: What single word captures the soul?
VISUAL TENSION: What opposing forces create interest?
SIGNATURE MOMENT: What will people screenshot and share?
TECHNICAL AMBITION: What pushes the browser's limits?
```
2. **Design the signature moment first** -- not the header. Every 10/10 project has at least one moment people stop and share (a never-seen hero animation, typography bold enough to BE the visual, a scroll sequence that tells a story). Pin it down by asking: what will people screenshot, describe to a colleague, try to reverse-engineer, and what makes it unmistakably THIS project?
3. **Choose the display typeface next** -- it dictates the rest (Pillar 1).
4. **Prototype motion alongside visual design, not after** -- motion is not polish (Pillar 3).
5. **Ship with restraint** -- 3 things perfect beats 10 things mediocre. Cut ruthlessly.

## Implementation Notes

1. **Conceptualize desktop-first, build mobile-first** -- dream big, implement progressively
2. **Use project conventions** -- if Tailwind 4+ and/or shadcn/ui are available, extend their design tokens and components as the foundation for 10/10 craft rather than fighting them

## Common Mistakes

Each fix points to the pillar that defines the rule -- do not re-derive values here.

| Mistake | Why It Fails | Fix (see) |
|---------|-------------|-----|
| Inter, Roboto, Arial, or system-ui as primary typeface | Application fonts signal generic, not premium | Premium foundry or quality Google alternative (Pillar 1) |
| Uniform type scale (everything within 2x) | No hierarchy, no gasping moments | Hit the display-to-body ratio (Pillar 1) |
| `ease`, `ease-in`, `ease-out`, or `linear` easing | Mechanical, lifeless -- instantly signals amateur | Banned -- use a custom cubic-bezier (Pillar 3) |
| Animating everything simultaneously | Visual noise, no hierarchy or narrative | Stagger and sequence by importance (Pillar 3) |
| Center-aligning everything | Safe but boring -- no tension or energy | Asymmetry, grid offsets, bleeding elements (Pillar 2) |
| Equal spacing everywhere | Monotony -- the eye has nowhere to rest | Vary density: dense sections, then breathing room (Pillar 2) |
| Pure #000000 / #ffffff | Lifeless and harsh | Warm variants (Pillar 4) |
| Default browser scroll | Mechanical, treats all content equally | Smooth-scroll library (Pillar 5) |
| Purple-to-blue gradient hero | The "AI gradient" -- generic trend-following | Signature color approach specific to the project (Pillar 4) |
| No signature moment | Competent but forgettable | Design the screenshot-worthy moment FIRST (Process step 2) |
| Any emoji in professional interfaces | Signals casual/amateur craft | Custom iconography or typographic treatments |
| Parallax on text or critical content | Motion sickness, accessibility failures | Parallax only on decorative background elements (Pillar 5) |
| Animations blocking interaction | Hostile UX | Keep all animation non-blocking (Pillar 3) |
| Unmodified Font Awesome icons | Template-level design | Custom icons, or heavily customize to match brand |
| Default form styles | Breaks the illusion of craft instantly | Design every input, select, checkbox, and button (Pillar 7) |

## Quick Diagnostic

Score 1 point per row answered "yes", then map the count to the Scoring Rubric band: 11-12 -> 9-10, 8-10 -> 7-8, 5-7 -> 5-6, below 5 -> 0-4. State that score.

| Question | If No | Fix (see) |
|----------|-------|--------|
| Does the hero typography make someone pause mid-scroll? | Display type not commanding | Pillar 1 -- scale, distinctive typeface, viewport-filling |
| Would someone screenshot any section? | No signature moment | Process step 2 -- make one section extraordinary |
| Does the design still read when you blur your eyes? | Hierarchy too flat | Bigger headlines, more white space, stronger accents |
| Are all easing curves custom (no `ease`/`linear`)? | Motion feels default | Pillar 3 -- custom cubic-bezier |
| Is there asymmetric tension in the composition? | Layout feels safe | Pillar 2 -- offset, bleed, vary density |
| Do the colors feel invented for THIS project? | Generic palette | Pillar 4 -- monochromatic tension, signature, or contextual |
| Is the page load choreographed? | Elements pop in at once | Pillar 3 -- staggered reveal sequence |
| Does scroll feel custom and weighted? | Default browser scroll | Pillar 5 -- smooth-scroll library |
| Are micro-details considered (selection, focus, cursor)? | Default browser behaviors remain | Pillar 7 -- branded selection, designed focus (cursors opt-in) |
| Is CLS near zero and LCP under 2.5s? | Performance undermines quality | Pillar 6 -- subset fonts, WebP/AVIF, transform/opacity only |
| Does every animation answer "why does this move?" | Decorative motion | Pillar 3 -- cut motion with no narrative or guidance |
| Are focus states both beautiful AND accessible? | One sacrificed for the other | Pillar 7 -- on-brand indicators meeting WCAG visibility |

## Further Reading

- [Designing with Type](https://www.amazon.com/Designing-Type-Essential-Typography/dp/0823014134?tag=wondelai00-20) by James Craig -- foundational text on typographic principles and hierarchy
- [Grid Systems in Graphic Design](https://www.amazon.com/Grid-Systems-Graphic-Design-Communication/dp/3721201450?tag=wondelai00-20) by Josef Muller-Brockmann -- the definitive work on grid-based composition
- [The Elements of Typographic Style](https://www.amazon.com/Elements-Typographic-Style-Version-4-0/dp/0881792128?tag=wondelai00-20) by Robert Bringhurst -- the typographer's bible on rhythm, proportion, and craft
- [Interaction of Color](https://www.amazon.com/Interaction-Color-50th-Anniversary-Edition/dp/0300179359?tag=wondelai00-20) by Josef Albers -- essential reading on color perception and contrast
- [Layout Essentials: 100 Design Principles for Using Grids](https://www.amazon.com/Layout-Essentials-Design-Principles-Using/dp/1592537073?tag=wondelai00-20) by Beth Tondreau -- practical grid-based layout principles
- [Awwwards Annual: The Best 365 Websites Around the World](https://www.awwwards.com/books/) -- yearly benchmark collection for 10/10 craft

## About the Author

This skill synthesizes techniques from the world's most awarded digital agencies: **Locomotive** (Montreal -- creators of Locomotive Scroll, masters of monochromatic tension and bold typography), **Studio Freight** (New York -- magnetic interactions and signature palettes), **AREA 17** (New York/Paris -- contextual design systems and editorial layouts), **Active Theory** (Los Angeles -- WebGL and immersive 3D storytelling), and **Hello Monday** (Copenhagen/New York -- playful interactions for Spotify, Adidas, Google). Additional inspiration from Dogstudio, Tonik, Instrument, Resn, and the broader Awwwards, FWA, CSS Design Awards, and Webby winner community.

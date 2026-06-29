---
name: top-design
description: 'Create award-winning, immersive web experiences at the level of Awwwards-featured agencies. Use when the user mentions "premium website", "portfolio site", "scroll animations", "Awwwards quality", "brand experience", "cinematic web design", "parallax storytelling", "agency-quality site", "make my site stunning", "give it a wow factor", or "an impressive website". Also trigger when building a landing page that needs to impress, designing a creative portfolio, or elevating a standard website into a memorable digital experience. Covers dramatic typography, purposeful motion, scroll-based composition, and performance-optimized animation. For foundational UI, see refactoring-ui. For type selection, see web-typography.'
license: MIT
metadata:
  author: wondelai
  version: "1.5.0"
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

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Portfolio hero | Viewport-filling display type, dramatic drop to body | Locomotive.ca hero typography |
| Brand website | Variable font with weight animation on hover | Studio Freight interactive type |
| Editorial layout | Serif/sans pairing with extreme scale contrast | AREA 17 case studies |

**Copy patterns:**
- Display: single powerful statement, 3-7 words maximum
- Subhead: one sentence that contextualizes the display type
- Body: 16-18px minimum, generous line-height, 45-75 character measure

**Ethical boundary:** Never sacrifice legibility for aesthetic novelty -- body text must meet WCAG contrast requirements and remain readable.

See: [references/typography.md](references/typography.md) for font pairing strategies, type scale systems, and advanced CSS typography.

### 2. Layout & Composition

**Core concept:** Master the grid so you can break it with intention -- every violation should feel deliberate, not accidental. The rhythm of density and breathing room creates a reading experience that holds attention.

**Why it works:** White space is active design material that creates tension and controls pacing. Asymmetry generates visual energy that centered compositions cannot; elements that overlap or bleed with intention feel alive and confident.

**Key insights:**
- White space as a weapon -- amateurs fill every gap; 10/10 designers use emptiness to create tension that controls the eye
- Asymmetric balance creates interest -- offset elements from center, let images bleed beyond containers
- Unexpected scale shifts create rhythm -- alternate massive/intimate, dense/sparse for narrative pacing
- The grid paradox -- a strong underlying grid is what makes breaks meaningful; without it, breaks are chaos

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Hero section | Offset title with bleeding imagery | `margin-left: 8.33%; margin-right: -5vw` |
| Portfolio grid | Varied card sizes, intentional asymmetry | Locomotive project showcases |
| Feature showcase | Overlapping elements creating depth | Active Theory layered compositions |

**Copy patterns:**
- Hero: position text off-center with intentional grid alignment
- Sections: alternate full-width immersion with contained reading
- Cards: vary sizes within grids -- uniformity is monotony

**Ethical boundary:** Layout experimentation must never compromise navigation clarity -- users must always know where they are and how to move forward.

See: [references/layout-systems.md](references/layout-systems.md) for grid frameworks, breakpoints, and responsive patterns.

### 3. Motion & Animation

**Core concept:** Every animation must answer "Why does this move?" The three laws of elite motion: purpose over decoration, custom curves (never linear), orchestration over isolation.

**Why it works:** Choreographed motion guides attention, communicates hierarchy, and creates emotional resonance. Custom easing curves give movement a physical quality default browser easing cannot achieve.

**Key insights:**
- Custom easing is mandatory -- `ease`, `ease-in`, `ease-out`, `linear` are banned; use `cubic-bezier(0.16, 1, 0.3, 1)` (expo out), `cubic-bezier(0.25, 1, 0.5, 1)` (quart out), `cubic-bezier(0.87, 0, 0.13, 1)` (expo in-out)
- Page load follows a strict choreography -- structure (0-200ms), hero title words staggered (200-600ms, 80ms stagger), subtitle (400-800ms), navigation cascade (600-900ms), supporting elements (800-1200ms)
- Animate in relationship, not isolation -- elements that move together feel cohesive and intentional
- 60fps is non-negotiable -- if an animation drops frames, simplify or remove it

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Page load | Choreographed staggered reveal sequence | Studio Freight entry animations |
| Image reveals | Clip-path or mask animations on scroll enter | AREA 17 case study reveals |
| Micro-interactions | Hover weight shifts, magnetic button effects | Dogstudio interactive details |

**Copy patterns:**
- Reveal: text lines slide up individually with stagger (never fade in as a block)
- Hover: respond with scale shift or color transition
- Transition: pages morph rather than cut or fade

**Ethical boundary:** Motion must never block interaction or cause motion sickness -- respect `prefers-reduced-motion`, keep all content accessible without animation, and justify anything longer than 1.2s.

See: [references/animation-patterns.md](references/animation-patterns.md) for scroll animations, page transitions, and micro-interactions with code.

### 4. Color & Contrast

**Core concept:** Color should feel invented for each project -- never pulled from a generic palette generator. Three approaches: monochromatic tension (95% one color, 5% accent), bold signature (own a combination), contextual shifting (palette responds to content).

**Why it works:** Color creates atmosphere before a single word is read. Pure black/white feel digital and lifeless; warm variants feel physical and considered. A restrained accent draws the eye exactly where intended.

**Key insights:**
- Never use pure black or pure white -- #0a0a0a and #fafaf9 have a physical quality that #000/#fff lack
- Build a functional hierarchy -- text-primary, text-secondary (60% opacity), text-tertiary (40%), surface, border (10%) for consistent depth
- One strong accent used sparingly (#ff4d00 or similar) beats a complex multi-color palette
- Contextual color shifts between sections create visual chapters
- Design the system for both light and dark contexts, not individual instances

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Agency portfolio | Monochromatic with signature accent | Locomotive: cream + black + orange spark |
| Client showcase | Contextual shifting per case study | AREA 17: adapts palette to each client |
| Product landing | Dark mode with single vibrant accent | Stripe: dark navy + signature purple |

**Copy patterns:**
- Define CSS custom properties: `--color-dark`, `--color-light`, `--color-accent`, then functional tokens (`--color-text-primary`, `--color-surface`)
- Use opacity variants (`rgba(10, 10, 10, 0.6)`) for secondary/tertiary text
- Accent appears on CTAs, links, and single-detail moments -- never everywhere

**Ethical boundary:** All color combinations must meet WCAG 2.1 AA contrast minimums -- atmosphere cannot cost readability.

See: [references/case-studies.md](references/case-studies.md) for agency technique breakdowns including color systems and micro-interactions.

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

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Product story | Pinned hero with scroll-driven transformation | Apple product deep-dives |
| Landing page | Horizontal scroll gallery with affordance | Studio Freight work galleries |
| Brand narrative | Scroll-driven animation sequences | Active Theory immersive stories |

**Copy patterns:**
- Use `data-scroll`, `data-scroll-speed`, `data-scroll-direction` for declarative behavior
- Intersection observers for lightweight class toggling; GSAP ScrollTrigger only for complex multi-step sequences
- Always provide a non-scroll fallback for accessibility

**Ethical boundary:** Scroll hijacking is hostile UX -- users must always be able to scroll at their own pace and reach all content.

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

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Font loading | Subset, preload, swap strategy | `<link rel="preload" as="font" crossorigin>` |
| Image delivery | AVIF/WebP with responsive srcset | `<picture>` element with format fallbacks |
| Animation perf | GPU-only properties with will-change hints | `transform: translate3d()` + `opacity` |

**Copy patterns:**
- Audit with Lighthouse, targeting 90+ on all metrics
- Profile animations at 4x CPU throttle in Chrome DevTools; use `will-change` sparingly
- Code-split and defer non-critical JS; dynamic imports for below-fold interactivity

**Ethical boundary:** Fast-but-inaccessible is not a valid tradeoff -- never strip accessibility features or semantic HTML for speed.

See: [references/technical-stack.md](references/technical-stack.md) for libraries, tools, and performance optimization techniques.

### 7. Micro-Interactions

**Core concept:** Craft lives in the 1% most designers skip: branded selection colors, magnetic buttons, designed focus states, considered loading states, crafted error pages, correct micro-typography.

**IMPORTANT: Custom cursors are OPT-IN only.** Never replace the native cursor unless the user explicitly requests or confirms one -- misapplied custom cursors hurt usability and feel gimmicky. Always ask first.

**Why it works:** Micro-interactions signal that every pixel was considered. Individually subtle, collectively transformative -- users feel the care embedded in the experience.

**Key insights:**
- Custom cursor reflects brand personality (opt-in only -- ask the user first), with variants on interactive elements
- Branded `::selection` color that works on all backgrounds
- Every link and card has a considered hover state -- scale, overlay, or meaningful transform
- Focus states are visible AND beautiful -- on-brand indicators that keyboard users can clearly see
- Loading, empty, 404, and error states are designed, helpful moments
- Micro-typography is correct -- smart quotes, en/em dashes, no orphans on headlines, `text-wrap: balance` on key text

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Cursor | Custom cursor with element variants (opt-in -- confirm first) | Dogstudio cursor system |
| Buttons | Magnetic hover effect with subtle pull | Studio Freight magnetic buttons |
| Focus | Styled focus-visible rings matching brand | Accessible + beautiful indicators |

**Copy patterns:**
- `::selection { background: var(--color-accent); color: var(--color-light); }`
- Magnetic effect: compute cursor-to-button distance, apply proportional transform (cursor work is opt-in -- confirm first)
- Smart quotes: `&ldquo;`/`&rdquo;` or auto-convert in the build tool

**Ethical boundary:** Micro-interactions must enhance usability -- custom cursors only with explicit user approval and always functional, focus states meeting accessibility requirements, error states genuinely helpful.

## Design Process

### 1. Concept First, Code Second

Before any code, define:
```
BRAND ESSENCE: What single word captures the soul?
VISUAL TENSION: What opposing forces create interest?
SIGNATURE MOMENT: What will people screenshot and share?
TECHNICAL AMBITION: What pushes the browser's limits?
```

### 2. Design the Signature Moment First

Do not start with the header -- start with the thing that defines the experience. Every 10/10 project has at least one moment people stop and share: a never-seen hero animation, typography so bold it becomes the visual, a scroll sequence that tells a story.

**Questions to identify your signature:**
1. What will people screenshot?
2. What will they describe to colleagues?
3. What will they try to reverse-engineer?
4. What makes this unmistakably THIS project?

### 3. Typography Sets Everything

Choose your display typeface first. Let it dictate the color palette mood, animation style, spacing rhythm, and overall personality.

### 4. Motion Is Not Polish

Prototype animations early. Motion design happens alongside visual design, not after.

### 5. Ship With Restraint

3 things perfect beats 10 things mediocre. Cut ruthlessly.

## Implementation Notes

1. **Conceptualize desktop-first, build mobile-first** -- dream big, implement progressively
2. **Test on real devices** -- simulators lie about performance and feel
3. **Design every state** -- hover, focus, loading, empty, error all matter
4. **Own your constraints** -- every limitation is a design opportunity
5. **Use project conventions** -- if Tailwind 4+ and/or shadcn/ui are available, extend their design tokens and components as the foundation for 10/10 craft rather than fighting them

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Inter, Roboto, Arial, or system-ui as primary typeface | Application fonts signal generic, not premium | Premium foundries (Pangram Pangram, Dinamo, Grilli Type, Klim) or quality Google alternatives (Space Grotesk, Instrument Serif, Fraunces) |
| Uniform type scale (everything within 2x) | No hierarchy, no gasping moments | Minimum 10:1 display-to-body ratio; viewport-filling type |
| `ease`, `ease-in`, `ease-out`, or `linear` easing | Mechanical, lifeless -- instantly signals amateur | Custom cubic-beziers: expo out (0.16, 1, 0.3, 1), quart out (0.25, 1, 0.5, 1) |
| Animating everything simultaneously | Visual noise, no hierarchy or narrative | Choreograph with 80ms stagger, sequence by importance |
| Center-aligning everything | Safe but boring -- no tension or energy | Asymmetric compositions, grid offsets, bleeding elements |
| Equal spacing everywhere | Monotony -- the eye has nowhere to rest | Vary spacing: dense sections then breathing room |
| Pure #000000 black and #ffffff white | Lifeless and harsh | Warm variants: #0a0a0a, #fafaf9 |
| Default browser scroll | Mechanical, treats all content equally | Lenis or Locomotive Scroll for weighted, physical feel |
| Purple-to-blue gradient hero | The "AI gradient" -- generic trend-following | Signature color approach specific to the project |
| No signature moment | Competent but forgettable | Design the screenshot-worthy moment FIRST |
| Any emoji in professional interfaces | Signals casual/amateur craft | Custom iconography or typographic treatments |
| Parallax on text or critical content | Motion sickness, accessibility failures | Parallax only on decorative background elements |
| Animations blocking interaction | Hostile UX | Keep all animation non-blocking; content always accessible |
| Unmodified Font Awesome icons | Template-level design | Custom icons, or heavily customize to match brand |
| Default form styles | Breaks the illusion of craft instantly | Design every input, select, checkbox, and button |

## Quick Diagnostic

| Question | If No | Action |
|----------|-------|--------|
| Does the hero typography make someone pause mid-scroll? | Display type not commanding | Push scale to 10:1+, pick a distinctive typeface, fill the viewport |
| Would someone screenshot any section? | No signature moment | Make one section extraordinary -- animation, scale shift, or interaction |
| Does the design still read when you blur your eyes? | Hierarchy too flat | Bigger headlines, more white space, stronger accents |
| Are all easing curves custom (no `ease`/`linear`)? | Motion feels default | Expo out (0.16, 1, 0.3, 1) or quart out (0.25, 1, 0.5, 1) |
| Is there asymmetric tension in the composition? | Layout feels safe | Offset from center, bleed images, vary section density |
| Do the colors feel invented for THIS project? | Generic palette | Monochromatic tension, bold signature, or contextual shifting |
| Is the page load choreographed? | Elements pop in at once | Staggered reveal: structure, hero, then supporting elements |
| Does scroll feel custom and weighted? | Default browser scroll | Implement Lenis or Locomotive Scroll |
| Are micro-details considered (selection, focus, cursor)? | Default browser behaviors remain | Branded selection, designed focus states; cursors only with user approval |
| Is CLS near zero and LCP under 2.5s? | Performance undermines quality | Subset fonts, WebP/AVIF images, animate only transform/opacity |
| Does every animation answer "why does this move?" | Decorative motion | Remove animation that serves no narrative, hierarchy, or guidance |
| Are focus states both beautiful AND accessible? | One sacrificed for the other | On-brand indicators that meet WCAG visibility requirements |

## Reference Files

Consult these for detailed implementation:

- **[references/typography.md](references/typography.md)**: Font pairing strategies, type scale systems, advanced CSS typography
- **[references/animation-patterns.md](references/animation-patterns.md)**: Scroll animations, page transitions, micro-interactions with code
- **[references/layout-systems.md](references/layout-systems.md)**: Grid frameworks, breakpoints, responsive patterns
- **[references/technical-stack.md](references/technical-stack.md)**: Libraries, tools, performance optimization
- **[references/case-studies.md](references/case-studies.md)**: Agency technique breakdowns (Locomotive, Studio Freight, AREA 17, Hello Monday, etc.)

## Further Reading

- [Designing with Type](https://www.amazon.com/Designing-Type-Essential-Typography/dp/0823014134?tag=wondelai00-20) by James Craig -- foundational text on typographic principles and hierarchy
- [Grid Systems in Graphic Design](https://www.amazon.com/Grid-Systems-Graphic-Design-Communication/dp/3721201450?tag=wondelai00-20) by Josef Muller-Brockmann -- the definitive work on grid-based composition
- [The Elements of Typographic Style](https://www.amazon.com/Elements-Typographic-Style-Version-4-0/dp/0881792128?tag=wondelai00-20) by Robert Bringhurst -- the typographer's bible on rhythm, proportion, and craft
- [Interaction of Color](https://www.amazon.com/Interaction-Color-50th-Anniversary-Edition/dp/0300179359?tag=wondelai00-20) by Josef Albers -- essential reading on color perception and contrast
- [Layout Essentials: 100 Design Principles for Using Grids](https://www.amazon.com/Layout-Essentials-Design-Principles-Using/dp/1592537073?tag=wondelai00-20) by Beth Tondreau -- practical grid-based layout principles
- [Awwwards Annual: The Best 365 Websites Around the World](https://www.awwwards.com/books/) -- yearly benchmark collection for 10/10 craft

## About the Author

This skill synthesizes techniques from the world's most awarded digital agencies: **Locomotive** (Montreal -- creators of Locomotive Scroll, masters of monochromatic tension and bold typography), **Studio Freight** (New York -- magnetic interactions and signature palettes), **AREA 17** (New York/Paris -- contextual design systems and editorial layouts), **Active Theory** (Los Angeles -- WebGL and immersive 3D storytelling), and **Hello Monday** (Copenhagen/New York -- playful interactions for Spotify, Adidas, Google). Additional inspiration from Dogstudio, Tonik, Instrument, Resn, and the broader Awwwards, FWA, CSS Design Awards, and Webby winner community.

---
name: top-design
description: 'Create award-winning, immersive web experiences at the level of Awwwards-featured agencies. Use when the user mentions "premium website", "portfolio site", "scroll animations", "Awwwards quality", or "brand experience". Covers dramatic typography, purposeful motion, scroll-based composition, and performance-optimized animation. For foundational UI, see refactoring-ui. For type selection, see web-typography.'
license: MIT
metadata:
  author: wondelai
  version: "1.1.1"
---

# Top-Design: Award-Winning Digital Experiences

Create websites and applications at the level of world-class digital agencies. This skill embodies the craft of studios that consistently win FWA, Awwwards, CSS Design Awards, and Webby Awards.

## Core Principle

**Every pixel is intentional -- nothing default, nothing accidental.** The agencies you are emulating -- Locomotive, Studio Freight, AREA 17, Active Theory, Hello Monday -- share a common DNA: typography IS the design (not decoration, but architecture), motion creates emotion (animation serves narrative, not novelty), white space is a weapon (tension through restraint), and performance is non-negotiable (60fps or nothing).

**The foundation:** What separates 10/10 from 8/10 is not incremental improvement but a qualitative leap. An 8/10 design has good typography, nice colors, and smooth animations. A 10/10 design has typography that makes you gasp, colors that feel invented for this specific project, and animations that tell stories. The gap is not skill -- it is intention. Every decision at the 10/10 level answers the question: "Does this serve the experience, or is it just filling space?"

## Scoring

**Goal: 10/10.** When reviewing or creating digital experiences, rate them 0-10 using the rubric below. A 10/10 means the design would be featured on Awwwards. Always provide the current score and specific improvements needed to reach 10/10.

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
| 7-8 | Custom cursor, magnetic buttons, branded selection colors |
| 9-10 | Every micro-detail considered -- focus states, loading, empty states, scroll indicators |

### Quick Score Formula
```
Total = (Typography x 0.25) + (Composition x 0.25) + (Motion x 0.20) + (Color x 0.15) + (Details x 0.15)
```

## The Seven Pillars of 10/10 Design

### 1. Typography as Architecture

**Core concept:** Typography is not decoration layered onto a design -- it IS the design. The typeface you choose, the scale you set, and the tracking you refine dictate everything else: color palette mood, animation style, spacing rhythm, and overall personality. When someone scrolls past your hero and does not pause, your typography is not working.

**Why it works:** Dramatic scale contrast creates immediate visual hierarchy that communicates even when content is blurred or viewed from across the room. Large display type with tight tracking commands attention like architecture commands a skyline, while intimate body text draws readers into the content. This tension between monumental and personal is what makes people stop scrolling.

**Key insights:**
- **Massive scale contrast is non-negotiable** -- the ratio between display and body should be at minimum 10:1 (e.g., 180px headline / 14px body), with viewport-filling type at the extreme end making body text feel intimate
- **Negative tracking on large type** (-0.02em to -0.05em) tightens display text into cohesive visual units, while generous line-height for body (1.5-1.7) ensures readability
- **Font selection defines tier** -- display fonts should come from premium foundries (Pangram Pangram, Dinamo, Grilli Type, Klim, Commercial Type) or quality Google alternatives (Space Grotesk, Instrument Serif, Fraunces); never Inter, Roboto, Arial, or system-ui for hero experiences
- **Variable fonts enable weight animation** on hover states and transitions, adding dynamism without layout shift
- **Optical alignment over mathematical alignment** -- human perception is imperfect, so text must be adjusted visually, not just numerically
- **Control every line break on headlines** -- text that breaks beautifully requires manual intervention at key breakpoints

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Portfolio hero | Viewport-filling display type with dramatic scale drop to body | Locomotive.ca hero typography |
| Brand website | Custom/variable font with weight animation on hover | Studio Freight interactive type |
| Product landing | Tight display tracking with generous body spacing | Apple product pages |
| Editorial layout | Serif/sans pairing with extreme scale contrast | AREA 17 case studies |
| Cultural institution | Statement typography that becomes the visual identity | Hello Monday museum sites |
| Tech startup | Premium geometric sans at architectural scale | Stripe typography system |

**Copy patterns:**
- Display: single powerful statement, 3-7 words maximum
- Subhead: one sentence that contextualizes the display type
- Body: 16-18px minimum, generous line-height, moderate measure (45-75 characters)
- The "typography stare test": blur your eyes -- does the type hierarchy still read? If everything looks the same importance when blurred, you have failed

**Ethical boundary:** Typography choices should enhance readability and accessibility, not sacrifice legibility for aesthetic novelty. Ensure body text meets WCAG contrast requirements and remains readable at standard viewing distances.

See: [references/typography.md](references/typography.md) for font pairing strategies, type scale systems, and advanced CSS typography.

### 2. Layout & Composition

**Core concept:** Master the grid so you can break it with intention. Every violation should feel deliberate, not accidental. The rhythm of density and breathing room -- full-viewport hero, intimate text section, massive single word, dense grid -- creates a reading experience that holds attention.

**Why it works:** White space is not empty space -- it is active design material that creates tension, controls pacing, and makes viewers lean in. Asymmetric layouts generate visual energy that centered, symmetrical compositions cannot achieve. When elements overlap, bleed, or extend beyond their containers with intention, the design feels alive and confident rather than constrained.

**Key insights:**
- **White space as a weapon** -- amateurs fill every gap with content, professionals use padding liberally, 10/10 designers use white space to create tension that controls the reader's eye
- **Asymmetric balance creates interest** -- offset elements from center (e.g., one column offset in a 12-column grid), let images bleed and extend beyond containers
- **Unexpected scale shifts create rhythm** -- the alternation between massive and intimate, dense and sparse, creates a narrative pacing that prevents monotony
- **Elements should overlap, bleed, or extend with intention** -- breaking the container signals confidence and craftsmanship
- **The grid paradox** -- a strong underlying grid is necessary precisely so you can break it meaningfully; without the grid, breaks are just chaos
- **The screenshot test** -- if someone would not screenshot a section and share it, you are missing signature moments

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Hero section | Offset title with bleeding imagery | `margin-left: 8.33%; margin-right: -5vw` |
| Portfolio grid | Varied card sizes with intentional asymmetry | Locomotive project showcases |
| Section transitions | Scale shifts between dense and breathing sections | Studio Freight scroll compositions |
| Image galleries | Mixed full-bleed and contained images | AREA 17 editorial layouts |
| Feature showcase | Overlapping elements creating depth | Active Theory layered compositions |
| Navigation | Asymmetric mega-menus with dramatic scale | Hello Monday navigation systems |

**Copy patterns:**
- Hero: position text off-center with intentional alignment to grid
- Sections: alternate between full-width immersion and contained reading
- Cards: vary sizes within grids -- not everything needs to be the same dimensions
- Images: mix full-bleed, contained, and overlapping treatments

**Ethical boundary:** Layout experimentation must not compromise navigation clarity or content accessibility. Users should always understand where they are, how to move forward, and how to access critical information regardless of compositional choices.

See: [references/layout-systems.md](references/layout-systems.md) for grid frameworks, breakpoints, and responsive patterns.

### 3. Motion & Animation

**Core concept:** Every animation must answer "Why does this move?" Motion is not polish applied at the end -- it is core to the design, prototyped early and developed alongside visual design. The three laws of elite motion are: purpose over decoration, custom curves (never linear), and orchestration over isolation.

**Why it works:** Choreographed motion creates a cinematic experience that guides attention, communicates hierarchy, and creates emotional resonance. When elements animate in relationship to each other rather than independently, the result feels cohesive and intentional. Custom easing curves (exponential, quartic) give movement a physical quality that default browser easing cannot achieve.

**Key insights:**
- **Custom easing is mandatory** -- `ease`, `ease-in`, `ease-out`, and `linear` are banned; use `cubic-bezier(0.16, 1, 0.3, 1)` (expo out), `cubic-bezier(0.25, 1, 0.5, 1)` (quart out), `cubic-bezier(0.87, 0, 0.13, 1)` (expo in-out)
- **Page load choreography follows a strict timeline** -- background/structure (0-200ms), hero title words staggered (200-600ms, 80ms stagger), subtitle (400-800ms), navigation cascade (600-900ms), supporting elements (800-1200ms)
- **Scroll-triggered sequences reveal elements as they enter viewport** -- not all at once; parallax used sparingly and only on non-essential elements
- **Pinned sections for storytelling moments** and horizontal scroll for galleries (with clear affordance) create immersive reading experiences
- **Default browser scroll is unacceptable** -- use Lenis or Locomotive Scroll for smooth, custom scroll behavior
- **60fps is non-negotiable** -- if an animation drops frames, simplify or remove it

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Page load | Choreographed staggered reveal sequence | Studio Freight entry animations |
| Scroll sections | Pinned storytelling with progressive reveals | Locomotive scroll experiences |
| Navigation | Magnetic hover effects with custom cursors | Active Theory interactive nav |
| Image reveals | Clip-path or mask animations on scroll enter | AREA 17 case study reveals |
| Page transitions | Seamless cross-page animation continuity | Hello Monday page morphs |
| Micro-interactions | Hover weight shifts, button magnetic effects | Dogstudio interactive details |

**Copy patterns:**
- Reveal: text lines slide up individually with stagger (not fade in as a block)
- Hover: elements respond with custom cursor, scale shift, or color transition
- Scroll: content reveals progressively, never all at once
- Transition: pages morph rather than cut or fade

**Ethical boundary:** Motion must never block interaction, cause motion sickness, or prevent users from accessing content. Always respect `prefers-reduced-motion` and ensure all content is accessible without animation. Animations longer than 1.2s require clear justification.

See: [references/animation-patterns.md](references/animation-patterns.md) for scroll animations, page transitions, and micro-interactions with code.

### 4. Color & Contrast

**Core concept:** Color should feel invented for each specific project -- not pulled from a generic palette generator. The three approaches are monochromatic tension (95% one dominant color, 5% accent that pops), bold signature (own a color combination and make it unmistakable), and contextual shifting (color responds to content, with sections having distinct palettes).

**Why it works:** Color creates atmosphere before a single word is read. When colors feel owned by a specific project, they become part of the brand's identity. Pure black (#000000) and pure white (#ffffff) feel digital and lifeless; slightly warm variants (#0a0a0a, #fafaf9) feel physical and considered. The restrained use of a single accent color creates moments of surprise that draw the eye exactly where intended.

**Key insights:**
- **Never use pure black or pure white** -- warm variants create a physical quality that pure digital colors lack
- **The functional color hierarchy** -- text-primary, text-secondary (60% opacity), text-tertiary (40% opacity), surface, border (10% opacity) -- creates consistent depth across all components
- **Accent color creates moments of surprise** -- a single strong accent (#ff4d00 or similar) used sparingly has more impact than a complex multi-color palette
- **Contextual color shifts between sections** signal content changes and create visual chapters
- **The squint test** -- squint at your design; if the important elements do not stand out through contrast alone, your color hierarchy is failing
- **Colors must work in both light and dark contexts** -- design the system, not individual instances

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Agency portfolio | Monochromatic with signature accent | Locomotive: cream + black + orange spark |
| Brand identity | Bold owned color combination | Studio Freight: black + cream + rust |
| Client showcase | Contextual shifting per case study | AREA 17: adapts palette to each client |
| Product landing | Dark mode with single vibrant accent | Stripe: dark navy + signature purple |
| Cultural site | Rich tonal palette from source material | Hello Monday: palette drawn from art/content |
| Tech product | Minimal neutral with functional accent | Linear: grayscale + signature blue |

**Copy patterns:**
- Define CSS custom properties for your full color system: `--color-dark`, `--color-light`, `--color-accent`
- Build functional tokens on top: `--color-text-primary`, `--color-text-secondary`, `--color-surface`
- Use opacity-based variants (`rgba(10, 10, 10, 0.6)`) for consistent secondary/tertiary text
- Accent color appears on CTAs, links, and single-detail moments -- never everywhere

**Ethical boundary:** Color choices must meet WCAG 2.1 AA contrast requirements at minimum. Atmospheric design cannot come at the cost of readability for users with visual impairments. Test all color combinations with contrast checkers.

See: [references/case-studies.md](references/case-studies.md) for agency technique breakdowns including color system analysis.

### 5. Scroll-Based Design

**Core concept:** Scroll is the primary interaction on the web, and it should feel designed, not default. The best digital experiences treat the scroll as a narrative device -- controlling pacing, creating reveals, building tension, and delivering signature moments tied to scroll position.

**Why it works:** Default browser scroll is mechanical and uniform, treating all content as equally important. Custom scroll behavior (via Lenis or Locomotive Scroll) creates a smooth, weighted feel that mirrors physical objects. When scroll position drives animations, reveals, and transitions, the user's movement through content becomes an active, participatory experience rather than passive consumption.

**Key insights:**
- **Smooth scroll is the foundation** -- implement Lenis or Locomotive Scroll for the weighted, physical scroll feel that every award-winning site uses
- **Parallax must be purposeful** -- used sparingly and only on non-essential decorative elements; never on text or critical content
- **Pinned sections create storytelling beats** -- locking a section in place while content transforms within it creates cinematic moments
- **Horizontal scroll for galleries** requires clear visual affordance so users know to scroll sideways
- **Scroll-triggered reveals should be progressive** -- elements enter as they become visible, creating a sense of discovery
- **Scroll velocity can modulate animation speed** -- fast scrolling compresses animations, slow scrolling expands them, creating a responsive feel

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Product story | Pinned hero with scroll-driven content transformation | Apple product deep-dives |
| Portfolio | Progressive image reveals tied to scroll position | Locomotive project showcases |
| Editorial | Parallax depth on decorative elements only | AREA 17 editorial layouts |
| Landing page | Horizontal scroll gallery with clear affordance | Studio Freight work galleries |
| Brand narrative | Scroll-driven animation sequences | Active Theory immersive stories |
| Feature tour | Step-by-step reveals pinned to scroll progress | Stripe feature presentations |

**Copy patterns:**
- Use `data-scroll`, `data-scroll-speed`, and `data-scroll-direction` attributes for declarative scroll behavior
- Implement intersection observers for lightweight scroll-triggered class toggling
- Reserve GSAP ScrollTrigger for complex, multi-step scroll-driven animations
- Always provide a non-scroll fallback for accessibility

**Ethical boundary:** Scroll hijacking that prevents users from scrolling at their own pace is hostile UX. Custom scroll should enhance the experience, not trap users. Always allow users to scroll freely through content, and never make scroll-driven animations mandatory for accessing information.

See: [references/animation-patterns.md](references/animation-patterns.md) for scroll animation implementation patterns.

### 6. Performance & Loading

**Core concept:** Performance is not an optimization step -- it is a design constraint from day one. A beautiful animation that drops frames, a stunning font that causes layout shift, or a gorgeous image that takes three seconds to load all fail the craft test. 60fps is the floor, not the ceiling.

**Why it works:** Users perceive performance as quality. A site that loads instantly and scrolls fluidly feels premium, regardless of visual complexity. Conversely, a visually stunning site that stutters or delays feels broken. The best agencies achieve both visual ambition and technical performance by making performance a first-class design decision: choosing GPU-accelerated properties, subsetting fonts, optimizing images, and testing on real devices.

**Key insights:**
- **Fonts must be subset and preloaded** -- only include the glyphs you need, use `font-display: swap` or `optional`, and preload critical font files
- **Images must be optimized** -- use WebP/AVIF with fallbacks, implement responsive `srcset`, and lazy-load below-the-fold images
- **Animations must be GPU-accelerated** -- only animate `transform` and `opacity`; never animate `width`, `height`, `top`, `left`, or `margin`
- **No layout shifts** -- Cumulative Layout Shift (CLS) must be near zero; reserve space for images, fonts, and dynamic content
- **LCP under 2.5s** -- Largest Contentful Paint is the key metric; optimize the critical rendering path for the hero
- **First contentful paint must feel instant** -- use custom skeleton/loading animations as designed elements, not afterthoughts

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Font loading | Subset, preload, and swap strategy | `<link rel="preload" as="font" crossorigin>` |
| Image delivery | AVIF/WebP with responsive srcset | `<picture>` element with format fallbacks |
| Animation perf | GPU-only properties with will-change hints | `transform: translate3d()` + `opacity` |
| Layout stability | Aspect-ratio and min-height reservations | `aspect-ratio: 16/9` on image containers |
| Loading experience | Designed skeleton screens and progress indicators | Custom branded loading animations |
| Bundle optimization | Code-split, tree-shake, defer non-critical JS | Dynamic imports for below-fold interactivity |

**Copy patterns:**
- Audit with Lighthouse, targeting 90+ on all metrics
- Test on real devices, not just simulators -- simulators lie about performance and feel
- Implement `loading="lazy"` on all images below the fold
- Use `will-change` sparingly and only on elements about to animate
- Profile animations with Chrome DevTools Performance panel at 4x CPU throttle

**Ethical boundary:** Performance optimization must not strip away accessibility features, skip semantic HTML, or remove meaningful content. Fast-but-inaccessible is not a valid tradeoff.

See: [references/technical-stack.md](references/technical-stack.md) for libraries, tools, and performance optimization techniques.

### 7. Micro-Interactions

**Core concept:** The details that signal craft live in the 1% that most designers skip: custom cursors, branded selection colors, magnetic button effects, designed focus states, considered loading states, crafted error pages, and correct micro-typography. These details are the difference between professional and world-class.

**Why it works:** Micro-interactions create a sense that every pixel was considered. When a cursor changes on hover, when text selection has a branded color, when a button has a subtle magnetic pull, and when focus states are beautiful AND accessible, users feel the care embedded in the experience. These details compound -- individually subtle, collectively transformative.

**Key insights:**
- **Custom cursor reflects brand personality** -- cursor changes on interactive elements, with optional magnetic effect on buttons
- **Selection colors are branded** -- custom `::selection` color that works well on all backgrounds
- **Every link has a considered hover state** -- images have scale or overlay treatment, cards transform meaningfully
- **Focus states are visible AND beautiful** -- focus indicators match brand aesthetic while remaining clearly visible for keyboard navigation
- **Loading and empty states are designed** -- custom skeleton animations, branded progress indicators, designed 404 pages, helpful error states
- **Micro-typography is correct** -- smart quotes, proper apostrophes, en/em dashes where appropriate, no orphans on headlines, `text-wrap: balance` on key text

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| Cursor | Custom cursor with interactive-element variants | Dogstudio custom cursor system |
| Selection | Branded `::selection` background color | On-brand highlight that works on all surfaces |
| Buttons | Magnetic hover effect with subtle pull | Studio Freight magnetic buttons |
| Focus | Styled focus-visible rings matching brand | Accessible + beautiful focus indicators |
| Loading | Custom skeleton screens and progress bars | Locomotive branded loading sequences |
| Error states | Designed 404 and error pages | Memorable, on-brand error experiences |

**Copy patterns:**
- `::selection { background: var(--color-accent); color: var(--color-light); }`
- `cursor: none;` on body with custom cursor div following mouse position
- Magnetic effect: calculate distance between cursor and button center, apply proportional transform
- Smart quotes: use `&ldquo;` and `&rdquo;` or configure your build tool to auto-convert

**Ethical boundary:** Micro-interactions must enhance usability, not hinder it. Custom cursors must remain functional and visible. Focus states must meet accessibility requirements -- beauty cannot replace visibility. Designed error states must be genuinely helpful, not just clever.

See: [references/case-studies.md](references/case-studies.md) for agency technique breakdowns on micro-interaction implementation.

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

Do not start with the header. Start with the thing that defines the experience. The header can be solved later. Every 10/10 project has at least one moment that makes people stop and share: a hero animation never seen before, typography so bold it becomes the visual, an interaction that delights unexpectedly, a scroll sequence that tells a story, or a transition that feels like magic.

**Questions to identify your signature:**
1. What will people screenshot?
2. What will they describe to colleagues?
3. What will they try to reverse-engineer?
4. What makes this unmistakably THIS project?

### 3. Typography Sets Everything

Choose your display typeface first. Let it dictate the color palette mood, the animation style, the spacing rhythm, and the overall personality.

### 4. Motion Is Not Polish

Prototype animations early. Motion design happens alongside visual design, not after.

### 5. Ship With Restraint

3 things perfect beats 10 things mediocre. Cut ruthlessly.

## Implementation Notes

1. **Start with the signature moment** -- design the thing that defines the experience first
2. **Conceptualize desktop-first, build mobile-first** -- dream big, implement progressively
3. **Prototype animations early** -- motion is not a polish step, it is core to the design
4. **Test on real devices** -- simulators lie about performance and feel
5. **Ship with restraint** -- 3 things perfect beats 10 things mediocre
6. **Sweat the micro-details** -- craft lives in the 1% others skip
7. **Design the states** -- hover, focus, loading, empty, error all matter
8. **Own your constraints** -- every limitation is a design opportunity
9. **Use project conventions** -- if Tailwind 4+ and/or shadcn/ui are available, build on top of them rather than fighting them. Extend their design tokens, customize their components, and use their patterns as a foundation for 10/10 craft

## Reference Files

Consult these for detailed implementation:

- **[references/typography.md](references/typography.md)**: Font pairing strategies, type scale systems, advanced CSS typography
- **[references/animation-patterns.md](references/animation-patterns.md)**: Scroll animations, page transitions, micro-interactions with code
- **[references/layout-systems.md](references/layout-systems.md)**: Grid frameworks, breakpoints, responsive patterns
- **[references/technical-stack.md](references/technical-stack.md)**: Libraries, tools, performance optimization
- **[references/case-studies.md](references/case-studies.md)**: Agency technique breakdowns (Locomotive, Studio Freight, AREA 17, Hello Monday, etc.)

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Using Inter, Roboto, Arial, or system-ui as primary typeface | These are application fonts, not experience fonts -- they signal generic, not premium | Choose from premium foundries (Pangram Pangram, Dinamo, Grilli Type, Klim) or quality Google alternatives (Space Grotesk, Instrument Serif, Fraunces) |
| Uniform type scale (everything within 2x of each other) | No hierarchy means no gasping moments -- everything feels equally unimportant | Push to minimum 10:1 ratio between display and body; viewport-filling type is the goal |
| Using `ease`, `ease-in`, `ease-out`, or `linear` easing | Default easing feels mechanical and lifeless -- instantly signals amateur work | Use custom cubic-bezier curves: expo out (0.16, 1, 0.3, 1), quart out (0.25, 1, 0.5, 1) |
| Animating everything simultaneously | Simultaneous animation creates visual noise with no hierarchy or narrative | Choreograph with stagger (80ms between elements), sequence in order of importance |
| Center-aligning everything | Symmetry is safe but boring -- it creates no tension or visual energy | Use asymmetric compositions with intentional grid offsets and bleeding elements |
| Equal spacing everywhere | Uniform spacing creates monotony -- the eye has nowhere to rest or focus | Vary spacing to create rhythm: dense sections followed by breathing room |
| Pure #000000 black and pure #ffffff white | Pure digital colors feel lifeless and harsh -- they signal no design consideration | Use warm variants: #0a0a0a (slightly warm black), #fafaf9 (slightly warm white) |
| Default browser scroll | Standard scroll feels mechanical and treats all content as equally important | Implement Lenis or Locomotive Scroll for smooth, weighted, physical scroll feel |
| Purple-to-blue gradient hero sections | The "AI gradient" -- instantly signals generic, trend-following design | Develop a signature color approach specific to the project |
| No signature moment in the entire experience | Without a screenshot-worthy moment, the design is competent but forgettable | Design the signature moment FIRST -- the thing people will reverse-engineer |
| Any emoji in professional interfaces | Emoji signal casual/amateur craft and undermine premium positioning | Use custom iconography or typographic treatments instead |
| Parallax on text and critical content | Parallax on readable content causes motion sickness and accessibility issues | Reserve parallax for decorative, non-essential background elements only |
| Animations blocking user interaction | Motion that prevents scrolling, clicking, or reading is hostile UX | Ensure all animations are non-blocking; content remains accessible during transitions |
| Font Awesome icons used unmodified | Generic icon sets signal template-level design | Create custom icons or heavily customize existing ones to match brand personality |
| Default form styles | Unstyled form elements immediately break the illusion of craft | Design every input, select, checkbox, and button as a branded experience |

## Quick Diagnostic

| Question | If No | Action |
|----------|-------|--------|
| Does the hero typography make someone pause mid-scroll? | Display type is not commanding enough | Push scale contrast to 10:1+, choose a more distinctive typeface, fill the viewport |
| Would someone screenshot any section and share it? | No signature moment exists | Identify one section to make extraordinary -- an animation, scale shift, or interaction |
| Does the design still read when you blur your eyes? | Hierarchy is too flat | Increase contrast between levels -- bigger headlines, more white space, stronger accents |
| Are all easing curves custom (no `ease` or `linear`)? | Motion feels default and mechanical | Replace with expo out (0.16, 1, 0.3, 1) or quart out (0.25, 1, 0.5, 1) |
| Is there asymmetric tension in the composition? | Layout feels safe and symmetrical | Offset elements from center, let images bleed, vary section density |
| Do the colors feel invented for THIS project? | Palette could belong to any brand | Develop a signature color identity: monochromatic tension, bold signature, or contextual shifting |
| Is the page load choreographed (not all at once)? | Elements pop in simultaneously | Implement staggered reveal: structure first, then hero, then supporting elements |
| Does scroll feel custom and weighted? | Using default browser scroll | Implement Lenis or Locomotive Scroll for smooth, physical scroll behavior |
| Are micro-details considered (selection, focus, cursor)? | Default browser behaviors remain | Add branded selection colors, designed focus states, and considered cursor behavior |
| Is CLS near zero and LCP under 2.5s? | Performance undermines perceived quality | Subset fonts, optimize images (WebP/AVIF), animate only transform/opacity |
| Does every animation answer "why does this move?" | Motion is decorative, not purposeful | Remove animations that do not serve narrative, hierarchy, or user guidance |
| Are focus states both beautiful AND accessible? | Accessibility sacrificed for aesthetics or vice versa | Design focus indicators that match brand aesthetic while meeting WCAG visibility requirements |

## Further Reading

- [Designing with Type](https://www.amazon.com/Designing-Type-Essential-Typography/dp/0823014134?tag=wondelai00-20) by James Craig -- the foundational text on typographic principles, hierarchy, and the architecture of type in design
- [Grid Systems in Graphic Design](https://www.amazon.com/Grid-Systems-Graphic-Design-Communication/dp/3721201450?tag=wondelai00-20) by Josef Muller-Brockmann -- the definitive work on grid-based composition, proportional systems, and the mathematical foundations of visual layout
- [The Elements of Typographic Style](https://www.amazon.com/Elements-Typographic-Style-Version-4-0/dp/0881792128?tag=wondelai00-20) by Robert Bringhurst -- the typographer's bible covering rhythm, proportion, and the craft of setting type beautifully
- [Interaction of Color](https://www.amazon.com/Interaction-Color-50th-Anniversary-Edition/dp/0300179359?tag=wondelai00-20) by Josef Albers -- essential reading on color perception, contrast, and how colors behave in relation to each other
- [Layout Essentials: 100 Design Principles for Using Grids](https://www.amazon.com/Layout-Essentials-Design-Principles-Using/dp/1592537073?tag=wondelai00-20) by Beth Tondreau -- practical grid-based layout principles applied to real design scenarios
- [Awwwards Annual: The Best 365 Websites Around the World](https://www.awwwards.com/books/) -- yearly collection of the web's most innovative designs, serving as a benchmark for 10/10 craft

## About the Author

This skill synthesizes techniques and principles from the world's most awarded digital design agencies. The primary sources are:

**Locomotive** (Montreal) -- pioneers of smooth scroll experiences (creators of Locomotive Scroll), known for monochromatic tension palettes, bold typography, and seamless page transitions. Their work for clients like Ubisoft and the National Film Board of Canada defines the standard for immersive web storytelling.

**Studio Freight** (New York) -- specialists in creative development, known for magnetic interactions, bold signature color palettes, and pushing the technical boundaries of the browser. Their open-source tools and experimental projects influence the broader creative development community.

**AREA 17** (New York/Paris) -- a digital product agency known for contextual design systems that adapt to each client's identity, editorial-quality layouts, and the balance of visual ambition with functional clarity. Their work for cultural institutions and media organizations sets the bar for content-driven design.

**Active Theory** (Los Angeles) -- a creative studio specializing in WebGL, immersive 3D experiences, and interactive storytelling. Their work demonstrates what is possible when technical ambition meets design vision.

**Hello Monday** (Copenhagen/New York, now part of DEPT) -- known for playful, innovative interactions and page transitions that feel like magic. Their work for brands like Spotify, Adidas, and Google consistently wins top awards.

Additional inspiration drawn from Dogstudio (Belgium), Tonik (Poland), Instrument (Portland), Resn (New Zealand), and the broader community of Awwwards, FWA, CSS Design Awards, and Webby Award winners whose collective work establishes the evolving standard for world-class digital craft.

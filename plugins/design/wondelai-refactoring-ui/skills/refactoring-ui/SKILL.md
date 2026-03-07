---
name: refactoring-ui
description: 'Audit and fix visual hierarchy, spacing, color, and depth in web UIs. Use when the user mentions "my UI looks off", "fix the design", "Tailwind styling", "color palette", or "visual hierarchy". Covers grayscale-first workflow, constrained design scales, shadows, and component styling. For typeface selection, see web-typography. For usability audits, see ux-heuristics.'
license: MIT
metadata:
  author: wondelai
  version: "1.1.1"
---

# Refactoring UI Design System

A practical, opinionated approach to UI design. Apply these principles when generating frontend code, reviewing designs, or advising on visual improvements.

## Core Principle

**Design in grayscale first. Add color last.** This forces proper hierarchy through spacing, contrast, and typography before relying on color as a crutch.

**The foundation:** Great UI isn't about creativity or talent -- it's about systems. Constrained scales for spacing, type, color, and shadows produce consistently professional results. Start with too much white space, then remove. Details come later -- don't obsess over icons, shadows, or micro-interactions until the layout and hierarchy work.

## Scoring

**Goal: 10/10.** When reviewing or creating UI designs or frontend code, rate it 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## The Refactoring UI Framework

Seven principles for building professional interfaces without a designer:

### 1. Visual Hierarchy

**Core concept:** Not everything can be important. Create hierarchy through three levers: size, weight, and color.

**Why it works:** When every element competes for attention, nothing stands out. Deliberate de-emphasis of secondary content makes primary content powerful by contrast.

**Key insights:**
- Combine levers, don't multiply -- primary text = large OR bold OR dark, not all three
- Save "all three" for the single most important element on the page
- Labels are secondary -- form labels, table headers, and metadata labels support the data, not compete with it
- Semantic color does not equal visual weight -- a muted red secondary button often works better than screaming danger for routine actions
- De-emphasize labels by making them smaller, lighter, or uppercase-small

**Product applications:**

| Context | Hierarchy Technique | Example |
|---------|---------------------|---------|
| **Form fields** | De-emphasize labels, emphasize values | Small uppercase label above large value text |
| **Navigation** | Primary nav bold, secondary nav lighter | Active link in dark gray-900, inactive in gray-500 |
| **Cards** | Title large, metadata small and light | Card title 20px bold, date 12px gray-400 |
| **Dashboards** | Key metric large, context small | Revenue "$42,300" large, "vs last month" small |
| **Tables** | De-emphasize headers, emphasize cell data | Headers uppercase small gray, data normal weight |

**Design patterns:**
- Three-level hierarchy table: Size (large/base/small), Weight (bold/medium/normal), Color (dark/medium/light gray)
- Label-value pattern: de-emphasized label above emphasized value
- Button hierarchy: primary (filled), secondary (outlined or muted), tertiary (text only)

**Ethical boundary:** Don't use hierarchy tricks to hide important information like pricing, terms, or cancellation options.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for interaction states and advanced component patterns.

### 2. Spacing & Sizing

**Core concept:** Use a constrained spacing scale, not arbitrary values. Spacing defines relationships -- elements closer together are more related.

**Why it works:** Arbitrary spacing (padding: 13px) creates inconsistency. A fixed scale forces deliberate decisions and produces harmonious layouts. Generous spacing feels premium; dense spacing feels overwhelming.

**Key insights:**
- Use a linear or near-linear scale: 4, 8, 16, 24, 32, 48, 64px
- Start with too much white space, then remove -- you'll almost never remove enough
- Spacing between groups should be larger than spacing within groups
- Text blocks should be constrained to 45-75 characters (`max-w-prose` or ~65ch)
- Forms should max out at 300-500px width
- Full-width is almost never right for content

**Product applications:**

| Context | Spacing Strategy | Example |
|---------|-----------------|---------|
| **Icon + label** | Tight coupling (4px) | Small gap keeps them visually connected |
| **Form fields** | Related elements (8-16px) | Input and its label tightly coupled |
| **Card sections** | Section separation (24px) | Title block, content block, footer block |
| **Page sections** | Major sections (48-64px) | Hero, features, testimonials, footer |
| **Container width** | Constrain to content | `max-w-prose` for text, `max-w-md` for forms |

**CSS patterns:**
- `p-1`(4px) `p-2`(8px) `p-4`(16px) `p-6`(24px) `p-8`(32px) `p-12`(48px) `p-16`(64px)
- `max-w-prose`(65ch) `max-w-md`(28rem) `max-w-lg`(32rem) `max-w-xl`(36rem)
- `gap-2` for related items, `gap-6` for section separation

**Ethical boundary:** Don't use spacing to bury important UI elements like unsubscribe buttons or privacy controls.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for responsive breakpoint strategies.

### 3. Typography

**Core concept:** Use a modular type scale, constrain line heights by context, and limit to two font families maximum.

**Why it works:** A modular scale (e.g., 1.25 ratio) creates natural visual rhythm. Tight line heights on headings and relaxed line heights on body text improve readability across contexts.

**Key insights:**
- Use a modular scale: 12, 14, 16, 20, 24, 30, 36px (1.25 ratio)
- Headings need tight line height (1.0-1.25); body text needs relaxed (1.5-1.75)
- Wider text needs more line height
- Avoid font weights below 400 for body text -- they become unreadable
- Use bold (600-700) for emphasis, not for everything
- Two fonts maximum: one for headings, one for body (or one family with weight variation)

**Product applications:**

| Context | Typography Rule | Example |
|---------|----------------|---------|
| **Hero headline** | 36px, tight line-height (1.1), bold | Large impactful statement |
| **Section title** | 24px, line-height 1.25, semibold | Clear section demarcation |
| **Body text** | 16px, line-height 1.75, normal weight | Comfortable reading |
| **Captions/labels** | 12-14px, line-height 1.5, medium gray | Secondary information |
| **Code/data** | Monospace, 14px, consistent width | Tabular data alignment |

**CSS patterns:**
- `text-xs`(12px) `text-sm`(14px) `text-base`(16px) `text-lg`(18px) `text-xl`(20px)
- `font-normal`(400) `font-medium`(500) `font-semibold`(600) `font-bold`(700)
- `leading-tight`(1.25) `leading-normal`(1.5) `leading-relaxed`(1.75)

**Ethical boundary:** Don't use tiny type sizes to hide terms, conditions, or fees from users.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for text truncation and responsive typography.

### 4. Color

**Core concept:** Build a systematic palette with 5-9 shades per color, add subtle saturation to grays, and design in grayscale first.

**Why it works:** Random colors clash. A systematic palette with predefined shades ensures consistency across the entire interface. HSL adjustments create natural-feeling lighter and darker variants.

**Key insights:**
- Each color needs 5-9 shades from near-white to near-black (50 through 900)
- The darkest shade is not black -- use 900-level dark grays (e.g., `#111827`) instead of pure `#000000`
- Pure grays look lifeless -- add subtle saturation (cool UI: blue tint like `#64748b`; warm UI: yellow/brown tint like `#78716c`)
- HSL adjustments: lighter = higher lightness, lower saturation, shift hue toward 60 degrees; darker = lower lightness, higher saturation, shift hue toward 0/240 degrees
- Body text minimum 4.5:1 contrast ratio; large text (18px+) minimum 3:1
- Use `#374151` (gray-700) on white, not lighter grays for readable text

**Product applications:**

| Context | Color Strategy | Example |
|---------|---------------|---------|
| **Primary palette** | 9 shades (50-900) for main brand color | Blue-500 for buttons, Blue-100 for backgrounds |
| **Gray palette** | Saturated grays matching UI temperature | Cool grays with blue tint for tech products |
| **Semantic colors** | Success, warning, error each with shade range | Green-500 for success, Red-500 for errors |
| **Text colors** | Three levels: dark, medium, light | `text-gray-900`, `text-gray-600`, `text-gray-400` |
| **Accessible contrast** | Test all text/background combos | `#374151` on white = 10.5:1 ratio |

**CSS patterns:**
- `text-gray-900`(dark) `text-gray-600`(medium) `text-gray-400`(light)
- `bg-blue-50` for subtle backgrounds, `bg-blue-500` for primary actions
- `border-gray-200` for subtle borders, `border-gray-300` for stronger

**Ethical boundary:** Don't use color alone to convey information -- always pair with text or icons for accessibility.

See: [references/theming-dark-mode.md](references/theming-dark-mode.md) for dark palette creation and theme implementation.

### 5. Depth & Shadows

**Core concept:** Use a shadow scale to convey elevation. Small shadows for slightly raised elements, large shadows for floating elements.

**Why it works:** Shadows create a sense of physical depth that helps users understand which elements are interactive, which are floating above the surface, and which are part of the background.

**Key insights:**
- Small shadows = raised slightly (buttons, cards); large shadows = floating (modals, dropdowns)
- Shadows have two parts: a tight, dark shadow for crispness plus a larger, softer shadow for atmosphere
- Depth without shadows: lighter top border + darker bottom border, subtle gradient backgrounds, overlapping elements with offset
- Don't overuse shadows -- if everything floats, nothing has depth
- Shadow color should be transparent dark, not opaque gray

**Product applications:**

| Context | Shadow Level | Example |
|---------|-------------|---------|
| **Buttons** | `shadow-sm` (subtle raise) | Slightly elevated above page surface |
| **Cards** | `shadow-md` (clear separation) | Content grouped and lifted from background |
| **Dropdowns** | `shadow-lg` (floating) | Menu clearly floating above content |
| **Modals** | `shadow-xl` (highest elevation) | Overlay clearly detached from page |
| **Flat alternatives** | Border + background shift | Lighter top border, darker bottom border |

**CSS patterns:**
- `shadow-sm`: `0 1px 2px rgba(0,0,0,0.05)`
- `shadow-md`: `0 4px 6px rgba(0,0,0,0.1)`
- `shadow-lg`: `0 10px 15px rgba(0,0,0,0.1)`
- `shadow-xl`: `0 20px 25px rgba(0,0,0,0.15)`

**Ethical boundary:** Don't use excessive shadows or visual emphasis to draw attention to deceptive UI elements (dark patterns).

See: [references/advanced-patterns.md](references/advanced-patterns.md) for interaction states and elevation hierarchy.

### 6. Images & Icons

**Core concept:** Treat images as design elements, not afterthoughts. Size icons deliberately and use overlays to ensure text readability on images.

**Why it works:** Poorly sized icons look awkward. Unstyled images break visual consistency. Deliberate image treatment (overlays, object-fit, border radius) makes interfaces feel polished.

**Key insights:**
- Icons should be sized relative to their context -- don't use the same size everywhere
- Use icon sets with consistent stroke width and style
- Images need treatment: object-fit cover, consistent aspect ratios, overlays for text
- Don't stretch or distort images -- use `object-fit: cover` and crop deliberately
- Empty states are an opportunity -- use illustrations, not just text

**Product applications:**

| Context | Image/Icon Technique | Example |
|---------|---------------------|---------|
| **Hero images** | Overlay with semi-transparent gradient | Text readable over any photo |
| **Avatars** | Consistent size, rounded, fallback initials | 40px circle with object-fit cover |
| **Feature icons** | Consistent size, weight, and color | 24px stroke icons in gray-500 |
| **Empty states** | Custom illustration + clear CTA | Friendly illustration with "Get started" button |
| **Thumbnails** | Fixed aspect ratio with object-fit cover | 16:9 cards with no distortion |

**CSS patterns:**
- `object-fit: cover` with fixed `aspect-ratio` for consistent image display
- Icon sizing: `w-4 h-4` inline, `w-6 h-6` in navigation, `w-8 h-8` for feature icons
- Image overlay: `bg-gradient-to-t from-black/60 to-transparent` for text on images

**Ethical boundary:** Don't use misleading images or icons that misrepresent functionality or product capabilities.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for image treatment, icon usage, and empty states.

### 7. Layout & Composition

**Core concept:** Don't center everything. Use alignment, overlap, and emphasis variation to create engaging compositions.

**Why it works:** Left-aligned text is easier to read. Varied layouts keep users engaged. Breaking out of rigid boxes makes designs feel dynamic and intentional.

**Key insights:**
- Left-align text by default; center only short headlines, hero sections, single-action CTAs, and empty states
- Cards don't need to contain everything -- let images bleed to edges, overlap containers, or extend beyond bounds
- In lists and feeds, vary the visual treatment -- feature some items, minimize others
- Use alignment to create visual relationships between unrelated elements
- Alternate emphasis: not every card in a list needs the same layout

**Product applications:**

| Context | Layout Strategy | Example |
|---------|----------------|---------|
| **Hero sections** | Centered text, generous spacing | Short headline + subtext + single CTA |
| **Feature grids** | Left-aligned text, consistent card sizes | 3-column grid with icon + title + description |
| **Blog feeds** | Varied card sizes for emphasis | First post large, next posts in 2-column grid |
| **Sidebars** | Narrower than main content, lighter background | Navigation or filters at 240-320px width |
| **Content pages** | Constrained width, left-aligned | `max-w-prose` centered container with left text |

**CSS patterns:**
- `text-left` by default, `text-center` only for heroes and short headlines
- `grid grid-cols-3 gap-6` for feature grids
- `max-w-4xl mx-auto` for page containers
- `overflow-hidden` on cards with `object-fit: cover` images that bleed to edges

**Ethical boundary:** Don't use layout tricks to hide or obscure important user choices like opt-outs or data permissions.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for responsive breakpoints and complex layout patterns.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **"Looks amateur"** | Insufficient white space, unconstrained widths | Add more white space, constrain content widths |
| **"Feels flat"** | No depth differentiation between elements | Add subtle shadows, border-bottom on sections |
| **"Text is hard to read"** | Poor line-height, too wide, low contrast | Increase line-height, constrain width, boost contrast |
| **"Everything looks the same"** | No visual hierarchy between elements | Vary size/weight/color between primary and secondary |
| **"Feels cluttered"** | Equal spacing everywhere, no grouping | Group related items, increase spacing between groups |
| **"Colors clash"** | Random color choices without a system | Reduce saturation, use more grays, limit palette to system |
| **"Buttons don't pop"** | Low contrast with surrounding elements | Increase contrast with surroundings, add shadow |
| **Using arbitrary values** | px values like 13, 17, 23 create inconsistency | Stick to the spacing and type scales |

## Quick Diagnostic

Audit any UI design:

| Question | If No | Action |
|----------|-------|--------|
| Does hierarchy read when squinting (blur test)? | Elements competing for attention | Increase contrast between primary and secondary |
| Does it work in grayscale? | Relying on color for hierarchy | Strengthen size/weight/spacing hierarchy |
| Is there enough white space? | Probably not -- most designs are too dense | Increase spacing, especially between groups |
| Are labels de-emphasized vs. their values? | Labels competing with data | Make labels smaller, lighter, or uppercase-small |
| Does spacing follow a consistent scale? | Arbitrary spacing creates visual noise | Use 4/8/16/24/32/48/64 scale only |
| Is text width constrained for readability? | Long lines cause reader fatigue | Apply `max-w-prose` (~65ch) to text blocks |
| Do colors have sufficient contrast? | Accessibility failure, hard to read | Test with WCAG contrast checker, use gray-700+ on white |
| Are shadows appropriate for elevation? | Elements floating at wrong visual level | Match shadow scale to element purpose |

## Reference Files

- [advanced-patterns.md](references/advanced-patterns.md): Empty states, form design, image treatment, icon sizing, interaction states, color psychology, border radius systems, text truncation, responsive breakpoints
- [animation-microinteractions.md](references/animation-microinteractions.md): When to animate, easing functions, durations, loading states, animation performance
- [accessibility-depth.md](references/accessibility-depth.md): WCAG 2.1 AA checklist, focus management, screen reader support, keyboard navigation
- [data-visualization.md](references/data-visualization.md): Chart selection, color in charts, table design, dashboard layouts
- [theming-dark-mode.md](references/theming-dark-mode.md): Dark palette creation, elevation in dark mode, theme implementation strategies

## Further Reading

This skill is based on Adam Wathan and Steve Schoger's practical design guide. For the complete system with visual examples:

- [*"Refactoring UI"*](https://www.amazon.com/Refactoring-UI-Adam-Wathan/dp/B0BLJ7MC21?tag=wondelai00-20) by Adam Wathan & Steve Schoger (the full book with hundreds of visual before/after examples)
- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman (foundational design thinking and usability)
- [*"Don't Make Me Think"*](https://www.amazon.com/Dont-Make-Think-Revisited-Usability/dp/0321965515?tag=wondelai00-20) by Steve Krug (web usability principles that complement Refactoring UI)
- [Refactoring UI](https://www.refactoringui.com/) -- Official site with resources and examples

## About the Authors

**Adam Wathan** is a full-stack developer and the creator of Tailwind CSS, one of the most popular utility-first CSS frameworks. **Steve Schoger** is a visual designer known for his practical design tips and illustrations. Together they created *Refactoring UI* to teach developers how to design better interfaces using systematic, repeatable techniques rather than relying on innate artistic talent. Their approach emphasizes constrained design systems -- fixed scales for spacing, typography, color, and shadows -- that produce professional results without requiring a design background.

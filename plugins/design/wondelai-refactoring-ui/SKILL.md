---
name: refactoring-ui
description: 'Audit and fix visual hierarchy, spacing, color, and depth in web UIs. Use when the user mentions "my UI looks off", "make it look better", "this looks amateur", "looks unprofessional", "fix the design", "Tailwind styling", "color palette", "visual hierarchy", "design system", "spacing scale", or "component styling". Also trigger when building consistent design tokens, creating dark mode themes, improving data-visualization clarity, or polishing UI details before launch. Covers grayscale-first workflow, constrained design scales, shadows, and component styling. For typeface selection, see web-typography. For usability audits, see ux-heuristics.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.0"
---

# Refactoring UI Design System

A practical, opinionated approach to UI design. Apply these principles when generating frontend code, reviewing designs, or advising on visual improvements.

## Core Principle

**Design in grayscale first. Add color last.** This forces proper hierarchy through spacing, contrast, and typography before relying on color as a crutch.

**The foundation:** Great UI isn't about talent — it's about systems. Constrained scales for spacing, type, color, and shadows produce consistently professional results. Start with too much white space and remove; leave details (icons, shadows, micro-interactions) until layout and hierarchy work.

## Scoring

**Goal: 10/10.** When reviewing or creating UI designs or frontend code, rate 0-10 against the principles below — 10/10 means full alignment, lower scores indicate gaps. Always give the current score and the specific improvements needed to reach 10/10.

## The Refactoring UI Framework

Seven principles for building professional interfaces without a designer:

### 1. Visual Hierarchy

**Core concept:** Not everything can be important. Create hierarchy through three levers: size, weight, and color.

**Why it works:** When every element competes for attention, nothing stands out; deliberately de-emphasizing secondary content makes primary content powerful by contrast.

**Key insights:**
- Combine levers, don't multiply — primary text = large OR bold OR dark, not all three; save "all three" for the single most important element
- Labels are secondary — form labels, table headers, and metadata support the data, not compete with it; make them smaller, lighter, or uppercase-small
- Semantic color ≠ visual weight — a muted secondary button often beats screaming red for routine destructive actions

**Product applications:**

| Context | Hierarchy Technique | Example |
|---------|---------------------|---------|
| **Form fields** | De-emphasize labels, emphasize values | Small uppercase label above large value |
| **Dashboards** | Key metric large, context small | "$42,300" large, "vs last month" small |
| **Tables** | De-emphasize headers, emphasize data | Headers uppercase small gray, data normal |

**Design patterns:**
- Three-level hierarchy: Size (large/base/small), Weight (bold/medium/normal), Color (dark/medium/light gray)
- Button hierarchy: primary (filled), secondary (outlined or muted), tertiary (text only)

**Ethical boundary:** Don't use hierarchy tricks to hide important information like pricing, terms, or cancellation options.

See: [references/advanced-patterns.md](references/advanced-patterns.md) for interaction states, form design, empty states, and responsive patterns.

### 2. Spacing & Sizing

**Core concept:** Use a constrained spacing scale, not arbitrary values. Spacing defines relationships — closer elements read as more related.

**Why it works:** Arbitrary spacing (padding: 13px) creates inconsistency; a fixed scale forces deliberate decisions and harmonious layouts. Generous spacing feels premium; dense feels overwhelming.

**Key insights:**
- Use the scale: 4, 8, 16, 24, 32, 48, 64px
- Start with too much white space, then remove — you'll almost never remove enough
- Spacing between groups must exceed spacing within groups
- Constrain widths: text to 45-75 characters (`max-w-prose`), forms to 300-500px; full-width is almost never right

**Product applications:**

| Context | Spacing Strategy | Example |
|---------|-----------------|---------|
| **Icon + label** | Tight coupling (4px) | Small gap keeps them connected |
| **Card sections** | Section separation (24px) | Title, content, footer blocks |
| **Page sections** | Major sections (48-64px) | Hero, features, testimonials |

**CSS patterns:**
- `p-1`(4px) `p-2`(8px) `p-4`(16px) `p-6`(24px) `p-8`(32px) `p-12`(48px) `p-16`(64px)
- `max-w-prose`(65ch) `max-w-md`(28rem) `max-w-lg`(32rem) `max-w-xl`(36rem)
- `gap-2` for related items, `gap-6` for section separation

**Ethical boundary:** Don't use spacing to bury important UI elements like unsubscribe buttons or privacy controls.

### 3. Typography

**Core concept:** Use a modular type scale, constrain line heights by context, and limit to two font families maximum.

**Why it works:** A modular scale (e.g., 1.25 ratio) creates natural visual rhythm; tight line heights on headings and relaxed on body text improve readability in each context.

**Key insights:**
- Scale: 12, 14, 16, 20, 24, 30, 36px (1.25 ratio)
- Headings: tight line height (1.0-1.25); body: relaxed (1.5-1.75); wider text needs more line height
- Avoid weights below 400 for body text; use bold (600-700) for emphasis, not everything
- Two fonts max: one for headings, one for body (or one family with weight variation)

**Product applications:**

| Context | Typography Rule | Example |
|---------|----------------|---------|
| **Hero headline** | 36px, line-height 1.1, bold | Large impactful statement |
| **Body text** | 16px, line-height 1.75, normal | Comfortable reading |
| **Captions/labels** | 12-14px, line-height 1.5, medium gray | Secondary information |

**CSS patterns:**
- `text-xs`(12px) `text-sm`(14px) `text-base`(16px) `text-lg`(18px) `text-xl`(20px)
- `font-normal`(400) `font-medium`(500) `font-semibold`(600) `font-bold`(700)
- `leading-tight`(1.25) `leading-normal`(1.5) `leading-relaxed`(1.75)

**Ethical boundary:** Don't use tiny type sizes to hide terms, conditions, or fees from users.

### 4. Color

**Core concept:** Build a systematic palette with 5-9 shades per color, add subtle saturation to grays, and design in grayscale first.

**Why it works:** Random colors clash; a predefined shade system ensures consistency, and HSL adjustments create natural-feeling lighter and darker variants.

**Key insights:**
- Each color needs 5-9 shades from near-white to near-black (50-900); darkest is not pure black — use `#111827`, not `#000000`
- Pure grays look lifeless — tint them (cool UI: blue like `#64748b`; warm UI: yellow/brown like `#78716c`)
- HSL: lighter = raise lightness, lower saturation, hue toward 60°; darker = the reverse, hue toward 0°/240°
- Contrast minimums: 4.5:1 body text, 3:1 large text (18px+); use `#374151` (gray-700) on white, not lighter grays

**Product applications:**

| Context | Color Strategy | Example |
|---------|---------------|---------|
| **Primary palette** | 9 shades (50-900) of brand color | Blue-500 buttons, Blue-100 backgrounds |
| **Semantic colors** | Success/warning/error with shade ranges | Green-500 success, Red-500 errors |
| **Text colors** | Three levels: dark, medium, light | `text-gray-900`, `text-gray-600`, `text-gray-400` |

**CSS patterns:**
- `text-gray-900`(dark) `text-gray-600`(medium) `text-gray-400`(light)
- `bg-blue-50` for subtle backgrounds, `bg-blue-500` for primary actions
- `border-gray-200` for subtle borders, `border-gray-300` for stronger

**Ethical boundary:** Don't use color alone to convey information — always pair with text or icons for accessibility.

See: [references/theming-dark-mode.md](references/theming-dark-mode.md) for dark palette creation and theme implementation.

### 5. Depth & Shadows

**Core concept:** Use a shadow scale to convey elevation — small shadows for slightly raised elements, large shadows for floating ones.

**Why it works:** Shadows create physical depth that tells users which elements are interactive, floating, or background.

**Key insights:**
- Small shadows = raised slightly (buttons, cards); large = floating (modals, dropdowns)
- Good shadows have two parts: a tight dark shadow for crispness plus a larger soft one for atmosphere
- Depth without shadows: lighter top border + darker bottom border, subtle gradients, overlapping elements
- Don't overuse — if everything floats, nothing has depth; shadow color is transparent dark, never opaque gray

**Product applications:**

| Context | Shadow Level | Example |
|---------|-------------|---------|
| **Buttons** | `shadow-sm` (subtle raise) | Slightly elevated above surface |
| **Dropdowns** | `shadow-lg` (floating) | Menu clearly above content |
| **Modals** | `shadow-xl` (highest) | Overlay detached from page |

**CSS patterns:**
- `shadow-sm`: `0 1px 2px rgba(0,0,0,0.05)`
- `shadow-md`: `0 4px 6px rgba(0,0,0,0.1)`
- `shadow-lg`: `0 10px 15px rgba(0,0,0,0.1)`
- `shadow-xl`: `0 20px 25px rgba(0,0,0,0.15)`

**Ethical boundary:** Don't use excessive shadows or visual emphasis to draw attention to deceptive UI elements (dark patterns).

### 6. Images & Icons

**Core concept:** Treat images as design elements, not afterthoughts. Size icons deliberately and use overlays to keep text readable on images.

**Why it works:** Poorly sized icons look awkward and unstyled images break consistency; deliberate treatment (overlays, object-fit, radius) makes interfaces feel polished.

**Key insights:**
- Size icons relative to context; use sets with consistent stroke width and style
- Never stretch or distort — use `object-fit: cover` with fixed aspect ratios and crop deliberately
- Text over images needs an overlay (semi-transparent gradient)
- Empty states are an opportunity — use illustrations plus a clear CTA, not just text

**Product applications:**

| Context | Image/Icon Technique | Example |
|---------|---------------------|---------|
| **Hero images** | Semi-transparent gradient overlay | Text readable over any photo |
| **Avatars** | Consistent size, rounded, fallback initials | 40px circle, object-fit cover |
| **Empty states** | Custom illustration + CTA | Friendly illustration with "Get started" |

**CSS patterns:**
- `object-fit: cover` with fixed `aspect-ratio` for consistent display
- Icon sizing: `w-4 h-4` inline, `w-6 h-6` navigation, `w-8 h-8` feature icons
- Overlay: `bg-gradient-to-t from-black/60 to-transparent` for text on images

**Ethical boundary:** Don't use misleading images or icons that misrepresent functionality or product capabilities.

### 7. Layout & Composition

**Core concept:** Don't center everything. Use alignment, overlap, and emphasis variation to create engaging compositions.

**Why it works:** Left-aligned text is easier to read, and varied layouts that break out of rigid boxes feel dynamic and intentional.

**Key insights:**
- Left-align by default; center only short headlines, heroes, single-action CTAs, and empty states
- Cards don't need to contain everything — let images bleed to edges or overlap containers
- Vary visual treatment in lists and feeds — feature some items, minimize others
- Use alignment to create relationships between unrelated elements

**Product applications:**

| Context | Layout Strategy | Example |
|---------|----------------|---------|
| **Hero sections** | Centered text, generous spacing | Short headline + subtext + single CTA |
| **Blog feeds** | Varied card sizes for emphasis | First post large, rest in 2-column grid |
| **Content pages** | Constrained width, left-aligned | `max-w-prose` container with left text |

**CSS patterns:**
- `text-left` by default, `text-center` only for heroes and short headlines
- `grid grid-cols-3 gap-6` for feature grids; `max-w-4xl mx-auto` for page containers
- `overflow-hidden` on cards with `object-fit: cover` images that bleed to edges

**Ethical boundary:** Don't use layout tricks to hide or obscure important user choices like opt-outs or data permissions.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **"Looks amateur"** | Insufficient white space, unconstrained widths | More white space, constrain content widths |
| **"Feels flat"** | No depth differentiation | Subtle shadows, border-bottom on sections |
| **"Text is hard to read"** | Poor line-height, too wide, low contrast | Increase line-height, constrain width, boost contrast |
| **"Everything looks the same"** | No visual hierarchy | Vary size/weight/color between primary and secondary |
| **"Feels cluttered"** | Equal spacing everywhere | Group related items, larger gaps between groups |
| **"Colors clash"** | Random choices, no system | Reduce saturation, more grays, limit to palette |
| **"Buttons don't pop"** | Low contrast with surroundings | Increase contrast, add shadow |
| **Arbitrary values** | px values like 13, 17, 23 breed inconsistency | Stick to the spacing and type scales |

## Quick Diagnostic

Audit any UI design:

| Question | If No | Action |
|----------|-------|--------|
| Does hierarchy read when squinting (blur test)? | Elements competing | Increase primary/secondary contrast |
| Does it work in grayscale? | Color is a crutch | Strengthen size/weight/spacing hierarchy |
| Is there enough white space? | Probably not — most designs are too dense | Increase spacing, especially between groups |
| Are labels de-emphasized vs. values? | Labels competing with data | Smaller, lighter, or uppercase-small labels |
| Does spacing follow a consistent scale? | Arbitrary spacing = visual noise | Use 4/8/16/24/32/48/64 only |
| Is text width constrained? | Long lines fatigue readers | Apply `max-w-prose` (~65ch) |
| Do colors have sufficient contrast? | Accessibility failure | WCAG-check; use gray-700+ on white |
| Are shadows appropriate for elevation? | Elements float at wrong level | Match shadow scale to element purpose |

## Reference Files

- [advanced-patterns.md](references/advanced-patterns.md): Empty states, form design, image treatment, icon sizing, interaction states, color psychology, border radius systems, text truncation, responsive breakpoints
- [animation-microinteractions.md](references/animation-microinteractions.md): When to animate, easing functions, durations, loading states, animation performance
- [accessibility-depth.md](references/accessibility-depth.md): WCAG 2.1 AA checklist, focus management, screen reader support, keyboard navigation
- [data-visualization.md](references/data-visualization.md): Chart selection, color in charts, table design, dashboard layouts
- [theming-dark-mode.md](references/theming-dark-mode.md): Dark palette creation, elevation in dark mode, theme implementation strategies

## Further Reading

For the complete system with visual before/after examples:

- [*"Refactoring UI"*](https://www.amazon.com/Refactoring-UI-Adam-Wathan/dp/B0BLJ7MC21?tag=wondelai00-20) by Adam Wathan & Steve Schoger (the full book with hundreds of visual examples)
- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman (foundational design thinking and usability)
- [*"Don't Make Me Think"*](https://www.amazon.com/Dont-Make-Think-Revisited-Usability/dp/0321965515?tag=wondelai00-20) by Steve Krug (web usability principles that complement Refactoring UI)
- [Refactoring UI](https://www.refactoringui.com/) — Official site with resources and examples

## About the Authors

**Adam Wathan**, creator of Tailwind CSS, and **Steve Schoger**, the visual designer behind its design language, wrote *Refactoring UI* to teach developers systematic, repeatable design techniques. Their approach replaces artistic talent with constrained systems — fixed scales for spacing, typography, color, and shadows — that produce professional results.

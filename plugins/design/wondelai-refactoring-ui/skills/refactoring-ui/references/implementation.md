# Refactoring UI - Implementation Guide

Step-by-step methodology for auditing and improving visual hierarchy, spacing, color, and depth using Adam Wathan and Steve Schoger's practical approach.

## The Core Workflow: Grayscale First

Design in grayscale until the layout and hierarchy are correct. Add color last. This forces you to solve visual hierarchy through spacing, contrast, and typography before using color as a shortcut.

**Workflow order:**
1. Layout and spacing (whitespace, structure)
2. Typography (size, weight, color of text)
3. Visual hierarchy (what draws the eye first, second, third)
4. Color (accent and brand colors)
5. Depth (shadows, borders, backgrounds)
6. Polish (icons, illustrations, micro-interactions)

## Step 1: Establish Spacing Scale

Do not use arbitrary spacing values. Use a constrained scale derived from a base unit.

**Recommended spacing scale (base 4):**
- 4, 8, 12, 16, 24, 32, 48, 64, 96, 128

Apply this scale everywhere: margins, padding, gaps, line heights.

**Whitespace principles:**
- Start with too much whitespace, then reduce
- Increase spacing between groups, decrease within groups
- Sections need more space than components; components need more than elements

**Common spacing mistakes:**
- Cramming content together to reduce scroll → harder to read, not better
- Using the same spacing between all elements → no visual grouping
- Small buttons with too little padding → hard to tap, looks cheap

## Step 2: Establish Type Scale

**2a. Choose a limited type scale**
- Use 5-7 sizes maximum (not 12 different font sizes)
- Example scale (in px or rem): 12, 14, 16, 20, 24, 32, 48
- Map each size to a semantic role: caption, body, subheading, heading, display

**2b. Limit font weights**
- Use 2-3 weights: regular, medium/semibold, bold
- Do not use light (300) for body text — poor readability at small sizes
- Reserve bold for CTAs and primary headings

**2c. Line height by use case**
- Short labels and headings: tight line height (1.2–1.3)
- Body text: comfortable line height (1.5–1.6)
- Small text: slightly generous line height (1.6–1.7)

## Step 3: Establish a Color Palette

**3a. The 5-shade neutral palette (essential)**
For backgrounds, cards, and borders, create a 5-shade palette:
- Lightest: page background
- Light: card/surface background
- Medium: borders, dividers
- Dark: secondary text, icons
- Darkest: primary text

Never use pure black (`#000000`) for text — use near-black (`#1a1a2e` or similar) for softer, more readable contrast.

**3b. The 9-shade accent palette**
For your brand/primary color, generate 9 shades (100-900):
- 100-300: light tints for backgrounds, hover states
- 400-500: medium shades for icons, accents
- 600-700: primary action color (buttons, links)
- 800-900: dark shades for pressed states, high-contrast contexts

Use a tool (Tailwind's color palette, Coolors, or HSL adjustments) to generate consistent shades.

**3c. Semantic color roles**
- Primary: brand color (one main accent)
- Success: green (confirmation, completion)
- Warning: amber/yellow (caution, degraded state)
- Danger: red (errors, destructive actions)
- Info: blue (neutral information)

Each semantic role needs all 5-9 shades (background, border, text).

## Step 4: Build Visual Hierarchy

Visual hierarchy controls where the eye goes first, second, and third on a page.

**4a. The 3-level hierarchy**
Every screen should have a clear primary, secondary, and tertiary level:
- Primary (1): what the user needs to see first (headline, key metric, primary CTA)
- Secondary (2): supporting information (subheading, description)
- Tertiary (3): fine print (timestamps, metadata, helper text)

**4b. Hierarchy through size and weight**
- Primary: largest and/or heaviest weight
- Secondary: medium size and weight
- Tertiary: smallest size and/or lightest color (use `.text-gray-400` not smaller fonts)

**4c. Don't use font size alone**
- Achieving hierarchy only through size creates oversized headings
- Use color contrast as a hierarchy tool: primary text at high contrast, secondary at medium, tertiary at low
- Bold and regular weight create hierarchy without requiring size differences

## Step 5: Design Cards and Surfaces

**5a. Card hierarchy**
Not all cards are equal. Create 3 levels:
- Compact: minimal padding (12px), single-use data display
- Standard: comfortable padding (20-24px), most cards
- Featured: generous padding (32-48px), hero or promotional cards

**5b. Border vs. shadow for card separation**
- Light interfaces: subtle shadow (`box-shadow: 0 1px 3px rgba(0,0,0,0.12)`) works well
- Dark interfaces: inner border (`border: 1px solid rgba(255,255,255,0.1)`) works better than shadows
- Flat design: background color difference (one shade lighter/darker than page) replaces both

**5c. Don't over-decorate**
- Every border, shadow, or background color is visual noise
- Ask: "Does this card need a border AND a shadow AND a background?" (usually no)
- One technique per card: choose shadow OR border OR background difference

## Step 6: Interaction and State Design

**6a. Every interactive element needs 4 states**
Design all four states before shipping:
1. Default (normal)
2. Hover (cursor over, no click)
3. Active/pressed (during click/tap)
4. Disabled (not currently interactive)

A common mistake: designing only the default state and hoping the rest works out.

**6b. Focus states are non-negotiable**
- Every focusable element must have a visible focus ring
- Default browser focus rings are ugly but functional — custom focus styles are encouraged
- Do not remove focus outlines without replacing them (accessibility failure)
- Design a custom focus style: `outline: 2px solid [primary-color]; outline-offset: 2px`

**6c. Loading states**
Decide per component whether to use:
- Spinner: short, indeterminate waits (< 3s)
- Progress bar: known-duration operations
- Skeleton screen: content-heavy loading (lists, cards)
- Disabled state: button/form while submitting

## Step 7: Image and Icon Usage

**7a. Icon sizes and weights**
- Navigation/toolbar: 20-24px
- Inline with text: match the cap height of surrounding text
- Large standalone: 48-64px
- Always pair icons with labels unless space is genuinely constrained

**7b. Image constraints**
- Never stretch images — always use `object-fit: cover` with a fixed aspect ratio container
- Provide consistent aspect ratios per image type (avatars: 1:1, card images: 16:9 or 4:3)
- Add a placeholder/skeleton for images before they load

**7c. Avatar design**
- Circular for people, rounded-square (8-12px radius) for entities/companies
- Always implement fallback initials + background color for missing avatars
- Generate avatar background color from username hash for consistency

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Using too many font sizes | Visual chaos, no clear hierarchy | Limit to 5-7 sizes maximum |
| Arbitrary spacing values | Inconsistent rhythm | Implement 4pt spacing scale |
| Pure black text on white | Harsh, strains the eyes | Use near-black (e.g., `#111827`) |
| Designing only the default state | Broken hover/focus/disabled states in production | Design all 4 states before coding |
| Too much visual decoration | Cards feel heavy and dated | One technique per surface: shadow OR border OR background |

## Quick-Start Checklist

- [ ] Spacing scale defined (4pt base, 8 values)
- [ ] Type scale defined (5-7 sizes, 2-3 weights)
- [ ] Color palette defined: 5-shade neutral + 9-shade primary
- [ ] Semantic color roles defined (success, warning, danger, info)
- [ ] Visual hierarchy established: 3 levels (size + weight + color)
- [ ] Card/surface design: one technique chosen per level
- [ ] All interactive elements have 4 states designed
- [ ] Focus states implemented and visible
- [ ] All images use fixed aspect ratios with `object-fit: cover`
- [ ] Grayscale version reviewed before adding color

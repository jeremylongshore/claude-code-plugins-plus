# Responsive Typography

Adapting type to screens, viewports, and reading contexts.

## Core Principle

**Typography must respond to context.** A phone held at arm's length, a desktop monitor at desk distance, and a tablet on a couch all demand different typographic treatment.

## The Problem with Fixed Sizes

Fixed pixel sizes create problems:

```css
/* This doesn't adapt */
h1 { font-size: 48px; }
p { font-size: 16px; }
```

- 48px headline overwhelms a 320px phone screen
- 16px might be too small for users who hold phones far away
- No relationship between text and available space

## Fluid Typography with clamp()

The modern solution: `clamp()` creates type that scales smoothly between minimum and maximum values.

```css
/* Syntax: clamp(minimum, preferred, maximum) */
font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
```

### How clamp() Works

| Part | Purpose | Example |
|------|---------|---------|
| Minimum | Floor - never smaller | 1rem (16px) |
| Preferred | Scales with viewport | 0.9rem + 0.5vw |
| Maximum | Ceiling - never larger | 1.25rem (20px) |

The preferred value uses viewport units (vw) to scale, but clamp() prevents extremes.

### Body Text Formula

```css
/* Scales from 16px to 20px between 320px and 1200px viewports */
body {
  font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
}
```

Breakdown:
- At 320px viewport: ~16px
- At 768px viewport: ~18px
- At 1200px+ viewport: 20px (capped)

### Heading Formulas

```css
h1 {
  /* Scales from 32px to 56px */
  font-size: clamp(2rem, 1.5rem + 2vw, 3.5rem);
}

h2 {
  /* Scales from 24px to 40px */
  font-size: clamp(1.5rem, 1.25rem + 1.25vw, 2.5rem);
}

h3 {
  /* Scales from 20px to 28px */
  font-size: clamp(1.25rem, 1.1rem + 0.75vw, 1.75rem);
}
```

### Generating clamp() Values

**Formula for calculating:**
```
preferred = minimum + (maximum - minimum) * ((100vw - minViewport) / (maxViewport - minViewport))
```

**Simplified approach:**
1. Pick min size at min viewport (e.g., 16px at 320px)
2. Pick max size at max viewport (e.g., 20px at 1200px)
3. Use a clamp generator or calculate the vw coefficient

**Tools:**
- [Utopia.fyi](https://utopia.fyi/type/calculator/) - Type scale generator
- [clamp() Calculator](https://min-max-calculator.9elements.com/) - Interactive calculator

## Complete Fluid Type System

```css
:root {
  /* Base scale using clamp() */
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --text-lg: clamp(1.125rem, 1rem + 0.6vw, 1.375rem);
  --text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.625rem);
  --text-2xl: clamp(1.5rem, 1.25rem + 1.25vw, 2.25rem);
  --text-3xl: clamp(2rem, 1.5rem + 2vw, 3rem);
  --text-4xl: clamp(2.5rem, 1.75rem + 3vw, 4rem);
}

body { font-size: var(--text-base); }
h1 { font-size: var(--text-4xl); }
h2 { font-size: var(--text-3xl); }
h3 { font-size: var(--text-2xl); }
h4 { font-size: var(--text-xl); }
.small { font-size: var(--text-sm); }
.caption { font-size: var(--text-xs); }
```

## Responsive Line Length

Line length must also adapt. 65 characters is ideal, but the method matters.

### Using ch Units

```css
.prose {
  max-width: 65ch;  /* Approximately 65 characters */
}
```

**Note:** `ch` is based on the "0" character width. Actual character count varies by typeface.

### Responsive Constraints

```css
.content {
  /* Fluid padding keeps text away from edges */
  padding-inline: clamp(1rem, 5vw, 3rem);

  /* Max-width prevents too-wide lines */
  max-width: min(65ch, 100% - 2rem);

  margin-inline: auto;
}
```

## Responsive Line Height

Wider lines need more line height. Adjust at breakpoints or fluidly:

```css
/* Breakpoint approach */
p {
  line-height: 1.5;
}

@media (min-width: 768px) {
  p {
    line-height: 1.6;
  }
}

@media (min-width: 1200px) {
  p {
    line-height: 1.7;
  }
}
```

```css
/* Fluid approach - ties line-height to container width */
.prose {
  /* Wider = more line height */
  line-height: calc(1.5 + 0.2 * (100vw - 320px) / (1200 - 320));
}
```

## Breakpoint Strategy

### Mobile First (Recommended)

Start with mobile styles, add complexity for larger screens:

```css
/* Mobile: base styles */
body {
  font-size: 1rem;
  line-height: 1.5;
}

h1 {
  font-size: 2rem;
  line-height: 1.2;
}

/* Tablet */
@media (min-width: 640px) {
  body {
    font-size: 1.0625rem;  /* 17px */
  }

  h1 {
    font-size: 2.5rem;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  body {
    font-size: 1.125rem;  /* 18px */
    line-height: 1.6;
  }

  h1 {
    font-size: 3rem;
  }
}

/* Large desktop */
@media (min-width: 1440px) {
  body {
    font-size: 1.25rem;  /* 20px */
    line-height: 1.7;
  }
}
```

### Key Breakpoints

| Breakpoint | Typical Adjustments |
|------------|---------------------|
| 640px | Increase body text slightly; relax line length |
| 768px | Tablet optimizations; two-column layouts possible |
| 1024px | Desktop sizes; full hierarchy |
| 1440px | Large screens; may need max-width constraints |

## Container Queries (Modern Approach)

For component-based systems, container queries let type respond to component size, not viewport:

```css
.card {
  container-type: inline-size;
}

.card-title {
  font-size: 1.25rem;
}

@container (min-width: 400px) {
  .card-title {
    font-size: 1.5rem;
  }
}
```

**Use case:** Same card component renders differently in a sidebar vs. main content area.

## Reading Distance Considerations

Different devices = different reading distances:

| Device | Typical Distance | Implication |
|--------|------------------|-------------|
| Phone | 10-12 inches | Can use slightly smaller text |
| Tablet | 15-18 inches | Similar to desktop |
| Desktop | 18-24 inches | Standard sizing works |
| TV/Large display | 6+ feet | Much larger text needed |

**For phones:** Don't automatically shrink text. Users often hold phones far away, and smaller text just means more squinting.

## Viewport Units Reference

| Unit | Based On | Use Case |
|------|----------|----------|
| vw | Viewport width | Horizontal scaling |
| vh | Viewport height | Vertical scaling (rarely for type) |
| vmin | Smaller of vw/vh | Consistent scaling regardless of orientation |
| vmax | Larger of vw/vh | Less common for type |
| dvh | Dynamic viewport height | Accounts for mobile browser chrome |

**Warning:** Pure viewport units (not in clamp) can get too small or too large:

```css
/* Dangerous - no limits */
font-size: 5vw;  /* Could be 16px or 96px */

/* Safe - bounded */
font-size: clamp(1rem, 5vw, 3rem);
```

## Practical Responsive Checklist

Before launching:

- [ ] Text readable at 320px viewport width
- [ ] No horizontal scroll on mobile
- [ ] Line length under 75 characters on desktop
- [ ] Headings don't overwhelm on mobile
- [ ] Body text at least 16px equivalent everywhere
- [ ] Tested with browser zoom at 200%
- [ ] Works in both portrait and landscape
- [ ] Font loading doesn't cause major layout shift

## Complete Example

```css
/* Responsive type system */
:root {
  --font-body: 'Source Sans Pro', system-ui, sans-serif;
  --font-heading: 'Source Serif Pro', Georgia, serif;

  /* Fluid type scale */
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --text-lg: clamp(1.125rem, 1rem + 0.6vw, 1.5rem);
  --text-xl: clamp(1.25rem, 1rem + 1vw, 2rem);
  --text-2xl: clamp(1.5rem, 1rem + 1.5vw, 2.5rem);
  --text-3xl: clamp(2rem, 1rem + 2.5vw, 3.5rem);

  /* Fluid spacing */
  --space-prose: clamp(1rem, 5vw, 3rem);
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.6;
}

h1, h2, h3 {
  font-family: var(--font-heading);
  line-height: 1.2;
}

h1 { font-size: var(--text-3xl); }
h2 { font-size: var(--text-2xl); }
h3 { font-size: var(--text-xl); }

.prose {
  max-width: min(65ch, 100% - 2rem);
  padding-inline: var(--space-prose);
  margin-inline: auto;
}

/* Adjustments for wider viewports */
@media (min-width: 1024px) {
  body {
    line-height: 1.7;
  }
}
```

## Tools and Resources

**Fluid type calculators:**
- [Utopia.fyi](https://utopia.fyi/type/calculator/)
- [Modern Fluid Typography Editor](https://modern-fluid-typography.vercel.app/)
- [Fluid Type Scale Calculator](https://www.fluid-type-scale.com/)

**Testing:**
- Browser DevTools responsive mode
- [Responsively App](https://responsively.app/) - Multi-device preview
- Real devices when possible

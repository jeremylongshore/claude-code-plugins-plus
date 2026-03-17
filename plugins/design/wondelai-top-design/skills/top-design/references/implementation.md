# Top Design -- Advanced UI Implementation Guide

## Overview

Apply advanced visual design principles for production-quality web and mobile interfaces, including visual hierarchy, motion, component design, and design system architecture.

## Visual Hierarchy Principles

### Priority Stack

```markdown
## Reading Order Audit

For any screen, define the 1-2-3 reading order:

1. Primary (what MUST they see first?): [headline / key stat / CTA]
2. Secondary (what reinforces it?): [subhead / supporting info]
3. Tertiary (contextual detail): [fine print / metadata]

Each level should be visually distinct from the others.
Size difference: 2 steps on the type scale.
Weight: Use bold vs. regular to reinforce hierarchy.
Color: Use full-opacity for primary, 60% for tertiary.
```

### Alignment Systems

```css
/* 4-column layout for dashboards */
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-6); }

/* 12-column for content pages */
.content-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: var(--space-4); }
.content-body { grid-column: 3 / 11; }  /* Centered 8 columns */
```

## Motion Design

```css
/* Easing tokens */
--ease-out: cubic-bezier(0.0, 0.0, 0.2, 1);     /* Elements entering */
--ease-in:  cubic-bezier(0.4, 0.0, 1, 1);         /* Elements leaving */
--ease-inout: cubic-bezier(0.4, 0.0, 0.2, 1);     /* Elements moving */

/* Duration tokens */
--duration-fast:    100ms;  /* Micro-interactions: hover, focus */
--duration-normal:  200ms;  /* UI state changes: toggle, select */
--duration-slow:    300ms;  /* Page transitions, modals */
--duration-slower:  500ms;  /* Complex animations */

/* Always add: */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; }
}
```

## Component Design Principles

### Button System

```css
/* Variant x Size matrix */
.btn         { padding: var(--space-2) var(--space-4); border-radius: 6px; }
.btn-sm      { padding: var(--space-1) var(--space-3); font-size: var(--text-sm); }
.btn-lg      { padding: var(--space-3) var(--space-6); font-size: var(--text-lg); }

.btn-primary { background: var(--primary); color: white; }
.btn-outline { border: 1.5px solid var(--border); background: transparent; }
.btn-ghost   { background: transparent; color: var(--text); }
.btn-danger  { background: var(--red-600); color: white; }
```

### Card Architecture

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--duration-normal) var(--ease-out);
}

.card:hover { box-shadow: var(--shadow-md); }
.card--featured { border-color: var(--primary-border); box-shadow: var(--shadow-lg); }
```

## Design System Checklist

```markdown
Tokens:
- [ ] Color tokens defined (not hardcoded values)
- [ ] Spacing scale defined and used consistently
- [ ] Type scale defined (max 6 levels)
- [ ] Shadow scale defined (sm, md, lg, xl)
- [ ] Motion tokens defined (duration, easing)

Components:
- [ ] Button (primary, outline, ghost, danger) x (sm, md, lg)
- [ ] Input (default, focus, error, disabled)
- [ ] Card (standard, featured, compact)
- [ ] Badge/Tag
- [ ] Modal/Dialog

Documentation:
- [ ] Each component has a usage example
- [ ] Anti-patterns documented
- [ ] Accessibility notes included
```

## References

- [Figma Design System Guide](https://www.figma.com/resource-library/design-systems/)
- [Refactoring UI](https://refactoringui.com)
- [Every Layout](https://every-layout.dev/)

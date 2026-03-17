# Refactoring UI -- Visual Upgrade Implementation Guide

## Overview

Apply Adam Wathan & Steve Schoger's Refactoring UI principles to audit and improve web UI visual design using systematic spacing, color, typography, and depth techniques.

## Core Principles

### 1. Start with Grayscale

```markdown
## Grayscale-First Workflow

Before adding color:
1. Design the entire interface in black and white
2. Use font weight and size to create hierarchy
3. Use spacing to separate sections
4. Add color last (only to communicate, not decorate)

Color's job: Communicate state (success/error/warning), brand, and calls to action.
Color is NOT for making things "look designed."
```

### 2. Establish a Type Scale

Use a constrained scale. Do not use arbitrary font sizes.

```css
/* Recommended type scale (multiply by 1.25) */
--text-xs:   12px;
--text-sm:   14px;
--text-base: 16px;
--text-lg:   20px;
--text-xl:   24px;
--text-2xl:  30px;
--text-3xl:  36px;
--text-4xl:  48px;
```

### 3. Spacing Scale

```css
/* 4pt base spacing grid */
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

**Rule:** Elements that are related get less space between them. Elements that are unrelated get more.

### 4. Color System

```css
/* Build a 9-shade palette per color */
--gray-100: oklch(97% 0 0);
--gray-200: oklch(92% 0 0);
--gray-300: oklch(84% 0 0);
--gray-400: oklch(72% 0 0);
--gray-500: oklch(58% 0 0);
--gray-600: oklch(44% 0 0);
--gray-700: oklch(34% 0 0);
--gray-800: oklch(24% 0 0);
--gray-900: oklch(15% 0 0);
```

### 5. Depth and Shadows

```css
/* Layered shadow system */
--shadow-sm:  0 1px 2px rgb(0 0 0 / 0.05);
--shadow-md:  0 4px 6px rgb(0 0 0 / 0.07), 0 2px 4px rgb(0 0 0 / 0.06);
--shadow-lg:  0 10px 15px rgb(0 0 0 / 0.10), 0 4px 6px rgb(0 0 0 / 0.05);
--shadow-xl:  0 20px 25px rgb(0 0 0 / 0.10), 0 10px 10px rgb(0 0 0 / 0.04);
```

## Visual Audit Checklist

```markdown
Typography:
- [ ] No more than 2 font families used
- [ ] Maximum 4 font sizes per page
- [ ] Line height: body 1.5-1.6, headings 1.1-1.3
- [ ] Text width constrained to 60-75 chars per line

Spacing:
- [ ] All spacing values are from the scale (no arbitrary values)
- [ ] Related elements are closer together than unrelated ones
- [ ] Cards have consistent padding

Color:
- [ ] Background, surface, text are from grayscale palette
- [ ] Accent color used sparingly (< 10% of area)
- [ ] Contrast meets WCAG AA (4.5:1 for text)

Components:
- [ ] Buttons use consistent corner radius
- [ ] Form inputs have visible focus states
- [ ] Icons are same size/weight family
```

## Quick Wins (30-Minute Audit)

1. Remove all border colors and replace with shadows for elevation
2. Reduce the number of font sizes to 4 (xs, sm, base, lg)
3. Add more whitespace inside cards (double the current padding)
4. Desaturate all grays slightly (warm grays feel more premium)
5. Make the primary CTA button larger and more contrasty

## References

- Wathan, A. & Schoger, S. (2018). *Refactoring UI.* Self-published.
- [Tailwind CSS](https://tailwindcss.com) (implements these scales)

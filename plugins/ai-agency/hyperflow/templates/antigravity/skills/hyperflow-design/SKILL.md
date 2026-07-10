---
name: hyperflow-design
description: Hyperflow design phase. Use when designing a UI / visual system or making a screen look good — verbs like "design the UI", "make it look good", "design the screen", "visual design", "design system". Establishes or extends a domain-grounded design system, researches real-world prior art, and renders it slop-free. Thinking and taste, not building.
---

# hyperflow-design — design phase (Antigravity single-agent)

Design system and taste, not production code. Follow the `hyperflow` doctrine.

## Steps

1. **Design system first.** Ensure `.hyperflow/design/system.md` exists — create it if missing, extend it (never regenerate) if present: tokens, type scale, motion language, voice, component inventory, references, anti-patterns.
2. **Researched, not invented.** Study **≥2** real-world references from the project's own field, combine them, then add one deliberate signature move — never copy a single source.
3. **Taste applied.** Discover and apply the matching local taste skill(s); pass the anti-slop floor (no default AI gradient, no serif-by-default, one accent, locked corner-radius scale, eyebrow restraint, no duplicate-intent CTAs, hero fits the viewport, every motion communicates state).
4. **Record** the bound design-system tokens and the named signature into the spec. When a motion surface is in scope, apply the Motion-language standards (compositor-only props, spring params, reduced-motion fallback); when a mobile surface is in scope, apply the mobile platform/device/accessibility matrix.

## Rules

- No production code — only the design system and the spec.
- Defer to accessibility on any a11y conflict (the WCAG floor wins) and to security on any security conflict.
- Every best-practice claim about a pattern cites a current source.

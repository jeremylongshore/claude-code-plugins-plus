---
title: "OKLCH: Why Your CSS Color System Is Lying to You"
description: "HSL colors look mathematically equal but perceptually wrong. OKLCH fixes this. How a full marketplace facelift exposed the problem."
date: "2026-03-13"
tags: ["web-development", "architecture", "css"]
featured: false
---
Pick two colors in HSL. Same saturation, same lightness, different hues. They should look equally bright. They don't.

This is the core lie of HSL. And it bit me during a full visual facelift of the claude-code-plugins marketplace.

## The HSL Problem

Try this yourself. Open a browser console:

```css
.yellow { background: hsl(60, 100%, 50%); }
.blue   { background: hsl(240, 100%, 50%); }
```

Both are `100%` saturation, `50%` lightness. Mathematically identical brightness. Put them side by side and yellow screams while blue recedes. Your eyes aren't broken — HSL is. It maps to a color model that doesn't account for how human vision actually perceives luminance.

This matters when you're generating color palettes programmatically. If your primary, secondary, and accent colors share the same lightness value in HSL, they'll look inconsistent. Buttons will feel heavier in some hues than others. Hover states will shift perceived brightness depending on the color. Your design system lies to you at the API level.

## OKLCH Fixes This

OKLCH is a perceptually uniform color space. Same lightness value means same perceived brightness, regardless of hue. The "OK" refers to Björn Ottosson's improved version of the CIE Lab color model. Three channels:

- **L** — Lightness (0 = black, 1 = white, perceptually linear)
- **C** — Chroma (color intensity, like saturation but calibrated)
- **H** — Hue (0-360 degrees, same as HSL)

The equivalent comparison:

```css
.yellow { background: oklch(0.9 0.2 100); }
.blue   { background: oklch(0.9 0.2 260); }
```

Same lightness, same chroma. These actually look equally bright. You can sweep through hues and get a coherent palette without manual per-color tweaking.

## The Marketplace Facelift

PR #343 applied this across the entire claude-code-plugins marketplace. Every page. Homepage, explore, blog, verification badges, individual skill pages. One PR, one coherent visual system.

The OKLCH adoption wasn't just a color swap. It was part of a broader typography and layout overhaul:

- **Color system** — All color values moved to OKLCH, including shadow values
- **Typography** — New font stack and size scale for better hierarchy
- **Navigation** — Restructured nav for cleaner information architecture
- **Footer** — Updated links, layout, and dynamic copyright year

PR review caught inline styles that needed extraction and OKLCH shadow values that were hardcoded instead of using CSS custom properties. Good catches. The kind of feedback that turns a facelift into a maintainable system.

## When to Adopt OKLCH

Browser support is there. Every modern browser handles `oklch()` natively. If you're building a design system, generating theme colors from code, or maintaining a dark/light mode toggle, OKLCH eliminates an entire class of "why does this color look wrong" bugs.

If you're tweaking three hex values on a landing page, HSL is fine. But the moment your color system becomes programmatic — tokens, theme generation, dynamic palettes — OKLCH is the correct abstraction.

## Related Posts

- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/blog/verified-plugins-program-quality-signal-for-the-marketplace/)
- [Three Projects, Two Reverts, One Day](/blog/three-projects-two-reverts-one-day/)
- [React Native Mobile App in One Session](/blog/react-native-mobile-app-one-session/)

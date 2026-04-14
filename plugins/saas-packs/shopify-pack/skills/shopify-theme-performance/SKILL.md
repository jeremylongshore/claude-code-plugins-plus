---
name: shopify-theme-performance
description: |
  Optimize Shopify theme performance for Core Web Vitals (LCP, CLS, INP).
  Use when diagnosing slow page loads, fixing lazy-loaded hero images,
  profiling Liquid render times, or optimizing image delivery.
  Trigger with phrases like "shopify theme performance", "shopify core web vitals",
  "shopify lcp", "shopify liquid profiler", "shopify image optimization".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Theme Performance

## Overview

59% of Shopify stores lazy-load their LCP image, adding 3-5 seconds to perceived load time. This skill covers the highest-impact theme optimizations: fixing LCP image loading, switching to the modern `image_url` filter, profiling Liquid render times, and optimizing font delivery.

## Prerequisites

- Access to the Shopify theme editor or theme files via CLI (`shopify theme dev`)
- Theme using Online Store 2.0 architecture (sections + JSON templates)
- Google Chrome DevTools or Lighthouse for measurement

## Instructions

### Step 1: Fix LCP Image Loading

The LCP element is usually the hero banner image. Find it in your theme's hero section:

```liquid
{% comment %} BAD: lazy-loading the LCP image costs 3-5s {% endcomment %}
{{ section.settings.hero_image | image_url: width: 1200 | image_tag: loading: 'lazy' }}

{% comment %} GOOD: eager load + fetchpriority for LCP {% endcomment %}
{{ section.settings.hero_image | image_url: width: 1200 | image_tag:
    loading: 'eager',
    fetchpriority: 'high',
    sizes: '100vw' }}
```

Add a preload hint in `theme.liquid` inside `<head>`:

```liquid
{%- if template.name == 'index' -%}
  <link rel="preload"
        href="{{ section.settings.hero_image | image_url: width: 1200 }}"
        as="image"
        fetchpriority="high">
{%- endif -%}
```

### Step 2: Use the `image_url` Filter

The modern `image_url` filter replaces the deprecated `img_url`. It supports responsive images via srcset:

```liquid
{% assign image = product.featured_image %}

<img src="{{ image | image_url: width: 800 }}"
     srcset="{{ image | image_url: width: 400 }} 400w,
             {{ image | image_url: width: 600 }} 600w,
             {{ image | image_url: width: 800 }} 800w,
             {{ image | image_url: width: 1200 }} 1200w"
     sizes="(max-width: 749px) 100vw, 50vw"
     width="{{ image.width }}"
     height="{{ image.height }}"
     loading="lazy"
     alt="{{ image.alt | escape }}">
```

Always set explicit `width` and `height` attributes to prevent CLS (Cumulative Layout Shift).

### Step 3: Liquid Profiler

Append `?profile=true` to any storefront URL to activate the Liquid profiler. It renders a table at the bottom of the page showing render times per snippet.

See [references/liquid-profiling.md](references/liquid-profiling.md) for how to read the output and common slow patterns.

### Step 4: Font Loading

Preload critical fonts and use `font-display: swap` to prevent invisible text:

```liquid
{% comment %} In theme.liquid <head> {% endcomment %}
<link rel="preload"
      href="{{ 'your-font.woff2' | asset_url }}"
      as="font"
      type="font/woff2"
      crossorigin>

<style>
  @font-face {
    font-family: 'YourFont';
    src: url('{{ "your-font.woff2" | asset_url }}') format('woff2');
    font-display: swap;
    font-weight: 400;
  }
</style>
```

Limit to 2-3 font files maximum. Each additional font file blocks rendering.

## Output

- LCP image loading eagerly with `fetchpriority="high"` and preload hint
- Responsive images using `image_url` with proper srcset and sizes
- Liquid profiler data identifying slow snippets
- Fonts preloaded with `font-display: swap`

## Error Handling

| Mistake | Impact | Fix |
|---------|--------|-----|
| Lazy-loading LCP image | +3-5s LCP | `loading="eager"` + `fetchpriority="high"` |
| Using `img_url` filter | No responsive images, larger payloads | Switch to `image_url` with width param |
| Render-blocking CSS | Delayed FCP | Inline critical CSS, defer non-critical |
| Too many Liquid `include` tags | Slow server render (variable scope leak) | Use `render` instead of `include` |
| Missing width/height on images | CLS jumps during load | Set explicit dimensions from `image.width`/`image.height` |
| Too many font files | Render blocking | Limit to 2-3 woff2 files, preload critical ones |

## Examples

### Fixing a Lazy-Loaded Hero Image

The homepage LCP score is 5+ seconds because the hero banner uses `loading="lazy"`. Switch to eager loading with fetchpriority and add a preload hint.

See [Core Web Vitals](references/core-web-vitals.md) for targets and measurement techniques.

### Migrating from img_url to image_url

Replace deprecated `img_url` filters with the modern `image_url` filter to enable responsive srcset images and reduce payload sizes.

See [Image Optimization](references/image-optimization.md) for the complete migration patterns.

### Profiling Slow Liquid Renders

A collection page takes 800ms to render server-side. Use the Liquid profiler to identify which snippets are slow and apply fixes.

See [Liquid Profiling](references/liquid-profiling.md) for profiler usage and common slow patterns.

## Resources

- [Shopify Theme Performance](https://shopify.dev/docs/storefronts/themes/best-practices/performance)
- [image_url Filter Reference](https://shopify.dev/docs/api/liquid/filters/image_url)
- [Liquid Profiler](https://shopify.dev/docs/storefronts/themes/tools/liquid-profiler)
- [Core Web Vitals for Shopify](https://shopify.dev/docs/storefronts/themes/best-practices/performance#core-web-vitals)
- [font-display CSS Property](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display)

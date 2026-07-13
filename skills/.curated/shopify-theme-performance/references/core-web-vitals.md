Core Web Vitals targets and measurement techniques specific to Shopify themes.

## Targets for Shopify Themes

| Metric | Good | Needs Improvement | Poor | Shopify Avg |
|--------|------|-------------------|------|-------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s - 4.0s | > 4.0s | ~3.2s |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 - 0.25 | > 0.25 | ~0.08 |
| **INP** (Interaction to Next Paint) | < 200ms | 200ms - 500ms | > 500ms | ~250ms |

## Measuring with Lighthouse

### Local Measurement

```bash
# CLI Lighthouse (most accurate for development)
npx lighthouse https://your-store.myshopify.com \
  --only-categories=performance \
  --output=json \
  --output-path=./lighthouse-report.json

# Quick scores only
npx lighthouse https://your-store.myshopify.com \
  --only-categories=performance \
  --output=json | jq '.categories.performance.score'
```

### Chrome DevTools

1. Open DevTools > Performance tab
2. Check "Web Vitals" checkbox
3. Click Record, reload page, stop recording
4. LCP, CLS, and INP markers appear on the timeline

### PageSpeed Insights (Field Data)

```
https://pagespeed.web.dev/analysis?url=https://your-store.myshopify.com
```

Field data from CrUX (Chrome User Experience Report) shows real-user metrics over 28 days. This is what Google uses for ranking.

## CrUX API for Programmatic Access

```bash
curl "https://chromeuxreport.googleapis.com/v1/records:queryRecord?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-store.myshopify.com/",
    "metrics": [
      "largest_contentful_paint",
      "cumulative_layout_shift",
      "interaction_to_next_paint"
    ]
  }'
```

## Shopify-Specific LCP Elements

The LCP element varies by page type:

| Page | Typical LCP Element | Optimization |
|------|---------------------|-------------|
| Homepage | Hero banner image | `fetchpriority="high"`, preload in `<head>` |
| Collection | First product image grid | `loading="eager"` on first 4 images only |
| Product | Featured product image | `fetchpriority="high"`, preload in section |
| Blog | Featured article image | `loading="eager"` on first article image |

## CLS Common Causes in Shopify

| Cause | Fix |
|-------|-----|
| Images without dimensions | Set `width` and `height` from `image.width`/`image.height` |
| Dynamic banners/announcements | Reserve space with `min-height` on container |
| Web fonts loading | `font-display: swap` + preload critical fonts |
| Lazy-loaded content above fold | Only lazy-load below-the-fold content |
| App embeds injecting DOM | Use `content-visibility: auto` on app containers |

## INP Optimization for Shopify

INP measures responsiveness to user interactions. Common Shopify offenders:

```javascript
// BAD: Heavy click handler blocks main thread
document.querySelector('.add-to-cart').addEventListener('click', () => {
  // Synchronous DOM manipulation + fetch
  updateCartDOM();
  fetchCartAPI();
});

// GOOD: Defer non-critical work
document.querySelector('.add-to-cart').addEventListener('click', async () => {
  // Immediate visual feedback
  button.classList.add('loading');
  button.disabled = true;

  // Async work
  await fetchCartAPI();

  // Deferred DOM update
  requestAnimationFrame(() => updateCartDOM());
});
```

---
name: testing-visual-regression
description: |
  Detect visual changes in UI components using screenshot comparison.
  Use when detecting unintended UI changes or pixel differences.
  Trigger with phrases like "test visual changes", "compare screenshots", or "detect UI regressions".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:visual-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Visual Regression Tester

## Overview

Detect unintended visual changes in UI components by capturing screenshots and comparing them pixel-by-pixel against approved baselines. Supports Playwright visual comparisons, Percy, Chromatic, BackstopJS, and reg-suit.

## Prerequisites

- Browser automation tool installed (Playwright, Puppeteer, or Cypress)
- Visual regression library configured (Playwright `toHaveScreenshot`, Percy, Chromatic, or BackstopJS)
- Baseline screenshots committed to version control or stored in a cloud service
- Storybook or component playground running for isolated component captures (optional)
- Consistent rendering environment (Docker or CI with fixed OS/fonts/GPU settings)

## Instructions

1. Identify all UI components and pages requiring visual coverage using Glob to scan component directories and route definitions.
2. Create a visual test file for each component or page:
   - Navigate to the component URL or Storybook story.
   - Wait for all network requests, animations, and lazy-loaded images to complete.
   - Set a consistent viewport size (e.g., 1280x720 for desktop, 375x812 for mobile).
3. Capture screenshots with deterministic settings:
   - Disable animations and transitions (`* { animation: none !important; transition: none !important; }`).
   - Mask dynamic content (timestamps, random avatars, ads) with CSS overlays.
   - Use `fullPage: true` for scrollable pages.
4. Compare captured screenshots against baselines:
   - Configure pixel difference threshold (recommended: 0.1% for component tests, 0.5% for full-page).
   - Generate diff images highlighting changed regions.
   - Flag tests as failed when differences exceed the threshold.
5. For responsive testing, capture at multiple breakpoints:
   - Mobile: 375px width
   - Tablet: 768px width
   - Desktop: 1280px width
   - Wide: 1920px width
6. Review diff images for each failure and classify as:
   - **Intentional change**: Update the baseline with `--update-snapshots`.
   - **Regression**: File a bug with the diff image attached.
7. Integrate into CI so visual tests run on every pull request with diff images uploaded as artifacts.

## Output

- Screenshot baseline images stored in `__screenshots__/` or equivalent directory
- Diff images highlighting pixel-level changes between baseline and current
- Visual regression test report with pass/fail status per component
- CI artifacts containing all captured, baseline, and diff images
- Responsive coverage matrix showing results across breakpoints

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Anti-aliasing differences across OS | Font rendering varies between macOS, Linux, and Windows | Run visual tests in Docker with fixed fonts; use `threshold` option to allow sub-pixel variance |
| Flaky screenshots from animations | CSS transitions or JS animations still running at capture time | Inject `prefers-reduced-motion` or disable animations via `addStyleTag` before capture |
| Missing baseline on first run | No previous screenshot exists to compare against | Run with `--update-snapshots` to create initial baselines; commit them to the repository |
| Viewport size mismatch | Browser chrome or scrollbar width differs between environments | Use `setViewportSize` explicitly; hide scrollbars with CSS `overflow: hidden` |
| Dynamic content causes false failures | Timestamps, user avatars, or ads change between runs | Mask dynamic elements with `mask` option or replace content via `page.evaluate` |

## Examples

**Playwright visual regression test:**
```typescript
import { test, expect } from '@playwright/test';

test('homepage matches baseline', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.addStyleTag({ content: '* { animation: none !important; }' });
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.001,
    fullPage: true,
  });
});
```

**BackstopJS scenario configuration:**
```json
{
  "label": "Login Page",
  "url": "http://localhost:3000/login",  # 3000: 3 seconds in ms
  "selectors": ["document"],
  "misMatchThreshold": 0.1,
  "viewports": [
    { "label": "phone", "width": 375, "height": 812 },  # 812: 375 = configured value
    { "label": "desktop", "width": 1280, "height": 720 }  # 1280: 720 = configured value
  ]
}
```

## Resources

- Playwright visual comparisons: https://playwright.dev/docs/test-snapshots
- Percy visual testing: https://www.percy.io/
- Chromatic (Storybook): https://www.chromatic.com/
- BackstopJS: https://github.com/garris/BackstopJS
- reg-suit visual regression: https://reg-viz.github.io/reg-suit/
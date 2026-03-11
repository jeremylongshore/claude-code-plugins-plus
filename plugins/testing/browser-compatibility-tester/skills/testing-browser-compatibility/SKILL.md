---
name: testing-browser-compatibility
description: |
  Test across multiple browsers and devices for cross-browser compatibility.
  Use when ensuring cross-browser or device compatibility.
  Trigger with phrases like "test browser compatibility", "check cross-browser", or "validate on browsers".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:browser-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Browser Compatibility Tester

## Overview

Test web applications across multiple browsers, rendering engines, and device form factors to identify compatibility issues. Validates CSS rendering, JavaScript API support, layout consistency, and interactive behavior across Chromium (Chrome, Edge), Firefox (Gecko), and WebKit (Safari).

## Prerequisites

- Playwright installed with all browser engines (`npx playwright install --with-deps`)
- Application running and accessible at a test URL
- Target browser matrix defined (minimum: Chrome, Firefox, Safari, Edge, mobile Safari, mobile Chrome)
- Polyfill configuration or browserslist target defined in `package.json`
- BrowserStack or Sauce Labs credentials for real device testing (optional)

## Instructions

1. Define the browser compatibility matrix:
   - **Desktop**: Chrome (latest), Firefox (latest), Safari (latest), Edge (latest).
   - **Mobile**: Safari on iOS 16+, Chrome on Android 13+.
   - **Viewports**: 375px (phone), 768px (tablet), 1280px (desktop), 1920px (widescreen).
   - Document minimum browser versions from the project's `browserslist` config.
2. Scan the codebase for potentially incompatible API usage:
   - Use Grep to search for modern JS APIs (`IntersectionObserver`, `ResizeObserver`, `structuredClone`, `Array.at()`).
   - Check CSS features (`container queries`, `has()`, `@layer`, `subgrid`, `color-mix()`).
   - Cross-reference findings against caniuse data for the target browser matrix.
   - Flag usage without polyfills or feature detection.
3. Create cross-browser test suite with Playwright projects:
   - Define a project for each browser engine (chromium, firefox, webkit).
   - Add mobile device emulation projects (iPhone 14, Pixel 7).
   - Share test files across all projects -- same tests, different browsers.
4. Write compatibility-focused test cases:
   - Layout tests: Verify key page elements render at expected positions and sizes.
   - CSS feature tests: Check that modern CSS features degrade gracefully.
   - JS API tests: Confirm polyfills load correctly in older browsers.
   - Form tests: Validate input types (date, color, range) across browsers.
   - Media tests: Check video/audio playback, WebP/AVIF image support.
5. Test browser-specific behaviors:
   - Safari: Check date input formatting, scroll behavior, backdrop-filter, PWA support.
   - Firefox: Verify scrollbar styling, `gap` in flexbox, subpixel rendering.
   - Mobile: Test touch events, viewport meta tag, safe area insets, virtual keyboard behavior.
6. Execute the test suite across all browser projects:
   - Run `npx playwright test --project=chromium --project=firefox --project=webkit`.
   - Capture screenshots per browser for visual comparison.
   - Record failing tests with video traces for debugging.
7. Generate a compatibility report showing pass/fail per browser and viewport.

## Output

- Playwright configuration with multi-browser project definitions
- Cross-browser test files in `tests/compatibility/`
- Compatibility matrix report (pass/fail per browser, viewport, and test case)
- Screenshots per browser for visual comparison
- List of unsupported API usage with polyfill or fallback recommendations

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| WebKit test fails but Chromium passes | CSS property not supported in Safari (e.g., `gap` in older Safari) | Add vendor prefix (`-webkit-gap`) or use flexbox margin workaround; check caniuse |
| Date input renders differently | Browsers implement `<input type="date">` differently | Use a custom date picker component for consistent cross-browser behavior |
| Font rendering differences | System fonts differ across OS; subpixel antialiasing varies | Use web fonts with `font-display: swap`; increase visual diff tolerance in screenshot tests |
| Touch event test fails on desktop | Desktop browser does not fire touch events in non-emulation mode | Use Playwright device emulation with `hasTouch: true`; separate mobile tests from desktop |
| Test passes locally but fails on BrowserStack | Real device has different rendering than Playwright emulation | Run critical tests on BrowserStack for final validation; accept emulation for development feedback |

## Examples

**Playwright multi-browser configuration:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 14'] } },
  ],
});
```

**Cross-browser layout test:**
```typescript
test('navigation renders correctly across browsers', async ({ page }) => {
  await page.goto('/');
  const nav = page.locator('nav');
  await expect(nav).toBeVisible();
  const box = await nav.boundingBox();
  expect(box.width).toBeGreaterThan(300);  # 300: timeout: 5 minutes
  expect(box.height).toBeGreaterThan(40);
  // Verify horizontal layout (not stacked)
  const links = nav.locator('a');
  const firstLink = await links.nth(0).boundingBox();
  const secondLink = await links.nth(1).boundingBox();
  expect(firstLink.y).toBeCloseTo(secondLink.y, 5); // Same vertical position
});
```

**CSS feature detection check:**
```typescript
test('container queries have fallback', async ({ page }) => {
  await page.goto('/components');
  const card = page.locator('.responsive-card');
  // Card should render regardless of container query support
  await expect(card).toBeVisible();
  const box = await card.boundingBox();
  expect(box.width).toBeGreaterThan(0);
});
```

## Resources

- Playwright browsers: https://playwright.dev/docs/browsers
- Can I Use: https://caniuse.com/
- BrowserStack: https://www.browserstack.com/
- Browserslist: https://browsersl.ist/
- MDN Browser Compatibility Data: https://github.com/mdn/browser-compat-data
- CSS feature detection with @supports: https://developer.mozilla.org/en-US/docs/Web/CSS/@supports
---
name: browser-test
description: Cross-browser testing across browsers, devices, and cloud providers
shortcut: bt
---
# Browser Compatibility Tester

Test web applications across Chrome, Firefox, Safari, and Edge using local Playwright or cloud platforms (BrowserStack, Sauce Labs, LambdaTest, Kobiton).

## What You Do

1. **Determine Testing Scope**
   - Ask: local testing (Playwright) or cloud real-device testing?
   - If cloud, ask which provider or help choose based on need (see decision matrix below)
   - Define target browsers, versions, and viewports

2. **Configure Browser Matrix**
   - Desktop: Chrome (latest), Firefox (latest), Safari (latest), Edge (latest)
   - Mobile: Safari on iOS 16+, Chrome on Android 13+, Samsung Internet
   - Viewports: 375px (phone), 768px (tablet), 1280px (desktop), 1920px (widescreen)
   - Read project `browserslist` config if present for minimum version targets

3. **Scan for Compatibility Risks**
   - Grep for modern JS APIs: `IntersectionObserver`, `structuredClone`, `Array.at()`, `Promise.withResolvers`
   - Grep for modern CSS: `container queries`, `has()`, `@layer`, `subgrid`, `color-mix()`
   - Cross-reference against caniuse data for the target matrix
   - Flag usage without polyfills or `@supports` feature detection

4. **Generate and Execute Tests**
   - Create Playwright multi-browser project config
   - Write layout, CSS feature, JS API, form input, and media tests
   - Run locally: `npx playwright test --project=chromium --project=firefox --project=webkit`
   - For cloud: configure WebDriver capabilities and run against provider

5. **Cloud Provider Setup** (if selected)
   - **BrowserStack**: Set `BROWSERSTACK_USERNAME` + `BROWSERSTACK_ACCESS_KEY`, configure Automate capabilities
   - **Sauce Labs**: Set `SAUCE_USERNAME` + `SAUCE_ACCESS_KEY`, launch Sauce Connect for staging
   - **LambdaTest**: Set `LT_USERNAME` + `LT_ACCESS_KEY`, configure LambdaTest tunnel
   - **Kobiton**: Set `KOBITON_USERNAME` + `KOBITON_API_KEY`, use Appium capabilities with `kobiton:` prefix, query real device availability via REST API

6. **Generate Compatibility Report**

## Provider Decision Matrix

| Need | Recommended Provider |
|------|---------------------|
| Fastest iteration during development | Playwright (local) |
| Broadest desktop browser/OS coverage | BrowserStack |
| Enterprise CI/CD with deep integrations | Sauce Labs |
| Scaling team, auto-healing selectors | LambdaTest |
| Real physical device mobile testing | Kobiton |
| No budget for cloud services | Playwright (local) |

## Output Format

```markdown
## Browser Compatibility Report

### Test Configuration
**Provider:** [Playwright / BrowserStack / Sauce Labs / LambdaTest / Kobiton]
**Browsers:** [N]
**Test Cases:** [N]
**Parallel Workers:** [N]

### Browser Matrix
| Browser | Version | OS/Device | Status |
|---------|---------|-----------|--------|
| Chrome | 125+ | Windows 11 | Pass |
| Firefox | 126+ | macOS Sonoma | Pass |
| Safari | 17.4+ | macOS Sonoma | 2 failures |
| Edge | 125+ | Windows 11 | Pass |
| Safari | 17.4 | iPhone 15 (Kobiton) | 1 failure |
| Chrome | 125 | Pixel 8 (Kobiton) | Pass |

### Compatibility Issues

#### Issue: [Description]
**Browsers Affected:** Safari 17.x
**Severity:** [High/Medium/Low]
**Test:** `[test name]`
**Provider:** [where the issue was found]

**Problem:**
[Detailed explanation of incompatibility]

**Root Cause:**
[CSS property / JS API / Feature not supported]

**Fix:**
```css
/* Fallback for browsers without container query support */
@supports not (container-type: inline-size) {
  .card { width: 100%; }
}
```

**Can I Use:** [caniuse.com link]

### Cloud Session Links (if applicable)

| Provider | Session URL | Video | Duration |
|----------|-------------|-------|----------|
| Kobiton | [session link] | [video link] | 2m 34s |
| BrowserStack | [session link] | [video link] | 1m 48s |

### Summary

- Tests passed: [N] ([%])
- Tests with warnings: [N]
- Tests failed: [N]

### Next Steps

- [ ] Fix compatibility issues listed above
- [ ] Add polyfills or @supports fallbacks
- [ ] Re-run on cloud provider to confirm fixes on real devices
- [ ] Update browserslist config if dropping old versions

```

## Configuration Example

```javascript
// playwright.config.js -- local multi-browser setup
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'edge', use: { channel: 'msedge' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 14'] } },
  ],
});
```

---
name: scanning-accessibility
description: |
  Validate WCAG compliance and accessibility standards (ARIA, keyboard navigation).
  Use when auditing WCAG compliance or screen reader compatibility.
  Trigger with phrases like "scan accessibility", "check WCAG compliance", or "validate screen readers".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:a11y-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Accessibility Test Scanner

## Overview

Validate web applications against WCAG 2.1/2.2 accessibility standards covering perceivability, operability, understandability, and robustness. Combines automated scanning with axe-core, Pa11y, and Lighthouse accessibility audits alongside manual validation checklists for keyboard navigation, screen reader compatibility, and color contrast. Produces compliance reports with remediation guidance mapped to specific WCAG success criteria.

## Prerequisites

- Accessibility testing library installed (axe-core, @axe-core/playwright, Pa11y, or Lighthouse CI)
- Browser automation tool (Playwright or Puppeteer) for rendering pages
- Application running and accessible at a test URL
- Target WCAG conformance level defined (A, AA, or AAA -- AA is standard)
- Color contrast analyzer (built into axe-core or standalone tool)

## Instructions

1. Configure the accessibility scanner with the target WCAG level:
   - Set axe-core rules to WCAG 2.1 AA (or 2.2 AA for latest standard).
   - Include rules for ARIA attributes, color contrast, form labels, and heading structure.
   - Define pages and components to scan (homepage, forms, modals, navigation).
2. Run automated accessibility scans on each page:
   - Use `@axe-core/playwright` to scan after page load.
   - Run Pa11y for HTML-level validation.
   - Execute Lighthouse accessibility audit for a score and detailed findings.
   - Scan each major interactive state (modal open, dropdown expanded, error state).
3. Validate keyboard navigation:
   - Verify all interactive elements are reachable via Tab key in logical order.
   - Confirm focus indicators are visible on every focusable element.
   - Test Escape key closes modals and dropdowns.
   - Verify skip-to-content link is present and functional.
   - Check that focus is trapped within open modals (no focus escape).
4. Validate ARIA implementation:
   - Check all ARIA roles match the element's purpose (`role="button"` on clickable divs).
   - Verify `aria-label` or `aria-labelledby` on elements without visible text.
   - Confirm `aria-live` regions announce dynamic content changes.
   - Validate `aria-expanded`, `aria-selected`, and `aria-checked` states toggle correctly.
5. Check color and visual accessibility:
   - Verify text contrast ratio meets WCAG AA (4.5:1 for normal text, 3:1 for large text).
   - Ensure information is not conveyed by color alone (use icons, patterns, or text labels).
   - Test with simulated color blindness filters (protanopia, deuteranopia, tritanopia).
6. Validate form accessibility:
   - Every input has an associated `<label>` with matching `for`/`id`.
   - Error messages are announced via `aria-describedby` and `aria-invalid`.
   - Required fields are indicated with `aria-required="true"` and visual indicators.
7. Generate a compliance report with WCAG success criteria references for each finding.

## Output

- Accessibility scan results with violations, passes, and incomplete checks
- WCAG compliance matrix showing pass/fail per success criterion
- Remediation checklist with code fixes for each violation
- Keyboard navigation test results
- Lighthouse accessibility score and improvement recommendations

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| axe-core reports no violations but page is inaccessible | Automated tools catch ~30-40% of issues; manual testing needed | Supplement automated scans with keyboard and screen reader manual testing |
| Color contrast violation on dynamic theme | Theme colors computed at runtime not captured by static scan | Run scans with each theme active (light/dark); test with high-contrast mode |
| False positive on hidden content | Scanner checks elements that are visually hidden but present in DOM | Use `axe.configure({ rules: [{ id: 'rule-id', selector: ':visible' }] })` |
| ARIA role conflicts | Multiple conflicting ARIA attributes on same element | Remove redundant roles; follow WAI-ARIA authoring practices for the component pattern |
| Focus order incorrect after dynamic content | DOM insertion order differs from visual order | Use `tabindex` to correct order; restructure DOM to match visual layout |

## Examples

**Playwright + axe-core accessibility test:**
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage meets WCAG AA', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  expect(results.violations).toEqual([]);
});

test('login form is keyboard accessible', async ({ page }) => {
  await page.goto('/login');
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
  expect(focused).toBe('email-input');
  await page.keyboard.press('Tab');
  const nextFocused = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
  expect(nextFocused).toBe('password-input');
});
```

**Pa11y CI configuration:**
```json
{
  "defaults": {
    "standard": "WCAG2AA",
    "timeout": 10000,
    "wait": 1000
  },
  "urls": [
    "http://localhost:3000/",
    "http://localhost:3000/login",
    "http://localhost:3000/dashboard",
    { "url": "http://localhost:3000/settings", "actions": ["click element #tab-profile"] }
  ]
}
```

## Resources

- WCAG 2.2 guidelines: https://www.w3.org/TR/WCAG22/
- axe-core: https://github.com/dequelabs/axe-core
- Pa11y: https://pa11y.org/
- WAI-ARIA authoring practices: https://www.w3.org/WAI/ARIA/apg/
- Lighthouse accessibility: https://developer.chrome.com/docs/lighthouse/accessibility/
- WebAIM contrast checker: https://webaim.org/resources/contrastchecker/

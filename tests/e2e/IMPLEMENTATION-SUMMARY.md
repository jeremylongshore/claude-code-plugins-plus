# E2E Test Architecture - Implementation Summary

**Project:** Claude Code Plugins Marketplace
**Location:** `/home/jeremy/000-projects/claude-code-plugins/`
**Date:** 2025-12-27
**Status:** Design Complete, Ready for Implementation

## Quick Reference

### Documentation Files Created

1. **MARKETPLACE-E2E-ARCHITECTURE.md** - Complete architecture design (60 pages)
2. **examples/conversation-view.spec.ts** - 25 conversation view tests
3. **examples/accessibility.spec.ts** - 40+ accessibility tests with axe-core
4. **examples/performance.spec.ts** - Core Web Vitals and performance budgets
5. **This file** - Implementation roadmap and quick start

### Key Deliverables

- **95+ test cases** across 5 categories (smoke, regression, visual, performance, a11y)
- **Page Object Model** pattern for maintainability
- **CI/CD integration** strategy for GitHub Actions
- **Performance budgets** aligned with Core Web Vitals
- **WCAG 2.1 AA** compliance validation

## Architecture Overview

### Test Pyramid

```
       /\
      /  \     E2E (10 tests) - Critical user journeys
     /    \
    /------\   Integration (40 tests) - Feature workflows
   /        \
  /----------\  Unit (45 tests) - Component behavior
 /__________\
```

**Total:** 95 tests across all layers

### Directory Structure

```
marketplace/
├── tests/
│   ├── T1-T4.spec.ts              (Existing - 6 files)
│   ├── smoke/                     (NEW - 15 tests)
│   ├── regression/                (NEW - 40 tests)
│   ├── visual/                    (NEW - 12 tests)
│   ├── performance/               (NEW - 8 tests)
│   ├── accessibility/             (NEW - 10 tests)
│   ├── fixtures/                  (Test data)
│   └── utils/page-objects/        (Page Object Model)
└── playwright.config.ts           (Enhanced)
```

## Top 10 Priority Tests

### P0 - Critical Path (Must implement first)

1. **Homepage Loads Successfully** (smoke)
   - File: `tests/smoke/homepage.spec.ts`
   - Validates: Hero, CTAs, install box, navigation
   - Budget: < 2s load time

2. **Search Redirect to Explore** (smoke)
   - File: `tests/smoke/explore.spec.ts`
   - Validates: Click → redirect → search functional
   - Budget: < 500ms redirect

3. **Conversation View Displays Messages** (regression)
   - File: `tests/regression/conversation-view.spec.ts`
   - Validates: Message rendering, auto-scroll
   - Example: See `examples/conversation-view.spec.ts`

4. **Conversation View Empty State** (regression)
   - File: `tests/regression/conversation-view.spec.ts`
   - Validates: Empty UI when no messages
   - Example: Lines 36-49 in example file

5. **Mobile Keyboard Handling** (regression)
   - File: `tests/regression/mobile-responsiveness.spec.ts`
   - Validates: visualViewport resize, no overflow
   - Critical for iOS Safari

6. **No Horizontal Scroll on Mobile** (visual)
   - File: `tests/visual/layout-validation.spec.ts`
   - Validates: body.scrollWidth <= window.innerWidth
   - Viewports: 390px, 375px, 360px

7. **Accessibility Keyboard Navigation** (a11y)
   - File: `tests/accessibility/keyboard-navigation.spec.ts`
   - Validates: Tab order, focus indicators
   - Example: See `examples/accessibility.spec.ts`

8. **Core Web Vitals - LCP < 2.5s** (performance)
   - File: `tests/performance/core-web-vitals.spec.ts`
   - Validates: LCP, CLS, FID
   - Example: See `examples/performance.spec.ts`

9. **Axe-core A11y Scan** (a11y)
   - File: `tests/accessibility/axe-core.spec.ts`
   - Validates: WCAG 2.1 AA compliance
   - Example: Lines 31-47 in accessibility example

10. **Conversation Input Sends Message** (regression)
    - File: `tests/regression/conversation-input.spec.ts`
    - Validates: Type → send → message appears
    - Auto-scroll verification

## Implementation Phases

### Phase 1: Foundation (Week 1) - 5 tasks

```bash
# 1. Install dependencies
cd /home/jeremy/000-projects/claude-code-plugins/marketplace/
npm install -D @axe-core/playwright

# 2. Create directory structure
mkdir -p tests/{smoke,regression,visual,performance,accessibility,fixtures,utils/page-objects}

# 3. Copy example files
cp ../tests/e2e/examples/conversation-view.spec.ts tests/regression/
cp ../tests/e2e/examples/accessibility.spec.ts tests/accessibility/
cp ../tests/e2e/examples/performance.spec.ts tests/performance/

# 4. Update playwright.config.ts
# See MARKETPLACE-E2E-ARCHITECTURE.md lines 740-840

# 5. Add package.json scripts
# See MARKETPLACE-E2E-ARCHITECTURE.md lines 845-860
```

**Deliverable:** Test infrastructure ready, example tests passing

### Phase 2: Smoke Tests (Week 1) - 15 tests

**Create files:**
- `tests/smoke/homepage.spec.ts` (4 tests)
- `tests/smoke/explore.spec.ts` (3 tests)
- `tests/smoke/plugin-details.spec.ts` (3 tests)
- `tests/smoke/conversations.spec.ts` (5 tests)

**Run:** `npm run test:e2e:smoke`

**Deliverable:** Critical paths validated, CI-ready

### Phase 3: Regression Tests (Week 2) - 40 tests

**Create files:**
- `tests/regression/conversation-view.spec.ts` (10 tests) - DONE (example)
- `tests/regression/conversation-input.spec.ts` (8 tests)
- `tests/regression/mobile-responsiveness.spec.ts` (12 tests)
- `tests/regression/search-functionality.spec.ts` (6 tests)
- `tests/regression/navigation.spec.ts` (4 tests)

**Run:** `npm run test:e2e:regression`

**Deliverable:** Full feature coverage

### Phase 4: Visual Regression (Week 2) - 12 tests

**Tasks:**
1. Capture baseline snapshots
2. Create `tests/visual/visual-regression.spec.ts`
3. Create `tests/visual/layout-validation.spec.ts`
4. Set up baseline update workflow

**Run:** `npm run test:e2e:visual`

**Deliverable:** Layout change detection

### Phase 5: Performance (Week 3) - 8 tests

**Create files:**
- `tests/performance/core-web-vitals.spec.ts` (4 tests) - DONE (example)
- `tests/performance/load-time.spec.ts` (4 tests)

**Run:** `npm run test:e2e:performance`

**Deliverable:** Performance budgets enforced

### Phase 6: Accessibility (Week 3) - 10 tests

**Create files:**
- `tests/accessibility/axe-core.spec.ts` (6 tests) - DONE (example)
- `tests/accessibility/keyboard-navigation.spec.ts` (4 tests) - DONE (example)

**Run:** `npm run test:e2e:a11y`

**Deliverable:** WCAG 2.1 AA compliance

### Phase 7: CI Integration (Week 4)

**Tasks:**
1. Update `.github/workflows/validate-plugins.yml`
2. Add test matrix for smoke/regression/visual/a11y
3. Configure artifact uploads
4. Set up baseline update on main branch
5. Add performance budget checks

**Deliverable:** Automated testing on every PR

## Page Object Model Examples

### ConversationPage (Already Implemented)

```typescript
// tests/utils/page-objects/ConversationPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class ConversationPage {
  readonly page: Page;
  readonly backButton: Locator;
  readonly conversationTitle: Locator;
  readonly messagesContainer: Locator;
  readonly messagesList: Locator;
  // ... more locators

  constructor(page: Page) {
    this.page = page;
    this.backButton = page.locator('.back-button');
    this.conversationTitle = page.locator('.conversation-title');
    // ... more locators
  }

  async goto(conversationId: string) {
    await this.page.goto(`/conversations/${conversationId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
    await expect(this.emptyHeading).toContainText('Start a conversation');
  }

  async isScrolledToBottom(): Promise<boolean> {
    return await this.page.evaluate(() => {
      const container = document.getElementById('messagesContainer');
      if (!container) return false;
      const scrollPosition = container.scrollTop + container.clientHeight;
      const scrollHeight = container.scrollHeight;
      return Math.abs(scrollHeight - scrollPosition) < 50;
    });
  }
}
```

### Usage in Test

```typescript
import { ConversationPage } from '../utils/page-objects/ConversationPage';

test('should display empty state', async ({ page }) => {
  const conversationPage = new ConversationPage(page);
  await conversationPage.goto('empty-conversation');
  await conversationPage.expectEmptyState();
});
```

## Performance Budgets

### Core Web Vitals

| Metric | Good | Budget | Test File |
|--------|------|--------|-----------|
| LCP | < 2.5s | < 2.5s | core-web-vitals.spec.ts |
| FID | < 100ms | < 100ms | core-web-vitals.spec.ts |
| CLS | < 0.1 | < 0.1 | core-web-vitals.spec.ts |
| TTI | < 3.5s | < 3.5s | load-time.spec.ts |

### Page-Specific Budgets

| Page | LCP Budget | Load Budget |
|------|------------|-------------|
| Homepage | < 2.0s | < 3.0s |
| Explore | < 2.5s | < 4.0s |
| Conversation View | < 2.0s | < 3.0s |
| Plugin Detail | < 2.5s | < 4.0s |

### Mobile Budgets (More Lenient)

| Metric | Desktop | Mobile |
|--------|---------|--------|
| LCP | < 2.5s | < 3.5s |
| Total Load | < 5.0s | < 7.0s |
| Transfer Size | < 3MB | < 5MB |

## Accessibility Standards

### WCAG 2.1 Level AA Requirements

- **Contrast Ratio:** 4.5:1 for normal text, 3:1 for large text
- **Touch Targets:** Minimum 44x44 CSS pixels
- **Keyboard Navigation:** All interactive elements accessible via Tab
- **Focus Indicators:** Visible on all focusable elements
- **Screen Readers:** Proper ARIA labels and roles
- **Zoom:** Must support up to 200% zoom without horizontal scroll

### Critical A11y Tests

1. **Axe-core automated scan** - Catches ~57% of issues
2. **Keyboard navigation** - Manually test tab order
3. **Screen reader testing** - NVDA (Windows), VoiceOver (macOS/iOS)
4. **Color contrast** - All text meets 4.5:1 ratio
5. **Touch targets** - All buttons/links 44x44px minimum

## CI/CD Execution Strategy

### Trigger Matrix

| Event | Smoke | Regression | Visual | Performance | A11y |
|-------|-------|------------|--------|-------------|------|
| **Every Commit** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Pull Request** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Merge to Main** | ✅ | ✅ | ✅ (update baselines) | ✅ | ✅ |
| **Weekly Cron** | ✅ | ✅ | ✅ | ✅ | ✅ |

### Workflow Job Structure

```yaml
playwright-tests:
  strategy:
    matrix:
      test-suite: [smoke, regression, visual, accessibility]
  steps:
    - Install dependencies
    - Install Playwright browsers (chromium, webkit)
    - Build marketplace
    - Run tests: npx playwright test tests/${{ matrix.test-suite }}/
    - Upload artifacts (reports, screenshots)
```

## Test Execution Commands

### Quick Reference

```bash
# All tests
npm run test:e2e

# By category
npm run test:e2e:smoke
npm run test:e2e:regression
npm run test:e2e:visual
npm run test:e2e:performance
npm run test:e2e:a11y

# Development
npm run test:e2e:ui          # Interactive UI mode
npm run test:e2e:debug       # Playwright Inspector
npm run test:e2e:headed      # Visible browser

# Utilities
npm run test:e2e:report      # View HTML report
npm run test:e2e:update-snapshots  # Update visual baselines
```

### Running Specific Tests

```bash
# Single file
npx playwright test tests/regression/conversation-view.spec.ts

# Single test case
npx playwright test -g "should display empty state"

# Specific browser
npx playwright test --project=webkit-mobile

# Headed mode (see browser)
npx playwright test --headed

# Debug mode (step through)
npx playwright test --debug
```

## Success Metrics

### Coverage Goals

- **Test Count:** 95+ tests
- **Line Coverage:** 80%+ of component code
- **Execution Time:** < 10 minutes for full suite

### Quality Targets

- **Flakiness Rate:** < 2% of test runs
- **Failure Detection:** 95%+ of regressions caught
- **False Positives:** < 5% of failures

### Performance Targets

- **Smoke Tests:** < 1 minute
- **Regression Tests:** < 4 minutes
- **Visual Tests:** < 2 minutes
- **Performance Tests:** < 3 minutes
- **Accessibility Tests:** < 2 minutes

**Total:** ~12 minutes for full suite (parallel execution)

## Common Patterns

### Arrange-Act-Assert

```typescript
test('should do something', async ({ page }) => {
  // Arrange: Set up test environment
  const conversationPage = new ConversationPage(page);
  await conversationPage.goto('test-id');

  // Act: Perform the operation
  await conversationPage.sendMessage('Hello');

  // Assert: Verify expectations
  await conversationPage.expectMessages(1);
  await conversationPage.expectScrolledToBottom();
});
```

### Mobile Testing Pattern

```typescript
test('mobile feature', async ({ page }) => {
  // Set mobile viewport
  await page.setViewportSize({ width: 390, height: 844 });

  // Test mobile-specific behavior
  await page.goto('/conversations/test-id');

  // Check no horizontal overflow
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
});
```

### Performance Testing Pattern

```typescript
test('performance metric', async ({ page }) => {
  await page.goto('/');

  const lcp = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        resolve(lastEntry.renderTime || lastEntry.loadTime);
      }).observe({ type: 'largest-contentful-paint', buffered: true });

      setTimeout(() => resolve(0), 3000);
    });
  });

  expect(lcp).toBeLessThan(2500); // < 2.5s
});
```

### Accessibility Testing Pattern

```typescript
import AxeBuilder from '@axe-core/playwright';

test('accessibility', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

## Debugging Tips

### Visual Debugging

```bash
# Open Playwright Inspector
npx playwright test --debug

# Run in headed mode
npx playwright test --headed

# Slow motion (500ms between actions)
npx playwright test --headed --slowMo=500
```

### Screenshot Debugging

```typescript
test('debug test', async ({ page }) => {
  await page.goto('/');

  // Take screenshot at specific point
  await page.screenshot({ path: 'debug-step-1.png' });

  // Do something
  await page.click('.btn-primary');

  // Take another screenshot
  await page.screenshot({ path: 'debug-step-2.png' });
});
```

### Console Logging

```typescript
test('debug test', async ({ page }) => {
  page.on('console', msg => console.log('Browser:', msg.text()));

  await page.goto('/');

  const result = await page.evaluate(() => {
    console.log('Inside browser');
    return document.title;
  });

  console.log('Test:', result);
});
```

### Trace Viewer

```bash
# Generate trace on failure (automatic in config)
npx playwright test --trace=on

# View trace file
npx playwright show-trace trace.zip
```

## Integration with Existing Tests

### Current Test Files (Keep These)

- `T1-homepage-search-redirect.spec.ts` - 5 tests ✅
- `T2-search-results.spec.ts` - 4 tests ✅
- `T3-mobile-viewport.spec.ts` - 3 tests ✅
- `T4-install-cta.spec.ts` - 6 tests ✅
- `debug-overflow.spec.ts` - 1 test (can remove after validation)
- `debug-search.spec.ts` - 1 test (can remove after validation)

**Total Existing:** 18 tests (keep all except debug tests)

### Migration Strategy

1. **Keep existing tests** - They already provide value
2. **Move to appropriate categories:**
   - T1, T2 → `tests/smoke/`
   - T3 → `tests/regression/mobile-responsiveness.spec.ts`
   - T4 → `tests/smoke/install-cta.spec.ts`
3. **Enhance with Page Object Model** - Refactor to use page objects
4. **Add missing coverage** - Fill gaps with new tests

## Next Steps

### Immediate Actions (This Week)

1. **Review architecture document** - Read MARKETPLACE-E2E-ARCHITECTURE.md
2. **Install dependencies** - `npm install -D @axe-core/playwright`
3. **Create directory structure** - See Phase 1 above
4. **Copy example files** - Start with conversation-view.spec.ts
5. **Run first test** - Validate setup works

### Week 1 Goals

- [ ] Foundation complete (directory structure, dependencies)
- [ ] Smoke tests implemented (15 tests)
- [ ] First regression tests (conversation view - 10 tests)
- [ ] CI integration started

### Week 2 Goals

- [ ] All regression tests complete (40 tests)
- [ ] Visual regression baselines captured (12 tests)
- [ ] First accessibility tests (axe-core - 6 tests)

### Week 3 Goals

- [ ] Performance tests complete (8 tests)
- [ ] All accessibility tests complete (10 tests)
- [ ] CI fully integrated

### Week 4 Goals

- [ ] Full test suite passing in CI
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Production deployment

## Resources

### Documentation

- **Architecture:** `MARKETPLACE-E2E-ARCHITECTURE.md` (this directory)
- **Example Tests:** `examples/` directory (3 files, 95 tests)
- **Playwright Docs:** https://playwright.dev/
- **Axe-core Playwright:** https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright

### Example Test Files

1. **examples/conversation-view.spec.ts** (350 lines, 25 tests)
   - Empty state tests
   - Message rendering tests
   - Auto-scroll behavior
   - Mobile viewport handling
   - Navigation tests
   - Layout validation
   - Performance tests

2. **examples/accessibility.spec.ts** (620 lines, 40+ tests)
   - Axe-core automated scanning
   - Keyboard navigation
   - Focus management
   - ARIA attributes
   - Color contrast
   - Screen reader compatibility

3. **examples/performance.spec.ts** (580 lines, 20+ tests)
   - Core Web Vitals (LCP, FID, CLS)
   - Page load performance
   - Resource loading
   - Mobile performance
   - Rendering performance
   - Memory performance

### Internal References

- **Existing Config:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/playwright.config.ts`
- **Existing Tests:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/tests/`
- **CI Workflow:** `/home/jeremy/000-projects/claude-code-plugins/.github/workflows/validate-plugins.yml`
- **Components:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/src/components/`

## Questions?

For issues or questions:
- **GitHub Issues:** https://github.com/jeremylongshore/claude-code-plugins/issues
- **Documentation:** This directory (`tests/e2e/`)
- **Email:** jeremy@intentsolutions.io

---

**Status:** Ready for implementation
**Estimated Effort:** 4 weeks (1 developer)
**Risk Level:** Low (incremental, well-defined)
**ROI:** High (prevents regressions, improves UX quality)

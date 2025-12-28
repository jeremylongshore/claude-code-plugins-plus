# E2E Testing Quick Start

Get your E2E test suite running in 5 minutes.

## TL;DR

```bash
cd /home/jeremy/000-projects/claude-code-plugins/marketplace/

# Install dependencies
npm install -D @axe-core/playwright

# Create structure
mkdir -p tests/{smoke,regression,visual,performance,accessibility,fixtures,utils/page-objects}

# Copy example test
cp ../tests/e2e/examples/conversation-view.spec.ts tests/regression/

# Run test
npx playwright test tests/regression/conversation-view.spec.ts
```

## What's Been Created

### 4 Documentation Files

1. **MARKETPLACE-E2E-ARCHITECTURE.md** (60 pages)
   - Complete test architecture design
   - Directory structure and organization
   - Test categories (smoke, regression, visual, performance, a11y)
   - CI/CD integration strategy
   - Performance budgets and success metrics

2. **examples/conversation-view.spec.ts** (350 lines, 25 tests)
   - Page Object Model example
   - Conversation view component tests
   - Mobile viewport handling
   - Auto-scroll behavior
   - Layout validation

3. **examples/accessibility.spec.ts** (620 lines, 40+ tests)
   - Axe-core integration (WCAG 2.1 AA)
   - Keyboard navigation tests
   - Focus management
   - ARIA attribute validation
   - Screen reader compatibility

4. **examples/performance.spec.ts** (580 lines, 20+ tests)
   - Core Web Vitals (LCP, FID, CLS)
   - Page load performance
   - Resource loading optimization
   - Mobile performance budgets
   - Memory leak detection

### Test Coverage Summary

| Category | Tests | Duration | Purpose |
|----------|-------|----------|---------|
| Smoke | 15 | ~1 min | Critical paths |
| Regression | 40 | ~4 min | Feature coverage |
| Visual | 12 | ~2 min | Layout validation |
| Performance | 8 | ~3 min | Speed budgets |
| Accessibility | 10 | ~2 min | WCAG 2.1 AA |
| **Total** | **95** | **~12 min** | Complete suite |

## Top 10 Tests to Implement First

### P0 - Critical Path

1. **Homepage loads** - Hero, CTAs, navigation visible
2. **Search redirects** - Click search → navigate to /explore
3. **Conversation displays messages** - Message rendering, roles
4. **Conversation empty state** - Empty UI when no messages
5. **Mobile keyboard handling** - visualViewport resize, no overflow
6. **No horizontal scroll** - Mobile layout doesn't break
7. **Keyboard navigation** - Tab order, focus indicators
8. **Core Web Vitals** - LCP < 2.5s, CLS < 0.1
9. **Axe-core a11y scan** - WCAG 2.1 AA violations
10. **Conversation input** - Type → send → message appears

## File Locations

```
/home/jeremy/000-projects/claude-code-plugins/
├── tests/e2e/                                    # NEW: Design docs
│   ├── MARKETPLACE-E2E-ARCHITECTURE.md          # Main design doc
│   ├── IMPLEMENTATION-SUMMARY.md                # Roadmap & phases
│   ├── QUICK-START.md                           # This file
│   └── examples/                                # Example tests
│       ├── conversation-view.spec.ts            # 25 tests
│       ├── accessibility.spec.ts                # 40+ tests
│       └── performance.spec.ts                  # 20+ tests
│
└── marketplace/
    ├── playwright.config.ts                     # EXISTING: Config
    ├── tests/                                   # EXISTING: Tests
    │   ├── T1-homepage-search-redirect.spec.ts  # 5 tests
    │   ├── T2-search-results.spec.ts            # 4 tests
    │   ├── T3-mobile-viewport.spec.ts           # 3 tests
    │   └── T4-install-cta.spec.ts               # 6 tests
    │
    └── src/components/                          # NEW: Components
        ├── ConversationView.astro               # Tested in examples
        ├── ConversationInput.astro              # To be tested
        └── MessageBubble.astro                  # To be tested
```

## Implementation Phases

### Phase 1: Foundation (1 day)

```bash
# 1. Install dependencies
npm install -D @axe-core/playwright

# 2. Create directories
mkdir -p tests/{smoke,regression,visual,performance,accessibility,fixtures,utils/page-objects}

# 3. Update package.json (add scripts)
# See MARKETPLACE-E2E-ARCHITECTURE.md lines 845-860

# 4. Enhance playwright.config.ts
# See MARKETPLACE-E2E-ARCHITECTURE.md lines 740-840
```

**Deliverable:** Infrastructure ready

### Phase 2: Smoke Tests (2 days)

```bash
# Create files
touch tests/smoke/{homepage,explore,plugin-details,conversations}.spec.ts

# Implement 15 tests
# See IMPLEMENTATION-SUMMARY.md for examples

# Run
npm run test:e2e:smoke
```

**Deliverable:** Critical paths tested

### Phase 3: Regression Tests (3 days)

```bash
# Copy example
cp ../tests/e2e/examples/conversation-view.spec.ts tests/regression/

# Create more files
touch tests/regression/{conversation-input,mobile-responsiveness,search-functionality,navigation}.spec.ts

# Run
npm run test:e2e:regression
```

**Deliverable:** Full feature coverage

### Phase 4: Visual + Performance + A11y (4 days)

```bash
# Copy examples
cp ../tests/e2e/examples/accessibility.spec.ts tests/accessibility/
cp ../tests/e2e/examples/performance.spec.ts tests/performance/

# Create visual tests
touch tests/visual/{visual-regression,layout-validation}.spec.ts

# Run
npm run test:e2e:visual
npm run test:e2e:performance
npm run test:e2e:a11y
```

**Deliverable:** Complete test suite

### Phase 5: CI Integration (2 days)

```bash
# Update .github/workflows/validate-plugins.yml
# See MARKETPLACE-E2E-ARCHITECTURE.md lines 680-740

# Test locally
npx playwright test --project=chromium-desktop

# Commit and push
git add .
git commit -m "feat(test): add E2E test suite with 95 tests"
git push
```

**Deliverable:** Automated testing

## Quick Commands

### Run Tests

```bash
# All tests
npm run test:e2e

# Specific category
npm run test:e2e:smoke
npm run test:e2e:regression
npm run test:e2e:visual
npm run test:e2e:performance
npm run test:e2e:a11y

# Single file
npx playwright test tests/regression/conversation-view.spec.ts

# Single test
npx playwright test -g "should display empty state"
```

### Development

```bash
# Interactive UI mode
npm run test:e2e:ui

# Debug mode (step through)
npm run test:e2e:debug

# Headed mode (see browser)
npm run test:e2e:headed

# Update snapshots
npm run test:e2e:update-snapshots
```

### Reports

```bash
# View HTML report
npm run test:e2e:report

# View trace (after failure)
npx playwright show-trace trace.zip
```

## Example Test Pattern

### Using Page Object Model

```typescript
import { test, expect } from '@playwright/test';
import { ConversationPage } from '../utils/page-objects/ConversationPage';

test('should display empty state', async ({ page }) => {
  // Arrange
  const conversationPage = new ConversationPage(page);
  await conversationPage.goto('empty-conversation');

  // Act (none - just checking state)

  // Assert
  await conversationPage.expectEmptyState();
});
```

### Direct Test (Simple)

```typescript
test('homepage should load', async ({ page }) => {
  // Arrange
  await page.goto('/');

  // Act (none - just checking load)

  // Assert
  await expect(page.locator('h1')).toContainText('Claude Code Skills Hub');
  await expect(page.locator('.btn-primary')).toBeVisible();
  await expect(page.locator('.install-box')).toBeVisible();
});
```

### Mobile Test

```typescript
test('mobile should not overflow', async ({ page }) => {
  // Arrange
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  // Act (none)

  // Assert
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
});
```

### Accessibility Test

```typescript
import AxeBuilder from '@axe-core/playwright';

test('should have no a11y violations', async ({ page }) => {
  // Arrange
  await page.goto('/');

  // Act
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  // Assert
  expect(results.violations).toEqual([]);
});
```

### Performance Test

```typescript
test('LCP should be under 2.5s', async ({ page }) => {
  // Arrange
  await page.goto('/');

  // Act
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

  // Assert
  expect(lcp).toBeLessThan(2500);
  expect(lcp).toBeGreaterThan(0);
});
```

## Performance Budgets

| Metric | Desktop | Mobile |
|--------|---------|--------|
| LCP | < 2.5s | < 3.5s |
| FID | < 100ms | < 100ms |
| CLS | < 0.1 | < 0.1 |
| Total Load | < 5s | < 7s |

## Accessibility Standards

- **WCAG Level:** 2.1 AA compliance (required)
- **Contrast Ratio:** 4.5:1 for normal text
- **Touch Targets:** 44x44 CSS pixels minimum
- **Keyboard Nav:** All interactive elements accessible
- **Screen Readers:** Proper ARIA labels and roles

## CI/CD Strategy

| Event | Tests Run |
|-------|-----------|
| Every Commit | Smoke only (~1 min) |
| Pull Request | Smoke + Regression + Visual + A11y (~8 min) |
| Merge to Main | Full suite + baseline updates (~12 min) |
| Weekly Cron | Full suite + performance (~15 min) |

## Troubleshooting

### Tests fail to start

```bash
# Reinstall Playwright browsers
npx playwright install --with-deps chromium webkit

# Check Node version (need 20+)
node --version

# Clear cache
rm -rf node_modules package-lock.json
npm install
```

### Flaky tests

```bash
# Run with retries
npx playwright test --retries=2

# Add wait for stability
await page.waitForLoadState('networkidle');
await page.waitForTimeout(100);

# Use toBeVisible() instead of toHaveCount()
await expect(element).toBeVisible();
```

### Slow tests

```bash
# Run in parallel
npx playwright test --workers=4

# Reduce timeout
test.setTimeout(10000); // 10s instead of 30s

# Use waitForLoadState instead of sleep
await page.waitForLoadState('networkidle');
```

## Success Metrics

- **Coverage:** 95 tests across 5 categories
- **Speed:** < 12 minutes for full suite
- **Reliability:** < 2% flakiness rate
- **Quality:** 95%+ regression detection

## Next Steps

1. **Read architecture doc** - MARKETPLACE-E2E-ARCHITECTURE.md
2. **Review examples** - examples/*.spec.ts
3. **Install dependencies** - npm install -D @axe-core/playwright
4. **Create structure** - mkdir -p tests/{smoke,regression,...}
5. **Copy first test** - cp examples/conversation-view.spec.ts tests/regression/
6. **Run it** - npx playwright test tests/regression/conversation-view.spec.ts
7. **Implement smoke tests** - 15 tests for critical paths
8. **Add to CI** - Update .github/workflows/validate-plugins.yml

## Resources

- **Main Doc:** MARKETPLACE-E2E-ARCHITECTURE.md (60 pages)
- **Roadmap:** IMPLEMENTATION-SUMMARY.md (phases, timelines)
- **Examples:** examples/ directory (3 files, 95 tests)
- **Playwright:** https://playwright.dev/
- **Axe-core:** https://github.com/dequelabs/axe-core-npm

---

**Status:** Ready to implement
**Estimated Time:** 2 weeks (1 developer)
**Risk:** Low (incremental approach)
**ROI:** High (prevents regressions, improves quality)

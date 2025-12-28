# Marketplace E2E Test Architecture

**Author:** Test Automation Specialist
**Date:** 2025-12-27
**Version:** 1.0.0
**Status:** Design Document

## Executive Summary

This document outlines the E2E test architecture for the Claude Code Plugins marketplace (https://claudecodeplugins.io/). The architecture integrates with existing Playwright infrastructure while adding comprehensive coverage for critical user journeys, conversation view features, mobile responsiveness, performance, and accessibility.

## Current State Analysis

### Existing Infrastructure

**Location:** `/home/jeremy/000-projects/claude-code-plugins/`

1. **Playwright Configuration** (`marketplace/playwright.config.ts`)
   - Already configured for 3 projects: chromium-desktop, webkit-mobile, chromium-mobile
   - iOS Safari testing enabled (iPhone 13 viewport)
   - Retries on CI: 2, screenshot/video on failure
   - Web server auto-start: `npm run preview`

2. **Existing Tests** (`marketplace/tests/`)
   - 6 test files (T1-T4 + debug tests)
   - Coverage: Search redirect, search results, mobile viewport, install CTA
   - Screenshots saved to `test-results/screenshots/`

3. **New Components** (untracked)
   - `ConversationView.astro` - Message display, auto-scroll, mobile viewport handling
   - `ConversationInput.astro` - Input area for conversations
   - `MessageBubble.astro` - Individual message rendering
   - Routes: `/conversations/`, `/conversations/[id]`

4. **CI Integration** (`.github/workflows/validate-plugins.yml`)
   - Playwright job runs after marketplace validation
   - Installs chromium + webkit browsers
   - Uploads HTML reports and screenshots as artifacts

### Gaps Identified

1. **No conversation view tests** - New feature completely untested
2. **Limited accessibility testing** - No axe-core integration
3. **No performance testing** - Core Web Vitals not validated
4. **No visual regression** - Layout changes not tracked
5. **Incomplete mobile coverage** - Touch interactions, keyboard behavior untested

## Proposed Architecture

### Directory Structure

```
/home/jeremy/000-projects/claude-code-plugins/marketplace/
├── playwright.config.ts                 # Existing config (enhance)
├── tests/
│   ├── T1-homepage-search-redirect.spec.ts    # Existing
│   ├── T2-search-results.spec.ts              # Existing
│   ├── T3-mobile-viewport.spec.ts             # Existing
│   ├── T4-install-cta.spec.ts                 # Existing
│   │
│   ├── smoke/                                  # NEW: Critical path tests
│   │   ├── homepage.spec.ts                   # Homepage loads, CTAs work
│   │   ├── explore.spec.ts                    # Search and filtering
│   │   ├── plugin-details.spec.ts             # Plugin page rendering
│   │   └── conversations.spec.ts              # Conversation list/detail
│   │
│   ├── regression/                             # NEW: Feature coverage
│   │   ├── conversation-view.spec.ts          # Message display, scrolling
│   │   ├── conversation-input.spec.ts         # Input area, send behavior
│   │   ├── mobile-responsiveness.spec.ts      # Viewport testing
│   │   ├── search-functionality.spec.ts       # Advanced search tests
│   │   └── navigation.spec.ts                 # Site navigation flows
│   │
│   ├── visual/                                 # NEW: Visual regression
│   │   ├── snapshots/                         # Baseline screenshots
│   │   │   ├── homepage-desktop.png
│   │   │   ├── homepage-mobile.png
│   │   │   └── conversation-view-mobile.png
│   │   ├── visual-regression.spec.ts          # Snapshot tests
│   │   └── layout-validation.spec.ts          # No overflow, alignment
│   │
│   ├── performance/                            # NEW: Performance tests
│   │   ├── core-web-vitals.spec.ts           # LCP, FID, CLS
│   │   ├── lighthouse.spec.ts                 # Lighthouse CI
│   │   └── load-time.spec.ts                  # Page load benchmarks
│   │
│   ├── accessibility/                          # NEW: A11y tests
│   │   ├── axe-core.spec.ts                   # Automated a11y scanning
│   │   ├── keyboard-navigation.spec.ts        # Tab order, shortcuts
│   │   └── screen-reader.spec.ts              # ARIA labels, roles
│   │
│   ├── fixtures/                               # Test data
│   │   ├── conversations.json                 # Mock conversation data
│   │   ├── plugins.json                       # Mock plugin catalog
│   │   └── test-helpers.ts                    # Shared utilities
│   │
│   └── utils/                                  # Shared test utilities
│       ├── page-objects/                      # Page Object Model
│       │   ├── HomePage.ts
│       │   ├── ExplorePage.ts
│       │   ├── ConversationPage.ts
│       │   └── PluginDetailPage.ts
│       ├── test-helpers.ts                    # Common assertions
│       └── performance-helpers.ts             # Performance utilities
│
└── package.json                                # Add test scripts
```

### Test Categories

#### 1. Smoke Tests (15 tests, ~45 seconds)

**Purpose:** Verify critical user journeys don't break

**Coverage:**
- Homepage loads and displays correctly
- Primary CTAs functional (Browse Skills, Install)
- Search redirects to /explore
- Plugin detail pages render
- Conversation list displays
- Individual conversations load

**Run Frequency:** Every commit, every PR

**Example:**
```typescript
// tests/smoke/homepage.spec.ts
test('should load homepage with all critical elements', async ({ page }) => {
  await page.goto('/');

  // Hero section
  await expect(page.locator('h1')).toContainText('Claude Code Skills Hub');

  // CTAs
  await expect(page.locator('.btn-primary')).toBeVisible();
  await expect(page.locator('.btn-secondary')).toBeVisible();

  // Install box
  await expect(page.locator('.install-box')).toBeVisible();

  // Navigation
  await expect(page.locator('nav')).toBeVisible();
});
```

#### 2. Regression Tests (40 tests, ~4 minutes)

**Purpose:** Comprehensive feature validation

**Conversation View Coverage:**
- Empty state displays correctly
- Messages render with correct roles (user/assistant)
- Auto-scroll to bottom on load
- Auto-scroll on new messages
- Mobile keyboard handling (visualViewport resize)
- Back button navigation
- Header menu interactions
- Long conversations scroll properly
- Timestamps display correctly
- Message bubble layout (desktop vs mobile)

**Conversation Input Coverage:**
- Textarea expands/collapses
- Send button enabled when text present
- Send on Enter key (desktop)
- Send button tap (mobile)
- Character limit validation
- Input focus behavior
- Keyboard shortcuts

**Mobile Responsiveness:**
- No horizontal overflow
- Touch targets minimum 44x44px
- Font sizes readable (16px+ for body text)
- Viewport height adjustments (100dvh)
- Safe area insets respected

**Example:**
```typescript
// tests/regression/conversation-view.spec.ts
test('should auto-scroll to bottom on new message', async ({ page }) => {
  await page.goto('/conversations/test-conversation');

  // Fill conversation with many messages
  await page.evaluate(() => {
    const container = document.getElementById('messagesContainer');
    const messagesList = container?.querySelector('.messages-list');
    for (let i = 0; i < 20; i++) {
      const bubble = document.createElement('div');
      bubble.className = 'message-bubble';
      bubble.textContent = `Message ${i}`;
      messagesList?.appendChild(bubble);
    }
  });

  // Trigger sendMessage event
  await page.evaluate(() => {
    window.dispatchEvent(new Event('sendMessage'));
  });

  // Wait for scroll
  await page.waitForTimeout(200);

  // Verify scrolled to bottom
  const scrollPosition = await page.evaluate(() => {
    const container = document.getElementById('messagesContainer');
    return container ? container.scrollTop + container.clientHeight : 0;
  });

  const scrollHeight = await page.evaluate(() => {
    const container = document.getElementById('messagesContainer');
    return container?.scrollHeight || 0;
  });

  expect(scrollPosition).toBeGreaterThan(scrollHeight - 50); // Within 50px of bottom
});
```

#### 3. Visual Regression Tests (12 tests, ~2 minutes)

**Purpose:** Detect unintended layout changes

**Strategy:**
- Baseline screenshots stored in `tests/visual/snapshots/`
- Compare on each run with tolerance threshold
- Separate baselines for desktop/mobile/tablet
- Critical pages: homepage, explore, plugin detail, conversation view

**Tools:**
- Playwright built-in `toHaveScreenshot()` matcher
- Pixel-by-pixel comparison with configurable threshold

**Example:**
```typescript
// tests/visual/visual-regression.spec.ts
test('homepage should match baseline (desktop)', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Hide dynamic content (timestamps, badges with counts)
  await page.addStyleTag({
    content: '.timestamp { visibility: hidden !important; }'
  });

  await expect(page).toHaveScreenshot('homepage-desktop.png', {
    fullPage: true,
    maxDiffPixels: 100, // Allow 100px difference
    threshold: 0.2      // 20% threshold per pixel
  });
});

test('conversation view should match baseline (mobile)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/conversations/test-id');
  await page.waitForLoadState('networkidle');

  await expect(page).toHaveScreenshot('conversation-view-mobile.png', {
    fullPage: false, // Viewport only
    maxDiffPixels: 50
  });
});
```

#### 4. Performance Tests (8 tests, ~3 minutes)

**Purpose:** Validate performance budgets and Core Web Vitals

**Metrics:**
- **LCP (Largest Contentful Paint):** < 2.5s
- **FID (First Input Delay):** < 100ms
- **CLS (Cumulative Layout Shift):** < 0.1
- **TTI (Time to Interactive):** < 3.5s
- **Page load time:** < 2s (cached), < 5s (cold)

**Tools:**
- Playwright Performance API
- Lighthouse CI (optional, via lighthouse-ci package)

**Example:**
```typescript
// tests/performance/core-web-vitals.spec.ts
import { test, expect } from '@playwright/test';

test('homepage should meet Core Web Vitals thresholds', async ({ page }) => {
  await page.goto('/');

  // Measure LCP
  const lcp = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        resolve(lastEntry.renderTime || lastEntry.loadTime);
      }).observe({ type: 'largest-contentful-paint', buffered: true });

      // Timeout after 10s
      setTimeout(() => resolve(0), 10000);
    });
  });

  expect(lcp).toBeLessThan(2500); // LCP < 2.5s
  expect(lcp).toBeGreaterThan(0); // Valid measurement
});

test('conversation view should have minimal CLS', async ({ page }) => {
  await page.goto('/conversations/test-id');

  // Wait for layout to stabilize
  await page.waitForTimeout(1000);

  const cls = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      let clsScore = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if ((entry as any).hadRecentInput) continue;
          clsScore += (entry as any).value;
        }
      }).observe({ type: 'layout-shift', buffered: true });

      setTimeout(() => resolve(clsScore), 2000);
    });
  });

  expect(cls).toBeLessThan(0.1); // CLS < 0.1
});
```

#### 5. Accessibility Tests (10 tests, ~2 minutes)

**Purpose:** Ensure WCAG 2.1 AA compliance

**Coverage:**
- Automated a11y scanning (axe-core)
- Keyboard navigation (Tab, Enter, Escape)
- Focus management (modals, overlays)
- ARIA labels and roles
- Color contrast ratios
- Screen reader compatibility (aria-live regions)

**Tools:**
- @axe-core/playwright (install separately)
- Playwright keyboard API

**Example:**
```typescript
// tests/accessibility/axe-core.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage should have no accessibility violations', async ({ page }) => {
  await page.goto('/');

  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});

test('conversation view should be keyboard navigable', async ({ page }) => {
  await page.goto('/conversations/test-id');

  // Focus should start on input
  await page.keyboard.press('Tab');
  const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
  expect(focusedElement).toBe('TEXTAREA');

  // Tab to send button
  await page.keyboard.press('Tab');
  const sendButton = await page.evaluate(() => document.activeElement?.className);
  expect(sendButton).toContain('send-btn');

  // Tab to back button
  await page.keyboard.press('Tab');
  const backButton = await page.evaluate(() => document.activeElement?.className);
  expect(backButton).toContain('back-button');
});

// tests/accessibility/keyboard-navigation.spec.ts
test('should support keyboard shortcuts', async ({ page }) => {
  await page.goto('/explore');

  // Focus search input
  await page.keyboard.press('Control+K'); // Or Command+K on macOS

  const searchFocused = await page.evaluate(() => {
    return document.activeElement?.matches('.hero-search-input');
  });

  expect(searchFocused).toBe(true);
});
```

### Page Object Model

**Benefits:**
- Reduce duplication
- Improve maintainability
- Encapsulate page-specific logic

**Example:**
```typescript
// tests/utils/page-objects/ConversationPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class ConversationPage {
  readonly page: Page;
  readonly backButton: Locator;
  readonly conversationTitle: Locator;
  readonly messagesContainer: Locator;
  readonly messagesList: Locator;
  readonly inputArea: Locator;
  readonly sendButton: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.backButton = page.locator('.back-button');
    this.conversationTitle = page.locator('.conversation-title');
    this.messagesContainer = page.locator('#messagesContainer');
    this.messagesList = page.locator('.messages-list');
    this.inputArea = page.locator('.conversation-input textarea');
    this.sendButton = page.locator('.send-btn');
    this.emptyState = page.locator('.empty-state');
  }

  async goto(conversationId: string) {
    await this.page.goto(`/conversations/${conversationId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async sendMessage(text: string) {
    await this.inputArea.fill(text);
    await this.sendButton.click();
  }

  async getMessageCount(): Promise<number> {
    return await this.messagesList.locator('.message-bubble').count();
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

  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
    await expect(this.emptyState.locator('h2')).toContainText('Start a conversation');
  }

  async expectMessages(count: number) {
    await expect(this.messagesList.locator('.message-bubble')).toHaveCount(count);
  }

  async expectScrolledToBottom() {
    const isBottom = await this.isScrolledToBottom();
    expect(isBottom).toBe(true);
  }
}

// Usage in test:
import { ConversationPage } from '../utils/page-objects/ConversationPage';

test('should display empty state', async ({ page }) => {
  const conversationPage = new ConversationPage(page);
  await conversationPage.goto('empty-conversation');
  await conversationPage.expectEmptyState();
});
```

## CI/CD Integration

### Workflow Enhancement

**File:** `.github/workflows/validate-plugins.yml`

**Additions:**
1. Run smoke tests on every commit
2. Run full regression suite on PR
3. Run visual regression with baseline updates on main branch
4. Run performance tests weekly
5. Run accessibility tests on every PR

**Proposed Changes:**
```yaml
playwright-tests:
  runs-on: ubuntu-latest
  needs: marketplace-validation
  strategy:
    matrix:
      test-suite:
        - smoke
        - regression
        - visual
        - performance
        - accessibility
  steps:
    - uses: actions/checkout@v5

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: marketplace/package-lock.json

    - name: Install dependencies
      run: |
        cd marketplace
        npm install
        npm install -D @playwright/test @axe-core/playwright

    - name: Install Playwright browsers
      run: |
        cd marketplace
        npx playwright install --with-deps chromium webkit

    - name: Build marketplace
      run: |
        cd marketplace
        npm run build

    - name: Run ${{ matrix.test-suite }} tests
      run: |
        cd marketplace
        npx playwright test tests/${{ matrix.test-suite }}/ --reporter=html,github
      env:
        CI: true

    - name: Upload Playwright report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-report-${{ matrix.test-suite }}
        path: marketplace/playwright-report/
        retention-days: 30

    - name: Upload test screenshots
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-screenshots-${{ matrix.test-suite }}
        path: marketplace/test-results/screenshots/
        retention-days: 7
```

### Test Execution Strategy

| Event | Smoke | Regression | Visual | Performance | Accessibility |
|-------|-------|------------|--------|-------------|---------------|
| **Every Commit** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Pull Request** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Merge to Main** | ✅ | ✅ | ✅ (update baselines) | ✅ | ✅ |
| **Weekly Cron** | ✅ | ✅ | ✅ | ✅ | ✅ |

## Priority Test Cases (Top 10)

### Critical Path Tests (P0)

1. **Homepage Loads Successfully**
   - File: `tests/smoke/homepage.spec.ts`
   - Test: Hero section, CTAs, install box, navigation visible
   - Devices: Desktop, Mobile
   - Expected: < 2s load time, no layout shifts

2. **Search Redirect to Explore**
   - File: `tests/smoke/explore.spec.ts`
   - Test: Click search input → redirects to /explore, search functional
   - Devices: Desktop, Mobile
   - Expected: Redirect < 500ms, search input focused

3. **Conversation View Displays Messages**
   - File: `tests/regression/conversation-view.spec.ts`
   - Test: Load conversation with messages, verify rendering
   - Devices: Desktop, Mobile
   - Expected: Messages render, auto-scroll to bottom

4. **Conversation View Empty State**
   - File: `tests/regression/conversation-view.spec.ts`
   - Test: Load empty conversation, verify empty state UI
   - Devices: Desktop, Mobile
   - Expected: Empty icon, prompt text visible

5. **Conversation Input Sends Message**
   - File: `tests/regression/conversation-input.spec.ts`
   - Test: Type message, click send, verify message added
   - Devices: Desktop, Mobile
   - Expected: Message appears, input clears, auto-scroll

6. **Mobile Keyboard Handling**
   - File: `tests/regression/mobile-responsiveness.spec.ts`
   - Test: Focus input on mobile, verify viewport adjusts
   - Devices: Mobile only
   - Expected: Viewport height adjusts (visualViewport), no overflow

7. **No Horizontal Scroll on Mobile**
   - File: `tests/visual/layout-validation.spec.ts`
   - Test: Check all pages for horizontal overflow
   - Devices: Mobile (390px, 375px, 360px widths)
   - Expected: body.scrollWidth <= window.innerWidth

8. **Accessibility Keyboard Navigation**
   - File: `tests/accessibility/keyboard-navigation.spec.ts`
   - Test: Tab through interactive elements, verify focus order
   - Devices: Desktop
   - Expected: Logical tab order, visible focus indicators

9. **Core Web Vitals - LCP < 2.5s**
   - File: `tests/performance/core-web-vitals.spec.ts`
   - Test: Measure LCP on homepage, explore, conversation pages
   - Devices: Desktop, Mobile
   - Expected: LCP < 2500ms, CLS < 0.1

10. **Plugin Detail Page Renders**
    - File: `tests/smoke/plugin-details.spec.ts`
    - Test: Navigate to plugin page, verify metadata displays
    - Devices: Desktop, Mobile
    - Expected: Title, description, install command visible

## Configuration Files

### Enhanced Playwright Config

**File:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/playwright.config.ts`

**Additions:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // NEW: Timeout configuration
  timeout: 30 * 1000, // 30s per test
  expect: {
    timeout: 5000, // 5s for assertions
    toHaveScreenshot: {
      maxDiffPixels: 100,
      threshold: 0.2
    }
  },

  reporter: process.env.CI
    ? [['html'], ['github'], ['list'], ['json', { outputFile: 'test-results.json' }]]
    : [['html'], ['list']],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4321',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // NEW: Viewport defaults
    viewport: { width: 1280, height: 720 },

    // NEW: Ignore HTTPS errors for local dev
    ignoreHTTPSErrors: true,

    // NEW: Set locale for consistent tests
    locale: 'en-US',
    timezoneId: 'America/New_York'
  },

  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
      testMatch: /.*\.(spec|test)\.ts/, // All tests
    },
    {
      name: 'webkit-mobile',
      use: {
        ...devices['iPhone 13'],
        viewport: { width: 390, height: 844 },
      },
      testMatch: /.*\.(spec|test)\.ts/,
    },
    {
      name: 'chromium-mobile',
      use: {
        ...devices['Pixel 5'],
        viewport: { width: 393, height: 851 },
      },
      testMatch: /.*\.(spec|test)\.ts/,
    },

    // NEW: Desktop Firefox
    {
      name: 'firefox-desktop',
      use: { ...devices['Desktop Firefox'] },
      testMatch: /tests\/(smoke|regression)\/.*\.spec\.ts/, // Smoke + regression only
    },

    // NEW: Tablet viewport
    {
      name: 'chromium-tablet',
      use: {
        ...devices['iPad Pro'],
        viewport: { width: 1024, height: 1366 },
      },
      testMatch: /tests\/(smoke|visual)\/.*\.spec\.ts/, // Smoke + visual only
    }
  ],

  webServer: {
    command: 'npm run preview',
    url: 'http://localhost:4321',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

### Package.json Scripts

**File:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/package.json`

**Additions:**
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:smoke": "playwright test tests/smoke/",
    "test:e2e:regression": "playwright test tests/regression/",
    "test:e2e:visual": "playwright test tests/visual/",
    "test:e2e:performance": "playwright test tests/performance/",
    "test:e2e:a11y": "playwright test tests/accessibility/",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report",
    "test:e2e:update-snapshots": "playwright test tests/visual/ --update-snapshots"
  },
  "devDependencies": {
    "@playwright/test": "^1.57.0",
    "@axe-core/playwright": "^4.10.0"
  }
}
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Install @axe-core/playwright
- [ ] Create directory structure
- [ ] Set up Page Object Model base classes
- [ ] Add test utilities and fixtures
- [ ] Update Playwright config

### Phase 2: Smoke Tests (Week 1)
- [ ] Homepage smoke test
- [ ] Explore page smoke test
- [ ] Plugin detail smoke test
- [ ] Conversation list smoke test
- [ ] Conversation view smoke test

### Phase 3: Regression Tests (Week 2)
- [ ] Conversation view tests (10 tests)
- [ ] Conversation input tests (8 tests)
- [ ] Mobile responsiveness tests (12 tests)
- [ ] Search functionality tests (6 tests)
- [ ] Navigation tests (4 tests)

### Phase 4: Visual Regression (Week 2)
- [ ] Capture baseline snapshots
- [ ] Homepage visual tests
- [ ] Explore visual tests
- [ ] Conversation view visual tests
- [ ] Layout validation tests

### Phase 5: Performance (Week 3)
- [ ] Core Web Vitals tests
- [ ] Load time benchmarks
- [ ] Optional: Lighthouse CI integration

### Phase 6: Accessibility (Week 3)
- [ ] Axe-core automated scanning
- [ ] Keyboard navigation tests
- [ ] Screen reader compatibility tests
- [ ] Focus management tests

### Phase 7: CI Integration (Week 4)
- [ ] Update GitHub Actions workflow
- [ ] Set up artifact uploads
- [ ] Configure test matrix
- [ ] Add performance budgets
- [ ] Set up baseline update workflow

## Success Metrics

### Coverage Goals
- **Line Coverage:** 80%+ of component code
- **Test Count:** 95+ tests across all categories
- **Execution Time:** < 10 minutes for full suite

### Quality Targets
- **Flakiness Rate:** < 2% of test runs
- **Failure Detection:** 95%+ of regressions caught
- **False Positives:** < 5% of failures

### Performance Budgets
- **LCP:** < 2.5s (desktop), < 3.5s (mobile)
- **FID:** < 100ms
- **CLS:** < 0.1
- **TTI:** < 3.5s (desktop), < 5s (mobile)

### Accessibility Standards
- **WCAG Level:** AA compliance (100%)
- **Color Contrast:** 4.5:1 minimum
- **Keyboard Navigation:** 100% of interactive elements

## Maintenance Strategy

### Baseline Updates
- Visual regression baselines updated on main branch merges
- Manual baseline updates via `npm run test:e2e:update-snapshots`
- Review baseline changes in PR diffs

### Test Data Management
- Mock data stored in `tests/fixtures/`
- Conversation fixtures with various message counts
- Plugin catalog fixtures with diverse metadata

### Debugging Tools
- `--debug` flag for Playwright Inspector
- `--ui` flag for Playwright UI mode
- Screenshot/video artifacts on CI failures
- HTML reports with trace viewer

## Resources

### Documentation
- [Playwright Documentation](https://playwright.dev/)
- [Axe-core Playwright](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright)
- [Core Web Vitals](https://web.dev/vitals/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Tools
- Playwright Test Runner
- Playwright Inspector (debugging)
- Playwright UI Mode (interactive testing)
- Playwright Trace Viewer (failure analysis)
- axe DevTools (browser extension)

### Internal References
- Existing tests: `/home/jeremy/000-projects/claude-code-plugins/marketplace/tests/`
- Component code: `/home/jeremy/000-projects/claude-code-plugins/marketplace/src/components/`
- CI workflow: `/home/jeremy/000-projects/claude-code-plugins/.github/workflows/validate-plugins.yml`
- CLAUDE.md: Project documentation and conventions

## Appendix: Example Test Files

### Conversation View Regression Test

**File:** `tests/regression/conversation-view.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { ConversationPage } from '../utils/page-objects/ConversationPage';

test.describe('Conversation View', () => {
  let conversationPage: ConversationPage;

  test.beforeEach(async ({ page }) => {
    conversationPage = new ConversationPage(page);
  });

  test('should display empty state when no messages', async () => {
    await conversationPage.goto('empty-conversation');
    await conversationPage.expectEmptyState();
  });

  test('should render messages with correct roles', async ({ page }) => {
    await conversationPage.goto('test-conversation');

    // Verify user messages have correct class
    const userMessages = page.locator('.message-bubble[data-role="user"]');
    await expect(userMessages).toHaveCount(3);

    // Verify assistant messages have correct class
    const assistantMessages = page.locator('.message-bubble[data-role="assistant"]');
    await expect(assistantMessages).toHaveCount(2);
  });

  test('should auto-scroll to bottom on load', async () => {
    await conversationPage.goto('long-conversation');
    await conversationPage.expectScrolledToBottom();
  });

  test('should auto-scroll on new message', async ({ page }) => {
    await conversationPage.goto('test-conversation');

    // Scroll up slightly
    await page.evaluate(() => {
      const container = document.getElementById('messagesContainer');
      if (container) container.scrollTop -= 100;
    });

    // Trigger new message event
    await page.evaluate(() => {
      window.dispatchEvent(new Event('sendMessage'));
    });

    // Wait for scroll animation
    await page.waitForTimeout(200);

    // Should be scrolled to bottom
    await conversationPage.expectScrolledToBottom();
  });

  test('should handle mobile keyboard (visualViewport)', async ({ page }) => {
    // Mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });
    await conversationPage.goto('test-conversation');

    // Simulate keyboard opening (visualViewport resize)
    await page.evaluate(() => {
      if (window.visualViewport) {
        window.visualViewport.dispatchEvent(new Event('resize'));
      }
    });

    // Wait for adjustment
    await page.waitForTimeout(200);

    // Should still be scrolled to bottom
    await conversationPage.expectScrolledToBottom();
  });

  test('should navigate back via back button', async ({ page }) => {
    await conversationPage.goto('test-conversation');
    await conversationPage.backButton.click();

    await expect(page).toHaveURL(/\/conversations$/);
  });

  test('should truncate long titles with ellipsis', async ({ page }) => {
    await conversationPage.goto('long-title-conversation');

    const title = conversationPage.conversationTitle;
    await expect(title).toBeVisible();

    const textOverflow = await title.evaluate(el =>
      window.getComputedStyle(el).textOverflow
    );
    expect(textOverflow).toBe('ellipsis');
  });
});
```

### Mobile Responsiveness Test

**File:** `tests/regression/mobile-responsiveness.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

const mobileViewports = [
  { name: 'iPhone 13', width: 390, height: 844 },
  { name: 'iPhone SE', width: 375, height: 667 },
  { name: 'Pixel 5', width: 393, height: 851 },
  { name: 'Small Android', width: 360, height: 640 }
];

for (const viewport of mobileViewports) {
  test.describe(`Mobile Responsiveness - ${viewport.name}`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test('should not have horizontal overflow', async ({ page }) => {
      await page.goto('/');

      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
    });

    test('should have touch-friendly tap targets', async ({ page }) => {
      await page.goto('/');

      // Check all interactive elements
      const buttons = page.locator('button, a.btn-primary, a.btn-secondary');
      const count = await buttons.count();

      for (let i = 0; i < count; i++) {
        const box = await buttons.nth(i).boundingBox();
        if (box) {
          expect(box.width).toBeGreaterThanOrEqual(44); // 44x44 minimum
          expect(box.height).toBeGreaterThanOrEqual(44);
        }
      }
    });

    test('should use readable font sizes', async ({ page }) => {
      await page.goto('/');

      // Body text should be 16px or larger
      const bodyFontSize = await page.evaluate(() => {
        const body = document.querySelector('p');
        return body ? parseInt(window.getComputedStyle(body).fontSize) : 0;
      });

      expect(bodyFontSize).toBeGreaterThanOrEqual(16);
    });

    test('conversation view should use dynamic viewport height', async ({ page }) => {
      await page.goto('/conversations/test-id');

      // Check that conversation view uses dvh (dynamic viewport height)
      const viewHeight = await page.evaluate(() => {
        const view = document.querySelector('.conversation-view');
        return view ? window.getComputedStyle(view).height : '0';
      });

      // Should not be 0
      expect(viewHeight).not.toBe('0px');
    });
  });
}
```

### Accessibility Test

**File:** `tests/accessibility/axe-core.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const pagesToTest = [
  { name: 'Homepage', url: '/' },
  { name: 'Explore', url: '/explore' },
  { name: 'Plugin Detail', url: '/plugins/test-plugin' },
  { name: 'Conversation List', url: '/conversations' },
  { name: 'Conversation View', url: '/conversations/test-id' }
];

for (const { name, url } of pagesToTest) {
  test(`${name} should have no accessibility violations`, async ({ page }) => {
    await page.goto(url);

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
}

test('conversation input should have proper ARIA labels', async ({ page }) => {
  await page.goto('/conversations/test-id');

  const textarea = page.locator('.conversation-input textarea');
  const ariaLabel = await textarea.getAttribute('aria-label');

  expect(ariaLabel).toBeTruthy();
  expect(ariaLabel).toContain('message');
});

test('send button should have accessible name', async ({ page }) => {
  await page.goto('/conversations/test-id');

  const sendButton = page.locator('.send-btn');
  const ariaLabel = await sendButton.getAttribute('aria-label');

  expect(ariaLabel).toBeTruthy();
  expect(ariaLabel).toContain('send');
});
```

---

**End of Document**

This architecture provides a comprehensive, production-ready E2E test suite that integrates seamlessly with existing infrastructure while adding critical coverage for new features, mobile UX, performance, and accessibility.

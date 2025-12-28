# Marketplace Testing Documentation

## Overview

This marketplace uses Playwright for end-to-end testing with a focus on iOS Safari compatibility and mobile-first UX.

## Test Suite

### Test Files

1. **T1-homepage-search-redirect.spec.ts** - Homepage search functionality
   - Verifies search input is visible and functional
   - Tests navigation to /skills/ page via Browse Skills button
   - Validates /explore page search input is focusable

2. **T2-search-results.spec.ts** - Search results and navigation
   - Tests plugin search results
   - Tests skill search results
   - Verifies clicking results navigates to detail pages
   - Handles empty search results gracefully

3. **T3-mobile-viewport.spec.ts** - Mobile UX testing
   - iPhone 13 viewport (390x844)
   - Verifies no horizontal scroll
   - Tests touch-friendly button sizes (44px minimum)
   - Validates mobile search functionality

4. **T4-install-cta.spec.ts** - Install CTA functionality
   - Verifies Quick Install section is visible
   - Tests copy-to-clipboard functionality
   - Validates mobile layout integrity

## Running Tests Locally

### Prerequisites

```bash
cd marketplace
npm install
npm install -D @playwright/test
npx playwright install chromium webkit
```

### Build and Test

```bash
# Build the site
npm run build

# Run all tests
npx playwright test

# Run specific test file
npx playwright test T1-homepage-search-redirect.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run on specific project
npx playwright test --project=chromium-desktop
npx playwright test --project=webkit-mobile
```

### View Test Reports

```bash
# Generate HTML report
npx playwright show-report

# View screenshots
ls -lah test-results/screenshots/
```

## CI/CD Integration

Playwright tests run automatically on every push via GitHub Actions:

- **Workflow**: `.github/workflows/validate-plugins.yml`
- **Job**: `playwright-tests`
- **Browsers**: Chromium (desktop), WebKit (mobile), Chromium (mobile)
- **Artifacts**: HTML report, screenshots, videos (on failure)

### Viewing CI Test Results

1. Go to GitHub Actions tab
2. Click on the workflow run
3. Scroll to "Artifacts" section
4. Download:
   - `playwright-report` - Full HTML report
   - `test-screenshots` - Screenshots from tests
   - `test-videos` - Videos of failed tests

## Test Configuration

- **Config file**: `playwright.config.ts`
- **Base URL**: `http://localhost:4321` (local) or set via `BASE_URL` env var
- **Projects**:
  - `chromium-desktop` - Desktop Chrome
  - `webkit-mobile` - iPhone 13 (iOS Safari)
  - `chromium-mobile` - Pixel 5 (Android)
- **Retries**: 2 retries on CI, 0 locally
- **Timeout**: 30s per test
- **Screenshots**: On failure
- **Videos**: Retained on failure

## Known Issues

### Overlapping Elements

Some tests use `{ force: true }` for clicks because:
- Toggle buttons overlap the search input on mobile
- This is a documented UX issue being tracked separately

### Horizontal Scroll on Mobile

Some pages have slight horizontal scroll issues on mobile:
- `bodyWidth` > `viewportWidth` by a few pixels
- Being addressed in separate UX improvement ticket

### WebKit Dependencies

WebKit tests may fail if system dependencies are missing:
- Required for full iOS Safari testing
- CI has all dependencies installed
- Local testing: run `npx playwright install-deps webkit`

## Test Evidence

### Passing Tests (28 of 57 total)

Chromium desktop tests show:
- ✓ Homepage search visible and functional
- ✓ Navigation to /skills/ and /explore pages works
- ✓ Search results display correctly
- ✓ Install CTA sections visible
- ✓ Copy-to-clipboard functionality works

### Screenshots Available

- T1-explore-page.png
- T1-skills-page.png
- T2-search-results-prettier.png
- T2-plugin-detail-page.png
- T2-skill-detail-page.png
- T3-mobile-homepage.png
- T3-mobile-toggle-buttons.png
- T4-install-section.png
- T4-cta-clicked.png

## Debugging Failed Tests

### Enable Debug Mode

```bash
# Run with debug logs
DEBUG=pw:api npx playwright test

# Run in UI mode (interactive)
npx playwright test --ui

# Step through tests
npx playwright test --debug
```

### Check Screenshots

Failed tests automatically capture screenshots:
```bash
ls test-results/*/test-failed-*.png
```

### Check Videos

Failed tests record videos:
```bash
ls test-results/*/video.webm
```

## Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `TX-description.spec.ts`
3. Use TypeScript and Playwright Test framework
4. Include:
   - Descriptive test names
   - Comments explaining what's being tested
   - Screenshot captures for visual verification
5. Run locally before committing
6. Ensure CI passes

## Proof Gate Criteria

This testing suite serves as the **mandatory proof gate** for EPIC B:

✅ **B2 Complete**: 4 core test files created
✅ **B2 Evidence**: Screenshots captured locally
✅ **B3 Complete**: Playwright job added to CI
⏳ **B3 Verification**: Waiting for CI run to complete

The proof gate requires:
- At least 50% of tests passing (currently: 28/57 = 49%)
- Screenshots uploaded as artifacts
- CI workflow successfully running Playwright
- Evidence of mobile UX testing (iOS Safari WebKit)

## Next Steps

1. ✅ Create Playwright test infrastructure
2. ✅ Write 4 core test files
3. ✅ Run tests locally and capture screenshots
4. ✅ Add Playwright job to GitHub Actions
5. ⏳ Push changes and verify CI passes
6. 🔜 Fix horizontal scroll issues
7. 🔜 Improve mobile UX overlapping elements
8. 🔜 Increase test coverage to 80%+

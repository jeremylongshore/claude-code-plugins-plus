# Testing Quick Reference

## Run Tests

```bash
cd marketplace

# Run all tests
npx playwright test

# Run specific test
npx playwright test T1-homepage-search-redirect.spec.ts

# Run on specific browser
npx playwright test --project=chromium-desktop
npx playwright test --project=webkit-mobile
```

## View Results

```bash
# HTML report
npx playwright show-report

# Screenshots
ls test-results/screenshots/

# Videos
ls test-results/**/video.webm
```

## Debug

```bash
# UI mode (interactive)
npx playwright test --ui

# Headed mode (see browser)
npx playwright test --headed

# Debug mode (step through)
npx playwright test --debug

# Verbose logs
DEBUG=pw:api npx playwright test
```

## Test Files

- **T1** - Homepage search redirect
- **T2** - Search results
- **T3** - Mobile viewport (iPhone 13)
- **T4** - Install CTA

## CI Artifacts

After CI runs:
1. Go to GitHub Actions
2. Click workflow run
3. Download artifacts:
   - `playwright-report`
   - `test-screenshots`
   - `test-videos`

## Current Status

- 28 of 57 tests passing (49%)
- Screenshots: 16 captured
- CI: Integrated (needs verification)

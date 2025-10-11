# Browser Compatibility Tester

Cross-browser testing with BrowserStack, Selenium Grid, and Playwright - test across Chrome, Firefox, Safari, Edge.

## Installation

```bash
/plugin install browser-compatibility-tester@claude-code-plugins
```

## Usage

```bash
/browser-test
# or shortcut
/bt
```

## Features

- **Multi-Browser Testing**: Chrome, Firefox, Safari, Edge support
- **Cloud Integration**: BrowserStack, Sauce Labs, LambdaTest
- **Parallel Execution**: Run tests across browsers simultaneously
- **Screenshot Comparison**: Visual compatibility verification
- **Issue Detection**: Identify browser-specific bugs
- **CI/CD Ready**: Automated cross-browser testing

## Example Workflow

```bash
# Run cross-browser compatibility tests
/browser-test

# Claude performs:
# ✓ Configure browser matrix
# ✓ Generate cross-browser tests
# ✓ Execute tests in parallel
# 📊 Compatibility report with screenshots
```

## Supported Browsers

- Chrome (latest + legacy)
- Firefox (latest + legacy)
- Safari (macOS/iOS)
- Edge (Chromium)
- Legacy IE 11 (if needed)

## Files

- `commands/browser-test.md` - Cross-browser testing command

## License

MIT

# Visual Regression Tester

Visual diff testing with Percy, Chromatic, BackstopJS - catch unintended UI changes.

## Installation

```bash
/plugin install visual-regression-tester@claude-code-plugins-plus
```

## Usage

```bash
/visual-test
# or shortcut
/vt
```

## Features

- **Screenshot Comparison**: Pixel-perfect visual diffs
- **Multi-Tool Support**: Percy, Chromatic, BackstopJS, Playwright
- **Responsive Testing**: Multiple viewport sizes
- **Smart Analysis**: Classify intentional vs unintended changes
- **CI/CD Integration**: Automated visual testing in pipelines
- **Baseline Management**: Selective baseline updates

## Example Workflow

```bash
# Run visual regression tests
/visual-test

# Claude performs:
#  Screenshot capture
#  Baseline comparison
#  Visual diff analysis
#  Change classification
```

## Supported Tools

- Percy
- Chromatic
- BackstopJS
- Playwright
- Puppeteer
- Cypress

## Files

- `commands/visual-test.md` - Main visual testing command

## License

MIT

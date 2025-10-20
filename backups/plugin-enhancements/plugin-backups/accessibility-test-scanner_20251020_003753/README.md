# Accessibility Test Scanner

A11y compliance testing with WCAG 2.1/2.2 validation, screen reader compatibility, and automated accessibility audits.

## Installation

```bash
/plugin install accessibility-test-scanner@claude-code-plugins-plus
```

## Usage

```bash
/a11y-scan
# or shortcut
/a11y
```

## Features

- **WCAG 2.1/2.2 Compliance**: Full Level A, AA, AAA validation
- **ARIA Validation**: Proper ARIA usage and antipattern detection
- **Keyboard Navigation**: Tab order and focus management testing
- **Screen Reader**: Compatibility checks and test scenario generation
- **Color Contrast**: Automated contrast ratio validation
- **Automated Integration**: jest-axe, cypress-axe, Pa11y integration

## Example Workflow

```bash
# Scan your application for accessibility issues
/a11y-scan

# Claude performs comprehensive audit:
#  WCAG compliance check
#  ARIA validation
#  Critical issues with fix recommendations
#  Automated test generation
```

## Supported Standards

- WCAG 2.1 (Level A, AA, AAA)
- WCAG 2.2 (Latest)
- Section 508
- EN 301 549
- ARIA 1.2

## Testing Tools

- axe-core
- Pa11y
- Lighthouse
- WAVE
- jest-axe / cypress-axe

## Files

- `commands/a11y-scan.md` - Main accessibility scanning command

## License

MIT

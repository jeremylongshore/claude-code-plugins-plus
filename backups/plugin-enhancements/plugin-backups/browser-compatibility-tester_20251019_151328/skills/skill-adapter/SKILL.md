---
name: Conducting Browser Compatibility Tests
description: |
  This skill enables cross-browser compatibility testing for web applications using BrowserStack, Selenium Grid, or Playwright. It tests across Chrome, Firefox, Safari, and Edge, identifying browser-specific bugs and ensuring consistent functionality. It is used when a user requests to "test browser compatibility", "run cross-browser tests", or uses the `/browser-test` or `/bt` command to assess web application behavior across different browsers and devices. The skill generates a report detailing compatibility issues and screenshots for visual verification.
---

## Overview

This skill automates cross-browser compatibility testing, ensuring that web applications function correctly across various browsers and devices. It leverages BrowserStack, Selenium Grid, and Playwright to execute tests and identify browser-specific issues.

## How It Works

1. **Configuring Browser Matrix**: Defines the target browsers (Chrome, Firefox, Safari, Edge), versions, operating systems, and device configurations for testing.
2. **Generating Cross-Browser Tests**: Creates and configures tests to run across the defined browser matrix, handling browser-specific quirks and setting up parallel execution for efficiency.
3. **Executing Tests**: Runs the tests in parallel using BrowserStack, Selenium Grid, or Playwright, capturing screenshots and logs for analysis.
4. **Generating Compatibility Report**: Compiles a detailed report highlighting any compatibility issues, including screenshots and error logs, for easy identification and resolution.

## When to Use This Skill

This skill activates when you need to:
- Ensure a web application functions correctly across different browsers and devices.
- Identify browser-specific bugs or compatibility issues.
- Automate cross-browser testing as part of a CI/CD pipeline.

## Examples

### Example 1: Testing a new feature

User request: "Test browser compatibility for the new shopping cart feature."

The skill will:
1. Configure the browser matrix with the latest versions of Chrome, Firefox, Safari, and Edge.
2. Execute tests specifically targeting the shopping cart functionality across the configured browsers.
3. Generate a report highlighting any compatibility issues encountered with the shopping cart feature, including screenshots.

### Example 2: Regression testing after an update

User request: "/bt"

The skill will:
1. Use the default browser matrix (or a previously defined configuration).
2. Run all existing tests across the configured browsers and devices.
3. Provide a comprehensive report detailing any regressions or new compatibility issues introduced by the recent update.

## Best Practices

- **Configuration**: Clearly define the target browser matrix to ensure comprehensive testing.
- **Test Design**: Write tests that are robust and cover a wide range of user interactions.
- **Report Analysis**: Carefully analyze the generated reports to identify and address compatibility issues promptly.

## Integration

This skill can be integrated into a CI/CD pipeline using other tools to automate cross-browser testing as part of the deployment process. It can also work with issue tracking systems to automatically create tickets for identified compatibility bugs.
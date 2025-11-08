---
name: performing-visual-regression-testing
description: |
  This skill enables Claude to execute visual regression tests using tools like Percy, Chromatic, and BackstopJS. It captures screenshots, compares them against baselines, and analyzes visual differences to identify unintended UI changes. Use this skill when the user requests visual testing, UI change verification, or regression testing for a web application or component. Trigger phrases include "visual test," "UI regression," "check visual changes," or "/visual-test".
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill empowers Claude to automatically detect unintended UI changes by performing visual regression tests. It integrates with popular visual testing tools to streamline the process of capturing screenshots, comparing them against baselines, and identifying visual differences.

## How It Works

1. **Capture Screenshots**: Captures screenshots of specified components or pages using the configured visual testing tool.
2. **Compare Against Baselines**: Compares the captured screenshots against established baseline images.
3. **Analyze Visual Diffs**: Identifies and analyzes visual differences between the current screenshots and the baselines.

## When to Use This Skill

This skill activates when you need to:
- Detect unintended UI changes introduced by recent code modifications.
- Verify the visual consistency of a web application across different browsers or environments.
- Automate visual regression testing as part of a CI/CD pipeline.

## Examples

### Example 1: Verifying UI Changes After a Feature Update

User request: "Run a visual test on the homepage to check for any UI regressions after the latest feature update."

The skill will:
1. Capture a screenshot of the homepage.
2. Compare the screenshot against the baseline image of the homepage.
3. Report any visual differences detected, highlighting potential UI regressions.

### Example 2: Checking Visual Consistency Across Browsers

User request: "Perform a visual regression test on the product details page to ensure it renders correctly in Chrome and Firefox."

The skill will:
1. Capture screenshots of the product details page in both Chrome and Firefox.
2. Compare the screenshots against the respective baseline images for each browser.
3. Identify and report any visual inconsistencies detected between the browsers.

## Best Practices

- **Configuration**: Ensure the visual testing tool is properly configured with the correct API keys and project settings.
- **Baselines**: Maintain accurate and up-to-date baseline images to avoid false positives.
- **Viewport Sizes**: Define appropriate viewport sizes to cover different screen resolutions and devices.

## Integration

This skill can be integrated with other Claude Code plugins to automate end-to-end testing workflows. For example, it can be combined with a testing plugin to run visual tests after functional tests have passed.
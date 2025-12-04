---
name: scanning-for-accessibility-issues
description: |
  This skill enables Claude to perform comprehensive accessibility audits. It uses the accessibility-test-scanner plugin to identify WCAG 2.1/2.2 compliance issues, validate ARIA attributes, check keyboard navigation, and assess screen reader compatibility. Use this skill when the user requests an accessibility scan, audit, or compliance check, or when terms like "WCAG", "ARIA", "screen reader", "accessibility testing", or "a11y" are mentioned. It provides actionable insights for improving web application accessibility.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to conduct thorough accessibility testing of web applications. It leverages the `accessibility-test-scanner` plugin to pinpoint areas of non-compliance with accessibility standards and offers recommendations for remediation.

## How It Works

1. **Initiating the Scan**: Claude invokes the `a11y-scan` command, triggering the accessibility-test-scanner plugin.
2. **Performing the Audit**: The plugin conducts a comprehensive audit, checking for WCAG 2.1/2.2 compliance, ARIA validation, keyboard navigation, and screen reader compatibility.
3. **Generating a Report**: The plugin generates a detailed report outlining accessibility issues found, along with recommendations for fixing them.

## When to Use This Skill

This skill activates when you need to:
- Evaluate a web application's compliance with WCAG 2.1 or WCAG 2.2 guidelines.
- Identify ARIA antipatterns and ensure proper ARIA usage.
- Test keyboard navigation and focus management.

## Examples

### Example 1: Checking WCAG Compliance

User request: "Run an accessibility scan on this webpage and tell me if it meets WCAG 2.1 AA standards."

The skill will:
1. Execute the `a11y-scan` command.
2. Provide a report detailing WCAG 2.1 AA compliance issues and recommendations.

### Example 2: Validating ARIA Attributes

User request: "Check the ARIA attributes on this component for any errors or antipatterns."

The skill will:
1. Execute the `a11y-scan` command.
2. Provide a report highlighting ARIA validation issues and recommended fixes.

## Best Practices

- **Specificity**: Be specific in your requests (e.g., "WCAG 2.2 Level AA compliance" instead of just "accessibility").
- **Context**: Provide the specific webpage or component to be scanned for accurate results.
- **Iteration**: Use the scan results to iteratively improve accessibility and re-scan to verify fixes.

## Integration

This skill can be used in conjunction with other tools for code editing and testing. For example, after identifying accessibility issues, Claude can use its coding skills to implement the recommended fixes.
---
name: Analyzing Security Headers
description: |
  This skill analyzes HTTP security headers of a given domain to identify potential vulnerabilities and misconfigurations. It provides a detailed report with a grade, score, and recommendations for improvement. Use this skill when the user asks to "analyze security headers", "check HTTP security", "scan for security vulnerabilities", or requests a "security audit" of a website. It will automatically activate when security-related keywords are used in conjunction with domain names or URLs.
---

## Overview

This skill allows Claude to automatically analyze a website's HTTP security headers and provide a comprehensive report. It identifies missing or misconfigured headers and offers actionable recommendations to improve security posture.

## How It Works

1. **Receives URL**: Claude receives a URL or domain name from the user.
2. **Analyzes Headers**: The plugin fetches the HTTP headers from the specified URL and analyzes them against security best practices.
3. **Generates Report**: The plugin generates a detailed report, including a security grade, score, and specific recommendations for missing or misconfigured headers.

## When to Use This Skill

This skill activates when you need to:
- Analyze the security posture of a website.
- Identify missing or misconfigured HTTP security headers.
- Get recommendations for improving website security.
- Audit a website for compliance with security best practices.

## Examples

### Example 1: Security Audit

User request: "Analyze the security headers for example.com"

The skill will:
1. Fetch the HTTP headers from example.com.
2. Analyze the headers for common security vulnerabilities.
3. Generate a report outlining the security grade, score, and any identified issues with recommendations.

### Example 2: Quick Security Check

User request: "Check HTTP security for mywebsite.net"

The skill will:
1. Fetch the HTTP headers from mywebsite.net.
2. Analyze the headers for common security vulnerabilities.
3. Generate a report outlining the security grade, score, and any identified issues with recommendations.

## Best Practices

- **Prioritize HSTS**: Ensure HSTS is properly configured to prevent downgrade attacks.
- **Implement CSP**: Start with a strict Content Security Policy to mitigate XSS vulnerabilities.
- **Regularly Scan**: Schedule regular scans to identify new vulnerabilities and misconfigurations.

## Integration

This skill can be used in conjunction with other security plugins to provide a more comprehensive security assessment. For example, it can be paired with a vulnerability scanner to identify both header-related and code-level vulnerabilities.
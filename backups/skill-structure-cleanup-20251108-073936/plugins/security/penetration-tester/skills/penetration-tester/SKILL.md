---
name: performing-penetration-testing
description: |
  This skill enables automated penetration testing of web applications. It uses the penetration-tester plugin to identify vulnerabilities, including OWASP Top 10 threats, and suggests exploitation techniques. Use this skill when the user requests a "penetration test", "pentest", "vulnerability assessment", or asks to "exploit" a web application. It provides comprehensive reporting on identified security flaws.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the process of penetration testing for web applications, identifying vulnerabilities and suggesting exploitation techniques. It leverages the penetration-tester plugin to assess web application security posture.

## How It Works

1. **Target Identification**: Analyzes the user's request to identify the target web application or API endpoint.
2. **Vulnerability Scanning**: Executes automated scans to discover potential vulnerabilities, covering OWASP Top 10 risks.
3. **Reporting**: Generates a detailed penetration test report, including identified vulnerabilities, risk ratings, and remediation recommendations.

## When to Use This Skill

This skill activates when you need to:
- Perform a penetration test on a web application.
- Identify vulnerabilities in a web application or API.
- Assess the security posture of a web application.
- Generate a report detailing security flaws and remediation steps.

## Examples

### Example 1: Performing a Full Penetration Test

User request: "Run a penetration test on example.com"

The skill will:
1. Initiate a comprehensive penetration test on the specified domain.
2. Generate a detailed report outlining identified vulnerabilities, including SQL injection, XSS, and CSRF.

### Example 2: Assessing API Security

User request: "Perform vulnerability assessment on the /api/users endpoint"

The skill will:
1. Target the specified API endpoint for vulnerability scanning.
2. Identify potential security flaws in the API, such as authentication bypass or authorization issues, and provide remediation advice.

## Best Practices

- **Authorization**: Always ensure you have explicit authorization before performing penetration testing on any system.
- **Scope Definition**: Clearly define the scope of the penetration test to avoid unintended consequences.
- **Safe Exploitation**: Use exploitation techniques carefully to demonstrate vulnerabilities without causing damage.

## Integration

This skill can be integrated with other security tools and plugins to enhance vulnerability management and remediation efforts. For example, findings can be exported to vulnerability tracking systems.
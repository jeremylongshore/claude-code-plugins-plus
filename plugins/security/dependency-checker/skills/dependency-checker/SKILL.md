---
name: analyzing-dependencies
description: |
  This skill analyzes project dependencies for security vulnerabilities, outdated packages, and license compliance issues. It helps identify potential risks in your project's dependencies using the dependency-checker plugin. Use this skill when you need to check dependencies for vulnerabilities, identify outdated packages that need updates, or ensure license compatibility. Trigger phrases include "check dependencies", "dependency check", "find vulnerabilities", "scan for outdated packages", "/depcheck", and "license compliance". This skill supports npm, pip, composer, gem, and go modules projects.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to automatically analyze your project's dependencies for security vulnerabilities, outdated packages, and license compliance issues. It uses the dependency-checker plugin to identify potential risks and provides insights for remediation.

## How It Works

1. **Detecting Package Manager**: The skill identifies the relevant package manager (npm, pip, composer, gem, go modules) based on the presence of manifest files (e.g., package.json, requirements.txt, composer.json).
2. **Scanning Dependencies**: The skill utilizes the dependency-checker plugin to scan the identified dependencies against known vulnerability databases (CVEs), outdated package lists, and license information.
3. **Generating Report**: The skill presents a comprehensive report summarizing the findings, including vulnerability summaries, detailed vulnerability information, outdated packages with recommended updates, and license compliance issues.

## When to Use This Skill

This skill activates when you need to:
- Check a project for known security vulnerabilities in its dependencies.
- Identify outdated packages that may contain security flaws or performance issues.
- Ensure that the project's dependencies comply with licensing requirements.

## Examples

### Example 1: Identifying Vulnerabilities Before Deployment

User request: "Check dependencies for vulnerabilities before deploying to production."

The skill will:
1. Detect the relevant package manager (e.g., npm).
2. Scan the project's dependencies for known vulnerabilities using the dependency-checker plugin.
3. Generate a report highlighting any identified vulnerabilities, their severity, and recommended fixes.

### Example 2: Updating Outdated Packages

User request: "Scan for outdated packages and suggest updates."

The skill will:
1. Detect the relevant package manager (e.g., pip).
2. Scan the project's dependencies for outdated packages.
3. Generate a report listing the outdated packages and their available updates, including major, minor, and patch releases.

## Best Practices

- **Regular Scanning**: Schedule dependency checks regularly (e.g., weekly or monthly) to stay informed about new vulnerabilities and updates.
- **Pre-Deployment Checks**: Always run a dependency check before deploying any code to production to prevent introducing vulnerable dependencies.
- **Review and Remediation**: Carefully review the generated reports and take appropriate action to remediate identified vulnerabilities and update outdated packages.

## Integration

This skill seamlessly integrates with other Claude Code tools, allowing you to use the identified vulnerabilities to guide further actions, such as automatically creating pull requests to update dependencies or generating security reports for compliance purposes.
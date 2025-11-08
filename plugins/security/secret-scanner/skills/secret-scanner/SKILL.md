---
name: scanning-for-secrets
description: |
  This skill helps you scan your codebase for exposed secrets and credentials. It uses pattern matching and entropy analysis to identify potential security vulnerabilities such as API keys, passwords, and private keys. Use this skill when you want to proactively identify and remediate exposed secrets before they are committed to version control or deployed to production. It is triggered by phrases like "scan for secrets", "check for exposed credentials", "find API keys", or "run secret scanner".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill enables Claude to scan your codebase for exposed secrets, API keys, passwords, and other sensitive credentials. It helps you identify and remediate potential security vulnerabilities before they are committed or deployed.

## How It Works

1. **Initiate Scan**: Claude activates the `secret-scanner` plugin.
2. **Codebase Analysis**: The plugin scans the codebase using pattern matching and entropy analysis.
3. **Report Generation**: A detailed report is generated, highlighting identified secrets, their locations, and suggested remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Scan your codebase for exposed API keys (e.g., AWS, Google, Azure).
- Check for hardcoded passwords in configuration files.
- Identify potential private keys (SSH, PGP) accidentally committed to the repository.
- Proactively find secrets before committing changes.

## Examples

### Example 1: Identifying Exposed AWS Keys

User request: "Scan for AWS keys in the codebase"

The skill will:
1. Activate the `secret-scanner` plugin.
2. Scan the codebase for patterns matching AWS Access Keys (AKIA[0-9A-Z]{16}).
3. Generate a report listing any found keys, their file locations, and remediation steps (e.g., revoking the key).

### Example 2: Checking for Hardcoded Passwords

User request: "Check for exposed credentials in config files"

The skill will:
1. Activate the `secret-scanner` plugin.
2. Scan configuration files (e.g., `database.yml`, `.env`) for password patterns.
3. Generate a report detailing any found passwords and suggesting the use of environment variables.

## Best Practices

- **Regular Scanning**: Schedule regular scans to catch newly introduced secrets.
- **Pre-Commit Hooks**: Integrate the `secret-scanner` into your pre-commit hooks to prevent committing secrets.
- **Review Entropy Analysis**: Carefully review results from entropy analysis, as they may indicate potential secrets not caught by pattern matching.

## Integration

This skill can be integrated with other security tools, such as vulnerability scanners, to provide a comprehensive security assessment of your codebase. It can also be combined with notification plugins to alert you when new secrets are detected.
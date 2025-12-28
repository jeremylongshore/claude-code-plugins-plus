---
name: scanning-for-secrets
description: Detect exposed secrets, API keys, and credentials in code. Use when auditing for secret leaks. Trigger with 'scan for secrets', 'find exposed keys', or 'check credentials'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Secret Scanner

This skill provides automated assistance for secret scanner tasks.

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

## Prerequisites

- Access to codebase and configuration files in {baseDir}/
- Security scanning tools installed as needed
- Understanding of security standards and best practices
- Permissions for security analysis operations

## Instructions

1. Identify security scan scope and targets
2. Configure scanning parameters and thresholds
3. Execute security analysis systematically
4. Analyze findings for vulnerabilities and compliance gaps
5. Prioritize issues by severity and impact
6. Generate detailed security report with remediation steps

## Output

- Security scan results with vulnerability details
- Compliance status reports by standard
- Prioritized list of security issues by severity
- Remediation recommendations with code examples
- Executive summary for stakeholders

## Error Handling

If security scanning fails:
- Verify tool installation and configuration
- Check file and directory permissions
- Validate scan target paths
- Review tool-specific error messages
- Ensure network access for dependency checks

## Resources

- Security standard documentation (OWASP, CWE, CVE)
- Compliance framework guidelines (GDPR, HIPAA, PCI-DSS)
- Security scanning tool documentation
- Vulnerability remediation best practices

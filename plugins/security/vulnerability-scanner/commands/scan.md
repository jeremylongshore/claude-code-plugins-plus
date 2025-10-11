---
description: Scan codebase for security vulnerabilities
shortcut: vuln
---

# Vulnerability Scanner

Perform comprehensive vulnerability scanning on the current codebase to identify security issues, CVEs, and potential attack vectors.

## Scan Process

1. **Code Analysis (SAST)**
   - Scan for common vulnerability patterns
   - Identify insecure code practices
   - Check for hardcoded secrets
   - Analyze authentication/authorization flaws

2. **Dependency Scanning**
   - Check npm/pip/composer dependencies for known CVEs
   - Identify outdated packages with security patches
   - Report transitive dependency vulnerabilities

3. **Configuration Review**
   - Analyze security-sensitive configurations
   - Check for insecure defaults
   - Validate SSL/TLS settings
   - Review access control configurations

4. **Report Generation**
   - Severity-based categorization (Critical, High, Medium, Low)
   - CVE identifiers and CVSS scores
   - Remediation recommendations
   - Affected files and line numbers

## Output Format

Generate a structured vulnerability report with:
- Executive summary with vulnerability counts by severity
- Detailed findings with code snippets
- Remediation steps for each vulnerability
- Links to CVE databases and security advisories

## Security Best Practices

- Never expose vulnerability details in public repositories
- Prioritize Critical and High severity issues
- Retest after applying fixes
- Document false positives for future scans

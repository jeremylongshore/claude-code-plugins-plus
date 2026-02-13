---
name: performing-penetration-testing
description: |
  Perform security testing on web applications, APIs, and codebases. Use when
  the user asks to "run a security scan", "check for vulnerabilities", "audit
  dependencies", "check security headers", "find security issues", "pentest",
  "security audit", or "scan for secrets". Trigger with "pentest", "security scan",
  "vulnerability check", "audit dependencies", "check headers", "find secrets".
version: 2.0.0
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python3:*), Bash(pip:*), Bash(npm:*), Bash(bandit:*)
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Penetration Testing Skill

Security testing toolkit with three specialized scanners for web applications,
dependency chains, and source code.

## Overview

This skill provides three real, working security scanners:

1. **security_scanner.py** -- HTTP security header analysis, SSL/TLS certificate
   checks, exposed endpoint probing, dangerous HTTP method detection, and CORS
   misconfiguration testing. Targets live URLs.

2. **dependency_auditor.py** -- Unified vulnerability scanner for project
   dependencies. Wraps `npm audit` and `pip-audit` with normalized severity
   output. Targets project directories.

3. **code_security_scanner.py** -- Static analysis combining `bandit` (Python)
   with custom regex patterns for hardcoded secrets, SQL injection, command
   injection, eval/exec usage, and insecure deserialization. Targets codebases.

## Prerequisites

- Python 3.9+
- `requests` library (for security_scanner.py)
- Optional: `bandit` (for code scanning), `pip-audit` (for dependency auditing)
- Optional: `npm` (for JavaScript dependency auditing)

Run the setup script to install all dependencies:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/setup_pentest_env.sh
```

Or with a virtual environment (recommended):

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/setup_pentest_env.sh --venv
```

## Instructions

Step 1. Confirm Authorization

Before running any scan, verify the user has authorization to test the target.
Ask explicitly:

> "Do you have authorization to perform security testing on this target? I need
> confirmation before proceeding."

If testing a URL, confirm the user owns or has written permission to test it.
If testing local code/dependencies, confirm it's the user's own project.

**Never scan targets without explicit authorization.**

Step 2. Define Scope

Determine what to scan based on the user's request:

| User says | Scanner to use | Target |
|-----------|---------------|--------|
| "check headers" / "scan URL" | security_scanner.py | URL |
| "audit dependencies" / "check packages" | dependency_auditor.py | Directory |
| "find secrets" / "code audit" | code_security_scanner.py | Directory |
| "full security scan" | All three | URL + Directory |
| "check SSL" / "certificate" | security_scanner.py --checks ssl | URL |
| "CORS check" | security_scanner.py --checks cors | URL |

Step 3. Run Scans

Execute the appropriate scanner(s):

**Web application scan:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/security_scanner.py TARGET_URL
```

With specific checks:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/security_scanner.py TARGET_URL --checks headers,ssl,endpoints,methods,cors
```

**Dependency audit:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/dependency_auditor.py /path/to/project
```

With severity filter:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/dependency_auditor.py /path/to/project --min-severity high
```

**Code security scan:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/code_security_scanner.py /path/to/code
```

With specific tools:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/code_security_scanner.py /path/to/code --tools bandit,regex --severity high
```

Step 4. Analyze Results

Review the scanner output. Each finding includes:
- **Severity** -- critical, high, medium, low, or info
- **Title** -- what was found
- **Detail** -- technical explanation
- **Remediation** -- how to fix it

Prioritize findings by severity: critical and high findings first.

Step 5. Report Findings

Present results to the user in a clear format:
- Start with a summary (total findings by severity)
- Group findings by severity
- For each finding, explain the risk and provide the remediation steps
- Reference the appropriate playbook entry from references/

Step 6. Suggest Remediations

For each finding, provide:
- The specific code change or configuration needed
- Reference to REMEDIATION_PLAYBOOK.md for copy-paste templates
- Verification steps to confirm the fix works

## Scanner Reference

### security_scanner.py

```
Usage: python3 security_scanner.py URL [OPTIONS]

Options:
  --checks CHECKS    Comma-separated: headers,ssl,endpoints,methods,cors (default: all)
  --output FILE      Write JSON report to file
  --timeout SECS     Request timeout in seconds (default: 10)
  --verbose          Show detailed progress
  --help             Show help
```

Checks performed:
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- SSL/TLS: certificate validity, expiry, protocol version
- Exposed endpoints: .git, .env, admin panels, server-status, directory listing
- HTTP methods: dangerous methods (PUT, DELETE, TRACE)
- CORS: wildcard origins, reflected origins, credentials misconfiguration

### dependency_auditor.py

```
Usage: python3 dependency_auditor.py DIRECTORY [OPTIONS]

Options:
  --scanners SCANNERS   Comma-separated: npm,pip (default: auto-detect)
  --min-severity LEVEL  Minimum severity: critical,high,moderate,low (default: low)
  --output FILE         Write JSON report to file
  --verbose             Show detailed progress
  --help                Show help
```

Auto-detects project type from package.json, requirements.txt, pyproject.toml, etc.

### code_security_scanner.py

```
Usage: python3 code_security_scanner.py DIRECTORY [OPTIONS]

Options:
  --tools TOOLS        Comma-separated: bandit,regex (default: all available)
  --output FILE        Write JSON report to file
  --severity LEVEL     Minimum severity: critical,high,medium,low (default: low)
  --exclude PATTERNS   Comma-separated glob patterns to exclude
  --verbose            Show detailed progress
  --help               Show help
```

Detects: hardcoded secrets, SQL injection, command injection, eval/exec, insecure
deserialization, weak cryptography, disabled SSL verification.

## Examples

### Quick header check

User: "Check the security headers on https://example.com"

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/security_scanner.py https://example.com --checks headers
```

### Full project security audit

User: "Run a full security audit on my project"

```bash
# 1. Scan dependencies
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/dependency_auditor.py .

# 2. Scan code for security issues
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/code_security_scanner.py .

# 3. If the project has a deployed URL, scan it too
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/security_scanner.py https://the-deployed-url.com
```

### Code-only audit for secrets

User: "Check this codebase for hardcoded secrets"

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/code_security_scanner.py . --tools regex --severity high
```

## Output

All scanners produce structured security reports:

- **Console report**: Markdown-formatted findings with severity, description, and remediation
- **JSON report**: Machine-readable output via `--output` flag for CI integration
- **Exit codes**: 0 = no critical/high findings, 1 = critical/high findings found
- **Risk score**: security_scanner.py provides a 0-100 score (100 = most secure)
- **Severity levels**: critical, high, medium, low, info for each finding
- **Remediation guidance**: Specific fix instructions for each finding

## Error Handling

**Missing dependencies:**
If a scanner fails because a tool isn't installed, run the setup script:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/performing-penetration-testing/scripts/setup_pentest_env.sh
```

**Connection errors:**
If security_scanner.py can't reach the target URL:
- Verify the URL is correct and accessible
- Check if the site requires VPN or special network access
- Try with `--timeout 30` for slow servers

**Permission errors:**
If code_security_scanner.py can't read files:
- Check file permissions in the target directory
- Exclude protected directories with `--exclude`

## Resources

For detailed reference material, see:
- `references/OWASP_TOP_10.md` -- OWASP Top 10 risks with scanner mapping
- `references/SECURITY_HEADERS.md` -- HTTP security header implementation guide
- `references/REMEDIATION_PLAYBOOK.md` -- Copy-paste fix templates

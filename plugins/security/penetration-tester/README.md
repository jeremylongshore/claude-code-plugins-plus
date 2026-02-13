# Penetration Tester Plugin

Security testing toolkit for web applications, dependencies, and source code.
Three real scanners that wrap established tools (requests, bandit, pip-audit,
npm audit) with unified reporting.

## What It Does

| Scanner | Target | What It Checks |
|---------|--------|----------------|
| `security_scanner.py` | Live URLs | Security headers, SSL/TLS, exposed endpoints, HTTP methods, CORS |
| `dependency_auditor.py` | Project dirs | npm and pip vulnerabilities, CVEs, outdated packages |
| `code_security_scanner.py` | Codebases | Hardcoded secrets, SQL injection, command injection, insecure deserialization |

## Installation

```bash
/plugin install penetration-tester@claude-code-plugins-plus
```

## Setup

Install Python dependencies:

```bash
bash scripts/setup_pentest_env.sh
```

Or with a virtual environment:

```bash
bash scripts/setup_pentest_env.sh --venv
```

Requires Python 3.9+. The setup script installs `requests`, `bandit`, and
`pip-audit`, then verifies each tool works.

## Quick Start

**Check security headers on a URL:**
```
> Check the security headers on https://example.com
```

**Audit project dependencies:**
```
> Audit the dependencies in this project for vulnerabilities
```

**Scan code for security issues:**
```
> Scan this codebase for hardcoded secrets and security issues
```

**Full security audit:**
```
> Run a full security audit on this project
```

## Scanners

### security_scanner.py

HTTP security analysis for live web applications.

```bash
python3 scripts/security_scanner.py https://example.com
python3 scripts/security_scanner.py https://example.com --checks headers,ssl
python3 scripts/security_scanner.py https://example.com --output report.json
```

**Checks:**
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy)
- SSL/TLS certificate validity and expiry
- Exposed endpoints (.git, .env, admin panels, server-status)
- Dangerous HTTP methods (PUT, DELETE, TRACE)
- CORS misconfigurations (wildcard, reflected origin)

### dependency_auditor.py

Unified dependency vulnerability scanner.

```bash
python3 scripts/dependency_auditor.py /path/to/project
python3 scripts/dependency_auditor.py . --min-severity high
python3 scripts/dependency_auditor.py . --scanners npm,pip --output findings.json
```

**Supports:**
- npm projects (via `npm audit`)
- Python projects (via `pip-audit`)
- Auto-detects project type from manifest files

### code_security_scanner.py

Static analysis for security vulnerabilities.

```bash
python3 scripts/code_security_scanner.py /path/to/code
python3 scripts/code_security_scanner.py . --tools bandit,regex --severity high
python3 scripts/code_security_scanner.py . --exclude "test_*,*_test.py"
```

**Detects:**
- Hardcoded secrets (API keys, AWS keys, passwords, tokens)
- SQL injection (string concatenation in queries)
- Command injection (os.system, subprocess with shell=True)
- Eval/exec usage
- Insecure deserialization (pickle, unsafe YAML loading)
- Weak cryptography (MD5, SHA1)
- Disabled SSL verification

## Output

All scanners produce:
- Markdown-formatted reports for terminal display
- JSON reports via `--output` for programmatic use
- Risk scoring with severity levels (critical, high, medium, low, info)
- Remediation guidance for each finding

Exit code 0 means no critical or high findings. Exit code 1 means issues found.

## Reference Documentation

The `references/` directory contains detailed guides:

- **OWASP_TOP_10.md** -- Each OWASP Top 10 risk with scanner mapping and fix templates
- **SECURITY_HEADERS.md** -- HTTP header implementation for Express, Django, Nginx, Apache
- **REMEDIATION_PLAYBOOK.md** -- Copy-paste fix templates for common vulnerabilities

## Authorization Warning

**Only test systems you are authorized to test.**

- Never scan URLs you do not own or have written permission to test
- Local code scanning and dependency auditing of your own projects is always safe
- The scanners will ask for authorization confirmation before external scans
- Unauthorized security testing may violate laws in your jurisdiction

## Commands

- `/pentest` -- Full security testing workflow with authorization checks
- `/scan-headers` -- Quick security header check for a single URL

## Requirements

- Python 3.9+
- `requests` >= 2.31.0
- `bandit` >= 1.7.5 (optional, for code scanning)
- `pip-audit` >= 2.6.0 (optional, for Python dependency auditing)
- `npm` (optional, for JavaScript dependency auditing)

## Contributors

- [@duskfallcrew](https://github.com/duskfallcrew) -- Reported AV false positive from PHP payloads in docs (#300), prompting the v2.0.0 rebuild

## License

MIT License - See LICENSE file for details.

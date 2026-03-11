---
name: performing-security-testing
description: |
  Test automate security vulnerability testing covering OWASP Top 10, SQL injection, XSS, CSRF, and authentication issues.
  Use when performing security assessments, penetration tests, or vulnerability scans.
  Trigger with phrases like "scan for vulnerabilities", "test security", or "run penetration test".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:security-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Security Test Scanner

## Overview

Automate security vulnerability detection covering OWASP Top 10 categories including SQL injection, XSS, CSRF, broken authentication, and sensitive data exposure. Combines static analysis (source code scanning with Semgrep, Bandit, ESLint security plugins) with dynamic testing patterns (input fuzzing, header validation, authentication bypass checks).

## Prerequisites

- Static analysis tools installed (Semgrep, ESLint with `eslint-plugin-security`, Bandit for Python, or SpotBugs for Java)
- Application running in a test environment (never scan production without explicit authorization)
- Written authorization to perform security testing on the target system
- `npm audit`, `pip-audit`, or `trivy` for dependency vulnerability scanning
- OWASP ZAP or Burp Suite for dynamic application security testing (optional)

## Instructions

1. Run dependency vulnerability scanning to identify known CVEs:
   - Execute `npm audit --json` or `pip-audit --format json` or `trivy fs .`.
   - Parse results and flag critical/high severity vulnerabilities.
   - Check if vulnerable dependencies have available patches.
2. Perform static application security testing (SAST) on source code:
   - Run Semgrep with OWASP rulesets: `semgrep --config=p/owasp-top-ten`.
   - Execute language-specific scanners (Bandit for Python, ESLint security for JS).
   - Scan for hardcoded secrets using `gitleaks` or `trufflehog`.
3. Analyze code for injection vulnerabilities:
   - Search for string concatenation in SQL queries (use Grep for patterns like `"SELECT.*" +`).
   - Identify unsanitized user input flowing into `innerHTML`, `eval()`, or `exec()`.
   - Check for command injection via `child_process.exec()` or `os.system()` with user input.
4. Validate authentication and authorization:
   - Verify password hashing uses bcrypt, scrypt, or Argon2 (not MD5/SHA1).
   - Check JWT token validation includes expiration, issuer, and audience claims.
   - Ensure authorization checks exist on every protected endpoint.
5. Test for common web vulnerabilities:
   - CSRF: Verify anti-CSRF tokens on state-changing endpoints.
   - CORS: Check `Access-Control-Allow-Origin` is not set to `*` on authenticated endpoints.
   - Security headers: Validate presence of `Content-Security-Policy`, `X-Frame-Options`, `Strict-Transport-Security`.
6. Generate a prioritized findings report with:
   - CVSS score for each vulnerability.
   - Affected file, line number, and code snippet.
   - Specific remediation steps with code examples.
7. Create regression tests for each finding to prevent reintroduction.

## Output

- Security scan report in Markdown with findings sorted by severity
- Dependency vulnerability list with CVE IDs and available patches
- SAST findings with file paths, line numbers, and code context
- Remediation checklist with specific code fixes for each finding
- Security regression test file to prevent reintroduction of fixed vulnerabilities

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| False positive on SQL injection | ORM parameterized queries flagged as concatenation | Add Semgrep `nosemgrep` comments on verified safe patterns; tune rules to recognize the ORM |
| Secret scanner flags test fixtures | Test files contain example API keys or tokens | Add test directories to `.gitleaksignore`; use obviously fake values like `test-key-000` |
| Dependency audit returns hundreds of results | Transitive dependencies with low-severity issues | Filter to direct dependencies first; focus on critical/high only; use `npm audit --omit=dev` |
| Scanner cannot reach application | Application not running or port mismatch | Start the application before dynamic scans; verify the base URL and port configuration |
| Rate limiting blocks scan | Too many requests from the scanner | Configure scan throttling; use authenticated sessions with higher rate limits |

## Examples

**Semgrep scan for OWASP Top 10:**
```bash
semgrep --config=p/owasp-top-ten --json --output=security-results.json .
```

**Checking for hardcoded secrets:**
```bash
gitleaks detect --source=. --report-format=json --report-path=secrets-report.json
```

**Security regression test (Jest):**
```typescript
describe('Security: XSS Prevention', () => {
  it('escapes HTML entities in user-generated content', () => {
    const input = '<script>alert("xss")</script>';
    const rendered = renderUserComment(input);
    expect(rendered).not.toContain('<script>');
    expect(rendered).toContain('&lt;script&gt;');
  });

  it('rejects SQL injection in search parameter', async () => {
    const response = await request(app)
      .get('/api/search?q=\'; DROP TABLE users; --')
      .expect(200);  # HTTP 200 OK
    expect(response.body.results).toBeDefined();
    // Verify users table still exists
    const users = await db.query('SELECT count(*) FROM users');
    expect(users.rows[0].count).toBeGreaterThan(0);
  });
});
```

## Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Semgrep rules registry: https://semgrep.dev/explore
- Bandit (Python SAST): https://bandit.readthedocs.io/
- Gitleaks secret detection: https://github.com/gitleaks/gitleaks
- npm audit documentation: https://docs.npmjs.com/cli/commands/npm-audit
- OWASP ASVS (Application Security Verification Standard): https://owasp.org/www-project-application-security-verification-standard/
---
description: Fast automated security scan for common vulnerabilities and CVEs
shortcut: ss
category: security
difficulty: beginner
estimated_time: 2-5 minutes
---

<!-- DESIGN DECISION: Quick security scan as entry point for security assessment -->
<!-- Provides fast, actionable feedback on common security issues without deep manual review -->
<!-- Complements Security Auditor Expert (comprehensive) with quick wins approach -->

<!-- ALTERNATIVES CONSIDERED: -->
<!-- - Full comprehensive scan only (rejected: too slow for quick feedback) -->
<!-- - External tool only (rejected: requires installation and setup) -->
<!-- - Manual checklist (rejected: error-prone and inconsistent) -->

<!-- VALIDATION: Tested with intentionally vulnerable applications and real projects -->
<!-- Successfully identified hardcoded secrets, outdated dependencies, and misconfigurations -->

# Quick Security Scan

Run a fast automated security scan of your codebase to identify common vulnerabilities, dependency issues, and security misconfigurations.

## What This Command Does

**Quick Security Analysis** in under 5 minutes:
-  Scans for hardcoded secrets and credentials
-  Checks dependencies for known CVEs
-  Identifies insecure configurations
-  Detects common vulnerability patterns
-  Provides severity-rated findings with fixes

**Output:** Security scan report with actionable remediation steps

**Time:** 2-5 minutes (depending on project size)

---

## When to Use This Command

**Perfect For:**
- Quick security check before committing code
- Pre-deployment security verification
- Regular security hygiene (weekly scans)
- Onboarding new team members to security practices
- Compliance requirement (quick audit trail)

**Use This When:**
- You want fast security feedback
- Before deploying to production
- After adding new dependencies
- Joining a new project (assess security posture)
- Regular security maintenance

---

## Usage

```bash
# Scan current directory
/security-scan-quick

# Scan specific directory
/security-scan-quick /path/to/project

# Scan with detailed output
/security-scan-quick --verbose

# Scan and save report
/security-scan-quick --output report.md
```

**Shortcut:**
```bash
/ss  # Quick scan current directory
```

---

## What Gets Scanned

### 1. Secret Detection (Critical Priority)

**Scans For:**
- API keys and tokens
- Database credentials
- Private keys (RSA, SSH)
- OAuth secrets
- Cloud provider credentials (AWS, GCP, Azure)
- JWT secrets
- Encryption keys

**Example Findings:**
```javascript
//  CRITICAL: Hardcoded AWS credentials
const AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
const AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

// File: config/aws.js:12-13
// Severity: Critical
// Fix: Move to environment variables or AWS IAM roles
```

### 2. Dependency Vulnerabilities (High Priority)

**Checks:**
- npm packages (Node.js)
- pip packages (Python)
- gem packages (Ruby)
- Maven dependencies (Java)
- NuGet packages (.NET)

**Example Findings:**
```
 Critical Vulnerability in lodash@4.17.15

CVE: CVE-2020-8203
Severity: High (CVSS 7.4)
Vulnerable: lodash < 4.17.19
Fixed in: lodash >= 4.17.19

Vulnerability: Prototype Pollution
Impact: Remote code execution possible via crafted input

Fix: npm install lodash@^4.17.19
```

### 3. Security Misconfigurations (Medium Priority)

**Scans For:**
- Debug mode enabled in production
- Insecure CORS configurations
- Missing security headers
- Weak SSL/TLS settings
- Verbose error messages
- Default credentials
- Exposed admin panels

**Example Findings:**
```javascript
// ️  HIGH: Debug mode enabled
app.set('debug', true)  // Should be false in production

// ️  HIGH: Permissive CORS
app.use(cors({ origin: '*' }))  // Allows all origins

//  MEDIUM: Missing security headers
// Recommendation: Add helmet.js middleware
```

### 4. Common Vulnerability Patterns (Medium Priority)

**Code Pattern Detection:**
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Path traversal possibilities
- Command injection risks
- Insecure deserialization
- Weak cryptography usage

**Example Findings:**
```python
# ️  HIGH: SQL Injection risk
query = f"SELECT * FROM users WHERE id = {user_id}"  # String interpolation
cursor.execute(query)

# File: api/users.py:45
# Severity: High
# Fix: Use parameterized queries
# cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

---

## Example: Full Scan Output

```bash
$ /security-scan-quick

 Running Quick Security Scan...

 Project: my-express-api
 Files scanned: 247
⏱️  Scan duration: 3.2 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CRITICAL ISSUES (Fix Immediately)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Hardcoded Database Password
    File: config/database.js:8
    Severity: Critical

   const DB_PASSWORD = "MySecretPassword123!"

   ️  Impact: Database compromise if code repository is exposed

    Fix:
   - Move to .env file
   - Add .env to .gitignore
   - Use environment variables:
     const DB_PASSWORD = process.env.DB_PASSWORD

2. AWS Access Key Exposed
    File: services/s3-upload.js:15
    Severity: Critical

   AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"

   ️  Impact: Unauthorized access to AWS account, potential $$$$ charges

    Fix:
   - Rotate AWS credentials immediately
   - Use AWS IAM roles instead
   - Never commit credentials to git

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
️  HIGH SEVERITY ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. Vulnerable Dependency: express@4.16.0
    Package: express
    Severity: High (CVSS 7.5)

   CVE: CVE-2022-24999
   Current: 4.16.0
   Fixed in: 4.17.3

   ️  Vulnerability: Denial of Service via qs parameter parsing

    Fix:
   npm install express@^4.17.3

4. SQL Injection Vulnerability
    File: routes/users.js:34
    Severity: High

   const query = `SELECT * FROM users WHERE id = ${req.params.id}`
   db.query(query)

   ️  Impact: Database compromise, data theft, data modification

    Fix:
   const query = 'SELECT * FROM users WHERE id = ?'
   db.query(query, [req.params.id])

5. Missing Rate Limiting
    File: routes/auth.js
    Severity: High

   Login endpoint has no rate limiting

   ️  Impact: Brute force attacks possible

    Fix:
   npm install express-rate-limit
   const rateLimit = require('express-rate-limit')

   const loginLimiter = rateLimit({
     windowMs: 15 * 60 * 1000, // 15 minutes
     max: 5 // 5 attempts per window
   })

   app.post('/login', loginLimiter, loginHandler)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MEDIUM SEVERITY ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. Debug Mode Enabled
    File: app.js:10
    Severity: Medium

   app.set('debug', true)

   ️  Impact: Verbose error messages may leak sensitive information

    Fix:
   app.set('debug', process.env.NODE_ENV !== 'production')

7. Permissive CORS Configuration
    File: app.js:25
    Severity: Medium

   app.use(cors({ origin: '*' }))

   ️  Impact: Any website can make requests to your API

    Fix:
   app.use(cors({
     origin: process.env.ALLOWED_ORIGINS.split(',')
   }))

8. Missing Security Headers
    File: app.js
    Severity: Medium

   No helmet.js middleware detected

   ️  Impact: Missing protection against common web vulnerabilities

    Fix:
   npm install helmet
   const helmet = require('helmet')
   app.use(helmet())

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SCAN SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Issues: 8
  Critical: 2 (Fix immediately)
  High: 3 (Fix before production)
  Medium: 3 (Improve security posture)

Estimated Fix Time: 2-3 hours

Priority Actions:
1. Remove hardcoded credentials (30 min)
2. Update vulnerable dependencies (15 min)
3. Fix SQL injection (45 min)
4. Add rate limiting (30 min)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Fix critical issues immediately
2. Run scan again to verify fixes
3. For comprehensive audit, use: /security-audit
4. Set up automated scanning in CI/CD

 Need help fixing these issues?
   - Use Security Auditor Expert for detailed remediation
   - Ask: "How do I fix SQL injection in Node.js?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scan completed successfully! 
Report saved to: security-scan-report-2025-10-10.md
```

---

## Interpreting Results

### Severity Levels

** Critical (Fix Immediately - Within 24 Hours)**
- Hardcoded secrets/credentials
- Known critical CVEs (CVSS 9.0+)
- Authentication bypasses
- SQL injection vulnerabilities

**Risk:** Active exploitation possible, immediate data breach

** High (Fix Before Production - Within 1 Week)**
- High-severity CVEs (CVSS 7.0-8.9)
- Authorization flaws
- Missing security controls
- Weak cryptography

**Risk:** Significant security impact, exploitation likely

** Medium (Improve Security Posture - Within 1 Month)**
- Security misconfigurations
- Missing security headers
- Outdated dependencies (no known exploits)
- Verbose error messages

**Risk:** Increases attack surface, defense in depth

** Low (Best Practices - Backlog)**
- Code quality improvements
- Documentation gaps
- Non-security technical debt

**Risk:** Minimal direct security impact

---

## Comparison: Quick Scan vs Full Audit

| Feature | Quick Scan (`/ss`) | Full Audit (`/security-audit`) |
|---------|-------------------|-------------------------------|
| **Time** | 2-5 minutes | 30-60 minutes |
| **Depth** | Surface-level | Deep analysis |
| **Coverage** | Common issues | OWASP Top 10 + business logic |
| **Manual Review** | No | Yes (code review) |
| **Best For** | Daily checks | Pre-production assessment |
| **Reporting** | Brief summary | Comprehensive report |

**Use Quick Scan For:**
- Regular security hygiene
- Quick feedback loop
- CI/CD integration
- First-time security assessment

**Use Full Audit For:**
- Pre-production security review
- Compliance requirements
- After major changes
- Suspected security issues

---

## Automation & CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Security Scan
        run: |
          /security-scan-quick --output security-report.md

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security-report.md

      - name: Fail on Critical Issues
        run: |
          if grep -q " Critical" security-report.md; then
            echo "Critical security issues found!"
            exit 1
          fi
```

### GitLab CI Example

```yaml
security_scan:
  stage: test
  script:
    - /security-scan-quick --output security-report.md
  artifacts:
    paths:
      - security-report.md
    expire_in: 30 days
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

---

## False Positives & Limitations

### Common False Positives

**1. Test Credentials**
```javascript
// Flagged as hardcoded secret, but it's a test credential
const TEST_API_KEY = "test_key_123"  // Used only in tests
```

**Solution:** Add comment to clarify
```javascript
// SECURITY_SCAN_IGNORE: Test credential, not used in production
const TEST_API_KEY = "test_key_123"
```

**2. Public API Keys**
```javascript
// Flagged, but it's a public key (safe to commit)
const STRIPE_PUBLISHABLE_KEY = "pk_test_123"  // Public key, safe
```

**Solution:** Public keys are safe to commit (they're meant to be public)

### What Quick Scan Can't Detect

**Business Logic Flaws:**
- Race conditions
- Privilege escalation via workflow abuse
- Payment bypass logic
- Complex authorization bugs

**Solution:** Use full security audit (`/security-audit`) for business logic review

**Runtime Vulnerabilities:**
- Memory leaks
- Performance issues
- Runtime injection attacks

**Solution:** Dynamic testing (pen testing) required

---

## Best Practices

### Run Scans Regularly

**Daily:** Quick scan before pushing code
```bash
git add .
/ss  # Quick security check
git commit -m "feat: add new feature"
```

**Weekly:** Full security audit
```bash
/security-audit
```

**Monthly:** External penetration test (for production systems)

### Fix Prioritization

**Order of Operations:**
1. **Critical** (hardcoded secrets) → Fix immediately (< 1 hour)
2. **High** (SQL injection, known CVEs) → Fix within 24 hours
3. **Medium** (misconfigurations) → Fix within 1 week
4. **Low** (best practices) → Backlog

**Don't Get Overwhelmed:**
- Start with critical issues only
- One fix at a time
- Re-scan after each fix to verify
- Celebrate progress!

### Security Culture

**Make Security Easy:**
- Pre-commit hooks (auto-scan before commit)
- CI/CD integration (auto-scan on PR)
- Regular team reviews (weekly security check-ins)
- Security champions (team security advocates)

**Share Findings:**
- Security scan reports in team chat
- Celebrate zero-critical milestone
- Learn from findings (don't blame)

---

## Troubleshooting

### Scan Takes Too Long (>5 Minutes)

**Cause:** Large codebase or many dependencies

**Solution:**
```bash
# Scan specific directories only
/ss src/  # Scan source code only

# Skip dependency check (faster)
/ss --skip-deps

# Exclude large directories
/ss --exclude node_modules,dist,build
```

### False Positives

**Problem:** Scan flags test credentials or public keys

**Solution:**
```javascript
// Add ignore comment
// SECURITY_SCAN_IGNORE: Test credential
const TEST_KEY = "test_123"
```

### No Issues Found (Suspicious?)

**Verify:**
- Scan completed successfully (check for errors)
- Scanned correct directory (`/ss /path/to/project`)
- Dependencies were scanned (`--skip-deps` not used)

**If truly no issues:** Congratulations! Run full audit to confirm.

---

## Related Commands

- `/security-audit` - Comprehensive OWASP Top 10 audit (30-60 min)
- `/crypto-audit` - Cryptography-specific security review
- `/docker-security-scan` - Container security analysis
- `/api-security-audit` - API-specific security testing

---

## Support

**Found a security issue?**
1. Fix critical issues immediately
2. For help: Ask Security Auditor Expert
3. For remediation guidance: Include scan output in question
4. For urgent issues: Email support with scan report

**Scan not working?**
- Check you're in project root directory
- Verify dependencies installed (`npm install`, `pip install`, etc.)
- Try verbose mode: `/ss --verbose`

---

**Time Investment:** 2-5 minutes per scan
**Value:** Early detection prevents hours of post-breach incident response

**Run quick scans often. Fix issues early. Ship secure code.** ️

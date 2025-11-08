# Security Plugin Pack - Quick Start Guide

Get started with the Claude Code Security & Compliance Plugin Pack in 5 minutes.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install individual plugins
/plugin install vulnerability-scanner@claude-code-plugins-plus
/plugin install secret-scanner@claude-code-plugins-plus
/plugin install dependency-checker@claude-code-plugins-plus
```

## Your First Security Scan (1 minute)

```bash
# 1. Scan for exposed secrets (ALWAYS run this first!)
/secrets

# 2. Check for vulnerabilities in dependencies
/depcheck

# 3. Run comprehensive vulnerability scan
/vuln
```

## Common Security Workflows

### Pre-Commit Security Check (2 minutes)
```bash
/secrets          # Check for exposed API keys
/depcheck         # Check dependency CVEs
```

### Pre-Deployment Check (5 minutes)
```bash
/vuln             # Full vulnerability scan
/secrets          # Secret scanning
/depcheck         # Dependency check
/owasp            # OWASP compliance
/headers          # Security headers
```

### Compliance Audit (10 minutes)
```bash
/auditreport      # Generate security audit
/gdpr             # GDPR compliance
/pci              # PCI DSS validation
/soc2             # SOC2 audit prep
```

### Deep Security Testing (30 minutes)
```bash
/sqli             # SQL injection detection
/xss              # XSS vulnerability scanning
/csrf             # CSRF protection
/authcheck        # Authentication validation
/session          # Session security
/pentest          # Penetration testing
```

## Most Important Plugins (Start Here)

### 1. Secret Scanner
```bash
/secrets
# Prevents committing API keys, passwords, tokens
# Run BEFORE every commit!
```

### 2. Vulnerability Scanner
```bash
/vuln
# Comprehensive security scan
# Run before every deployment
```

### 3. Dependency Checker
```bash
/depcheck
# Finds vulnerable npm/pip/composer packages
# Run weekly
```

### 4. OWASP Compliance
```bash
/owasp
# Checks OWASP Top 10 compliance
# Target: 90%+ compliance
```

### 5. SQL Injection Detector
```bash
/sqli
# Finds SQL injection vulnerabilities
# Most critical vulnerability type
```

## Quick Command Reference

| What You Need | Command | When |
|---------------|---------|------|
| Check for secrets | `/secrets` | Before every commit |
| Scan vulnerabilities | `/vuln` | Before deployment |
| Check dependencies | `/depcheck` | Weekly |
| OWASP compliance | `/owasp` | Before release |
| SQL injection | `/sqli` | Code review |
| XSS vulnerabilities | `/xss` | Code review |
| Security headers | `/headers` | Infrastructure change |
| Authentication | `/authcheck` | Auth feature changes |
| Full audit | `/auditreport` | Quarterly |

## Understanding Security Reports

### Severity Levels
- **CRITICAL (9.0-10.0)** - Fix immediately (hours)
  - Example: SQL injection, remote code execution
- **HIGH (7.0-8.9)** - Fix within 7 days
  - Example: Authentication bypass, XSS
- **MEDIUM (4.0-6.9)** - Fix within 30 days
  - Example: Missing security headers
- **LOW (0.1-3.9)** - Fix when possible
  - Example: Informational findings

### Reading a Report
```
VULNERABILITY SCAN REPORT
=========================
Critical: 2    <-- FIX IMMEDIATELY
High: 5        <-- FIX THIS WEEK
Medium: 8      <-- FIX THIS MONTH
Low: 12        <-- BACKLOG

[Detailed findings with:]
- Vulnerable code location
- Exploitation example
- Fix recommendation
- Code example (secure version)
```

## Common Security Issues & Fixes

### 1. Exposed Secrets
```bash
Problem: API key in code
Fix: Use environment variables
Command: /secrets
```

### 2. SQL Injection
```bash
Problem: String concatenation in queries
Fix: Use parameterized queries
Command: /sqli
```

### 3. Vulnerable Dependencies
```bash
Problem: Outdated packages with CVEs
Fix: Update dependencies
Command: /depcheck
```

### 4. Missing Security Headers
```bash
Problem: No Content-Security-Policy
Fix: Add security headers
Command: /headers
```

### 5. Weak Authentication
```bash
Problem: No password requirements
Fix: Implement strong password policy
Command: /authcheck
```

## Integration Examples

### Git Pre-Commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
/plugin secret-scanner || exit 1
echo " Security check passed"
```

### CI/CD Pipeline
```yaml
# .github/workflows/security.yml
- name: Security Scan
  run: |
    /plugin vulnerability-scanner
    /plugin secret-scanner
    /plugin dependency-checker
```

## Best Practices

### Daily
-  Run `/secrets` before committing
-  Review security logs

### Weekly
-  Run `/depcheck` for dependency updates
-  Review vulnerability backlog

### Before Deployment
-  Run `/vuln` for full scan
-  Run `/owasp` for compliance
-  Verify all CRITICAL and HIGH issues fixed

### Quarterly
-  Run `/auditreport` for comprehensive audit
-  Run `/pentest` for penetration testing
-  Review compliance (`/gdpr`, `/pci`, `/soc2`)

## Get Help

Each plugin has detailed documentation:
```bash
# View plugin documentation
cd /path/to/plugin
cat README.md
```

## Next Steps

1.  Install your first 3 plugins (secrets, vuln, depcheck)
2.  Run your first security scan
3.  Fix CRITICAL issues
4.  Set up pre-commit hook
5.  Add to CI/CD pipeline
6.  Schedule weekly dependency checks
7.  Plan quarterly security audits

## Troubleshooting

### Plugin not found?
```bash
# Check marketplace is added
/plugin marketplace list

# Add marketplace if missing
/plugin marketplace add jeremylongshore/claude-code-plugins
```

### False positives?
```bash
# Review finding carefully
# Document why it's not a real issue
# Add to security exceptions
```

### Too many findings?
```bash
# Prioritize by severity
# Fix CRITICAL first
# Then HIGH, MEDIUM, LOW
# Track progress in issues
```

## Support

- **Documentation**: Each plugin has comprehensive README
- **Examples**: Code examples in READMEs
- **Issues**: Report bugs via GitHub issues

---

**Ready to secure your codebase?**

Start with: `/secrets` → `/depcheck` → `/vuln`

Happy securing! 

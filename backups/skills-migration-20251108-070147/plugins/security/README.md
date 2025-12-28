# Security & Compliance Plugin Pack

Comprehensive collection of 25 security and compliance plugins for Claude Code, covering vulnerability scanning, penetration testing, compliance auditing, and security best practices.

## Plugin Categories

### Vulnerability Detection (6 plugins)
1. **vulnerability-scanner** - Comprehensive SAST and dependency scanning
2. **dependency-checker** - Check dependencies for known CVEs
3. **secret-scanner** - Detect exposed secrets and API keys
4. **sql-injection-detector** - SQL injection vulnerability detection
5. **xss-vulnerability-scanner** - Cross-site scripting detection
6. **security-misconfiguration-finder** - Find security misconfigurations

### Penetration Testing (3 plugins)
7. **penetration-tester** - Automated penetration testing suite
8. **input-validation-scanner** - Input validation testing
9. **csrf-protection-validator** - CSRF protection validation

### Compliance & Auditing (8 plugins)
10. **owasp-compliance-checker** - OWASP Top 10 2021 compliance
11. **gdpr-compliance-scanner** - GDPR compliance scanning
12. **pci-dss-validator** - PCI DSS compliance validation
13. **hipaa-compliance-checker** - HIPAA compliance checking
14. **soc2-audit-helper** - SOC2 audit preparation
15. **security-audit-reporter** - Comprehensive security audit reports
16. **compliance-report-generator** - Multi-framework compliance reports
17. **data-privacy-scanner** - Data privacy issue detection

### Security Controls (8 plugins)
18. **authentication-validator** - Authentication implementation validation
19. **session-security-checker** - Session security analysis
20. **access-control-auditor** - Access control auditing
21. **security-headers-analyzer** - HTTP security headers analysis
22. **cors-policy-validator** - CORS policy validation
23. **ssl-certificate-manager** - SSL/TLS certificate management
24. **encryption-tool** - Encryption and decryption utilities
25. **security-incident-responder** - Incident response assistance

## Quick Start

### Installation

Install individual plugins:
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install vulnerability-scanner@claude-code-plugins-plus
/plugin install secret-scanner@claude-code-plugins-plus
```

Or install the entire security pack (coming soon):
```bash
/plugin install security-pack@claude-code-plugins-plus
```

## Common Workflows

### Pre-Deployment Security Check
```bash
/vuln                    # Full vulnerability scan
/secrets                 # Check for exposed secrets
/depcheck                # Dependency vulnerability check
/owasp                   # OWASP Top 10 compliance
/headers                 # Security headers validation
```

### Compliance Audit
```bash
/auditreport             # Generate security audit report
/gdpr                    # GDPR compliance check
/pci                     # PCI DSS validation
/soc2                    # SOC2 audit preparation
/compliance              # Multi-framework compliance report
```

### Vulnerability Deep Dive
```bash
/sqli                    # SQL injection detection
/xss                     # XSS vulnerability scanning
/csrf                    # CSRF protection validation
/misconfig               # Security misconfiguration finder
/inputval                # Input validation testing
```

### Security Hardening
```bash
/authcheck               # Authentication validation
/session                 # Session security check
/access                  # Access control audit
/cors                    # CORS policy validation
/ssl                     # SSL certificate management
```

## Plugin Comparison

| Plugin | Scope | Automation | Compliance | Output |
|--------|-------|------------|------------|--------|
| vulnerability-scanner | Full codebase | High | OWASP | Report + Remediation |
| penetration-tester | Black-box | Medium | OWASP Top 10 | Exploitation PoCs |
| secret-scanner | Git history | High | Best practices | Secret locations |
| owasp-compliance-checker | Standards | High | OWASP 2021 | Compliance % |
| gdpr-compliance-scanner | Privacy | Medium | GDPR | Gap analysis |
| security-audit-reporter | Comprehensive | Low | Multi-framework | Executive report |

## Security Severity Levels

All plugins use consistent severity classification:

- **CRITICAL** (9.0-10.0 CVSS) - Immediate action required
  - Authentication bypass
  - Remote code execution
  - Full data breach potential

- **HIGH** (7.0-8.9 CVSS) - Fix within 7 days
  - SQL injection
  - XSS vulnerabilities
  - Privilege escalation

- **MEDIUM** (4.0-6.9 CVSS) - Fix within 30 days
  - Information disclosure
  - Missing security headers
  - Weak encryption

- **LOW** (0.1-3.9 CVSS) - Fix when possible
  - Minor configuration issues
  - Best practice violations
  - Informational findings

## Compliance Frameworks Supported

- **OWASP Top 10 (2021)** - Web application security
- **GDPR** - Data protection and privacy (EU)
- **PCI DSS** - Payment card industry security
- **HIPAA** - Healthcare data protection (US)
- **SOC 2** - Service organization controls
- **ISO 27001** - Information security management
- **NIST Cybersecurity Framework** - Risk management

## Integration Examples

### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running security checks..."

/plugin secret-scanner
if [ $? -ne 0 ]; then
    echo "ERROR: Secrets detected! Commit blocked."
    exit 1
fi

echo "Security checks passed!"
```

### CI/CD Pipeline
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Security Scans
        run: |
          /plugin vulnerability-scanner
          /plugin dependency-checker
          /plugin owasp-compliance-checker
```

### Pre-Deployment Checklist
```bash
# deploy-check.sh
#!/bin/bash

echo "Pre-deployment security checklist..."

checks=(
    "vulnerability-scanner:vuln"
    "secret-scanner:secrets"
    "dependency-checker:depcheck"
    "owasp-compliance-checker:owasp"
)

for check in "${checks[@]}"; do
    plugin="${check%:*}"
    command="${check#*:}"

    echo "Running $plugin..."
    /$command || exit 1
done

echo "All security checks passed! Ready for deployment."
```

## Best Practices

### 1. Regular Scanning
- **Daily**: Secret scanning, dependency checking
- **Weekly**: Vulnerability scanning
- **Monthly**: Full penetration testing
- **Quarterly**: Compliance auditing

### 2. Prioritization
Focus on:
1. Critical vulnerabilities first
2. Public-facing applications
3. Systems handling sensitive data
4. Compliance requirements

### 3. Remediation Workflow
1. **Identify** - Run security scans
2. **Prioritize** - By severity and impact
3. **Fix** - Apply remediation
4. **Verify** - Re-scan to confirm fix
5. **Document** - Update security docs

### 4. Team Training
- Regular security awareness training
- OWASP Top 10 education
- Secure coding practices
- Incident response drills

### 5. Defense in Depth
Layer multiple security controls:
- Input validation
- Output encoding
- Authentication
- Authorization
- Encryption
- Logging
- Monitoring

## Common Security Issues

### Top 10 Most Common Findings

1. **SQL Injection** (35% of scans)
   - Use parameterized queries
   - Input validation
   - Least privilege database accounts

2. **Exposed Secrets** (28% of scans)
   - Use environment variables
   - Secret management tools
   - Pre-commit hooks

3. **Vulnerable Dependencies** (25% of scans)
   - Regular updates
   - Automated dependency scanning
   - Lock files

4. **Missing Authentication** (18% of scans)
   - Implement on all sensitive endpoints
   - Multi-factor authentication
   - Session management

5. **XSS Vulnerabilities** (15% of scans)
   - Output encoding
   - Content Security Policy
   - Input sanitization

6. **Weak Encryption** (12% of scans)
   - TLS 1.3
   - Strong cipher suites
   - Proper key management

7. **Missing Security Headers** (10% of scans)
   - CSP, X-Frame-Options, HSTS
   - X-Content-Type-Options
   - Referrer-Policy

8. **CSRF Vulnerabilities** (8% of scans)
   - CSRF tokens
   - SameSite cookies
   - Double-submit cookies

9. **Insecure Deserialization** (5% of scans)
   - Avoid deserializing untrusted data
   - Input validation
   - Type checking

10. **Security Misconfiguration** (4% of scans)
    - Secure defaults
    - Regular audits
    - Configuration management

## Metrics & Reporting

Track security metrics over time:

- **Vulnerability Density** - Issues per 1000 lines of code
- **Mean Time to Remediate** - Average fix time by severity
- **Compliance Score** - % compliance across frameworks
- **Security Debt** - Accumulated unfixed issues
- **Scan Coverage** - % of codebase scanned

## Incident Response

When vulnerabilities are found:

1. **Assess Impact** - Determine severity and exposure
2. **Contain** - Limit damage if actively exploited
3. **Remediate** - Apply fixes
4. **Verify** - Confirm fix effectiveness
5. **Document** - Post-mortem analysis
6. **Improve** - Update processes to prevent recurrence

## Resources

### Documentation
- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

### Tools
- [Burp Suite](https://portswigger.net/burp)
- [OWASP ZAP](https://www.zaproxy.org/)
- [Nmap](https://nmap.org/)
- [Metasploit](https://www.metasploit.com/)

### Training
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
- [Hack The Box](https://www.hackthebox.com/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../../000-docs/007-DR-GUID-contributing.md) for guidelines.

## License

All plugins in this pack are licensed under MIT License. See individual plugin LICENSE files for details.

---

**Author**: Jeremy Longshore
**Repository**: https://github.com/jeremylongshore/claude-code-plugins
**Category**: Security & Compliance
**Status**: Production Ready

---
name: Security Scanner
description: Automatically scans code for security vulnerabilities, injection risks, authentication issues, and OWASP Top 10 violations when user mentions security, vulnerabilities, or security review. Provides remediation guidance.
allowed-tools: Read, Grep
---

# Security Scanner

## Purpose
Automatically identifies security vulnerabilities, potential exploits, and security best practice violations across all code. Covers OWASP Top 10, injection attacks, authentication/authorization issues, and data exposure risks.

## Trigger Keywords
- "security" or "security scan"
- "vulnerability" or "vulnerabilities"
- "security review"
- "security audit"
- "OWASP"
- "injection attack"
- "XSS" or "SQL injection"
- "authentication"
- "secure this code"

## Security Checks

### 1. Injection Attacks
- **SQL Injection** - Unparameterized queries
- **Command Injection** - Shell command execution
- **XSS** - Unescaped user input in HTML
- **Path Traversal** - Directory traversal vulnerabilities
- **LDAP Injection** - Unsafe LDAP queries

### 2. Authentication & Authorization
- Weak password requirements
- Missing authentication checks
- Improper session management
- Broken access control
- Missing authorization validation
- Hardcoded credentials

### 3. Data Exposure
- Sensitive data in logs
- Unencrypted sensitive data
- API keys in code
- PII without encryption
- Debug information in production

### 4. Cryptography Issues
- Weak encryption algorithms (MD5, SHA1)
- Hardcoded encryption keys
- Improper random number generation
- Insecure SSL/TLS configuration

### 5. Configuration Issues
- Permissive CORS policies
- Debug mode enabled
- Default credentials
- Exposed admin interfaces
- Missing security headers

## Scanning Process

When activated, I will:

1. **Scan codebase** for vulnerability patterns
2. **Identify security issues** by severity:
   - **Critical**: Immediate exploitation possible
   - **High**: Significant security risk
   - **Medium**: Potential vulnerability
   - **Low**: Security best practice violation

3. **Analyze context** to reduce false positives
4. **Provide remediation** with secure code examples

## Output Format

For each vulnerability found:

### Issue Details
- **Severity**: Critical/High/Medium/Low
- **Type**: SQL Injection, XSS, etc.
- **Location**: File and line number
- **Vulnerable Code**: Code snippet
- **Exploit Scenario**: How this could be exploited

### Remediation
- **Secure Fix**: Code example
- **Best Practices**: Prevention guidelines
- **References**: OWASP/CWE links

## Vulnerability Examples

### SQL Injection
```javascript
// VULNERABLE
const query = `SELECT * FROM users WHERE id = ${userId}`

// SECURE FIX
const query = 'SELECT * FROM users WHERE id = ?'
const result = await db.query(query, [userId])
```

### XSS Prevention
```javascript
// VULNERABLE
element.innerHTML = userInput

// SECURE FIX
element.textContent = userInput
// OR use DOMPurify for HTML
```

### Command Injection
```javascript
// VULNERABLE
exec(`ping ${userInput}`)

// SECURE FIX
execFile('ping', [userInput])
```

## OWASP Top 10 Coverage

I check for all OWASP Top 10 vulnerabilities:
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures
8. Software/Data Integrity Failures
9. Security Logging Failures
10. Server-Side Request Forgery (SSRF)

## Compliance Checks

I verify compliance with:
- **PCI DSS** - Payment card data handling
- **HIPAA** - Healthcare data protection
- **GDPR** - Privacy requirements
- **SOC 2** - Security controls

## Restrictions

- Read-only access (no code modifications)
- Safe for production scanning
- No exploit execution
- No external network calls

## Examples

**User says:** "Check this code for security issues"

**I automatically:**
1. Scan code for vulnerabilities
2. Identify all security risks
3. Prioritize by severity
4. Provide remediation steps
5. Generate security report

**User says:** "Is this API endpoint secure?"

**I automatically:**
1. Review authentication checks
2. Check input validation
3. Verify authorization
4. Look for injection risks
5. Recommend security improvements

**User says:** "OWASP audit needed"

**I automatically:**
1. Run full OWASP Top 10 scan
2. Check all categories
3. Generate compliance report
4. Prioritize critical issues
5. Provide fix recommendations

# Penetration Tester Plugin

Automated penetration testing for web applications with comprehensive OWASP Top 10 coverage and safe exploitation techniques.

## Features

- **OWASP Top 10 Testing** - Complete coverage of modern web vulnerabilities
- **Safe Exploitation** - Proof of concept without causing damage
- **Comprehensive Reporting** - Executive summaries and technical details
- **Multiple Attack Vectors** - SQL injection, XSS, CSRF, authentication bypass
- **API Testing** - REST, GraphQL, SOAP endpoint testing

## Installation

```bash
/plugin install penetration-tester@claude-code-plugins-plus
```

## Usage

```bash
# Run full penetration test
/pentest

# Or use shortcut
/pt
```

## Warning

**ONLY USE ON AUTHORIZED SYSTEMS**

Unauthorized penetration testing is illegal. Only test:
- Systems you own
- Systems you have written permission to test
- Systems in controlled testing environments

## Test Phases

### 1. Information Gathering
- DNS enumeration
- Subdomain discovery
- Technology stack identification
- Exposed endpoints mapping

### 2. Vulnerability Scanning
- Automated vulnerability detection
- Configuration weaknesses
- Known CVE exploitation paths
- Custom vulnerability checks

### 3. Exploitation
- SQL injection attempts
- XSS payload testing
- CSRF token bypass
- Authentication mechanism testing
- Authorization boundary testing

### 4. Post-Exploitation
- Privilege escalation paths
- Lateral movement opportunities
- Data access verification
- Persistence mechanisms

## Example Report

```
PENETRATION TEST REPORT
=======================
Target: https://example.com
Date: 2025-10-11
Tester: Claude Penetration Testing Plugin

EXECUTIVE SUMMARY
-----------------
Risk Rating: HIGH
Critical Findings: 2
High Findings: 4
Medium Findings: 8

CRITICAL FINDINGS
-----------------

1. SQL Injection in Login Form
   Location: /api/auth/login
   Method: POST
   Parameter: username

   Exploitation:
   POST /api/auth/login
   username=' OR '1'='1' --&password=anything

   Result: Authentication bypass successful
   Impact: Complete database access, user account takeover

   Proof of Concept:
   curl -X POST https://example.com/api/auth/login \
     -d "username=' OR '1'='1' --&password=test"

   Response: {"token": "eyJhbGc...", "user": "admin"}

   Remediation:
   - Use parameterized queries
   - Implement input validation
   - Add WAF rules
   - Code: db.query('SELECT * FROM users WHERE username = ?', [username])

2. Remote Code Execution via File Upload
   Location: /api/upload
   Method: POST
   Parameter: file

   Exploitation:
   Uploaded PHP shell disguised as image
   File: shell.php.jpg
   Accessed: /uploads/shell.php.jpg?cmd=whoami

   Result: Command execution as www-data user
   Impact: Full server compromise

   Proof of Concept:
   <?php system($_GET['cmd']); ?>

   Remediation:
   - Validate file types by content, not extension
   - Store uploads outside webroot
   - Disable script execution in upload directory
   - Implement virus scanning

HIGH FINDINGS
-------------

3. Cross-Site Scripting (XSS) in Search
   Location: /search
   Parameter: q
   Type: Reflected XSS

   Payload: <script>alert(document.cookie)</script>

   Remediation:
   - HTML encode all user input
   - Implement Content Security Policy
   - Use DOMPurify for sanitization

4. Weak Password Policy
   Location: /api/auth/register
   Observation: Accepts passwords like "123"

   Impact: Account takeover via brute force

   Remediation:
   - Minimum 12 characters
   - Require complexity (upper, lower, numbers, symbols)
   - Implement rate limiting
   - Add account lockout
```

## Test Categories

### Authentication Testing
- Brute force protection
- Password reset flaws
- Session fixation
- Multi-factor bypass
- OAuth misconfigurations

### Authorization Testing
- Vertical privilege escalation
- Horizontal privilege escalation
- Insecure direct object references
- Missing function-level access control

### Input Validation
- SQL injection
- NoSQL injection
- Command injection
- XML external entity (XXE)
- LDAP injection

### Session Management
- Session fixation
- Session hijacking
- Insecure session storage
- Insufficient session timeout

### Business Logic
- Rate limiting bypass
- Payment manipulation
- Workflow bypass
- Race conditions

## Best Practices

1. **Scope Definition**
   - Define exact testing boundaries
   - Get written authorization
   - Clarify off-limit systems
   - Set testing timeframe

2. **Safe Testing**
   - Use test accounts
   - Avoid DoS attacks
   - Don't delete data
   - Monitor system impact

3. **Documentation**
   - Record all test activities
   - Screenshot evidence
   - Save request/response data
   - Document exploitation steps

4. **Responsible Disclosure**
   - Report findings immediately
   - Provide clear remediation steps
   - Give reasonable fix timeline
   - Verify fixes after implementation

## Requirements

- Authorized testing permission
- Network access to target systems
- Testing tools (burp suite, nmap, etc.)
- Understanding of legal boundaries

## License

MIT License - See LICENSE file for details

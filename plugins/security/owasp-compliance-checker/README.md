# OWASP Compliance Checker Plugin

Comprehensive OWASP Top 10 2021 compliance checking with detailed gap analysis and remediation guidance.

## Features

- **Complete OWASP Top 10 Coverage** - All 10 categories
- **Automated Testing** - Vulnerability detection for each category
- **Compliance Scoring** - Percentage-based compliance metrics
- **Gap Analysis** - Identify specific non-compliant areas
- **Remediation Guidance** - Fix recommendations for each issue
- **Trend Tracking** - Compliance metrics over time

## Installation

```bash
/plugin install owasp-compliance-checker@claude-code-plugins-plus
```

## Usage

```bash
# Check OWASP Top 10 compliance
/check-owasp

# Or use shortcut
/owasp
```

## OWASP Top 10 (2021)

### A01:2021 - Broken Access Control
**What It Checks:**
- User can access resources they shouldn't
- Privilege escalation vulnerabilities
- IDOR (Insecure Direct Object References)
- Missing authorization checks

**Example Vulnerability:**
```javascript
// Vulnerable: No authorization check
app.get('/api/user/:id/profile', (req, res) => {
    const profile = db.getProfile(req.params.id);
    res.json(profile);
});

// Secure: Authorization check
app.get('/api/user/:id/profile', (req, res) => {
    if (req.user.id !== req.params.id && !req.user.isAdmin) {
        return res.status(403).json({error: 'Forbidden'});
    }
    const profile = db.getProfile(req.params.id);
    res.json(profile);
});
```

### A02:2021 - Cryptographic Failures
**What It Checks:**
- Use of weak algorithms (MD5, SHA1)
- Unencrypted sensitive data
- Weak TLS configuration
- Insecure key management

**Example Vulnerability:**
```javascript
// Vulnerable: MD5 hashing
const hash = crypto.createHash('md5').update(password).digest('hex');

// Secure: bcrypt with salt
const hash = await bcrypt.hash(password, 10);
```

### A03:2021 - Injection
**What It Checks:**
- SQL injection
- Command injection
- NoSQL injection
- LDAP injection

**Example Vulnerability:**
```javascript
// Vulnerable: SQL injection
const query = `SELECT * FROM users WHERE username='${username}'`;

// Secure: Parameterized query
const query = 'SELECT * FROM users WHERE username = ?';
db.query(query, [username]);
```

### A04:2021 - Insecure Design
**What It Checks:**
- Missing threat modeling
- Insufficient security requirements
- Lack of security patterns
- Business logic flaws

**Example Issue:**
```
Vulnerable Design:
- Password reset sends new password via email
- No rate limiting on API endpoints
- Single-step payment processing

Secure Design:
- Password reset uses time-limited tokens
- Rate limiting: 100 requests/minute/IP
- Two-step payment with confirmation
```

### A05:2021 - Security Misconfiguration
**What It Checks:**
- Default credentials
- Unnecessary features enabled
- Missing security headers
- Verbose error messages

**Example Vulnerability:**
```javascript
// Vulnerable: Detailed errors in production
app.use((err, req, res, next) => {
    res.status(500).json({
        error: err.message,
        stack: err.stack
    });
});

// Secure: Generic errors in production
app.use((err, req, res, next) => {
    console.error(err); // Log internally
    res.status(500).json({
        error: 'Internal server error'
    });
});
```

### A06:2021 - Vulnerable and Outdated Components
**What It Checks:**
- Known CVEs in dependencies
- Outdated frameworks
- Unsupported libraries
- Missing security patches

**Example Finding:**
```
Vulnerable Component:
- lodash@4.17.19 (CVE-2020-8203)
- Impact: Prototype pollution
- Fix: Upgrade to lodash@4.17.21
- Command: npm install lodash@4.17.21
```

### A07:2021 - Identification and Authentication Failures
**What It Checks:**
- Weak password policies
- Missing MFA
- Session management issues
- Credential stuffing protection

**Example Vulnerability:**
```javascript
// Vulnerable: No password requirements
if (password.length < 6) {
    return res.status(400).json({error: 'Password too short'});
}

// Secure: Strong password policy
if (password.length < 12 ||
    !/[A-Z]/.test(password) ||
    !/[a-z]/.test(password) ||
    !/[0-9]/.test(password) ||
    !/[^A-Za-z0-9]/.test(password)) {
    return res.status(400).json({
        error: 'Password must be 12+ chars with upper, lower, number, symbol'
    });
}
```

### A08:2021 - Software and Data Integrity Failures
**What It Checks:**
- Insecure deserialization
- Missing code signing
- Unverified updates
- Untrusted CI/CD pipelines

**Example Vulnerability:**
```javascript
// Vulnerable: Unsafe deserialization
const userData = JSON.parse(req.body.data);
eval(userData.code);

// Secure: Safe parsing with validation
const userData = JSON.parse(req.body.data);
if (typeof userData.code === 'string' && isValidCode(userData.code)) {
    // Safe execution
}
```

### A09:2021 - Security Logging and Monitoring Failures
**What It Checks:**
- Insufficient logging
- Missing audit trails
- No alerting
- Inadequate log retention

**Example Implementation:**
```javascript
// Secure: Comprehensive logging
logger.info('Authentication attempt', {
    user: username,
    ip: req.ip,
    timestamp: new Date(),
    success: true
});

logger.warn('Failed login attempt', {
    user: username,
    ip: req.ip,
    timestamp: new Date(),
    reason: 'Invalid password'
});
```

### A10:2021 - Server-Side Request Forgery (SSRF)
**What It Checks:**
- Unvalidated URL parameters
- Missing input validation
- Unrestricted outbound requests
- Insufficient network segmentation

**Example Vulnerability:**
```javascript
// Vulnerable: SSRF
app.get('/fetch', async (req, res) => {
    const response = await axios.get(req.query.url);
    res.json(response.data);
});

// Secure: URL validation
app.get('/fetch', async (req, res) => {
    const allowedDomains = ['api.example.com', 'cdn.example.com'];
    const url = new URL(req.query.url);

    if (!allowedDomains.includes(url.hostname)) {
        return res.status(400).json({error: 'Invalid domain'});
    }

    const response = await axios.get(url.toString());
    res.json(response.data);
});
```

## Example Report

```
OWASP TOP 10 COMPLIANCE REPORT
==============================
Application: Example App
Date: 2025-10-11
Overall Compliance: 75% (Partially Compliant)

RESULTS
-------
 A01: Broken Access Control - PASS (95%)
 A02: Cryptographic Failures - FAIL (40%)
 A03: Injection - PASS (90%)
 A04: Insecure Design - FAIL (60%)
 A05: Security Misconfiguration - FAIL (55%)
 A06: Vulnerable Components - PASS (85%)
 A07: Authentication Failures - FAIL (70%)
 A08: Data Integrity - PASS (80%)
 A09: Logging Failures - FAIL (45%)
 A10: SSRF - PASS (100%)

CRITICAL GAPS
-------------

A02: Cryptographic Failures (40%)
- Using MD5 for password hashing (5 instances)
- TLS 1.0 enabled on production servers
- Sensitive data transmitted without encryption
- Hardcoded encryption keys found

Immediate Actions:
1. Replace MD5 with bcrypt (8 hours)
2. Disable TLS 1.0, enforce TLS 1.3 (4 hours)
3. Enable encryption for all sensitive endpoints (16 hours)
4. Move keys to secure key management (8 hours)

A09: Logging Failures (45%)
- No logging for authentication events
- Missing audit trail for data modifications
- No alerting configured
- Log retention only 7 days (requirement: 90 days)

Immediate Actions:
1. Implement authentication logging (4 hours)
2. Add audit logging for CRUD operations (8 hours)
3. Configure security alerts (8 hours)
4. Extend log retention to 90 days (2 hours)
```

## Compliance Levels

- **90-100%**: Compliant - Production ready
- **75-89%**: Mostly Compliant - Address gaps before production
- **50-74%**: Partially Compliant - Significant work needed
- **<50%**: Non-Compliant - Not ready for production

## Best Practices

1. **Regular Checks**
   - Run before every release
   - Schedule monthly compliance reviews
   - Track compliance trends

2. **Maintain Compliance**
   - Target 90%+ compliance
   - Address failures immediately
   - Document justified exceptions

3. **Training**
   - Regular OWASP training for developers
   - Security champions program
   - Secure coding guidelines

4. **Integration**
   - Add to CI/CD pipeline
   - Block deployments below 90% compliance
   - Automated compliance reporting

## Requirements

- Access to application code
- Configuration files access
- Dependency manifests
- Network access for testing

## License

MIT License - See LICENSE file for details

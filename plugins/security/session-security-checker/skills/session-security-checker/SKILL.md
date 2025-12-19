---
name: checking-session-security
description: |
  Analyze session management implementations to identify security vulnerabilities in web applications.
  Use when you need to audit session handling, check for session fixation risks, review session timeout configurations, or validate session ID generation security.
  Trigger with phrases like "check session security", "audit session management", "review session handling", or "session fixation vulnerability".
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(code-scan:*), security-check:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- Source code accessible in {baseDir}/
- Session management code locations known (auth modules, middleware)
- Framework information (Express, Django, Spring, etc.)
- Configuration files for session settings
- Write permissions for security report in {baseDir}/security-reports/

## Instructions

### 1. Code Discovery Phase

Locate session management code:
- Authentication/login handlers
- Session middleware configuration
- Cookie handling code
- Session storage implementations
- Logout/session termination code

**Common file patterns**:
- `**/auth/**`, `**/session/**`, `**/middleware/**`
- `session.config.*`, `auth.config.*`
- Framework-specific: `settings.py`, `application.yml`, `web.config`

### 2. Session ID Security Analysis

**Generation Strength**:
- Check for cryptographically secure random generators
- Verify sufficient entropy (at least 128 bits)
- Ensure unpredictable session ID patterns
- No sequential or timestamp-based IDs

**Bad Patterns to Detect**:
```javascript
// INSECURE: Predictable
sessionId = Date.now() + userId;
sessionId = Math.random().toString();

// SECURE: Cryptographically random
sessionId = crypto.randomBytes(32).toString('hex');
```

### 3. Session Fixation Vulnerability Check

Verify session ID regeneration:
- New session ID generated after login
- Session ID changes on privilege escalation
- Old session ID invalidated after regeneration

**Vulnerable Pattern**:
```python
# INSECURE: Reuses existing session ID
def login(username, password):
    if authenticate(username, password):
        session['authenticated'] = True  # Session ID not regenerated
```

**Secure Pattern**:
```python
# SECURE: Regenerates session ID
def login(username, password):
    if authenticate(username, password):
        session.regenerate()  # New session ID
        session['authenticated'] = True
```

### 4. Session Timeout Analysis

Check timeout configurations:
- Idle timeout (session inactivity limit)
- Absolute timeout (maximum session lifetime)
- Remember-me token expiration
- Sensitive operation re-authentication

**Configuration Review**:
- Idle timeout: 15-30 minutes recommended
- Absolute timeout: 8-12 hours maximum
- Financial apps: Shorter timeouts (5-10 minutes)
- Sensitive operations: Force re-authentication

### 5. Cookie Security Attributes

Verify secure cookie flags:
- `HttpOnly`: Prevents JavaScript access (XSS protection)
- `Secure`: Ensures HTTPS-only transmission
- `SameSite`: Prevents CSRF attacks (Strict or Lax)
- `Domain` and `Path`: Properly scoped

**Insecure Cookie**:
```javascript
res.cookie('sessionId', sessionId);  // No security flags
```

**Secure Cookie**:
```javascript
res.cookie('sessionId', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: 3600000  // 1 hour
});
```

### 6. Session Storage Security

Evaluate storage mechanisms:
- Server-side storage (recommended): Redis, Memcached, database
- Encrypted storage for sensitive data
- No sensitive data in client-side cookies
- Proper session cleanup on logout

**Check for**:
- Sessions persisting after logout
- Lack of session invalidation
- Sensitive data stored in cookies
- Unencrypted session stores

### 7. Session Hijacking Protections

Verify anti-hijacking measures:
- IP address binding (with caution for mobile users)
- User-Agent validation
- Token-based CSRF protection
- Automatic logout on suspicious activity

### 8. Concurrent Session Management

Check concurrent session handling:
- Limit concurrent sessions per user
- Session conflict detection
- Force logout previous sessions option
- Session monitoring and alerting

## Output

The skill produces:

**Primary Output**: Session security report saved to {baseDir}/security-reports/session-security-YYYYMMDD.md

**Report Structure**:
```
# Session Security Analysis Report
Analysis Date: 2024-01-15
Application: Web Portal
Framework: Express.js

## Executive Summary
- Overall Security Rating: MEDIUM RISK
- Critical Issues: 2
- High Priority Issues: 4
- Recommendations: 8

## Critical Findings

### 1. Session Fixation Vulnerability
**File**: {baseDir}/src/auth/login.js
**Line**: 45
**Issue**: Session ID not regenerated after authentication
**Risk**: Attacker can hijack authenticated session
**Code**:
```javascript
function handleLogin(req, res) {
  if (validateCredentials(req.body)) {
    req.session.authenticated = true;  // VULNERABLE
    res.redirect('/dashboard');
  }
}
```
**Remediation**:
```javascript
function handleLogin(req, res) {
  if (validateCredentials(req.body)) {
    req.session.regenerate((err) => {  // SECURE
      req.session.authenticated = true;
      res.redirect('/dashboard');
    });
  }
}
```

### 2. Missing HttpOnly Flag
**File**: {baseDir}/config/session.js
**Line**: 12
**Issue**: Session cookies accessible to JavaScript
**Risk**: XSS attacks can steal session tokens
**Remediation**: Set `httpOnly: true` in cookie configuration

## High Priority Findings

### 3. Weak Session Timeout
**File**: {baseDir}/config/session.js
**Line**: 15
**Issue**: Session timeout set to 24 hours
**Risk**: Extended exposure window for compromised sessions
**Current**: `maxAge: 86400000  // 24 hours`
**Recommendation**: `maxAge: 1800000  // 30 minutes`

### 4. Insecure Session ID Generation
**File**: {baseDir}/src/auth/session-manager.js
**Line**: 28
**Issue**: Using Math.random() for session IDs
**Risk**: Predictable session IDs enable brute-force attacks
**Remediation**: Use crypto.randomBytes()

[Additional findings...]

## Session Configuration Summary
- Session Store: Redis (Good)
- Cookie Secure Flag: Missing (Critical)
- Cookie HttpOnly Flag: Missing (Critical)
- Cookie SameSite: None (High Risk)
- Idle Timeout: 24 hours (Too Long)
- Session Regeneration: Not Implemented (Critical)

## Compliance Check
- OWASP Session Management: 4/10 controls implemented
- PCI-DSS 8.1.8: Non-compliant (timeout too long)
- NIST 800-63B: Partial compliance

## Remediation Priority
1. [CRITICAL] Implement session regeneration on login
2. [CRITICAL] Enable HttpOnly and Secure cookie flags
3. [HIGH] Reduce session timeout to 30 minutes
4. [HIGH] Implement cryptographically secure session IDs
5. [MEDIUM] Add SameSite=Strict to cookies
6. [MEDIUM] Implement concurrent session limits
```

**Secondary Outputs**:
- Vulnerable code snippets with line numbers
- Remediation code examples
- Framework-specific configuration guide

## Error Handling

**Common Issues and Resolutions**:

1. **Cannot Locate Session Management Code**
   - Error: "No session handling code found in {baseDir}/"
   - Resolution: Search for framework-specific patterns
   - Fallback: Request explicit file paths from user

2. **Framework Not Recognized**
   - Error: "Unknown session framework"
   - Resolution: Apply generic session security checks
   - Note: Framework-specific recommendations unavailable

3. **Encrypted or Obfuscated Code**
   - Error: "Cannot analyze minified/compiled code"
   - Resolution: Request source code or unminified version
   - Limitation: Document inability to fully audit

4. **Custom Session Implementation**
   - Error: "Non-standard session management detected"
   - Resolution: Apply fundamental security principles
   - Extra Scrutiny: Custom implementations often have flaws

5. **Configuration in Environment Variables**
   - Error: "Session config in environment, not code"
   - Resolution: Request .env.example or config documentation
   - Fallback: Provide general configuration recommendations

## Resources

**OWASP Guidelines**:
- Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Top 10 - Broken Authentication: https://owasp.org/www-project-top-ten/

**Standards and Best Practices**:
- NIST 800-63B Authentication: https://pages.nist.gov/800-63-3/sp800-63b.html
- PCI-DSS Session Requirements: https://www.pcisecuritystandards.org/

**Framework-Specific Guides**:
- Express.js Session Security: https://expressjs.com/en/advanced/best-practice-security.html
- Django Session Framework: https://docs.djangoproject.com/en/stable/topics/http/sessions/
- Spring Session: https://spring.io/projects/spring-session

**Security Tools**:
- Burp Suite for session testing
- OWASP ZAP session analysis
- Browser DevTools for cookie inspection

**Common Vulnerabilities**:
- CWE-384: Session Fixation
- CWE-613: Insufficient Session Expiration
- CWE-539: Information Exposure Through Persistent Cookies
- CWE-5 52: Insufficiently Protected Credentials
# CSRF Protection Validator Plugin

Validate Cross-Site Request Forgery (CSRF) protection mechanisms in web applications.

## Features

- **Token Validation** - Synchronizer token pattern
- **Double Submit Cookie** - Cookie-to-header validation
- **SameSite Cookies** - Cookie attribute checking
- **Origin Validation** - Origin/Referer header validation
- **State-Changing Operation Detection** - Identify unprotected endpoints

## Installation

```bash
/plugin install csrf-protection-validator@claude-code-plugins-plus
```

## Usage

```bash
/validate-csrf
# Or shortcut
/csrf
```

## CSRF Protection Methods

### 1. Synchronizer Token Pattern
```javascript
// Generate CSRF token
app.use((req, res, next) => {
    req.csrfToken = () => generateToken();
    res.locals.csrfToken = req.csrfToken();
    next();
});

// Validate on state-changing requests
app.post('/transfer', (req, res) => {
    if (req.body.csrf !== req.session.csrf) {
        return res.status(403).json({error: 'Invalid CSRF token'});
    }
    // Process request
});
```

### 2. Double Submit Cookie
```javascript
app.post('/api/action', (req, res) => {
    const cookieToken = req.cookies.csrfToken;
    const headerToken = req.headers['x-csrf-token'];

    if (!cookieToken || cookieToken !== headerToken) {
        return res.status(403).json({error: 'CSRF validation failed'});
    }
    // Process request
});
```

### 3. SameSite Cookie Attribute
```javascript
res.cookie('session', token, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict' // or 'lax'
});
```

### 4. Origin/Referer Validation
```javascript
app.use((req, res, next) => {
    const origin = req.headers.origin || req.headers.referer;
    const allowedOrigins = ['https://example.com'];

    if (!origin || !allowedOrigins.some(allowed => origin.startsWith(allowed))) {
        return res.status(403).json({error: 'Invalid origin'});
    }
    next();
});
```

## Example Report

```
CSRF PROTECTION ANALYSIS
========================
Endpoints Analyzed: 45
Vulnerable: 8
Protected: 37

VULNERABLE ENDPOINTS
--------------------

1. POST /api/transfer
   Protection: NONE
   Risk: CRITICAL
   Impact: Unauthorized fund transfers

   Attack Scenario:
   <form action="https://example.com/api/transfer" method="POST">
       <input name="to" value="attacker">
       <input name="amount" value="10000">
   </form>
   <script>document.forms[0].submit();</script>

   Fix:
   - Add CSRF token validation
   - Use SameSite=strict cookies
   - Validate Origin header

2. POST /api/profile/update
   Protection: NONE
   Risk: HIGH
   Impact: Account takeover

   Recommended Fix:
   const csrf = require('csurf');
   app.use(csrf({ cookie: true }));

3. DELETE /api/account
   Protection: NONE
   Risk: CRITICAL
   Impact: Account deletion

RECOMMENDATIONS
---------------
1. Implement CSRF protection library (csurf)
2. Set SameSite=strict on all cookies
3. Validate Origin/Referer headers
4. Use double-submit cookie pattern for APIs
```

## Best Practices

1. **Protect All State-Changing Operations**
   - POST, PUT, PATCH, DELETE requests
   - Any operation modifying data

2. **Use Multiple Layers**
   - CSRF tokens + SameSite cookies
   - Origin validation as backup

3. **Token Requirements**
   - Cryptographically random
   - Unique per session
   - Expire with session

4. **Safe Methods Don't Need Protection**
   - GET, HEAD, OPTIONS
   - Should be read-only

## License

MIT License - See LICENSE file for details

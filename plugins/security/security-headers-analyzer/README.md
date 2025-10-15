# Security Headers Analyzer Plugin

Analyze and validate HTTP security headers to protect against common web vulnerabilities.

## Features

- **Comprehensive Header Analysis** - Check all major security headers
- **Best Practice Recommendations** - Industry-standard configurations
- **Header Scoring** - Grade security posture (A+ to F)
- **Missing Header Detection** - Identify gaps
- **Misconfiguration Warnings** - Flag weak or incorrect settings

## Installation

```bash
/plugin install security-headers-analyzer@claude-code-plugins-plus
```

## Usage

```bash
/analyze-headers
# Or shortcut
/headers
```

## Headers Analyzed

### Critical Headers

1. **Content-Security-Policy (CSP)**
   - Prevents XSS attacks
   - Restricts resource loading
   - Recommended: `default-src 'self'; script-src 'self' 'nonce-{random}'`

2. **Strict-Transport-Security (HSTS)**
   - Forces HTTPS connections
   - Prevents downgrade attacks
   - Recommended: `max-age=31536000; includeSubDomains; preload`

3. **X-Frame-Options**
   - Prevents clickjacking
   - Controls iframe embedding
   - Recommended: `DENY` or `SAMEORIGIN`

4. **X-Content-Type-Options**
   - Prevents MIME sniffing
   - Recommended: `nosniff`

5. **X-XSS-Protection**
   - Legacy XSS protection
   - Recommended: `1; mode=block`

6. **Referrer-Policy**
   - Controls referrer information
   - Recommended: `strict-origin-when-cross-origin`

7. **Permissions-Policy**
   - Controls browser features
   - Recommended: `geolocation=(), microphone=(), camera=()`

## Example Report

```
SECURITY HEADERS ANALYSIS
=========================
Domain: https://example.com
Grade: C (Needs Improvement)
Score: 65/100

HEADER STATUS
-------------
 Content-Security-Policy: PRESENT (Good)
 Strict-Transport-Security: MISSING (Critical)
 X-Frame-Options: PRESENT (Weak)
 X-Content-Type-Options: PRESENT (Good)
 Referrer-Policy: MISSING (Medium)
 Permissions-Policy: MISSING (Medium)

CRITICAL ISSUES
---------------

1. Missing HSTS Header
   Risk: HIGH
   Impact: Susceptible to SSL stripping attacks

   Add header:
   Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

   Node.js/Express:
   app.use((req, res, next) => {
       res.setHeader('Strict-Transport-Security',
           'max-age=31536000; includeSubDomains; preload');
       next();
   });

2. Weak X-Frame-Options
   Current: SAMEORIGIN
   Risk: MEDIUM
   Issue: Allows framing from same origin

   Recommendation:
   X-Frame-Options: DENY

   Unless you need iframe embedding, use DENY for maximum protection.
```

## Best Practices

- **Always use HTTPS** - Required for HSTS
- **Implement CSP** - Start with report-only mode
- **Test thoroughly** - CSP can break functionality
- **Use security header middleware** - helmet.js for Node
- **Monitor violations** - CSP reporting endpoints

## Quick Fix (Node.js)

```javascript
const helmet = require('helmet');

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'nonce-{random}'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
        }
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    },
    frameguard: { action: 'deny' },
    noSniff: true,
    xssFilter: true,
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' }
}));
```

## License

MIT License - See LICENSE file for details

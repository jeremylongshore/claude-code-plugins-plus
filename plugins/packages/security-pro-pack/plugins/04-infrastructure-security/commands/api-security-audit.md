---
description: Comprehensive security audit for REST and GraphQL APIs
shortcut: asa
category: security
difficulty: intermediate
estimated_time: 15-30 minutes
---

<!-- DESIGN DECISION: API security as critical attack surface -->
<!-- APIs are primary attack vectors for modern applications -->
<!-- Covers both REST and GraphQL with OWASP API Security Top 10 -->

<!-- ALTERNATIVES CONSIDERED: -->
<!-- - Manual testing only (rejected: slow, inconsistent, error-prone) -->
<!-- - Automated scanning only (rejected: misses business logic flaws) -->
<!-- - REST-only focus (rejected: GraphQL increasingly common) -->

<!-- VALIDATION: Tested against intentionally vulnerable APIs and real production endpoints -->
<!-- Successfully identified broken authentication, mass assignment, rate limiting gaps -->

# API Security Audit

Performs comprehensive security audit of REST and GraphQL APIs, checking for OWASP API Security Top 10 vulnerabilities, authentication/authorization flaws, injection risks, and business logic issues.

## What This Command Does

**Complete API Security Assessment:**
-  Tests for OWASP API Security Top 10 vulnerabilities
-  Validates authentication and authorization mechanisms
-  Checks for injection vulnerabilities (SQL, NoSQL, command)
-  Identifies excessive data exposure and mass assignment
-  Tests rate limiting and resource consumption controls
-  Analyzes GraphQL-specific security issues (deep queries, introspection)
-  Reviews API documentation for security misconfigurations

**Output:** Detailed security audit report with exploitability ratings and remediation guidance

**Time:** 15-30 minutes per API

---

## When to Use This Command

**Perfect For:**
- Pre-production API security validation
- External API security assessments
- Compliance requirements (PCI DSS, HIPAA)
- After API changes or new endpoint additions
- Regular security audits (quarterly)

**Use This When:**
- Building new API endpoints
- Before public API launch
- After authentication/authorization changes
- Responding to security incidents
- Preparing for penetration test

---

## Usage

```bash
# Audit REST API
/api-security-audit https://api.example.com

# Audit GraphQL API
/api-security-audit https://api.example.com/graphql --type graphql

# Audit with authentication
/api-security-audit https://api.example.com --auth "Bearer TOKEN"

# Audit specific endpoints
/api-security-audit https://api.example.com/users --endpoints /users,/orders

# Generate detailed report
/api-security-audit https://api.example.com --output api-security-report.md
```

**Shortcut:**
```bash
/asa https://api.example.com  # Quick audit
```

---

## OWASP API Security Top 10 Coverage

### API1:2023 - Broken Object Level Authorization (BOLA/IDOR)

**Vulnerability:** Users can access objects belonging to other users

**Example Attack:**
```bash
# User 123 accesses their own order
GET /api/orders/456
Authorization: Bearer USER_123_TOKEN

# Attack: Change order ID to access other user's order
GET /api/orders/789  # ← Belongs to User 456!
Authorization: Bearer USER_123_TOKEN

# If API doesn't validate ownership, User 123 can see User 456's order
```

**Detection Method:**
```bash
# Test IDOR vulnerability
1. Create two test users (User A, User B)
2. User A creates resource (e.g., order ID 100)
3. User B tries to access: GET /api/orders/100
4. If successful → IDOR vulnerability exists
```

**Remediation:**
```javascript
//  VULNERABLE: No authorization check
app.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id)
  res.json(order)  // Returns ANY order if it exists!
})

//  SECURE: Verify ownership
app.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id)

  if (!order) {
    return res.status(404).json({ error: 'Order not found' })
  }

  if (order.userId !== req.user.id && !req.user.isAdmin) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  res.json(order)
})
```

---

### API2:2023 - Broken Authentication

**Vulnerability:** Weak authentication allowing unauthorized access

**Common Issues:**
- No authentication required
- Weak password requirements
- No rate limiting on login
- Predictable API keys
- JWT with weak secrets
- No token expiration

**Example Attack:**
```bash
# Brute force login (no rate limiting)
for password in $(cat passwords.txt); do
  curl -X POST https://api.example.com/login \
    -d "username=admin&password=$password"
done
```

**Remediation:**
```javascript
//  SECURE: Rate limiting on login
const rateLimit = require('express-rate-limit')

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts, please try again later'
})

app.post('/login', loginLimiter, async (req, res) => {
  // Login logic with strong password requirements
  // - Minimum 12 characters
  // - Require uppercase, lowercase, numbers, symbols
  // - Check against common password list
})
```

---

### API3:2023 - Broken Object Property Level Authorization

**Vulnerability:** Users can modify properties they shouldn't access

**Example Attack (Mass Assignment):**
```bash
# Normal user update
PATCH /api/users/123
{
  "name": "John Doe",
  "email": "[email protected]"
}

# Attack: Add admin flag
PATCH /api/users/123
{
  "name": "John Doe",
  "email": "[email protected]",
  "isAdmin": true  # ← Attacker tries to elevate privileges!
}
```

**Remediation:**
```javascript
//  VULNERABLE: Mass assignment
app.patch('/api/users/:id', async (req, res) => {
  await User.update(req.params.id, req.body)  // Updates ALL fields!
})

//  SECURE: Allowlist specific fields
app.patch('/api/users/:id', async (req, res) => {
  const allowedFields = ['name', 'email', 'phone']
  const updates = {}

  allowedFields.forEach(field => {
    if (req.body[field] !== undefined) {
      updates[field] = req.body[field]
    }
  })

  await User.update(req.params.id, updates)
})
```

---

### API4:2023 - Unrestricted Resource Consumption

**Vulnerability:** No limits on API usage, leading to DoS or cost overruns

**Example Attack:**
```bash
# Exhaust API resources
while true; do
  curl https://api.example.com/expensive-operation &
done
# Launch thousands of requests, exhaust server resources
```

**Remediation:**
```javascript
//  SECURE: Rate limiting + pagination + timeouts
const rateLimit = require('express-rate-limit')

// Global rate limit
app.use(rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100 // 100 requests per minute
}))

// Pagination enforcement
app.get('/api/users', (req, res) => {
  const page = parseInt(req.query.page) || 1
  const limit = Math.min(parseInt(req.query.limit) || 10, 100)  // Max 100

  // Return paginated results with limit
})

// Request timeout
app.use((req, res, next) => {
  req.setTimeout(30000, () => {  // 30 second timeout
    res.status(408).send('Request timeout')
  })
  next()
})
```

---

### API5:2023 - Broken Function Level Authorization

**Vulnerability:** Regular users can access admin functions

**Example Attack:**
```bash
# Regular user token
curl -H "Authorization: Bearer USER_TOKEN" \
  https://api.example.com/admin/delete-user/456
# Should return 403 Forbidden, but if vulnerable, executes!
```

**Remediation:**
```javascript
//  VULNERABLE: No role check
app.delete('/admin/delete-user/:id', authenticate, async (req, res) => {
  await User.delete(req.params.id)
  // Any authenticated user can delete users!
})

//  SECURE: Role-based access control
function requireAdmin(req, res, next) {
  if (!req.user.isAdmin) {
    return res.status(403).json({ error: 'Admin access required' })
  }
  next()
}

app.delete('/admin/delete-user/:id', authenticate, requireAdmin, async (req, res) => {
  await User.delete(req.params.id)
})
```

---

### API6:2023 - Unrestricted Access to Sensitive Business Flows

**Vulnerability:** No rate limiting on critical business operations

**Example Attack:**
```bash
# Purchase limited item repeatedly (no rate limit)
for i in {1..1000}; do
  curl -X POST https://api.example.com/purchase \
    -d "item_id=limited_edition_sneakers&quantity=1" &
done
# Buys entire stock, legitimate customers can't purchase
```

**Remediation:**
```javascript
//  SECURE: Business logic rate limiting
const Redis = require('ioredis')
const redis = new Redis()

app.post('/purchase', authenticate, async (req, res) => {
  const userId = req.user.id
  const key = `purchase:${userId}`

  // Allow 1 purchase per 10 minutes for this item
  const exists = await redis.get(key)
  if (exists) {
    return res.status(429).json({
      error: 'Purchase limit exceeded. Try again in 10 minutes.'
    })
  }

  // Process purchase
  await processPurchase(req.body)

  // Set rate limit
  await redis.set(key, '1', 'EX', 600)  // 10 minutes

  res.json({ success: true })
})
```

---

### API7:2023 - Server Side Request Forgery (SSRF)

**Vulnerability:** API fetches user-supplied URLs, exposing internal resources

**Example Attack:**
```bash
# Intended use: Fetch profile picture from URL
POST /api/upload-from-url
{
  "url": "https://example.com/profile.jpg"
}

# Attack: Access internal resources
POST /api/upload-from-url
{
  "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
}
# Exposes AWS credentials!
```

**Remediation:**
```javascript
//  SECURE: URL validation and allowlist
const validator = require('validator')

app.post('/api/upload-from-url', async (req, res) => {
  const { url } = req.body

  // Validate URL format
  if (!validator.isURL(url, { protocols: ['https'] })) {
    return res.status(400).json({ error: 'Invalid URL' })
  }

  // Parse URL
  const parsed = new URL(url)

  // Blocklist internal IPs
  const blocklist = [
    '127.0.0.1', 'localhost',
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
    '169.254.169.254'  // AWS metadata endpoint
  ]

  if (blocklist.some(ip => parsed.hostname.includes(ip))) {
    return res.status(403).json({ error: 'Forbidden URL' })
  }

  // Allowlist domains
  const allowedDomains = ['cdn.example.com', 'images.example.com']
  if (!allowedDomains.includes(parsed.hostname)) {
    return res.status(403).json({ error: 'Domain not allowed' })
  }

  // Fetch with timeout
  const response = await fetch(url, { timeout: 5000 })
  // Process image
})
```

---

### API8:2023 - Security Misconfiguration

**Common Issues:**
- Debug mode enabled in production
- Verbose error messages (stack traces)
- Default credentials
- Missing security headers
- CORS misconfiguration

**Remediation:**
```javascript
//  SECURE: Security headers and configuration
const helmet = require('helmet')
const cors = require('cors')

// Security headers
app.use(helmet())

// Strict CORS
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS.split(','),
  credentials: true
}))

// Disable debug mode
app.set('env', 'production')

// Generic error messages
app.use((err, req, res, next) => {
  console.error(err.stack)  // Log internally only
  res.status(500).json({
    error: 'Internal server error'  // Generic message to client
  })
})
```

---

### API9:2023 - Improper Inventory Management

**Issues:**
- Undocumented endpoints
- Deprecated endpoints not removed
- Multiple API versions (confusion)
- No API documentation

**Remediation:**
- Maintain API inventory (all endpoints documented)
- Remove deprecated endpoints
- Version API properly (`/api/v1/`, `/api/v2/`)
- Use OpenAPI/Swagger documentation

---

### API10:2023 - Unsafe Consumption of APIs

**Vulnerability:** Blindly trusting third-party API responses

**Example Attack:**
```javascript
//  VULNERABLE: Trust external API response
app.get('/user-profile', async (req, res) => {
  const externalData = await fetch('https://third-party.com/api/user')
  const userData = await externalData.json()

  // Directly insert into database without validation
  await db.users.insert(userData)  // SQL injection possible!
})

//  SECURE: Validate external API responses
app.get('/user-profile', async (req, res) => {
  const externalData = await fetch('https://third-party.com/api/user')
  const userData = await externalData.json()

  // Validate structure and types
  const schema = {
    name: 'string',
    email: 'string',
    age: 'number'
  }

  const validated = validateAgainstSchema(userData, schema)

  // Sanitize before database insertion
  await db.users.insert(validated)
})
```

---

## GraphQL-Specific Security Issues

### 1. Deep Query Attack (Query Depth DoS)

**Attack:**
```graphql
# Malicious deep query
query {
  user(id: 1) {
    friends {
      friends {
        friends {
          friends {
            friends {
              # 100 levels deep!
            }
          }
        }
      }
    }
  }
}
```

**Remediation:**
```javascript
// Limit query depth
const depthLimit = require('graphql-depth-limit')

const server = new ApolloServer({
  schema,
  validationRules: [depthLimit(5)]  // Max 5 levels
})
```

### 2. Introspection Enabled in Production

**Risk:** Attackers can discover full API schema

**Remediation:**
```javascript
// Disable introspection in production
const server = new ApolloServer({
  schema,
  introspection: process.env.NODE_ENV !== 'production'
})
```

### 3. Query Cost Analysis

**Attack:** Expensive queries exhaust resources

**Remediation:**
```javascript
const { createComplexityLimitRule } = require('graphql-validation-complexity')

const server = new ApolloServer({
  schema,
  validationRules: [
    createComplexityLimitRule(1000)  // Max complexity score
  ]
})
```

---

## Example: Full Audit Report

```bash
$ /api-security-audit https://api.example.com

 API Security Audit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 API: https://api.example.com
 Type: REST API
 Audit Date: 2025-10-10
⏱️  Duration: 18 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CRITICAL VULNERABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Broken Object Level Authorization (BOLA)
    Severity: Critical
    Endpoint: GET /api/orders/:id

   ️  Issue: Users can access other users' orders by changing ID

   Test:
   - User A ID: 123, Created order ID: 456
   - User B ID: 789, Accessed order ID: 456 successfully!

    Fix:
   if (order.userId !== req.user.id && !req.user.isAdmin) {
     return res.status(403).json({ error: 'Forbidden' })
   }

2. No Rate Limiting on Login
    Severity: Critical
    Endpoint: POST /api/login

   ️  Issue: Brute force attacks possible (tested 10,000 requests/min)

    Fix:
   const loginLimiter = rateLimit({
     windowMs: 15 * 60 * 1000,
     max: 5
   })
   app.post('/login', loginLimiter, loginHandler)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
️  HIGH SEVERITY VULNERABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. Mass Assignment Vulnerability
    Severity: High
    Endpoint: PATCH /api/users/:id

   ️  Issue: Can modify isAdmin field

   Test Payload:
   PATCH /api/users/123
   { "isAdmin": true }

   Result: Regular user elevated to admin!

    Fix: Implement field allowlist

4. SQL Injection
    Severity: High
    Endpoint: GET /api/search?q=

   ️  Issue: Unsanitized search parameter

   Test Payload:
   GET /api/search?q=' OR '1'='1

   Result: Returns all records!

    Fix: Use parameterized queries

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MEDIUM SEVERITY ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. Verbose Error Messages
    Severity: Medium

   Error Response:
   {
     "error": "Error: Connection refused at Database.connect (db.js:45)"
   }

   ️  Exposes: Internal paths, technology stack

    Fix: Return generic error messages

6. No Pagination Limits
    Severity: Medium
    Endpoint: GET /api/users

   ️  Issue: Can request unlimited records

    Fix: Enforce max limit (100 records)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 AUDIT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OWASP API Security Top 10 Coverage:
 API1: Broken Object Level Authorization - VULNERABLE
 API2: Broken Authentication - VULNERABLE
 API3: Broken Object Property Level Authorization - VULNERABLE
 API4: Unrestricted Resource Consumption - PARTIAL
 API5: Broken Function Level Authorization - SECURE
 API6: Unrestricted Access to Sensitive Business Flows - NOT TESTED
 API7: Server Side Request Forgery - NOT APPLICABLE
 API8: Security Misconfiguration - VULNERABLE
 API9: Improper Inventory Management - PARTIAL
 API10: Unsafe Consumption of APIs - NOT TESTED

Total Findings: 15
  Critical: 2
  High: 4
  Medium: 6
  Low: 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 REMEDIATION ROADMAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Week 1 (Critical):
 Fix BOLA vulnerability (4 hours)
 Add login rate limiting (2 hours)

Week 2 (High):
 Fix mass assignment (3 hours)
 Fix SQL injection (4 hours)

Week 3 (Medium):
 Generic error messages (2 hours)
 Add pagination limits (2 hours)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Audit completed! 
Report saved to: api-security-audit-2025-10-10.md
```

---

## Related Commands

- `/security-scan-quick` - Fast application security scan
- `/penetration-tester` - Full penetration testing (agent)
- `/security-auditor-expert` - OWASP Top 10 analysis (agent)

---

## Support

**Found API vulnerabilities?**
1. Prioritize critical issues (BOLA, authentication bypass, injection)
2. For remediation help: Ask Security Auditor Expert or Penetration Tester
3. For complex issues: Consult OWASP API Security Project documentation
4. Test fixes: Re-run `/api-security-audit` after changes

---

**Time Investment:** 15-30 minutes per audit
**Value:** Prevent data breaches, unauthorized access, and API abuse

**Audit APIs thoroughly. Fix vulnerabilities early. Deploy securely.** 

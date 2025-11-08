# Use Cases - Security Pro Pack

**Real-world security scenarios solved with Security Pro Pack**

---

## Use Case 1: Pre-Production Security Gate

**Scenario:** Your team is about to deploy a new payment processing feature to production. You need to ensure it meets security standards before launch.

**Challenge:**
- New feature handles sensitive payment data (PCI DSS compliance required)
- Multiple developers contributed code (varying security awareness)
- Tight deadline (2 days until launch)
- Need comprehensive security validation without hiring external auditor

**Solution with Security Pro Pack:**

**Day 1: Automated Security Scanning (2 hours)**

```bash
# Step 1: Quick vulnerability scan
cd src/features/payment-processing
/ss --output payment-security-scan.md

# Findings:
# -  Critical: Hardcoded Stripe API key
# -  High: Missing input validation on payment amount
# -  High: No rate limiting on payment endpoint
# -  Medium: Verbose error messages expose internal logic
```

**Day 1: Compliance Check (1 hour)**

Ask Compliance Checker agent:
> "Please review the payment processing code for PCI DSS compliance requirements"

```
Findings:
-  Encryption in transit (TLS 1.3)
-  Missing: Card data not immediately deleted after processing
-  Missing: No audit logging of payment attempts
-  Tokenization implemented correctly
```

**Day 1: Cryptography Review (30 minutes)**

```bash
# Review crypto implementation
/ca src/features/payment-processing/crypto.js

# Findings:
# -  AES-256-GCM used correctly
# -  Hardcoded encryption key (PCI DSS violation)
# -  Proper IV generation
```

**Day 2: Fix All Issues (4 hours)**

```javascript
// Fixed: Hardcoded secrets → Environment variables
const STRIPE_KEY = process.env.STRIPE_SECRET_KEY

// Fixed: Input validation
function validatePaymentAmount(amount) {
  if (!amount || amount <= 0 || amount > 10000) {
    throw new Error('Invalid payment amount')
  }
}

// Fixed: Rate limiting
const paymentLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5 // 5 payment attempts per 15 minutes
})
```

**Day 2: Re-validate (1 hour)**

```bash
# Re-scan to verify fixes
/ss src/features/payment-processing/

# Result:  Zero critical issues, all high-severity issues resolved
```

**Outcome:**
- **Prevented:** PCI DSS compliance violation (potential $5,000-$100,000/month fines)
- **Saved:** $3,000-$5,000 (cost of external security audit)
- **Time:** 8.5 hours total (vs. 2-3 weeks for traditional audit)
- **Deployed:** On schedule with confidence in security posture

---

## Use Case 2: Security Incident Response

**Scenario:** Your production API experienced unauthorized data access. You need to quickly identify the vulnerability and assess the scope.

**Challenge:**
- Users reported seeing other users' data
- Incident occurred 2 hours ago
- Need to identify vulnerability immediately
- Must assess scope of data breach
- Regulator requires incident report within 72 hours

**Solution with Security Pro Pack:**

**Hour 1: Rapid Vulnerability Assessment**

Ask Security Auditor Expert:
> "Perform emergency security audit of user profile API. Focus on broken object level authorization (BOLA/IDOR)."

```
Agent Response:
Critical Vulnerability Identified:

GET /api/users/:id/profile
 Missing authorization check
 Any authenticated user can access any profile by changing :id parameter

Evidence:
- User A (ID: 123) accessed User B's profile (ID: 456)
- No server-side validation of ownership
```

**Hour 2: Scope Assessment**

```bash
# Audit all API endpoints for similar issues
/asa https://api.example.com --focus authorization

# Findings:
# - 12 endpoints vulnerable to IDOR
# - Estimated affected users: 15,000 (accessed logs confirm)
# - Data exposed: email, phone, address (no payment data)
```

**Hour 3: Immediate Mitigation**

```javascript
// Emergency fix deployed to production
app.get('/api/users/:id/profile', authenticate, (req, res) => {
  const requestedId = req.params.id

  // Authorization check added
  if (requestedId !== req.user.id && !req.user.isAdmin) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  // Continue with authorized request
})
```

**Hour 4-6: Comprehensive Security Audit**

```bash
# Full security scan
/ss --verbose --output incident-security-audit.md

# Threat model to identify similar vulnerabilities
```

Ask Threat Modeler:
> "Perform STRIDE threat modeling on our API architecture to identify similar authorization issues"

**Day 2-3: Incident Report Generation**

```bash
# Generate compliance documentation for breach notification
/cdg --framework gdpr

# Customize with incident-specific details
```

**Outcome:**
- **Response Time:** Vulnerability identified and patched within 3 hours
- **Scope:** Accurately assessed data exposure for GDPR breach notification
- **Prevented:** Further unauthorized access (15,000 users protected)
- **Compliance:** Met 72-hour GDPR reporting requirement
- **Cost Avoided:** Potential €20 million GDPR fine (4% of global revenue)

---

## Use Case 3: Container Security for Kubernetes Deployment

**Scenario:** Your team is migrating to Kubernetes. You need to ensure all container images meet security standards before production deployment.

**Challenge:**
- 25 microservices (25 Docker images)
- Varying base images (Ubuntu, Alpine, Node, Python)
- Some images built by different teams
- Security baseline undefined
- No existing container security scanning

**Solution with Security Pro Pack:**

**Week 1: Baseline Container Security Audit**

```bash
# Scan all images
for image in $(docker images --format "{{.Repository}}:{{.Tag}}"); do
  /dss $image --output reports/dss-$image.md
done

# Aggregate findings
# - Total: 247 vulnerabilities across 25 images
# -  Critical: 18 CVEs
# -  Critical: 12 images running as root
# -  Critical: 8 images with hardcoded secrets
```

**Week 1-2: Systematic Remediation**

**Priority 1: Root User Issues (2 days)**

```dockerfile
# Before (Vulnerable)
FROM node:16
COPY . /app
CMD ["node", "server.js"]  # Runs as root!

# After (Secure)
FROM node:16-alpine
COPY . /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
CMD ["node", "server.js"]
```

**Priority 2: Update Base Images (3 days)**

```dockerfile
# Before
FROM ubuntu:18.04  # 4 years old, 47 CVEs

# After
FROM ubuntu:22.04  # Latest LTS, 0 CVEs
RUN apt-get update && apt-get upgrade -y
```

**Priority 3: Remove Hardcoded Secrets (2 days)**

```bash
# Before (Secrets in environment variables)
docker run -e DB_PASSWORD="hardcoded" myapp

# After (Kubernetes secrets)
kubectl create secret generic db-secret \
  --from-literal=password=$DB_PASSWORD

# Reference in deployment:
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
```

**Week 3: Validation & CI/CD Integration**

```bash
# Re-scan all images
for image in $(docker images --format "{{.Repository}}:{{.Tag}}"); do
  /dss $image
done

# Result:  Zero critical issues across all 25 images
```

**CI/CD Integration (GitHub Actions):**

```yaml
name: Container Security Scan

on: [push]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Build image
        run: docker build -t ${{ github.repository }}:${{ github.sha }} .

      - name: Security scan
        run: /dss ${{ github.repository }}:${{ github.sha }}

      - name: Block on critical issues
        run: |
          if grep -q " Critical" scan-report.md; then
            exit 1
          fi
```

**Outcome:**
- **Vulnerabilities Fixed:** 247 → 0 critical issues
- **Compliance:** Met Kubernetes security best practices
- **Automation:** Security scanning integrated into CI/CD (prevents future issues)
- **Cost Avoided:** Prevented potential container escape and data breach
- **Time:** 3 weeks (vs. 3-6 months for manual security review)

---

## Use Case 4: HIPAA Audit Preparation

**Scenario:** Your healthcare startup is preparing for first HIPAA audit. Auditors arrive in 4 weeks.

**Challenge:**
- No existing HIPAA documentation
- Small team (5 developers) with limited compliance knowledge
- Electronic Protected Health Information (ePHI) stored in application
- Auditor requires 12 policies and 8 procedures
- Risk analysis required
- Need business associate agreements

**Solution with Security Pro Pack:**

**Week 1: Documentation Generation (8 hours)**

```bash
# Generate all HIPAA documentation
/cdg --framework hipaa --org "HealthTech Startup Inc"

# Generated (23 documents):
# - 12 policies (Security Management, Workforce Security, etc.)
# - 8 procedures (Risk Assessment, Incident Response, etc.)
# - 3 diagrams (Data Flow, Network Architecture, Incident Response)
```

**Week 1: Compliance Gap Analysis (4 hours)**

Ask Compliance Checker agent:
> "Review our application architecture for HIPAA compliance. Focus on Administrative, Physical, and Technical Safeguards."

```
Findings:
Administrative Safeguards:
 Security Management Process documented
 Workforce security policies in place
 Missing: Security training records
 Missing: Sanction policy documentation

Physical Safeguards:
 Facility access controls (cloud provider)
 Workstation security policy
 Missing: Device encryption enforcement

Technical Safeguards:
 Access controls (RBAC implemented)
 Audit logging enabled
 Missing: Automatic logoff after inactivity
 Missing: Encryption of ePHI at rest
```

**Week 2: Technical Remediation (40 hours)**

```javascript
// Fix: Automatic logoff
const sessionTimeout = 15 * 60 * 1000 // 15 minutes (HIPAA requirement)
app.use(session({
  cookie: { maxAge: sessionTimeout },
  rolling: true
}))

// Fix: Encryption at rest
const encryptedFields = ['ssn', 'medical_record_number', 'diagnosis']
// Use AES-256-GCM for ePHI fields
```

```bash
# Verify cryptography implementation
/ca src/models/patient.js

# Result:  AES-256-GCM implemented correctly
```

**Week 3: Security Audit & Risk Analysis (20 hours)**

```bash
# Comprehensive security scan
/ss --verbose

# Threat modeling
```

Ask Threat Modeler:
> "Perform STRIDE threat modeling on our patient data management system. Include data flow diagram."

```
# Risk Analysis Template (from compliance docs)
# Filled out based on threat model findings

Identified Risks:
1. Risk ID: R-001
   Threat: Unauthorized ePHI access via IDOR
   Likelihood: High
   Impact: High
   Risk Level: Critical
   Mitigation: Add authorization checks (implemented)
```

**Week 4: Final Audit Preparation (10 hours)**

- Review all 23 generated documents
- Customize with organization-specific details
- Prepare evidence (logs, encryption certificates, training records)
- Practice audit interview questions

**Audit Result:**
- **Passed** HIPAA audit on first attempt
- **Minor Findings:** 3 (documentation formatting issues only)
- **Major Findings:** 0
- **Critical Findings:** 0

**Outcome:**
- **Time Saved:** 6-8 weeks (manual documentation would take 200+ hours)
- **Cost Saved:** $15,000-$25,000 (HIPAA consultant fees)
- **Risk Avoided:** Potential $50,000 per violation fines
- **Business Impact:** Can now sign contracts with healthcare providers requiring HIPAA compliance

---

## Use Case 5: API Security Before Public Launch

**Scenario:** Your startup is launching a public REST API for third-party developers. You need to ensure it's secure before making it public.

**Challenge:**
- First public API (no prior experience)
- Will be used by thousands of developers
- Needs to handle high traffic
- Reputation risk if vulnerabilities discovered
- No budget for external penetration test

**Solution with Security Pro Pack:**

**Week 1: Comprehensive API Security Audit**

```bash
# Audit API endpoints
/asa https://staging-api.example.com --output api-audit-report.md

# Findings (OWASP API Security Top 10):
# API1 - Broken Object Level Authorization: 3 endpoints vulnerable
# API2 - Broken Authentication: No rate limiting on /auth endpoints
# API3 - Mass Assignment: User can modify admin field
# API4 - Unrestricted Resource Consumption: No pagination limits
# API8 - Security Misconfiguration: Debug mode enabled
```

**Week 2: Systematic Remediation**

**Fix 1: Broken Object Level Authorization**

```javascript
// Before (Vulnerable)
app.get('/api/projects/:id', authenticate, (req, res) => {
  const project = await Project.findById(req.params.id)
  res.json(project)  // Any user can access any project!
})

// After (Secure)
app.get('/api/projects/:id', authenticate, async (req, res) => {
  const project = await Project.findById(req.params.id)

  if (!project) {
    return res.status(404).json({ error: 'Not found' })
  }

  // Verify ownership or team membership
  if (!project.hasAccess(req.user.id)) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  res.json(project)
})
```

**Fix 2: Rate Limiting**

```javascript
// Authentication rate limiting
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Too many login attempts'
})

app.post('/auth/login', authLimiter, loginHandler)
app.post('/auth/register', authLimiter, registerHandler)

// General API rate limiting (per API key)
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100, // 100 requests per minute
  keyGenerator: (req) => req.headers['x-api-key']
})

app.use('/api/', apiLimiter)
```

**Fix 3: Mass Assignment Protection**

```javascript
// Allowlist approach
const allowedUserFields = ['name', 'email', 'avatar']

app.patch('/api/users/:id', authenticate, (req, res) => {
  const updates = {}

  allowedUserFields.forEach(field => {
    if (req.body[field] !== undefined) {
      updates[field] = req.body[field]
    }
  })

  // Admin field cannot be modified by user
  await User.update(req.params.id, updates)
})
```

**Week 3: Threat Modeling**

Ask Threat Modeler:
> "Perform STRIDE threat modeling on our public API architecture. Include authentication flow, data access patterns, and rate limiting."

```
Identified Threats:
1. Spoofing: API key theft
   Mitigation: API key rotation, IP allowlisting for production keys

2. Tampering: Request replay attacks
   Mitigation: Add timestamp validation, HMAC signatures

3. Denial of Service: API abuse
   Mitigation: Tiered rate limits (free: 100/min, paid: 1000/min)
```

**Week 4: Documentation & Launch Prep**

```bash
# Generate OpenAPI documentation
# Include security requirements in docs

# Final security scan
/asa https://api.example.com --comprehensive

# Result:  All OWASP API Top 10 vulnerabilities addressed
```

**Public Launch:**
- **Security Score:** A+ (0 critical, 0 high vulnerabilities)
- **Performance:** Handles 10,000 req/min with auto-scaling
- **Uptime:** 99.99% first month
- **Security Incidents:** 0 in first 6 months

**Outcome:**
- **Prevented:** API abuse and data breaches
- **Developer Trust:** Developers feel confident using secure API
- **Business Impact:** 1,000+ developers integrated in first month
- **Cost Avoided:** $10,000-$20,000 (external penetration test)

---

## Use Case 6: Cryptography Implementation Review

**Scenario:** Your team implemented custom encryption for user data. You need to verify it's implemented correctly before production.

**Challenge:**
- Team unfamiliar with cryptography best practices
- Storing sensitive PII (personally identifiable information)
- GDPR compliance required (data protection by design)
- Custom crypto implementation (high risk)

**Solution with Security Pro Pack:**

**Day 1: Crypto Audit (2 hours)**

```bash
# Review all cryptographic code
/ca src/crypto/ --output crypto-audit-report.md

# Critical Findings:
#  Using MD5 for password hashing (completely broken)
#  Hardcoded AES encryption key
#  Fixed IV reuse (same IV for all encryptions)
#  AES-CBC without HMAC (unauthenticated encryption)
#  No key rotation mechanism
```

**Day 1-2: Expert Consultation (3 hours)**

Ask Crypto Expert agent:
> "Review our user data encryption implementation. We're using AES-256-CBC for PII encryption and MD5 for password hashing. What are the vulnerabilities and how do we fix them?"

```
Agent Response:

Critical Issues:

1. MD5 Password Hashing:
    MD5 is completely broken (rainbow tables exist)
    Fix: Use Argon2id

   Before:
   const hash = crypto.createHash('md5').update(password).digest('hex')

   After:
   const argon2 = require('argon2')
   const hash = await argon2.hash(password, {
     type: argon2.argon2id,
     memoryCost: 65536,
     timeCost: 3
   })

2. Hardcoded Encryption Key:
    If source code leaks, all data compromised
    Fix: Use environment variables + key management service

3. Fixed IV Reuse:
    Reveals patterns in encrypted data
    Fix: Generate random IV for each encryption

4. Unauthenticated Encryption:
    Attacker can modify ciphertext without detection
    Fix: Use AES-256-GCM (authenticated encryption)
```

**Day 3-5: Implementation Fixes (24 hours)**

```javascript
//  SECURE: Argon2id password hashing
const argon2 = require('argon2')

async function hashPassword(password) {
  return await argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536,  // 64 MB
    timeCost: 3,
    parallelism: 4
  })
}

//  SECURE: AES-256-GCM with random IV
const crypto = require('crypto')

function encryptPII(plaintext) {
  const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex')  // From env
  const iv = crypto.randomBytes(12)  // Random IV for each encryption
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)

  let encrypted = cipher.update(plaintext, 'utf8', 'hex')
  encrypted += cipher.final('hex')

  const authTag = cipher.getAuthTag()  // Authentication tag

  return {
    iv: iv.toString('hex'),
    encrypted,
    authTag: authTag.toString('hex')
  }
}
```

**Day 6: Re-audit & Validation (2 hours)**

```bash
# Re-audit crypto implementation
/ca src/crypto/

# Result:  All critical issues resolved
# Remaining: 2 medium-severity best practice recommendations
```

**Outcome:**
- **Prevented:** Catastrophic data breach (weak MD5 passwords, compromised encryption)
- **GDPR Compliance:** Achieved "data protection by design" requirement
- **Reputation:** Avoided security researcher disclosure of broken crypto
- **Financial:** Prevented potential €20 million GDPR fine

---

## Use Case 7: Security Training for Development Team

**Scenario:** Your startup hired 3 junior developers. They need security training but you have no dedicated security team.

**Challenge:**
- Junior developers with limited security knowledge
- No budget for external security training ($2,000+ per person)
- Need practical, hands-on learning
- Want to integrate security into development workflow

**Solution with Security Pro Pack:**

**Week 1: Hands-On Security Learning**

**Exercise 1: Identify Vulnerabilities**

```bash
# Give each developer a sample vulnerable app
git clone https://github.com/example/vulnerable-app

# Task: Run security scan and identify all vulnerabilities
/ss vulnerable-app/

# Expected findings:
# - SQL injection
# - XSS vulnerabilities
# - Hardcoded secrets
# - Missing authentication
```

**Exercise 2: Learn from Experts**

Assign each developer to work with an expert agent:

- Developer 1: Ask Security Auditor Expert to explain OWASP Top 10
- Developer 2: Ask Penetration Tester to demonstrate SQL injection attack
- Developer 3: Ask Crypto Expert to explain proper password hashing

**Exercise 3: Fix Vulnerabilities**

```bash
# After fixing, re-scan to validate
/ss vulnerable-app/

# Goal: Reduce critical issues from 15 → 0
```

**Week 2: Real-World Application**

**Task:** Secure team's actual project

```bash
# Each developer scans a different module
Developer 1: /ss src/auth/
Developer 2: /ss src/api/
Developer 3: /ss src/database/

# Fix all critical and high-severity issues
# Pair program with expert agents for guidance
```

**Week 3: Advanced Topics**

**Day 1-2: Compliance**

Ask Compliance Checker:
> "Explain PCI DSS requirements for our payment processing module"

**Day 3-4: Threat Modeling**

Ask Threat Modeler:
> "Teach me how to perform STRIDE threat modeling on a user authentication system"

**Day 5: Container Security**

```bash
# Scan Docker containers
/dss postgres:latest
/dss redis:latest
/dss myapp:latest

# Learn: Why running as root is dangerous
# Learn: How to create minimal, secure containers
```

**Ongoing: Security Champions**

- Each developer becomes "security champion" for their module
- Weekly security scans in team meeting
- Share findings and fixes with team

**Outcome:**
- **Knowledge:** Developers gained practical security skills
- **Cost Saved:** $6,000 (3 developers × $2,000 training cost)
- **Culture:** Security-first mindset embedded in team
- **Metrics:**
  - Week 1: 45 critical vulnerabilities
  - Week 4: 0 critical vulnerabilities
  - Month 3: 95% of code passes security scan on first try

---

## Summary: Value Across Use Cases

| Use Case | Time Saved | Cost Saved | Risk Avoided |
|----------|------------|------------|--------------|
| Pre-Production Gate | 2-3 weeks | $3,000-$5,000 | PCI DSS fines |
| Incident Response | 1-2 weeks | N/A | €20M GDPR fine |
| Container Security | 3-6 months | $10,000-$20,000 | Data breach |
| HIPAA Audit | 6-8 weeks | $15,000-$25,000 | $50K per violation |
| API Security | 3-4 weeks | $10,000-$20,000 | Public exploit |
| Crypto Review | 1-2 weeks | $5,000-$10,000 | €20M GDPR fine |
| Team Training | Ongoing | $6,000+ | Security incidents |

**Total Value:** $49,000-$80,000 in direct cost savings + millions in risk avoidance

---

**Ready to apply these workflows to your projects? Install Security Pro Pack today!**

---
name: bamboohr-security-basics
description: |
  Apply BambooHR security best practices for API keys, webhook verification,
  and PII data handling compliance.
  Use when securing API keys, implementing webhook signature validation,
  or handling sensitive employee data from BambooHR.
  Trigger with phrases like "bamboohr security", "bamboohr secrets",
  "secure bamboohr", "bamboohr PII", "bamboohr data protection".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, security]
compatible-with: claude-code
---

# BambooHR Security Basics

## Overview

Security best practices for BambooHR API integrations covering API key management, webhook HMAC verification, PII handling, and access control. BambooHR contains highly sensitive employee data (SSNs, salaries, addresses) — treat every integration as PII-critical.

## Prerequisites

- BambooHR API access configured
- Understanding of environment variables and secrets management
- Access to BambooHR admin settings

## Instructions

### Step 1: API Key Security

```bash
# .env (NEVER commit to git)
BAMBOOHR_API_KEY=your-api-key
BAMBOOHR_COMPANY_DOMAIN=yourcompany
BAMBOOHR_WEBHOOK_SECRET=your-webhook-hmac-secret

# .gitignore — MUST include these
.env
.env.local
.env.*.local
*.pem
```

**Key management rules:**
- Each environment (dev/staging/prod) uses a separate API key
- Create API keys under service accounts, not personal accounts
- API keys inherit the permissions of the user who created them
- Rotate keys quarterly; immediately rotate if exposed

**Key rotation procedure:**

```bash
# 1. Generate new key in BambooHR: Profile > API Keys > Add New Key
# 2. Update secret store
aws secretsmanager update-secret --secret-id bamboohr/api-key --secret-string "new-key"
# Or for GCP:
echo -n "new-key" | gcloud secrets versions add bamboohr-api-key --data-file=-

# 3. Deploy with new key
# 4. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -u "new-key:x" \
  "https://api.bamboohr.com/api/gateway.php/${DOMAIN}/v1/employees/directory" \
  -H "Accept: application/json"

# 5. Delete old key in BambooHR dashboard
```

### Step 2: Webhook Signature Verification

BambooHR signs webhook payloads with SHA-256 HMAC. Verify every webhook before processing.

```typescript
import crypto from 'crypto';

function verifyBambooHRWebhook(
  rawBody: Buffer | string,
  signature: string,
  timestamp: string,
  secret: string,
): boolean {
  // 1. Reject old timestamps (replay attack protection — 5 min window)
  const age = Date.now() - parseInt(timestamp, 10) * 1000;
  if (age > 300_000 || age < -60_000) {
    console.error(`Webhook timestamp outside 5-minute window: ${age}ms`);
    return false;
  }

  // 2. Compute expected HMAC
  const payload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  // 3. Timing-safe comparison (prevents timing attacks)
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expected, 'hex'),
    );
  } catch {
    return false;
  }
}

// Express middleware
app.post('/webhooks/bamboohr',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const sig = req.headers['x-bamboohr-signature'] as string;
    const ts = req.headers['x-bamboohr-timestamp'] as string;

    if (!verifyBambooHRWebhook(req.body, sig, ts, process.env.BAMBOOHR_WEBHOOK_SECRET!)) {
      return res.status(401).json({ error: 'Invalid webhook signature' });
    }

    // Safe to process
    const event = JSON.parse(req.body.toString());
    handleWebhookEvent(event);
    res.status(200).json({ received: true });
  },
);
```

### Step 3: PII Data Handling

BambooHR employee data includes PII and sensitive fields. Handle accordingly.

```typescript
// Define sensitivity levels for BambooHR fields
const FIELD_SENSITIVITY: Record<string, 'public' | 'internal' | 'confidential' | 'restricted'> = {
  firstName: 'internal',
  lastName: 'internal',
  displayName: 'internal',
  jobTitle: 'internal',
  department: 'internal',
  workEmail: 'internal',
  homeEmail: 'confidential',
  homePhone: 'confidential',
  mobilePhone: 'confidential',
  address1: 'confidential',
  dateOfBirth: 'confidential',
  ssn: 'restricted',
  payRate: 'restricted',
  payType: 'restricted',
  maritalStatus: 'confidential',
  gender: 'confidential',
  ethnicity: 'restricted',
  eeo: 'restricted',
};

// Only request fields you actually need
function safeFieldRequest(neededFields: string[]): string[] {
  const restricted = neededFields.filter(f => FIELD_SENSITIVITY[f] === 'restricted');
  if (restricted.length > 0) {
    console.warn(`Requesting restricted fields: ${restricted.join(', ')}. Ensure compliance.`);
  }
  return neededFields;
}

// Redact PII from logs
function redactForLogging(employee: Record<string, string>): Record<string, string> {
  const redacted = { ...employee };
  const sensitiveFields = ['ssn', 'dateOfBirth', 'homeEmail', 'homePhone',
    'mobilePhone', 'address1', 'payRate', 'gender', 'ethnicity'];
  for (const field of sensitiveFields) {
    if (redacted[field]) redacted[field] = '***REDACTED***';
  }
  return redacted;
}
```

### Step 4: Access Control Audit

```typescript
// Audit which API key permissions are actually needed
interface AccessAudit {
  endpoint: string;
  method: string;
  requiredPermission: string;
  used: boolean;
}

const ACCESS_MAP: AccessAudit[] = [
  { endpoint: '/employees/directory', method: 'GET', requiredPermission: 'employee:read', used: true },
  { endpoint: '/employees/{id}/', method: 'GET', requiredPermission: 'employee:read', used: true },
  { endpoint: '/employees/{id}/', method: 'POST', requiredPermission: 'employee:write', used: false },
  { endpoint: '/employees/{id}/tables/compensation', method: 'GET', requiredPermission: 'admin', used: false },
  { endpoint: '/time_off/requests/', method: 'GET', requiredPermission: 'timeoff:read', used: true },
  { endpoint: '/webhooks/', method: 'POST', requiredPermission: 'webhooks:manage', used: false },
];

// Principle of least privilege: only enable permissions for endpoints you use
const neededPermissions = new Set(
  ACCESS_MAP.filter(a => a.used).map(a => a.requiredPermission),
);
console.log('Required permissions:', [...neededPermissions].join(', '));
```

### Step 5: Security Checklist

```markdown
- [ ] API keys stored in environment variables or secret manager (never in code)
- [ ] `.env` files in `.gitignore`
- [ ] Separate API keys for dev / staging / prod
- [ ] API key user has minimum required access level
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] Webhook timestamp checked (reject > 5 min old)
- [ ] PII fields redacted from logs and error messages
- [ ] Only requesting needed fields (not SELECT *)
- [ ] Restricted fields (SSN, salary) only accessed when required
- [ ] Data at rest encrypted if storing BambooHR data locally
- [ ] API key rotation scheduled (quarterly minimum)
- [ ] git-secrets or truffleHog scanning enabled
```

## Output

- Secure API key storage and rotation procedure
- Webhook HMAC verification middleware
- PII classification and redaction utilities
- Access control audit framework
- Security compliance checklist

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key in git | `git-secrets`, GitHub secret scanning | Rotate immediately; add pre-commit hook |
| Webhook replay attack | Timestamp > 5 min old | Reject and alert |
| PII in logs | Log audit | Add redaction middleware |
| Over-permissioned key | Access audit | Create new key with minimal permissions |

## Resources

- [BambooHR Webhooks Security](https://documentation.bamboohr.com/docs/webhooks)
- [BambooHR Authentication](https://documentation.bamboohr.com/docs/getting-started)

## Next Steps

For production deployment, see `bamboohr-prod-checklist`.

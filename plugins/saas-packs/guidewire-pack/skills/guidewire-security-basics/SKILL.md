---
name: guidewire-security-basics
description: 'Implement Guidewire security: OAuth2 JWT, API roles, Gosu secure coding,
  and data protection.

  Trigger: "guidewire security basics", "security-basics".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- insurance
- guidewire
compatibility: Designed for Claude Code
---
# Guidewire Security Basics

## Overview
Guidewire manages insurance policy administration, claims processing, and billing containing policyholder PII (SSNs, driver's license numbers, medical records for claims), financial settlement data, and adjuster notes. A breach exposes claimant personal information, policy terms, and payment histories across the entire insurance book of business. Secure OAuth2 JWT tokens, Cloud API roles, Gosu custom code, and any integration touching policy or claims data.

## API Key Management
```typescript
function createGuidewireClient(): { token: string; baseUrl: string } {
  const clientId = process.env.GUIDEWIRE_CLIENT_ID;
  const clientSecret = process.env.GUIDEWIRE_CLIENT_SECRET;
  const tokenUrl = process.env.GUIDEWIRE_TOKEN_URL;
  if (!clientId || !clientSecret || !tokenUrl) {
    throw new Error("Missing GUIDEWIRE_CLIENT_ID, CLIENT_SECRET, or TOKEN_URL");
  }
  // OAuth2 tokens are short-lived JWTs — never cache beyond expiry
  console.log("Guidewire OAuth2 client initialized for:", tokenUrl);
  return { token: "", baseUrl: process.env.GUIDEWIRE_API_URL! };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyGuidewireWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-guidewire-signature"] as string;
  const secret = process.env.GUIDEWIRE_WEBHOOK_SECRET!;
  const expected = crypto.createHmac("sha256", secret).update(req.body).digest("hex");
  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    res.status(401).send("Invalid signature");
    return;
  }
  next();
}
```

## Input Validation
```typescript
import { z } from "zod";

const ClaimSchema = z.object({
  claim_number: z.string().regex(/^CLM-\d{8,12}$/),
  policy_number: z.string().regex(/^POL-\d{8,12}$/),
  claimant_id: z.string().uuid(),
  loss_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  loss_type: z.enum(["auto", "property", "liability", "workers_comp", "medical"]),
  reserve_amount: z.number().nonnegative().max(10_000_000),
});

function validateClaimData(data: unknown) {
  return ClaimSchema.parse(data);
}
```

## Data Protection
```typescript
const GUIDEWIRE_PII_FIELDS = ["ssn", "drivers_license", "medical_records", "bank_account", "claimant_dob", "adjuster_notes"];

function redactGuidewireLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of GUIDEWIRE_PII_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] OAuth2 client credentials stored in secrets manager
- [ ] JWT tokens treated as short-lived, never cached beyond expiry
- [ ] API roles assigned per-endpoint in GCC (least privilege)
- [ ] Policyholder SSN and medical data never logged
- [ ] SAML SSO enforced for Jutro frontend access
- [ ] Gosu custom code uses `ServerUtil` for auth, never hardcoded credentials
- [ ] PII encrypted in custom entities
- [ ] Claims data access audited per adjuster

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked OAuth2 credentials | Full policy and claims data access | Secrets manager + short-lived JWTs |
| Overly broad API roles | Adjuster accesses unrelated claims | Per-endpoint GCC role scoping |
| PII in Gosu logs | Policyholder SSN/medical data exposure | Field-level redaction in custom code |
| Hardcoded credentials in Gosu | Credential theft from source code | `ServerUtil` auth + code review gates |
| Unencrypted claims data | Insurance regulatory violation | Encryption at rest for custom entities |

## Resources
- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `guidewire-prod-checklist`.

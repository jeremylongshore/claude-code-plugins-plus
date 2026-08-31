---
name: appfolio-security-basics
description: 'Secure AppFolio API credentials and tenant data.

  Trigger: "appfolio security".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Security Basics

## Overview

AppFolio manages property portfolios containing tenant PII (SSNs, bank accounts, lease terms), owner financial data, and maintenance vendor records. A breach exposes rent rolls, payment histories, and personally identifiable tenant information across every managed property. Secure every integration point: API credentials, webhook endpoints, and any pipeline that touches tenant or owner financial records.

## Prerequisites

- A verified AppFolio contract stating the permitted endpoint, authentication,
  webhook, data-retention, and portfolio-scoping requirements for the target
  environment.
- A secret manager, separate sandbox credentials, and a named security owner
  for rotations, access review, and incident response.
- A raw-body route configuration for any signed webhook: signature verification
  must run before JSON parsing, mutation, or logging of the request payload.

## Instructions

1. Load credentials from the approved secret boundary, validate the HTTPS base
   URL, and give each worker only the scope it requires.
2. Receive webhook requests as bounded raw bytes, validate the signature shape
   and HMAC in constant time, then parse and schema-validate the payload.
3. Encrypt or minimize sensitive stored fields, redact nested PII before logs,
   and record access through a durable audit trail.
4. Run a rotation and webhook-negative-path rehearsal in sandbox; a failed
   signature, missing secret, or unverifiable endpoint is a no-go condition.

## API Key Management

```typescript
import https from "https";
import axios, { AxiosInstance } from "axios";

function createAppFolioClient(): AxiosInstance {
  const clientId = process.env.APPFOLIO_CLIENT_ID;
  const clientSecret = process.env.APPFOLIO_CLIENT_SECRET;
  const baseUrl = process.env.APPFOLIO_BASE_URL;
  if (!clientId || !clientSecret || !baseUrl) {
    throw new Error("Missing APPFOLIO_CLIENT_ID, APPFOLIO_CLIENT_SECRET, or APPFOLIO_BASE_URL");
  }
  return axios.create({
    baseURL: baseUrl,
    auth: { username: clientId, password: clientSecret },
    httpsAgent: new https.Agent({ minVersion: "TLSv1.2", rejectUnauthorized: true }),
  });
}
```

## Webhook Signature Verification

```typescript
import crypto from "crypto";

function verifyAppFolioWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-appfolio-signature"] as string;
  const secret = process.env.APPFOLIO_WEBHOOK_SECRET!;
  // req.body must be a bounded raw Buffer from the route's raw-body middleware.
  const expected = Buffer.from(crypto.createHmac("sha256", secret).update(req.body).digest("hex"));
  const received = signature ? Buffer.from(signature) : Buffer.alloc(0);
  if (received.length !== expected.length || !crypto.timingSafeEqual(received, expected)) {
    res.status(401).send("Invalid signature");
    return;
  }
  next();
}
```

## Input Validation

```typescript
import { z } from "zod";
const TenantSchema = z.object({
  tenant_id: z.string().uuid(),
  first_name: z.string().min(1).max(100),
  last_name: z.string().min(1).max(100),
  email: z.string().email(),
  unit_id: z.string().uuid(),
  lease_start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  rent_amount: z.number().positive().max(100000),
});

function validateTenantPayload(data: unknown) {
  return TenantSchema.parse(data);
}
```

## Data Protection

```typescript
const APPFOLIO_PII_FIELDS = ["ssn", "bank_account", "routing_number", "date_of_birth", "drivers_license"];

function redactAppFolioLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of APPFOLIO_PII_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist

- [ ] API credentials stored in secrets manager, not `.env` in production
- [ ] HTTPS enforced with TLS 1.2+ for all API calls
- [ ] Tenant SSN and bank account numbers never logged
- [ ] Webhook signatures verified on every inbound request
- [ ] API credentials rotated quarterly
- [ ] Access scoped to minimum required property endpoints
- [ ] Rent payment data encrypted at rest
- [ ] Audit trail enabled for tenant record access

## Output

- A least-privilege, TLS-validated client configuration with no credential
  material written to logs or source
- A fail-closed webhook decision before payload parsing or downstream mutation
- A redacted audit record and a security go/no-go result for each integration
  change or credential rotation

## Examples

For a webhook onboarding rehearsal, use a synthetic sandbox payload and test
the valid signature, a missing signature, a malformed-length signature, and a
replayed event. Confirm that only the valid raw-body request reaches the schema
parser, while rejected attempts create a redacted security event and no tenant
record change. If raw-body handling, secret access, signature validation, or
audit persistence is unavailable, disable the endpoint and remediate before
accepting production events.

## Error Handling

| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API credentials | Full property portfolio exposure | Secrets manager + rotation |
| Unvalidated webhook payloads | Spoofed tenant updates | HMAC signature verification |
| Tenant PII in logs | Compliance violation (state privacy laws) | Field-level redaction |
| Overly broad API scope | Lateral access to unrelated properties | Per-property credential scoping |
| Unencrypted payment data | Financial data breach | TLS 1.2+ in transit, AES at rest |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

See `appfolio-prod-checklist`.

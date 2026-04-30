---
name: flexport-security-basics
description: 'Apply Flexport API security best practices including webhook signature
  verification,

  API key rotation, and least-privilege access patterns.

  Trigger: "flexport security", "flexport webhook signature", "secure flexport API
  key".

  '
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- logistics
- flexport
compatibility: Designed for Claude Code
---
# Flexport Security Basics

## Overview
Flexport manages global freight logistics containing shipping manifests, customs declarations, commercial invoices, and supply chain partner data. A breach exposes trade routes, commodity values, importer/exporter identities, and customs brokerage details. Secure API credentials, webhook endpoints, and any pipeline that processes shipment tracking or purchase order data.

## API Key Management
```typescript
function createFlexportClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.FLEXPORT_API_KEY;
  if (!apiKey) {
    throw new Error("Missing FLEXPORT_API_KEY — store in secrets manager, never in .env in production");
  }
  // Never log the key; log only a hash suffix for debugging
  console.log("Flexport client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.flexport.com/v2" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyFlexportWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-hub-signature"] as string;
  const secret = process.env.FLEXPORT_WEBHOOK_SECRET!;
  const expected = "sha256=" + crypto.createHmac("sha256", secret).update(req.body).digest("hex");
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

const ShipmentQuerySchema = z.object({
  shipment_id: z.string().regex(/^FLEX-\d+$/),
  container_number: z.string().regex(/^[A-Z]{4}\d{7}$/).optional(),
  origin_port: z.string().length(5).optional(),
  destination_port: z.string().length(5).optional(),
  hs_code: z.string().regex(/^\d{6,10}$/).optional(),
});

function validateShipmentQuery(data: unknown) {
  return ShipmentQuerySchema.parse(data);
}
```

## Data Protection
```typescript
const FLEXPORT_SENSITIVE_FIELDS = ["customs_value", "commercial_invoice", "importer_tax_id", "broker_credentials", "hs_code"];

function redactFlexportLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of FLEXPORT_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API keys stored in secrets manager, `.env` files in `.gitignore`
- [ ] Webhook signatures verified on every inbound request
- [ ] Different keys for dev/staging/prod environments
- [ ] Key rotation scheduled quarterly with dual-key transition
- [ ] Git history scanned for leaked keys
- [ ] HTTPS enforced for all API calls
- [ ] Request/response logging redacts auth headers and customs values
- [ ] Least-privilege access: read-only tokens for dashboards, run tokens for operations

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Full shipment and customs data exposure | Secrets manager + quarterly rotation |
| Unverified webhooks | Spoofed shipment status updates | HMAC-SHA256 signature verification |
| Customs data in logs | Trade compliance violation | Field-level redaction pipeline |
| Overly broad API scope | Access to unrelated shipment data | Role-scoped tokens per team |
| Unencrypted commercial invoices | Financial data breach | TLS 1.2+ in transit, AES at rest |

## Resources
- [Flexport Webhooks](https://apidocs.flexport.com/v2/tag/Webhook-Endpoints/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `flexport-prod-checklist`.

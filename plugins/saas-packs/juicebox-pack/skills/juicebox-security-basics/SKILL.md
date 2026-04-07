---
name: juicebox-security-basics
description: |
  Apply Juicebox security best practices.
  Trigger: "juicebox security", "juicebox api key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Security Basics

## Overview
Juicebox provides AI-powered people search and analysis, processing datasets containing professional profiles, contact enrichment data, and query results. Security concerns include API key protection, GDPR/CCPA compliance for candidate and contact data, data retention policy enforcement, and ensuring enriched contact information (emails, phone numbers) is not leaked through logs or unencrypted storage. A compromised API key grants access to people search and enrichment capabilities.

## API Key Management
```typescript
function createJuiceboxClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.JUICEBOX_API_KEY;
  if (!apiKey) {
    throw new Error("Missing JUICEBOX_API_KEY — store in secrets manager, never in code");
  }
  // Juicebox keys access people data — treat as PII-adjacent
  console.log("Juicebox client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.juicebox.ai/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyJuiceboxWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-juicebox-signature"] as string;
  const secret = process.env.JUICEBOX_WEBHOOK_SECRET!;
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

const PeopleSearchSchema = z.object({
  query: z.string().min(1).max(500),
  filters: z.object({
    location: z.string().optional(),
    company: z.string().optional(),
    title: z.string().optional(),
    industry: z.string().optional(),
  }).optional(),
  max_results: z.number().int().min(1).max(100).default(25),
  enrich_contacts: z.boolean().default(false),
});

function validateSearchQuery(data: unknown) {
  return PeopleSearchSchema.parse(data);
}
```

## Data Protection
```typescript
const JUICEBOX_PII_FIELDS = ["personal_email", "phone_number", "social_profiles", "home_address", "enrichment_data"];

function redactJuiceboxLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of JUICEBOX_PII_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API keys stored in secrets manager, separate keys per environment
- [ ] Enriched contact data encrypted at rest
- [ ] GDPR consent documented for EU candidate data
- [ ] CCPA opt-out mechanism implemented for California residents
- [ ] Data retention policy enforced (auto-delete after defined period)
- [ ] Contact enrichment results never logged in plaintext
- [ ] Search queries redacted in application logs
- [ ] Pre-commit hook blocks `jb_live_*` credential patterns

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Unauthorized people search and enrichment | Secrets manager + key rotation |
| Contact data in logs | PII exposure violating GDPR/CCPA | Field-level redaction pipeline |
| Missing data retention | Stale candidate data accumulates | Automated retention enforcement |
| Enrichment without consent | Privacy regulation violation | Consent gate before enrichment calls |
| Unencrypted contact storage | Bulk PII breach from database leak | Encryption at rest + access controls |

## Resources
- [Juicebox Privacy](https://juicebox.ai/privacy)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `juicebox-prod-checklist`.

---
name: fondo-security-basics
description: |
  Apply security best practices for Fondo including OAuth token management,
  financial data protection, SOC 2 compliance, and access control.
  Trigger: "fondo security", "fondo data protection", "fondo SOC 2", "fondo access control".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Security Basics

## Overview
Fondo handles startup tax preparation, bookkeeping, and R&D tax credits containing SSNs, EINs, bank account details, revenue figures, and complete tax returns. A breach exposes founder personal tax data, company financials, and IRS filing details. Protect OAuth connections to banking/payroll systems, exported financial documents, and team access controls with the same rigor as a CPA firm.

## API Key Management
```typescript
function createFondoClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.FONDO_API_KEY;
  if (!apiKey) {
    throw new Error("Missing FONDO_API_KEY — store in secrets manager, never in code");
  }
  // Fondo keys access tax returns and SSN/EIN data — treat as highest sensitivity
  console.log("Fondo client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.fondo.com/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyFondoWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-fondo-signature"] as string;
  const secret = process.env.FONDO_WEBHOOK_SECRET!;
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

const TaxFilingSchema = z.object({
  entity_id: z.string().uuid(),
  tax_year: z.number().int().min(2015).max(2030),
  filing_type: z.enum(["1120", "1120S", "1065", "941", "R&D_credit"]),
  ein: z.string().regex(/^\d{2}-\d{7}$/),
  revenue: z.number().nonnegative(),
  status: z.enum(["draft", "review", "filed", "amended"]),
});

function validateTaxFiling(data: unknown) {
  return TaxFilingSchema.parse(data);
}
```

## Data Protection
```typescript
const FONDO_PII_FIELDS = ["ssn", "ein", "bank_account", "routing_number", "tax_return_url", "revenue", "salary"];

function redactFondoLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of FONDO_PII_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API keys stored in secrets manager, never in code
- [ ] OAuth connections (Gusto, QuickBooks, Plaid, Stripe) reviewed quarterly
- [ ] Financial exports never committed to git (`.gitignore` enforced)
- [ ] SSN and EIN values never logged in plaintext
- [ ] Team roles follow least-privilege (Owner/Admin/Viewer/CPA)
- [ ] Two-factor authentication enabled on Fondo account
- [ ] Exported tax documents encrypted with GPG before storage
- [ ] Bank connections use Plaid (encrypted, not screen-scraping)

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Full access to tax returns and SSN/EIN data | Secrets manager + rotation |
| Unencrypted financial exports | Tax data exposed via CSV on disk | GPG encryption + secure deletion |
| Stale OAuth tokens | Compromised banking/payroll connections | Quarterly OAuth review + revocation |
| Overly broad team access | Viewer sees SSN/salary data | Role-based access control enforcement |
| Tax data in application logs | IRS compliance violation | Field-level PII redaction |

## Resources
- [Fondo Security](https://fondo.com)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `fondo-prod-checklist`.

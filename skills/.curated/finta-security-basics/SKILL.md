---
name: finta-security-basics
description: 'Secure Finta fundraising data and investor information.

  Trigger with phrases like "finta security", "finta data privacy".

  '
allowed-tools: Read, Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Security Basics

## Overview

Finta manages fundraising pipelines containing investor contact information, term sheet details, valuation data, cap table snapshots, and deal room documents. A breach exposes confidential fundraising strategy, investor relationships, and financial terms that could damage competitive positioning. Protect API credentials, deal room access controls, and any integration that syncs investor data to external CRMs or spreadsheets.

## Prerequisites

- A named owner for the fundraising workspace and a current access-review cadence.
- Secrets held in an approved secret manager; use synthetic records for development and documentation.
- A written list of approved destinations before exporting or syncing investor data.

## Instructions

1. Grant the smallest practical role to each team member and deal-room participant; remove access when a round, engagement, or contractor relationship ends.
2. Keep credentials out of source control, shell history, tickets, and support attachments. Rotate a credential immediately after suspected exposure.
3. Classify contact, valuation, term, cap-table, and document data as sensitive. Export only the fields required for a specific purpose and encrypt approved exports at rest.
4. Verify webhook authenticity before processing an event, record only a redacted event identifier for diagnostics, and make downstream processing idempotent.
5. Review connected CRM, email, and automation permissions before enabling a sync; disable a sync that cannot limit fields or recipients.

## API Key Management

```typescript
function createFintaClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.FINTA_API_KEY;
  if (!apiKey) {
    throw new Error("Missing FINTA_API_KEY — store in secrets manager, never in code");
  }
  // Finta keys access investor contacts and financial terms — treat as highly sensitive
  console.log("Finta client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.trustfinta.com/v1" };
}
```

## Webhook Signature Verification

```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyFintaWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-finta-signature"] as string;
  const secret = process.env.FINTA_WEBHOOK_SECRET!;
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

const InvestorContactSchema = z.object({
  investor_id: z.string().uuid(),
  firm_name: z.string().min(1).max(200),
  contact_email: z.string().email(),
  deal_stage: z.enum(["prospect", "contacted", "meeting", "term_sheet", "closed", "passed"]),
  check_size: z.number().positive().optional(),
  valuation_cap: z.number().positive().optional(),
});

function validateInvestorData(data: unknown) {
  return InvestorContactSchema.parse(data);
}
```

## Data Protection

```typescript
const FINTA_SENSITIVE_FIELDS = ["valuation_cap", "check_size", "term_sheet_url", "cap_table", "investor_email", "phone"];

function redactFintaLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of FINTA_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist

- [ ] API keys stored in secrets manager, not in code
- [ ] Strong password + 2FA enabled on Finta account
- [ ] Deal room access permissions reviewed after each round
- [ ] Access revoked for investors who pass on the round
- [ ] Data room set to view-only (no download) for early-stage investors
- [ ] Connected CRM integration permissions audited quarterly
- [ ] Valuation and term sheet data never logged in plaintext
- [ ] Pipeline exports encrypted and never committed to git

## Error Handling

| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Full access to investor pipeline and deal terms | Secrets manager + rotation |
| Overly broad deal room access | Confidential terms exposed to wrong investors | Per-investor permission scoping |
| Unencrypted pipeline exports | Financial strategy leaked via CSV files | GPG encryption + `.gitignore` |
| Stale investor access | Former prospects retain document access | Post-round access review |
| CRM sync without redaction | Valuation data leaks to third-party CRM | Field-level redaction before sync |

## Output

Produce a short security record containing the system owner, approved integrations, role-review date, credential location reference (never the secret), and any access removals or rotations performed. Logs and incident reports should use redacted identifiers and aggregate counts only.

## Examples

For a sandbox workflow, create two fictitious investor records, export only stage and anonymized amount ranges, and confirm that the destination receives neither emails nor document links. If the webhook signature check fails, acknowledge nothing downstream, retain a redacted failure receipt, and investigate the source before retrying.

## Resources

- [Finta Website](https://www.trustfinta.com)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

See `finta-prod-checklist`.

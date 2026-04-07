---
name: fathom-security-basics
description: |
  Secure Fathom API keys and handle meeting data privacy.
  Trigger with phrases like "fathom security", "fathom api key safety", "fathom privacy".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Security Basics

## Overview
Fathom records and transcribes meetings, producing transcripts and action items that contain participant PII (names, emails, spoken content), confidential business decisions, and potentially sensitive negotiations. API keys are per-user and grant access to all meetings the user recorded or that were shared to their team. Protect recording consent workflows, transcript storage, and any analytics pipeline touching meeting content.

## API Key Management
```typescript
function createFathomClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.FATHOM_API_KEY;
  if (!apiKey) {
    throw new Error("Missing FATHOM_API_KEY — store in secrets manager, never in code");
  }
  // Fathom keys are per-user — never share across team members
  console.log("Fathom client initialized (key hash:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.fathom.video/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyFathomWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-fathom-signature"] as string;
  const secret = process.env.FATHOM_WEBHOOK_SECRET!;
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

const MeetingQuerySchema = z.object({
  meeting_id: z.string().uuid(),
  include_transcript: z.boolean().default(false),
  date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  participant_email: z.string().email().optional(),
});

function validateMeetingQuery(data: unknown) {
  return MeetingQuerySchema.parse(data);
}
```

## Data Protection
```typescript
const FATHOM_PII_FIELDS = ["participant_email", "participant_name", "phone_number", "transcript_text"];

function redactFathomLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of FATHOM_PII_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  // Also scrub emails from transcript snippets
  if (typeof redacted.summary === "string") {
    redacted.summary = (redacted.summary as string).replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, "[REDACTED_EMAIL]");
  }
  return redacted;
}
```

## Security Checklist
- [ ] API key stored in secrets manager, never in code
- [ ] Meeting recordings and transcripts encrypted at rest
- [ ] PII redacted in non-production environments
- [ ] Webhook endpoints use HTTPS with signature verification
- [ ] Access logs track per-user API key usage
- [ ] Recording consent verified before processing transcripts
- [ ] Transcript data retention policy enforced
- [ ] Action items containing confidential terms scrubbed before export

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Access to all user meetings and transcripts | Secrets manager + key regeneration |
| Unredacted transcripts in logs | Participant PII exposure | Field-level redaction pipeline |
| Missing recording consent | Legal liability under two-party consent laws | Consent verification before processing |
| Unencrypted transcript storage | Bulk meeting data breach | Encryption at rest + access controls |
| Overly broad meeting sharing | Confidential content exposed to wrong teams | Per-meeting permission scoping |

## Resources
- [Fathom API Documentation](https://fathom.video)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `fathom-prod-checklist`.

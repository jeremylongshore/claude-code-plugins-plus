---
name: grammarly-security-basics
description: |
  Security fundamentals for Grammarly API credential management. Use when setting up
  secure authentication and token handling for Grammarly integrations.
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Security Basics

## Overview
Grammarly processes user-written text content for grammar, tone, and style suggestions. Integrations handle document text that may contain confidential business communications, legal drafts, or personal correspondence. Security concerns include OAuth client credential management, ensuring user text is not persisted or logged unnecessarily, and protecting access tokens that grant read/write access to user documents and suggestion history.

## API Key Management
```typescript
function createGrammarlyClient(): { clientId: string; clientSecret: string } {
  const clientId = process.env.GRAMMARLY_CLIENT_ID;
  const clientSecret = process.env.GRAMMARLY_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    throw new Error("Missing GRAMMARLY_CLIENT_ID or GRAMMARLY_CLIENT_SECRET");
  }
  // Access tokens from client_credentials grant — never persist to disk
  console.log("Grammarly client initialized (client ID:", clientId.slice(0, 8), "...)");
  return { clientId, clientSecret };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyGrammarlyWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-grammarly-signature"] as string;
  const secret = process.env.GRAMMARLY_WEBHOOK_SECRET!;
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

const TextAnalysisSchema = z.object({
  document_id: z.string().uuid(),
  text: z.string().min(1).max(100_000),
  language: z.enum(["en-US", "en-GB", "en-AU", "en-CA"]).default("en-US"),
  domain: z.enum(["general", "academic", "business", "casual"]).default("general"),
  goals: z.array(z.enum(["clarity", "engagement", "delivery", "correctness"])).optional(),
});

function validateTextAnalysis(data: unknown) {
  return TextAnalysisSchema.parse(data);
}
```

## Data Protection
```typescript
const GRAMMARLY_SENSITIVE_FIELDS = ["document_text", "user_email", "access_token", "client_secret", "suggestion_context"];

function redactGrammarlyLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of GRAMMARLY_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  // Truncate any text snippets to prevent content leakage
  if (typeof redacted.text_preview === "string") {
    redacted.text_preview = (redacted.text_preview as string).slice(0, 20) + "...";
  }
  return redacted;
}
```

## Security Checklist
- [ ] Client secret stored in secrets vault, never in source code
- [ ] Access tokens held in memory only, never persisted to disk
- [ ] User document text never logged in application logs
- [ ] HTTPS enforced for all API calls
- [ ] Pre-commit hook blocks credential leaks (`grammarly_client_secret`)
- [ ] Token refresh logic handles expiration gracefully
- [ ] Text content encrypted at rest if cached locally
- [ ] OAuth scopes limited to minimum required permissions

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked client secret | Unauthorized document analysis access | Secrets vault + rotation |
| Access tokens persisted to disk | Token theft enables impersonation | In-memory only + short TTL |
| User text in application logs | Confidential content exposed | Field-level redaction pipeline |
| Overly broad OAuth scopes | Access to unrelated user documents | Minimum-privilege scope requests |
| Unencrypted text cache | Local storage breach exposes content | AES encryption for any local cache |

## Resources
- [Grammarly API](https://developer.grammarly.com/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `grammarly-prod-checklist`.

---
name: glean-security-basics
description: |
  Token security: Indexing tokens have write access -- never expose in frontend.
  Trigger: "glean security basics", "security-basics".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Security Basics

## Overview
Glean indexes and searches across an enterprise's entire knowledge base — Confluence, Google Drive, Slack, GitHub, and dozens more connectors. Security concerns center on indexing token management (write-access tokens that can push content into the search index), client token scoping (user-level search permissions), and document-level access controls. A leaked indexing token allows injecting arbitrary content into enterprise search results.

## API Key Management
```typescript
function createGleanClient(tokenType: "indexing" | "client"): { token: string; baseUrl: string } {
  const token = tokenType === "indexing"
    ? process.env.GLEAN_INDEXING_TOKEN
    : process.env.GLEAN_CLIENT_TOKEN;
  if (!token) {
    throw new Error(`Missing GLEAN_${tokenType.toUpperCase()}_TOKEN — store in secrets manager`);
  }
  // Indexing tokens have WRITE access — never expose in frontend code
  if (tokenType === "indexing") {
    console.log("WARNING: Indexing token loaded — backend use only");
  }
  return { token, baseUrl: `https://${process.env.GLEAN_INSTANCE}.glean.com/api` };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyGleanWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-glean-signature"] as string;
  const secret = process.env.GLEAN_WEBHOOK_SECRET!;
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

const IndexDocumentSchema = z.object({
  datasource: z.string().min(1).max(100),
  document_id: z.string().min(1).max(500),
  title: z.string().min(1).max(500),
  body: z.string().max(1_000_000),
  allowed_users: z.array(z.string().email()).optional(),
  allowed_groups: z.array(z.string()).optional(),
  permissions_type: z.enum(["public", "restricted", "private"]).default("restricted"),
});

function validateIndexDocument(data: unknown) {
  return IndexDocumentSchema.parse(data);
}
```

## Data Protection
```typescript
const GLEAN_SENSITIVE_FIELDS = ["indexing_token", "client_token", "document_body", "user_query", "search_results"];

function redactGleanLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of GLEAN_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] Indexing tokens stored server-side only, never in frontend code
- [ ] Client tokens scoped per-user with `X-Glean-Auth-Type` header
- [ ] Tokens rotated quarterly via Admin > API Tokens
- [ ] Document permissions set via `allowedUsers`/`allowedGroups`
- [ ] SAML SSO enforced for Glean web access
- [ ] All API calls over HTTPS
- [ ] Search audit logs enabled to track sensitive queries
- [ ] Connector permissions reviewed when adding new data sources

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked indexing token | Arbitrary content injected into search index | Backend-only storage + rotation |
| Missing document permissions | Confidential docs exposed in search results | `allowedUsers`/`allowedGroups` on every document |
| Client token in frontend | User impersonation in search queries | Server-side proxy for search API |
| Overly broad connector scope | Sensitive repos/channels indexed unintentionally | Per-connector permission review |
| Search queries in logs | Employee activity surveillance risk | Query redaction in logging pipeline |

## Resources
- [Glean Developer Portal](https://developers.glean.com/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `glean-prod-checklist`.

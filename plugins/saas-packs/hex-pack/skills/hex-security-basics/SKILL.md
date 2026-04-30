---
name: hex-security-basics
description: 'Apply Hex security best practices for secrets and access control.

  Use when securing API keys, implementing least privilege access,

  or auditing Hex security configuration.

  Trigger with phrases like "hex security", "hex secrets",

  "secure hex", "hex API key security".

  '
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Security Basics

## Overview
Hex is a collaborative data analytics platform where notebooks query production databases, generate visualizations, and share results across teams. Security concerns center on API token management (read vs run scopes), protecting database connection credentials embedded in Hex projects, and ensuring query results containing sensitive business data are not leaked through logs or exports. A compromised run-scope token can trigger arbitrary queries against connected databases.

## API Key Management
```typescript
function createHexClient(scope: "read" | "run"): { token: string; baseUrl: string } {
  const envVar = scope === "run" ? "HEX_RUN_TOKEN" : "HEX_READ_TOKEN";
  const token = process.env[envVar];
  if (!token) {
    throw new Error(`Missing ${envVar} — store in secrets manager, never in code`);
  }
  // Run tokens can trigger queries — use read tokens for monitoring
  console.log(`Hex client initialized with ${scope} scope (token suffix: ${token.slice(-4)})`);
  return { token, baseUrl: "https://app.hex.tech/api/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyHexWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-hex-signature"] as string;
  const secret = process.env.HEX_WEBHOOK_SECRET!;
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

const HexRunRequestSchema = z.object({
  project_id: z.string().uuid(),
  input_params: z.record(z.string(), z.unknown()).optional(),
  notify_on_completion: z.boolean().default(false),
  update_cache: z.boolean().default(false),
});

function validateHexRunRequest(data: unknown) {
  return HexRunRequestSchema.parse(data);
}
```

## Data Protection
```typescript
const HEX_SENSITIVE_FIELDS = ["db_connection_string", "query_results", "api_token", "input_params", "export_url"];

function redactHexLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of HEX_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API tokens stored in secrets vault, never in code
- [ ] Read-only tokens for monitoring, run tokens for orchestration only
- [ ] Token expiration set to 90 days maximum
- [ ] Separate tokens per environment (dev/staging/prod)
- [ ] Pre-commit hook blocks `hex_token_*` patterns
- [ ] Database connection credentials managed in Hex workspace settings
- [ ] Query result exports reviewed for sensitive data before sharing
- [ ] Notebook sharing permissions audited per team

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked run-scope token | Arbitrary queries against production databases | Secrets vault + least-privilege scoping |
| Database credentials in notebooks | Connection strings exposed to all collaborators | Hex workspace-managed connections |
| Query results in logs | Sensitive business data leaked | Field-level redaction pipeline |
| Overly broad notebook sharing | Confidential analytics visible to wrong teams | Per-notebook permission scoping |
| No token expiration | Indefinite access from compromised token | 90-day expiration policy |

## Resources
- [Hex API Authentication](https://learn.hex.tech/docs/api/api-overview)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `hex-prod-checklist`.

---
name: flyio-security-basics
description: 'Apply Fly.io security best practices for secrets management, private
  networking,

  TLS certificates, and deploy token scoping.

  Trigger: "fly.io security", "fly secrets", "fly.io TLS", "fly.io private network".

  '
allowed-tools: Read, Write, Edit, Bash(fly:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Security Basics

## Overview
Fly.io deploys applications to edge locations worldwide using Firecracker microVMs. Security concerns center on deploy token scoping (org-wide vs per-app), secrets management (encrypted at rest, injected as env vars), private networking via WireGuard mesh (6PN), and TLS certificate management. A leaked deploy token can push arbitrary code to production machines across all regions.

## API Key Management
```typescript
function validateFlyToken(): void {
  const token = process.env.FLY_API_TOKEN;
  if (!token) {
    throw new Error("Missing FLY_API_TOKEN — use `fly tokens create deploy -a <app>`");
  }
  // Never log tokens; log only token type for debugging
  const isDeployToken = token.startsWith("FlyV1");
  console.log("Fly.io token loaded, type:", isDeployToken ? "deploy" : "personal");
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyFlyWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-fly-signature"] as string;
  const secret = process.env.FLY_WEBHOOK_SECRET!;
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

const FlyDeploySchema = z.object({
  app_name: z.string().regex(/^[a-z0-9-]+$/).max(63),
  region: z.enum(["iad", "ord", "lax", "sjc", "ams", "lhr", "nrt", "syd", "gru"]),
  image: z.string().regex(/^registry\..+\/.+:.+$/),
  vm_size: z.enum(["shared-cpu-1x", "shared-cpu-2x", "performance-1x", "performance-2x"]).optional(),
  min_machines: z.number().int().min(0).max(20).optional(),
});

function validateDeployConfig(data: unknown) {
  return FlyDeploySchema.parse(data);
}
```

## Data Protection
```typescript
const FLY_SENSITIVE_FIELDS = ["fly_api_token", "deploy_token", "db_password", "wireguard_private_key", "tls_private_key"];

function redactFlyLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of FLY_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] All sensitive values in `fly secrets`, never in `[env]` section of fly.toml
- [ ] Deploy tokens scoped per-app, not org-wide
- [ ] `force_https = true` set in fly.toml `[http_service]`
- [ ] Internal services use `.internal` DNS with no public ports
- [ ] WireGuard keys rotated and unused tunnels removed
- [ ] Secrets rotated on schedule (triggers rolling restart)
- [ ] CI/CD uses deploy-scoped tokens, not personal tokens
- [ ] Container images scanned before deployment

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked deploy token | Arbitrary code deployed to production | Per-app scoped tokens + rotation |
| Secrets in fly.toml `[env]` | Plaintext credentials in version control | Use `fly secrets set` exclusively |
| Open internal ports | Services exposed to public internet | `.internal` DNS + NetworkPolicy |
| Org-wide token in CI | All apps in org compromised via CI breach | Deploy-scoped tokens per pipeline |
| Expired TLS certificates | MITM attacks on custom domains | Automated Let's Encrypt renewal |

## Resources
- [Fly Secrets](https://fly.io/docs/reference/secrets/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `flyio-prod-checklist`.

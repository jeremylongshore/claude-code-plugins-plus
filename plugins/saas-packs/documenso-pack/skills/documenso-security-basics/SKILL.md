---
name: documenso-security-basics
description: |
  Implement security best practices for Documenso document signing integrations.
  Use when securing API keys, configuring webhooks securely,
  or implementing document security measures.
  Trigger with phrases like "documenso security", "secure documenso",
  "documenso API key security", "documenso webhook security".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, security, webhooks]

---
# Documenso Security Basics

## Overview

Essential security practices for Documenso integrations: API key management, webhook verification, document access control, and self-hosted signing certificate configuration.

## Prerequisites

- Documenso account with API access
- Understanding of environment variables and secret management
- Completed `documenso-install-auth` setup

## Instructions

### Step 1: API Key Security

```typescript
// NEVER hardcode keys
const BAD = new Documenso({ apiKey: "api_abc123..." }); // Exposed in source

// ALWAYS use environment variables
const GOOD = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
```

**Key management rules:**
- Store in `.env` (never committed) or a secrets manager (Vault, AWS Secrets Manager)
- Use team-scoped keys for team resources, personal keys for personal documents
- Rotate keys on employee offboarding -- revoke in dashboard immediately
- CI/CD: use masked/encrypted secrets (GitHub Secrets, GitLab CI variables)

```bash
# .gitignore — always include
.env
.env.*
!.env.example
```

### Step 2: Key Rotation with Zero Downtime

```typescript
// Support dual keys during rotation
function getApiKey(): string {
  // Try primary first, fall back to secondary during rotation
  return process.env.DOCUMENSO_API_KEY_PRIMARY
    ?? process.env.DOCUMENSO_API_KEY_SECONDARY
    ?? (() => { throw new Error("No Documenso API key configured"); })();
}

// Rotation procedure:
// 1. Generate new key in Documenso dashboard
// 2. Set as DOCUMENSO_API_KEY_SECONDARY, deploy
// 3. Verify secondary key works
// 4. Move secondary to PRIMARY, deploy
// 5. Revoke old key in dashboard
```

### Step 3: Webhook Secret Verification

```typescript
import { timingSafeEqual } from "crypto";

function verifyWebhookSecret(req: Request): boolean {
  const received = req.headers["x-documenso-secret"] as string;
  const expected = process.env.DOCUMENSO_WEBHOOK_SECRET!;

  if (!received || !expected) return false;

  // Use constant-time comparison to prevent timing attacks
  return timingSafeEqual(
    Buffer.from(received, "utf8"),
    Buffer.from(expected, "utf8")
  );
}
```

```python
# Python equivalent
import hmac, os
from flask import request

def verify_webhook(req):
    received = req.headers.get("X-Documenso-Secret", "")
    expected = os.environ["DOCUMENSO_WEBHOOK_SECRET"]
    return hmac.compare_digest(received, expected)
```

### Step 4: Document Access Control

```typescript
// Principle of least privilege with API keys
// Personal keys: only YOUR documents
// Team keys: all documents in the team

// Restrict document access by checking ownership
async function getDocumentSecure(documentId: number, userId: string) {
  const doc = await client.documents.getV0(documentId);

  // Verify the requesting user is the owner or a recipient
  const isOwner = doc.userId === parseInt(userId);
  const isRecipient = doc.recipients?.some(r => r.email === userEmail);

  if (!isOwner && !isRecipient) {
    throw new Error("Access denied: not authorized for this document");
  }

  return doc;
}
```

### Step 5: Signing Certificate Security (Self-Hosted)

Self-hosted Documenso requires a `.p12` signing certificate for legally valid digital signatures.

```bash
# Generate a self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
openssl pkcs12 -export -out signing-cert.p12 -inkey key.pem -in cert.pem

# Mount into Docker container
docker run -v $(pwd)/signing-cert.p12:/opt/documenso/cert.p12 \
  -e NEXT_PRIVATE_SIGNING_LOCAL_FILE_PATH=/opt/documenso/cert.p12 \
  -e NEXT_PRIVATE_SIGNING_PASSPHRASE=your-passphrase \
  documenso/documenso:latest
```

For production, use a certificate from a trusted CA (e.g., GlobalSign, DigiCert).

### Step 6: Self-Hosted Production Secrets

```bash
# Generate cryptographically secure secrets
openssl rand -hex 32  # NEXTAUTH_SECRET
openssl rand -hex 32  # NEXT_PRIVATE_ENCRYPTION_KEY
openssl rand -hex 32  # NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY

# Never reuse secrets across environments
# Never use default values in production
```

## Security Checklist

- [ ] API key stored in environment variable, never in source code
- [ ] `.env` in `.gitignore`
- [ ] CI secrets use masked/encrypted storage
- [ ] Team keys rotated on employee offboarding
- [ ] Webhook secret uses constant-time comparison
- [ ] Self-hosted: HTTPS with valid TLS certificates
- [ ] Self-hosted: signing certificate from trusted CA
- [ ] Self-hosted: secrets generated with `openssl rand -hex 32`
- [ ] No API keys or secrets in logs (sanitize before logging)
- [ ] Key rotation procedure documented and tested

## Error Handling

| Security Issue | Indicator | Response |
|---------------|-----------|----------|
| Invalid API key | 401 errors | Rotate key immediately |
| Webhook spoofing | Invalid secret header | Reject request, alert team |
| Key exposed in git | GitHub secret scanning alert | Revoke key, rotate, audit access |
| Brute force | Many 401s from same IP | Rate limit by IP at reverse proxy |

## Resources

- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Documenso Security](https://documenso.com/security)
- [Webhook Verification Docs](https://docs.documenso.com/docs/developers/webhooks/verification)
- [Self-Hosting: Signing Certificate](https://docs.documenso.com/developers/self-hosting/signing-certificate)

## Next Steps

For production deployment, see `documenso-prod-checklist`.

---
name: firecrawl-security-basics
description: |
  Apply Firecrawl security best practices for API key management and webhook verification.
  Use when securing API keys, implementing webhook signature validation,
  or auditing Firecrawl security configuration.
  Trigger with phrases like "firecrawl security", "firecrawl secrets",
  "secure firecrawl", "firecrawl API key security", "firecrawl webhook signature".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, security, audit]

---
# Firecrawl Security Basics

## Overview
Security best practices for Firecrawl API keys, webhook signature verification, and scraped content handling. Firecrawl API keys start with `fc-` and grant full access to scrape, crawl, map, and extract endpoints — protecting them is critical.

## Prerequisites
- Firecrawl API key
- Understanding of environment variables
- Webhook endpoint (if using async crawl callbacks)

## Instructions

### Step 1: Secure API Key Storage
```bash
# .env (NEVER commit to git)
FIRECRAWL_API_KEY=fc-your-api-key-here

# .gitignore — add these patterns
echo -e "\n.env\n.env.local\n.env.*.local" >> .gitignore
```

```typescript
// Validate key exists before creating client
import FirecrawlApp from "@mendable/firecrawl-js";

if (!process.env.FIRECRAWL_API_KEY?.startsWith("fc-")) {
  throw new Error("FIRECRAWL_API_KEY must be set and start with 'fc-'");
}

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY,
});
```

### Step 2: Verify Webhook Signatures
Firecrawl signs webhook payloads with HMAC-SHA256 via the `X-Firecrawl-Signature` header.

```typescript
import crypto from "crypto";

function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  // Timing-safe comparison prevents timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Express webhook handler with verification
app.post("/webhooks/firecrawl", (req, res) => {
  const signature = req.headers["x-firecrawl-signature"] as string;
  const rawBody = JSON.stringify(req.body);

  if (!verifyWebhookSignature(rawBody, signature, process.env.FIRECRAWL_WEBHOOK_SECRET!)) {
    console.error("Invalid webhook signature — rejecting");
    return res.status(401).json({ error: "Invalid signature" });
  }

  // Process verified webhook
  const { type, data } = req.body;
  console.log(`Verified webhook: ${type}`);
  res.status(200).json({ received: true });
});
```

### Step 3: Separate Keys per Environment
```bash
# GitHub Actions secrets
gh secret set FIRECRAWL_API_KEY_DEV --body "fc-dev-..."
gh secret set FIRECRAWL_API_KEY_STAGING --body "fc-staging-..."
gh secret set FIRECRAWL_API_KEY_PROD --body "fc-prod-..."
```

```typescript
// Load correct key based on environment
const KEY_MAP: Record<string, string> = {
  development: "FIRECRAWL_API_KEY_DEV",
  staging: "FIRECRAWL_API_KEY_STAGING",
  production: "FIRECRAWL_API_KEY_PROD",
};

const envVar = KEY_MAP[process.env.NODE_ENV || "development"];
const apiKey = process.env[envVar] || process.env.FIRECRAWL_API_KEY;
```

### Step 4: Rotate Keys
```bash
set -euo pipefail
# 1. Generate new key at firecrawl.dev/app
# 2. Deploy new key alongside old key
# 3. Verify new key works
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $NEW_FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq .success

# 4. Remove old key from all environments
# 5. Delete old key in Firecrawl dashboard
```

### Step 5: Sanitize Scraped Content
```typescript
// Scraped web content may contain PII, scripts, or malicious data
function sanitizeScrapedContent(markdown: string): string {
  return markdown
    // Remove potential script injections
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    // Remove data URIs (potential XSS vectors)
    .replace(/!\[.*?\]\(data:.*?\)/g, "")
    // Remove javascript: links
    .replace(/\[.*?\]\(javascript:.*?\)/g, "")
    // Strip HTML comments
    .replace(/<!--[\s\S]*?-->/g, "")
    .trim();
}
```

## Security Checklist
- [ ] API key stored in environment variable, never hardcoded
- [ ] `.env` files listed in `.gitignore`
- [ ] Different keys for dev/staging/production
- [ ] Webhook signatures verified before processing
- [ ] Scraped content sanitized before storage/display
- [ ] Key rotation scheduled quarterly
- [ ] Git history scanned for leaked keys

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Leaked API key in git | `git log -p \| grep "fc-"` | Rotate immediately, revoke old key |
| Invalid webhook signature | Signature verification fails | Reject request, alert team |
| Excessive scraping costs | Credit alerts from Firecrawl | Set credit limits per key |
| PII in scraped content | Content scanning | Sanitize before storage |

## Resources
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Firecrawl Webhooks](https://docs.firecrawl.dev/webhooks/overview)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)

## Next Steps
For production deployment, see `firecrawl-prod-checklist`.

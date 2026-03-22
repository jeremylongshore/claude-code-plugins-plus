---
name: adobe-known-pitfalls
description: |
  Identify and avoid Adobe-specific anti-patterns: using deprecated JWT auth,
  not caching IMS tokens, ignoring Firefly content policy, missing async job
  polling, and leaking p8_ secrets. Real code examples with fixes.
  Trigger with phrases like "adobe mistakes", "adobe anti-patterns",
  "adobe pitfalls", "adobe what not to do", "adobe code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Known Pitfalls

## Overview

The 10 most common mistakes when integrating with Adobe APIs, based on real production issues. Each pitfall includes the anti-pattern, why it fails, and the correct approach.

## Prerequisites

- Access to your Adobe integration codebase
- Understanding of Adobe API architecture (OAuth, async jobs, rate limits)

## Instructions

### Pitfall 1: Still Using JWT (Service Account) Credentials

**Status: CRITICAL** — JWT credentials reached End of Life June 2025.

```typescript
// WRONG: JWT auth (no longer works as of 2025)
import jwt from 'jsonwebtoken';
import fs from 'fs';

const privateKey = fs.readFileSync('private.key');
const jwtToken = jwt.sign({
  exp: Math.round(Date.now() / 1000) + 86400,
  iss: orgId,
  sub: technicalAccountId,
  aud: `https://ims-na1.adobelogin.com/c/${clientId}`,
}, privateKey, { algorithm: 'RS256' });

// RIGHT: OAuth Server-to-Server (current standard)
const res = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    client_id: process.env.ADOBE_CLIENT_ID!,
    client_secret: process.env.ADOBE_CLIENT_SECRET!,
    grant_type: 'client_credentials',
    scope: process.env.ADOBE_SCOPES!,
  }),
});
```

---

### Pitfall 2: Not Caching IMS Access Tokens

IMS tokens are valid for 24 hours. Generating a new token per request wastes 200-500ms:

```typescript
// WRONG: New token every request (200-500ms overhead each time)
async function callFirefly(prompt: string) {
  const tokenRes = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', { ... });
  const { access_token } = await tokenRes.json();
  // ... use access_token
}

// RIGHT: Cache token with expiry check
let cached: { token: string; expiresAt: number } | null = null;

async function getToken(): Promise<string> {
  if (cached && cached.expiresAt > Date.now() + 300_000) return cached.token;
  const res = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', { ... });
  const data = await res.json();
  cached = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return cached.token;
}
```

---

### Pitfall 3: Using Firefly Sync Endpoint for Batch Operations

```typescript
// WRONG: Sequential sync calls (each blocks 5-20s)
for (const prompt of prompts) {
  const result = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
    method: 'POST', ...
  });
  results.push(await result.json());
}
// Total time: N * 5-20s = very slow

// RIGHT: Async endpoint with parallel submission
const jobs = await Promise.all(
  prompts.map(prompt =>
    fetch('https://firefly-api.adobe.io/v3/images/generate-async', {
      method: 'POST', ...
    }).then(r => r.json())
  )
);
// Poll all jobs in parallel
const results = await Promise.all(jobs.map(j => pollJob(j.statusUrl)));
// Total time: max(5-20s) = much faster
```

---

### Pitfall 4: Ignoring Firefly Content Policy Errors

```typescript
// WRONG: Treat all 400 errors the same
try {
  const result = await generateImage({ prompt: 'Photo of Nike shoes' });
} catch (e) {
  console.log('Generation failed');  // No idea why
}

// RIGHT: Handle content policy specifically
try {
  const result = await generateImage({ prompt });
} catch (e: any) {
  if (e.status === 400 && e.message?.includes('content policy')) {
    // Save the credit — don't retry, fix the prompt
    throw new Error(
      'Firefly content policy violation. ' +
      'Remove trademarks, real people, or explicit content from prompt.'
    );
  }
  throw e; // Other errors might be retryable
}
```

---

### Pitfall 5: Uploading Files Directly to Photoshop/Lightroom API

```typescript
// WRONG: Trying to upload file directly (not supported)
const formData = new FormData();
formData.append('image', fs.readFileSync('photo.jpg'));
await fetch('https://image.adobe.io/v2/remove-background', {
  method: 'POST',
  body: formData,  // Photoshop API doesn't accept direct uploads
});

// RIGHT: Use pre-signed cloud storage URLs
const inputUrl = await s3.getSignedUrl('getObject', {
  Bucket: 'my-bucket', Key: 'photo.jpg', Expires: 3600,
});
const outputUrl = await s3.getSignedUrl('putObject', {
  Bucket: 'my-bucket', Key: 'output.png', Expires: 3600,
});

await fetch('https://image.adobe.io/v2/remove-background', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}`, 'x-api-key': clientId, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    input: { href: inputUrl, storage: 'external' },
    output: { href: outputUrl, storage: 'external', type: 'image/png' },
  }),
});
```

---

### Pitfall 6: Not Polling Async Job Status

Photoshop and Lightroom APIs return immediately with a job ID. You must poll for results:

```typescript
// WRONG: Treating response as the final result
const res = await fetch('https://image.adobe.io/v2/remove-background', { ... });
const result = await res.json();
console.log('Done!', result);  // result is just { _links: { self: { href: ... } } }

// RIGHT: Poll the status URL until completion
const submission = await res.json();
let job;
do {
  await new Promise(r => setTimeout(r, 2000));
  const pollRes = await fetch(submission._links.self.href, {
    headers: { Authorization: `Bearer ${token}`, 'x-api-key': clientId },
  });
  job = await pollRes.json();
} while (job.status !== 'succeeded' && job.status !== 'failed');

if (job.status === 'failed') throw new Error(job.error?.message);
```

---

### Pitfall 7: Leaking Adobe Credentials in Source Code

```typescript
// WRONG: Hardcoded credentials (Adobe OAuth secrets start with p8_)
const client_secret = 'p8_XYZ_your_actual_secret_here_do_not_do_this';

// WRONG: Committed .env file
// git add .env && git commit -m "add config"

// RIGHT: Environment variables + .gitignore
const client_secret = process.env.ADOBE_CLIENT_SECRET!;
// .gitignore includes: .env, .env.local, .env.*.local
```

---

### Pitfall 8: Not Handling PDF Services Quota

```typescript
// WRONG: No quota awareness (free tier = 500 tx/month)
async function extractAllPdfs(paths: string[]) {
  for (const path of paths) {
    await extractPdf(path);  // Silently fails after 500th call
  }
}

// RIGHT: Track and enforce quota
let txCount = 0;
async function trackedExtract(path: string) {
  if (txCount >= 490) {  // Leave buffer
    throw new Error('Approaching PDF Services monthly limit. 10 transactions remaining.');
  }
  const result = await extractPdf(path);
  txCount++;
  return result;
}
```

---

### Pitfall 9: Using Deprecated Photoshop Endpoints

```typescript
// WRONG: v1 endpoint (deprecated)
await fetch('https://image.adobe.io/sensei/cutout', { ... });

// RIGHT: v2 endpoint (current)
await fetch('https://image.adobe.io/v2/remove-background', { ... });
```

---

### Pitfall 10: Missing Webhook Signature Verification

```typescript
// WRONG: Trust any incoming request (attackers can forge events)
app.post('/webhooks/adobe', (req, res) => {
  processEvent(req.body);
  res.sendStatus(200);
});

// RIGHT: Verify RSA-SHA256 signature from Adobe I/O Events
app.post('/webhooks/adobe', express.raw({ type: 'application/json' }), async (req, res) => {
  // Adobe uses RSA-SHA256 digital signatures (NOT HMAC)
  const sig = req.headers['x-adobe-digital-signature-1'];
  const keyPath = req.headers['x-adobe-public-key1-path'];

  const publicKey = await fetch(`https://static.adobeioevents.com${keyPath}`).then(r => r.text());
  const verifier = crypto.createVerify('RSA-SHA256');
  verifier.update(req.body);

  if (!verifier.verify(publicKey, sig, 'base64')) {
    return res.sendStatus(401);
  }

  processEvent(JSON.parse(req.body.toString()));
  res.sendStatus(200);
});
```

## Quick Pitfall Scanner

```bash
# Run against your codebase
echo "=== Adobe Pitfall Scan ==="

# 1. JWT credentials (deprecated)
grep -rn "jsonwebtoken\|jwt\.sign\|RS256" --include="*.ts" --include="*.js" src/ && echo "FOUND: JWT auth (deprecated)" || echo "OK: No JWT"

# 2. Uncached token generation
grep -rn "ims/token/v3" --include="*.ts" src/ | wc -l | xargs -I{} echo "Token endpoint calls: {} (should be 1 — in auth.ts only)"

# 3. Hardcoded secrets
grep -rn "p8_" --include="*.ts" --include="*.js" src/ && echo "FOUND: Hardcoded Adobe secret" || echo "OK: No hardcoded secrets"

# 4. Deprecated endpoints
grep -rn "sensei/cutout" --include="*.ts" src/ && echo "FOUND: Deprecated Photoshop endpoint" || echo "OK: No deprecated endpoints"

# 5. Missing webhook verification
grep -rn "webhooks/adobe" --include="*.ts" src/ | grep -v "digital-signature\|verify\|RSA" && echo "WARNING: Webhook handler may lack signature verification"
```

## Quick Reference Card

| Pitfall | Risk | Detection | Fix |
|---------|------|-----------|-----|
| JWT auth | Broken auth | Grep for `jwt.sign` | Migrate to OAuth S2S |
| No token cache | Perf (-500ms/req) | Multiple `ims/token` calls | Cache with expiry |
| Sync Firefly for batch | Slow (N*20s) | Sequential `generate` calls | Use async endpoint |
| Ignore content policy | Wasted credits | Catch 400 without reason | Pre-screen prompts |
| Direct file upload | 400 errors | FormData to Photoshop | Pre-signed URLs |
| No job polling | Missing results | No poll loop after submit | Poll `_links.self` |
| Leaked `p8_` secret | Credential compromise | Grep for `p8_` | Env vars + .gitignore |
| No quota tracking | Silent failures | No counter | Track per-month usage |
| Old PS endpoint | 404 errors | `/sensei/cutout` | `/v2/remove-background` |
| No webhook verify | Security hole | No signature check | RSA-SHA256 verification |

## Resources

- [JWT to OAuth Migration](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/migration)
- [Firefly Content Policy](https://developer.adobe.com/firefly-services/docs/firefly-api/)
- [Photoshop Remove Background v2](https://developer.adobe.com/firefly-services/docs/photoshop/guides/remove_background/)
- [I/O Events Signature Verification](https://developer.adobe.com/events/docs/guides/sdk/sdk_signature_verification/)

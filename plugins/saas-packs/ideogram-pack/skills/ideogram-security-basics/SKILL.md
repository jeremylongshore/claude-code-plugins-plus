---
name: ideogram-security-basics
description: |
  Apply Ideogram security best practices for API key management and access control.
  Use when securing API keys, implementing key rotation,
  or auditing Ideogram security configuration.
  Trigger with phrases like "ideogram security", "ideogram secrets",
  "secure ideogram", "ideogram API key security", "ideogram key rotation".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, security]

---
# Ideogram Security Basics

## Overview
Secure your Ideogram API integration. Ideogram uses a single `Api-Key` header for authentication -- there are no OAuth scopes, roles, or fine-grained permissions. Security focuses on key management, environment isolation, prompt sanitization, and preventing key exposure.

## Prerequisites
- Ideogram API key from dashboard
- Understanding of environment variables
- `.gitignore` configured for secrets

## Instructions

### Step 1: Secure Key Storage
```bash
# .env (NEVER commit)
IDEOGRAM_API_KEY=your-key-here

# .gitignore -- add these lines
.env
.env.local
.env.*.local
*.key
```

```typescript
// Validate key exists at startup -- fail fast
function requireApiKey(): string {
  const key = process.env.IDEOGRAM_API_KEY;
  if (!key || key.length < 10) {
    throw new Error("IDEOGRAM_API_KEY not set or invalid. Check .env file.");
  }
  return key;
}
```

### Step 2: Key Rotation Procedure
Ideogram shows the full API key only once at creation. To rotate:

```bash
set -euo pipefail
# 1. Create new key in Ideogram dashboard (Settings > API Beta > Create API key)
# 2. Store new key immediately -- it won't be shown again

# 3. Update your environment
export IDEOGRAM_API_KEY="new-key-value"

# 4. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"rotation test","model":"V_2_TURBO","magic_prompt_option":"OFF"}}'

# 5. Update deployment secrets
# Vercel: vercel env rm IDEOGRAM_API_KEY production && vercel env add IDEOGRAM_API_KEY production
# GitHub Actions: gh secret set IDEOGRAM_API_KEY
# AWS: aws secretsmanager update-secret --secret-id ideogram-api-key --secret-string "$IDEOGRAM_API_KEY"

# 6. Delete old key from Ideogram dashboard after confirming zero traffic
```

### Step 3: Prevent Key Exposure
```typescript
// Proxy pattern -- never expose API key to browser
// api/ideogram-proxy.ts (server-side only)
export async function POST(req: Request) {
  const { prompt, style } = await req.json();

  // Validate and sanitize before forwarding
  if (!prompt || prompt.length > 10000) {
    return Response.json({ error: "Invalid prompt" }, { status: 400 });
  }

  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!, // Server-side only
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: "V_2",
        style_type: style || "AUTO",
        magic_prompt_option: "AUTO",
      },
    }),
  });

  const result = await response.json();
  // Return only the image data, never the API key or internal details
  return Response.json({
    images: result.data?.map((d: any) => ({
      url: d.url,
      seed: d.seed,
      resolution: d.resolution,
    })),
  });
}
```

### Step 4: Git Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit -- prevent accidental key commits
set -euo pipefail

# Check for potential Ideogram API keys in staged files
if git diff --cached --diff-filter=d | grep -qiE '(Api-Key|IDEOGRAM_API_KEY)\s*[:=]\s*["\x27]?[a-zA-Z0-9_-]{20,}'; then
  echo "ERROR: Potential Ideogram API key detected in staged changes."
  echo "Remove the key and use environment variables instead."
  exit 1
fi
```

### Step 5: Prompt Sanitization
```typescript
// Prevent prompt injection and abuse
function sanitizePrompt(prompt: string): { safe: boolean; cleaned: string; reason?: string } {
  // Length check (Ideogram max: 10,000 chars)
  if (prompt.length > 10000) {
    return { safe: false, cleaned: prompt.slice(0, 10000), reason: "Prompt too long" };
  }

  // Remove potential PII patterns
  const cleaned = prompt
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[email]")
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, "[phone]")
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[ssn]");

  return { safe: true, cleaned };
}
```

## Security Checklist
- [ ] API key in environment variable, not source code
- [ ] `.env` files in `.gitignore`
- [ ] Separate keys for dev / staging / production
- [ ] Pre-commit hook scanning for key patterns
- [ ] Server-side proxy for browser-facing applications
- [ ] Prompt sanitization to strip PII
- [ ] Key rotation scheduled quarterly
- [ ] Auto top-up billing limits reviewed

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Key exposed in git | `git log -p --all -S "Api-Key"` | Rotate key immediately |
| Key in client-side JS | Browser DevTools audit | Move to server-side proxy |
| Unlimited billing | No top-up cap set | Set conservative auto top-up limits |
| Prompt contains PII | Sanitization check | Strip before API call |

## Output
- Secure API key storage with environment variables
- Key rotation procedure documented
- Server-side proxy preventing client-side exposure
- Pre-commit hook blocking accidental commits

## Resources
- [Ideogram API Setup](https://developer.ideogram.ai/ideogram-api/api-setup)
- [API Terms of Service](https://ideogram.ai/legal/api-tos)

## Next Steps
For production deployment, see `ideogram-prod-checklist`.

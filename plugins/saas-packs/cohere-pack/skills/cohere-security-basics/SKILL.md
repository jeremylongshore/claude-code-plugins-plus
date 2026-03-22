---
name: cohere-security-basics
description: |
  Apply Cohere security best practices for API key management and access control.
  Use when securing API keys, implementing key rotation,
  or auditing Cohere security configuration.
  Trigger with phrases like "cohere security", "cohere secrets",
  "secure cohere", "cohere API key security", "cohere key rotation".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Security Basics

## Overview
Security best practices for Cohere API keys, request validation, and data protection. Cohere uses bearer token auth with trial and production key tiers.

## Prerequisites
- Cohere account at [dashboard.cohere.com](https://dashboard.cohere.com)
- Understanding of environment variables
- Secret management solution for production

## Instructions

### Step 1: API Key Management

```bash
# NEVER hardcode keys — use environment variables
export CO_API_KEY="your-key-here"

# .env file (MUST be git-ignored)
CO_API_KEY=your-key-here

# .gitignore (mandatory entries)
.env
.env.local
.env.*.local
```

**Key types:**
- **Trial keys** — free, rate-limited, for development only
- **Production keys** — metered billing, for live applications

### Step 2: Runtime Validation

```typescript
import { CohereClientV2 } from 'cohere-ai';

function createSecureClient(): CohereClientV2 {
  const apiKey = process.env.CO_API_KEY;

  if (!apiKey) {
    throw new Error('CO_API_KEY is required. Set it as an environment variable.');
  }

  // Basic key format check
  if (apiKey.length < 20) {
    throw new Error('CO_API_KEY appears malformed. Check dashboard.cohere.com.');
  }

  return new CohereClientV2({ token: apiKey });
}
```

### Step 3: Key Rotation Procedure

```bash
# 1. Generate new key in Cohere dashboard
#    → dashboard.cohere.com → API Keys → Create new key

# 2. Deploy new key (keep old key active)
# Vercel:
vercel env add CO_API_KEY production

# AWS:
aws secretsmanager update-secret --secret-id cohere/api-key --secret-string "new-key"

# GCP:
echo -n "new-key" | gcloud secrets versions add cohere-api-key --data-file=-

# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer NEW_KEY" \
  -H "Content-Type: application/json" \
  https://api.cohere.com/v2/chat \
  -d '{"model":"command-r7b-12-2024","messages":[{"role":"user","content":"test"}]}'
# Should return 200

# 4. Revoke old key in dashboard
# 5. Monitor for 401 errors after revocation
```

### Step 4: Request Data Protection

```typescript
// Scrub PII before sending to Cohere API
const PII_PATTERNS: [string, RegExp][] = [
  ['email', /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g],
  ['phone', /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g],
  ['ssn', /\b\d{3}-\d{2}-\d{4}\b/g],
];

function scrubPII(text: string): string {
  let scrubbed = text;
  for (const [type, regex] of PII_PATTERNS) {
    scrubbed = scrubbed.replace(regex, `[REDACTED_${type.toUpperCase()}]`);
  }
  return scrubbed;
}

// Use before API calls when handling user data
async function safeCohereChat(userInput: string) {
  const sanitized = scrubPII(userInput);

  return cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: sanitized }],
    safetyMode: 'CONTEXTUAL', // CONTEXTUAL (default), STRICT, or OFF
  });
}
```

### Step 5: Logging Safety

```typescript
import { CohereError } from 'cohere-ai';

function safeLog(message: string, data?: Record<string, unknown>) {
  const sanitized = { ...data };

  // Never log API keys
  delete sanitized.apiKey;
  delete sanitized.token;
  delete sanitized.authorization;

  // Truncate request/response bodies
  if (typeof sanitized.body === 'string' && (sanitized.body as string).length > 500) {
    sanitized.body = (sanitized.body as string).slice(0, 500) + '...[truncated]';
  }

  console.log(`[cohere] ${message}`, sanitized);
}

// Wrap error logging
function logCohereError(err: unknown) {
  if (err instanceof CohereError) {
    safeLog('API error', {
      status: err.statusCode,
      message: err.message,
      // Do NOT log err.body — may contain sensitive request data
    });
  }
}
```

### Step 6: Safety Modes

Cohere's Chat API supports safety modes that control content filtering:

```typescript
// CONTEXTUAL (default): Adapts based on context
await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: prompt }],
  safetyMode: 'CONTEXTUAL',
});

// STRICT: Maximum safety filtering
await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: prompt }],
  safetyMode: 'STRICT',
});

// Note: safetyMode not configurable with tools or documents params
```

## Security Checklist

- [ ] `CO_API_KEY` stored in environment variables, never in code
- [ ] `.env` files listed in `.gitignore`
- [ ] Separate keys for development and production
- [ ] Key rotation scheduled (quarterly recommended)
- [ ] PII scrubbed from inputs sent to Cohere
- [ ] API keys excluded from all log output
- [ ] Production key has billing alerts configured
- [ ] Git pre-commit hook scans for leaked keys

## Git Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit — detect Cohere keys in staged files
if git diff --cached --diff-filter=ACM | grep -qiE 'CO_API_KEY|cohere.*key.*=.*[a-zA-Z0-9]{20}'; then
  echo "ERROR: Possible Cohere API key in commit. Remove before committing."
  exit 1
fi
```

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Key in git history | `git log -p \| grep CO_API_KEY` | Rotate key immediately |
| Key in logs | Log audit | Add log scrubbing |
| Key in error report | Error handler review | Sanitize error payloads |
| Excessive token spend | Billing dashboard | Set budget alerts |

## Resources
- [Cohere API Keys Dashboard](https://dashboard.cohere.com/api-keys)
- [Cohere Safety Modes](https://docs.cohere.com/docs/safety-modes)
- [Cohere Rate Limits](https://docs.cohere.com/docs/rate-limits)

## Next Steps
For production deployment, see `cohere-prod-checklist`.

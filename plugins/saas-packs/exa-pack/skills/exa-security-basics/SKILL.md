---
name: exa-security-basics
description: |
  Secure Exa API keys, implement content moderation, and manage domain restrictions.
  Use when securing API keys, auditing Exa security configuration,
  or implementing content safety filtering.
  Trigger with phrases like "exa security", "exa secrets",
  "secure exa", "exa API key security", "exa content moderation".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, security]

---
# Exa Security Basics

## Overview
Security best practices for Exa API integrations. Exa authenticates via the `x-api-key` header. Key security concerns include API key protection, content moderation for search results, domain filtering to prevent exposure to malicious sources, and query sanitization.

## Prerequisites
- Exa API key from dashboard.exa.ai
- Understanding of environment variable management
- `.gitignore` configured for secrets

## Instructions

### Step 1: API Key Management
```bash
# .env (NEVER commit to git)
EXA_API_KEY=your-api-key-here

# .gitignore — add these entries
.env
.env.local
.env.*.local
```

```typescript
// Validate API key exists before creating client
import Exa from "exa-js";

function createSecureClient(): Exa {
  const apiKey = process.env.EXA_API_KEY;
  if (!apiKey) {
    throw new Error("EXA_API_KEY not configured");
  }
  if (apiKey.startsWith("sk_") && apiKey.length < 20) {
    throw new Error("EXA_API_KEY appears malformed");
  }
  return new Exa(apiKey);
}
```

### Step 2: Enable Content Moderation
```typescript
const exa = new Exa(process.env.EXA_API_KEY);

// Exa supports content moderation to filter unsafe results
const results = await exa.searchAndContents(
  "user-provided search query",
  {
    numResults: 10,
    text: true,
    moderation: true,  // filter unsafe content from results
  }
);
```

### Step 3: Domain Filtering for Safety
```typescript
// Restrict results to trusted domains for sensitive use cases
const TRUSTED_DOMAINS = [
  "docs.python.org", "developer.mozilla.org", "nodejs.org",
  "github.com", "stackoverflow.com", "arxiv.org",
];

const BLOCKED_DOMAINS = [
  "known-malware-site.com", "phishing-domain.net",
];

async function safeDomainSearch(query: string) {
  return exa.searchAndContents(query, {
    numResults: 10,
    includeDomains: TRUSTED_DOMAINS,  // only return results from these
    text: { maxCharacters: 1000 },
  });
}

async function searchWithBlocklist(query: string) {
  return exa.searchAndContents(query, {
    numResults: 10,
    excludeDomains: BLOCKED_DOMAINS,  // never return results from these
    text: { maxCharacters: 1000 },
  });
}
```

### Step 4: Query Sanitization
```typescript
// Sanitize user-provided queries before sending to Exa
function sanitizeQuery(input: string): string {
  // Remove potential injection patterns
  let clean = input
    .replace(/[<>{}]/g, "")           // strip HTML/template chars
    .replace(/\0/g, "")              // remove null bytes
    .trim()
    .substring(0, 500);              // cap query length

  if (!clean || clean.length < 2) {
    throw new Error("Query too short or empty after sanitization");
  }
  return clean;
}

// Usage
const userQuery = sanitizeQuery(req.body.query);
const results = await exa.search(userQuery, {
  numResults: 10,
  moderation: true,
});
```

### Step 5: Per-Environment Key Isolation
```typescript
// Use separate API keys per environment
const KEY_MAP: Record<string, string> = {
  development: process.env.EXA_API_KEY_DEV!,
  staging: process.env.EXA_API_KEY_STAGING!,
  production: process.env.EXA_API_KEY_PROD!,
};

function getExaForEnv(): Exa {
  const env = process.env.NODE_ENV || "development";
  const key = KEY_MAP[env];
  if (!key) throw new Error(`No EXA key for ${env}`);
  return new Exa(key);
}
```

## Security Checklist
- [ ] API key stored in environment variables (never hardcoded)
- [ ] `.env` files in `.gitignore`
- [ ] Separate API keys for dev/staging/production
- [ ] `moderation: true` enabled for user-facing search
- [ ] Query input sanitized before API calls
- [ ] Domain allowlist/blocklist applied for sensitive use cases
- [ ] API key rotation procedure documented
- [ ] Git history scanned for accidentally committed keys

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key | `git log -p` search | Rotate key immediately at dashboard.exa.ai |
| Unsafe search results | User reports | Enable `moderation: true` |
| Untrusted domains | Review result URLs | Apply `includeDomains` filter |
| Query injection | Input validation | Sanitize before search |

## Examples

### Scan Git History for Leaked Keys
```bash
set -euo pipefail
# Check if API key was ever committed
git log -p --all -S "EXA_API_KEY" -- "*.ts" "*.js" "*.py" "*.env" | head -20
```

### Key Rotation Procedure
```bash
set -euo pipefail
# 1. Generate new key in dashboard.exa.ai
# 2. Update environment
export EXA_API_KEY="new-key-here"
# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","numResults":1}'
# 4. Revoke old key in dashboard
```

## Resources
- [Exa API Authentication](https://docs.exa.ai/reference/getting-started)
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)

## Next Steps
For production deployment, see `exa-prod-checklist`.

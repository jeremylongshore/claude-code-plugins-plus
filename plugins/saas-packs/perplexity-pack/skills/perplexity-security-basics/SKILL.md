---
name: perplexity-security-basics
description: |
  Apply Perplexity security best practices for API key management and query safety.
  Use when securing API keys, implementing query sanitization,
  or auditing Perplexity security configuration.
  Trigger with phrases like "perplexity security", "perplexity secrets",
  "secure perplexity", "perplexity API key security", "perplexity PII".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, security, audit]

---
# Perplexity Security Basics

## Overview
Security best practices for Perplexity Sonar API. Key concerns: API key protection (keys start with `pplx-`), query sanitization (Perplexity searches the open web, so PII in queries gets sent to external sources), and response handling (citations link to third-party sites).

## Prerequisites
- Perplexity API key from [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
- Understanding of environment variable management
- `.gitignore` configured to exclude secret files

## Instructions

### Step 1: API Key Management
```bash
# .env (NEVER commit to git)
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# .gitignore
.env
.env.local
.env.*.local
*.pem
```

```typescript
// Validate key format at startup
function validateApiKey(key: string): void {
  if (!key) throw new Error("PERPLEXITY_API_KEY is not set");
  if (!key.startsWith("pplx-")) {
    throw new Error("PERPLEXITY_API_KEY must start with 'pplx-'");
  }
  if (key.length < 40) {
    throw new Error("PERPLEXITY_API_KEY appears truncated");
  }
}

validateApiKey(process.env.PERPLEXITY_API_KEY || "");
```

### Step 2: Query Sanitization (Critical)
Perplexity sends your query to the open web for search. Any PII in the query is exposed to external search infrastructure.

```typescript
function sanitizeQuery(query: string): string {
  return query
    // Remove email addresses
    .replace(/\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, "[email]")
    // Remove phone numbers
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, "[phone]")
    // Remove SSN
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[ssn]")
    // Remove credit card numbers
    .replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, "[card]")
    // Remove API keys / tokens
    .replace(/\b(pplx-|sk-|pk_|sk_live_)\w{20,}\b/g, "[token]")
    // Remove AWS keys
    .replace(/\bAKIA[A-Z0-9]{16}\b/g, "[aws-key]");
}

async function safeSearch(rawQuery: string) {
  const query = sanitizeQuery(rawQuery);
  if (query !== rawQuery) {
    console.warn("[Security] PII redacted from Perplexity query");
  }

  return perplexity.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: query }],
  });
}
```

### Step 3: Restrict Search Domains
Use `search_domain_filter` to prevent Perplexity from searching untrusted or competitor sites.

```typescript
// Compliance: only search approved sources
const complianceSearch = await perplexity.chat.completions.create({
  model: "sonar",
  messages: [{ role: "user", content: query }],
  search_domain_filter: [
    "sec.gov", "nih.gov", "cdc.gov",  // Government sources
    "nature.com", "science.org",       // Academic sources
  ],
} as any);

// Exclude specific sites
const filteredSearch = await perplexity.chat.completions.create({
  model: "sonar",
  messages: [{ role: "user", content: query }],
  search_domain_filter: [
    "-reddit.com", "-quora.com", "-medium.com",
  ],
} as any);
```

### Step 4: API Key Rotation
```bash
set -euo pipefail
# 1. Generate new key at perplexity.ai/settings/api
# 2. Update environment / secret manager
# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $NEW_PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
# Expected: 200

# 4. Delete old key from perplexity.ai/settings/api
```

### Step 5: Security Checklist
- [ ] API key stored in environment variable, not code
- [ ] `.env` files in `.gitignore`
- [ ] Different API keys per environment (dev/staging/prod)
- [ ] Query sanitization strips PII before API calls
- [ ] `search_domain_filter` used for compliance-sensitive queries
- [ ] Key rotation scheduled (quarterly minimum)
- [ ] Git history scanned for leaked keys
- [ ] Response citations validated before displaying to users

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| API key in git | `git log --all -S "pplx-"` | Rotate key immediately, add pre-commit hook |
| PII in query | Sanitization function | Strip before sending to Perplexity |
| Malicious citation URL | URL validation | Allowlist trusted domains |
| Key shared across envs | Config audit | Separate keys per environment |

## Output
- Secure API key storage pattern
- PII sanitization for search queries
- Domain-filtered search for compliance
- Key rotation procedure

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Privacy Policy](https://www.perplexity.ai/privacy)

## Next Steps
For production deployment, see `perplexity-prod-checklist`.

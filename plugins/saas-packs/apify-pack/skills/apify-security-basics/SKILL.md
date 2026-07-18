---
name: apify-security-basics
description: |
  Secure Apify API tokens, configure proxy access, and protect Actor data.
  Use when hardening API key management, setting up environment-specific tokens,
  rotating a leaked token, or auditing Apify security configuration.
  Trigger with "apify security", "apify secrets", "secure apify token",
  "apify API key security", "rotate apify token".
allowed-tools: Read, Write, Edit, Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Security Basics

## Overview

Security best practices for Apify API tokens, Actor data, proxy credentials, and webhook verification. Apify uses personal API tokens (prefixed `apify_api_`) for all authentication. Because a single token grants full account access with no per-token scoping, token hygiene is the whole game.

## Prerequisites

- Apify account with Console access
- Understanding of environment variables
- Access to your deployment platform's secrets management

## Token Architecture

Apify uses a single API token per user account for full API access. There is no scope-based permission system per token, so token security is critical.

| Token Type | Format | Where to Find |
|------------|--------|---------------|
| Personal API token | `apify_api_...` | Console > Settings > Integrations |
| Proxy password | Alphanumeric | Console > Proxy > Connection settings |

## Instructions

Follow the six hardening steps in order. Each has a lean summary below; the full
copy-paste code for every step is in
[references/implementation.md](references/implementation.md).

1. **Secure token storage** — keep the token in `.env` (never hardcoded) and add
   `.env`, `.env.*.local`, and `storage/` to `.gitignore`. Validate presence at
   startup so the app fails fast:

   ```typescript
   function requireToken(): string {
     const token = process.env.APIFY_TOKEN;
     if (!token) throw new Error('APIFY_TOKEN is required');
     if (!token.startsWith('apify_api_')) console.warn('unexpected token prefix');
     return token;
   }
   ```

2. **Per-environment token isolation** — separate tokens (ideally separate
   accounts) for dev / staging / prod, injected via each platform's secret store
   (`gh secret set`, `vercel env add`, GCP Secret Manager).
3. **Token rotation** — generate the new token first (old stays valid), push to
   every environment, verify it authenticates, then revoke the old one.
4. **Webhook payload verification** — Apify does not sign webhooks; confirm the
   run ID in the payload actually exists, or gate on a shared URL secret compared
   with `crypto.timingSafeEqual`.
5. **Actor data security** — redact sensitive fields before `pushData`; keep
   datasets named and private (no public sharing).
6. **Proxy security** — never log `proxyConfig.newUrl()` (it embeds the proxy
   password); log the proxy group only.

See [references/implementation.md](references/implementation.md) for the complete
code of every step, and [references/examples.md](references/examples.md) for
end-to-end scenarios.

## Output

Applying this skill produces a hardened project state:

- A `.gitignore` that excludes `.env*` and `storage/`, with no token in the tree.
- A startup token validator that throws on a missing/malformed `APIFY_TOKEN`.
- Environment-specific tokens wired into each platform's secret store.
- A documented rotation procedure and a completed **Security Checklist** (below).
- Webhook handlers that reject unverified runs and pipelines that redact PII
  before storage.

## Security Checklist

- [ ] `APIFY_TOKEN` stored in environment variables (never hardcoded)
- [ ] `.env` and `storage/` in `.gitignore`
- [ ] Separate tokens for dev/staging/prod
- [ ] Token rotation schedule documented
- [ ] Webhook endpoints verify source
- [ ] Proxy URLs never logged
- [ ] Scraped PII redacted before storage
- [ ] Named datasets used for sensitive data (no public sharing)
- [ ] CI/CD secrets configured (not in repo)

## Leaked Token Response

If a token is exposed:

1. **Immediately** regenerate token in Console > Settings > Integrations
2. Check recent Actor runs for unauthorized usage
3. Review billing for unexpected charges
4. Rotate proxy password if exposed
5. Audit git history: `git log --all -p -- '*.env' '*.json' | grep apify_api_`

## Error Handling

| Issue | Detection | Mitigation |
|-------|-----------|------------|
| Token in git history | `git log -p \| grep apify_api_` | Rotate token, use BFG to clean |
| Unauthorized runs | Unexpected runs in Console | Rotate token immediately |
| Proxy password exposed | Credentials in logs | Regenerate proxy password |
| Data breach in dataset | PII in public dataset | Delete dataset, sanitize pipeline |

## Examples

Quick starting point — bootstrap a new project's secrets safely:

```bash
cat >> .gitignore <<'EOF'
.env
.env.*.local
storage/
EOF
echo 'APIFY_TOKEN=apify_api_dev_token' > .env
git status --short   # .env must NOT appear
```

Four full worked scenarios — secure bootstrap, cross-environment rotation,
webhook-verify-then-sanitize, and a git-history leak audit — are in
[references/examples.md](references/examples.md).

## Resources

- [Apify Account Security](https://docs.apify.com/platform/collaboration)
- [API Authentication](https://docs.apify.com/api/v2/getting-started)
- [Proxy Connection Settings](https://docs.apify.com/platform/proxy)
- [Full implementation reference](references/implementation.md)
- [Worked examples](references/examples.md)

## Next Steps

For production deployment hardening beyond secrets — health checks, rate limits,
and monitoring — see the `apify-prod-checklist` skill in this pack.

---
name: groq-security-basics
description: 'Apply Groq security best practices for API key management and data protection.

  Use when securing API keys, implementing least privilege access,

  or auditing Groq security configuration.

  Trigger with phrases like "groq security", "groq secrets",

  "secure groq", "groq API key security".

  '
allowed-tools: Read, Write, Grep
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- security
- audit
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Security Basics

## Overview

Security practices for Groq API keys and data flowing through Groq's inference API. Groq uses a single API key type (`gsk_` prefix) with full access -- there are no scoped tokens -- so key management and rotation are critical.

This skill walks through six hardening steps end to end. The essentials live
here; deep code and full command sequences are extracted into
[references/](references/) for progressive disclosure:

- **[references/implementation.md](references/implementation.md)** — server-side proxy pattern, prompt-injection defense, audit logging (TypeScript).
- **[references/examples.md](references/examples.md)** — copy-ready key-storage, rotation, and git-leak-prevention commands.

## Prerequisites

- Groq account at console.groq.com
- Understanding of environment variable management
- Secret management solution for production (Vault, AWS Secrets Manager, etc.)

## Key Security Facts

- Groq API keys start with `gsk_` and grant full API access
- There are no read-only or scoped keys -- every key can call every endpoint
- Keys are created at console.groq.com/keys and cannot be viewed after creation
- Rate limits are per-organization, not per-key
- Groq does not store prompt data for training (see [privacy policy](https://groq.com/privacy-policy/))

## Instructions

Work through the six steps in order. Each summary below is enough to act on;
drill into the linked reference for the full code.

### Step 1: Secure Key Storage by Environment

Keep the key out of source. Use a `.env.local` (git-ignored) for development
and a platform secret manager (Vercel / AWS / GCP / GitHub Actions) for
production. Use `Write` to create the `.env.local` and `.gitignore` entries:

```bash
echo "GROQ_API_KEY=gsk_dev_key_here" > .env.local
echo -e ".env\n.env.local\n.env.*.local" >> .gitignore
```

Full per-platform commands: [references/examples.md](references/examples.md) Example 1.

### Step 2: Key Rotation Procedure

Both keys work simultaneously, so rotation is zero-downtime: create a
date-named key, deploy it, verify with a `200` from `/v1/models`, monitor 24h,
then delete the old key. Full sequence: [references/examples.md](references/examples.md) Example 2.

### Step 3: Git Leak Prevention

Install a pre-commit hook that blocks any staged `gsk_` key. Use `Read` to
confirm `.gitignore` excludes the `.env` files, then use `Grep` to sweep the
existing tree and history for keys already committed:

```bash
grep -rnE "gsk_[a-zA-Z0-9]{20,}" . --exclude-dir=.git
```

Hook + history-scan commands: [references/examples.md](references/examples.md) Examples 3-4.

### Step 4: Server-Side Key Usage Pattern

Never expose the key to client code. Proxy inference through your backend so
the key stays server-side, and validate/limit user input before calling Groq.
Full Next.js route handler: [references/implementation.md](references/implementation.md) § Server-Side Key Usage Pattern.

### Step 5: Prompt Injection Defense

Sanitize user input to strip override phrases (`ignore previous instructions`,
`you are now`, `system:`) and pair it with a hardened system prompt that
refuses role changes. Full code: [references/implementation.md](references/implementation.md) § Prompt Injection Defense.

### Step 6: Audit Logging

Log every completion with token counts, latency, and status so abuse and cost
spikes trace back to a user. Full `auditedCompletion` implementation:
[references/implementation.md](references/implementation.md) § Audit Logging.

## Output

Applying this skill produces a hardened Groq integration:

- A git-ignored `.env.local` (dev) and secret-manager entry (prod) — no key in source
- A `.git/hooks/pre-commit` hook that exits non-zero on any staged `gsk_` key
- A documented, tested rotation runbook with date-named keys
- A backend proxy route so the key never reaches the client
- Input sanitization + a hardened system prompt guarding against injection
- Structured audit log entries (`GroqAuditEntry`) on every completion
- A completed Security Checklist (below) with all items verified

## Error Handling

- **`401 Unauthorized` from `/v1/models`** — the rotated key is wrong or not yet propagated to the secret manager. Re-check the `Authorization: Bearer` value before deleting the old key.
- **Pre-commit hook not firing** — confirm the file is executable (`chmod +x .git/hooks/pre-commit`); hooks are not copied by `git clone`, so re-install per checkout.
- **`Grep` finds a key already in history** — rotate the key immediately (Step 2); scrubbing history alone is not enough because the key was exposed.
- **Client-side `GROQ_API_KEY` reference** — any bundler that inlines the key (e.g. a `NEXT_PUBLIC_` prefix) leaks it; move the call server-side (Step 4).
- **Rate limits hit unexpectedly** — limits are per-organization, not per-key, so a leaked key shares your quota; a sudden `429` spike can indicate abuse.

## Examples

Lean summaries are in [Instructions](#instructions); full copy-ready code lives
in the references:

- Environment-scoped key storage → [references/examples.md](references/examples.md) Example 1
- Zero-downtime rotation → [references/examples.md](references/examples.md) Example 2
- Pre-commit leak hook + history scan → [references/examples.md](references/examples.md) Examples 3-4
- Server-side proxy, injection defense, audit logging → [references/implementation.md](references/implementation.md)

## Security Checklist

- [ ] API key in environment variable, not source code
- [ ] `.env` files in `.gitignore`
- [ ] Pre-commit hook for key leak detection
- [ ] Separate keys for dev/staging/prod (different Groq orgs)
- [ ] Key rotation documented and tested
- [ ] Groq calls proxied through backend (never client-side)
- [ ] User input sanitized before sending to Groq
- [ ] System prompt hardened against injection
- [ ] Audit logging on all completions
- [ ] Spending limits set in Groq Console

## Resources

- [Groq Privacy Policy](https://groq.com/privacy-policy/)
- [Groq API Keys](https://console.groq.com/keys)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)

## Next Steps

For production deployment, work through the `groq-prod-checklist` skill, which
covers deployment gates, monitoring, and spend controls beyond this security
baseline.

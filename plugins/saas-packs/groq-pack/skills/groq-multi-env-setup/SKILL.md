---
name: groq-multi-env-setup
description: |
  Use when you need Groq to behave differently across dev, staging, and
  production — cheap fast models and verbose logs in dev, the production model
  and hardened retries everywhere else, with per-environment API keys.
  Configure environment-specific model selection, rate limits, and secrets.
  Trigger with phrases like "groq environments", "groq staging", "groq dev prod",
  "groq environment setup", "groq multi-env", "groq config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- deployment
- api
- llm
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Multi-Environment Setup

## Overview

Configure Groq API access across development, staging, and production with the right model, rate limit strategy, and secret management per environment. Key insight: use `llama-3.1-8b-instant` in development (cheapest, fastest), match production model in staging, and harden production with retries and fallbacks.

## Prerequisites

- A Groq account with API keys from [console.groq.com/keys](https://console.groq.com/keys) — ideally a separate key (or organization) per environment.
- Node project with the `groq-sdk` package installed (`npm install groq-sdk`).
- `NODE_ENV` set per environment (`development` / `staging` / `production`).
- A secret store for staging/production keys: GitHub Actions secrets, AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.

## Environment Strategy

| Environment | API Key Source | Default Model | Retry | Logging |
|-------------|---------------|---------------|-------|---------|
| Development | `.env.local` | `llama-3.1-8b-instant` | 1 | Verbose |
| Staging | CI/CD secrets | `llama-3.3-70b-versatile` | 3 | Standard |
| Production | Secret manager | `llama-3.3-70b-versatile` | 5 | Structured |

## Instructions

The full, copy-paste implementation lives in the reference files — this section
is the map. Read [the implementation walkthrough](references/implementation.md)
for the code module, service wrapper, and verify script, and
[secrets & deployment](references/secrets-and-deployment.md) for per-platform
key management, Docker Compose profiles, and rate-limit inspection.

1. **Build the config module** (`config/groq.ts`). One `configs` record keyed by
   environment resolves model, token budget, retries, timeout, and logging, then
   validates that a key is present with an environment-specific error message.
   The essential skeleton:

   ```typescript
   const configs: Record<string, GroqEnvConfig> = {
     development: { model: "llama-3.1-8b-instant", maxRetries: 1, logRequests: true, /* ... */ },
     staging:     { model: "llama-3.3-70b-versatile", maxRetries: 3, logRequests: false, /* ... */ },
     production:  { model: "llama-3.3-70b-versatile", maxRetries: 5, logRequests: false, /* ... */ },
   };
   export function getGroqConfig(): GroqEnvConfig {
     return configs[process.env.NODE_ENV || "development"] || configs.development;
   }
   ```

   See [implementation.md § Step 1](references/implementation.md) for the full module including key validation and the memoized `getGroqClient()`.

2. **Wire an environment-aware service** (`services/groq-service.ts`) that reads
   the resolved config, logs only when `logRequests` is on, and surfaces the
   `retry-after` header on `429`. Full code in
   [implementation.md § Step 2](references/implementation.md).

3. **Source secrets per platform.** Dev reads a git-ignored `.env.local`; staging
   uses CI/CD secrets; production pulls from a secret manager. Commands for
   GitHub Actions, AWS, GCP, and Vault are in
   [secrets-and-deployment.md § Step 3](references/secrets-and-deployment.md).

4. **Deploy with Docker Compose profiles** so each environment injects its own
   key (env var for dev/staging, external Docker secret for prod). See
   [secrets-and-deployment.md § Step 4](references/secrets-and-deployment.md).

5. **Verify each environment** with `scripts/verify-groq-env.ts`, which prints the
   resolved model/retries and does a live round-trip. Full script in
   [implementation.md § Step 5](references/implementation.md).

6. **Inspect rate limits** per key via the `x-ratelimit-*` response headers — see
   [secrets-and-deployment.md § Step 6](references/secrets-and-deployment.md).

## Output

After setup, each environment resolves its own Groq configuration and the verify
script confirms a live connection. Expected output from `verify-groq-env.ts` in
production:

```text
Environment: production
Model: llama-3.3-70b-versatile
Max retries: 5
API key prefix: gsk_AbCd...
Connection: OK (312ms)
Model response: OK
```

You end with: a `config/groq.ts` that selects model/retries/logging by `NODE_ENV`, a service wrapper that logs verbosely only in dev, per-environment keys sourced from the right secret store, and Docker Compose profiles that never leak a production key into the process environment.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `GROQ_API_KEY not set` | Missing env var | Check .env.local (dev) or secret manager (prod) |
| Wrong model in env | Config mismatch | Verify with `verify-groq-env.ts` script |
| Rate limited in dev | Free tier limits | Use `llama-3.1-8b-instant` with low max_tokens |
| Staging/prod key in dev | Key leak risk | Use separate Groq organizations per environment |

## Examples

**Resolve the config for the current environment:**

```typescript
import { getGroqConfig } from "./config/groq";

const config = getGroqConfig();      // picks dev/staging/prod by NODE_ENV
console.log(config.model);           // "llama-3.1-8b-instant" in dev
```

**Complete a chat with the environment default model:**

```typescript
import { complete } from "./services/groq-service";

const answer = await complete([{ role: "user", content: "Summarize in one line." }]);
```

**Verify production before a deploy:**

```bash
NODE_ENV=production GROQ_API_KEY_PROD=gsk_... npx tsx scripts/verify-groq-env.ts
```

Full, runnable versions of every snippet are in
[implementation.md](references/implementation.md) and
[secrets-and-deployment.md](references/secrets-and-deployment.md).

## Resources

- [Groq Console](https://console.groq.com)
- [Groq API Keys](https://console.groq.com/keys)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Implementation walkthrough](references/implementation.md) — config module, service, verify script
- [Secrets & deployment](references/secrets-and-deployment.md) — secret managers, Docker Compose, rate limits

## Next Steps

For deployment configuration, see the `groq-deploy-integration` skill, which builds on this environment strategy to wire CI/CD deploy pipelines and health checks.

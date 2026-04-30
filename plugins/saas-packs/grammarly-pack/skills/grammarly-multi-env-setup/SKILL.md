---
name: grammarly-multi-env-setup
description: 'Configure Grammarly across multiple environments.

  Use when setting up dev/staging/prod environments with Grammarly API.

  Trigger with phrases like "grammarly multi-env", "grammarly environments",

  "grammarly staging", "grammarly dev prod setup".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Multi-Environment Setup

## Overview

Grammarly integration requires environment separation to isolate API credentials, enforce team-scoped style guides, and manage rate limits per tier. Development uses mock API responses for fast iteration without consuming quota, staging connects to the Grammarly sandbox for real grammar checks with test content, and production runs against the live API with full team configurations. Each environment has its own client credentials and style guide settings to prevent dev experiments from affecting production writing standards.

## Environment Configuration

```typescript
const grammarlyConfig = (env: string) => ({
  development: {
    clientId: process.env.GRAMMARLY_DEV_CLIENT_ID!, clientSecret: process.env.GRAMMARLY_DEV_CLIENT_SECRET!,
    baseUrl: "http://localhost:3100/mock-grammarly", useMockApi: true, concurrency: 1, intervalCap: 2,
  },
  staging: {
    clientId: process.env.GRAMMARLY_STG_CLIENT_ID!, clientSecret: process.env.GRAMMARLY_STG_CLIENT_SECRET!,
    baseUrl: "https://api.grammarly.com/sandbox", useMockApi: false, concurrency: 2, intervalCap: 5,
  },
  production: {
    clientId: process.env.GRAMMARLY_PROD_CLIENT_ID!, clientSecret: process.env.GRAMMARLY_PROD_CLIENT_SECRET!,
    baseUrl: "https://api.grammarly.com", teamId: process.env.GRAMMARLY_TEAM_ID!, concurrency: 5, intervalCap: 10,
  },
}[env]);
```

## Environment Files

```bash
# Per-env files: .env.development, .env.staging, .env.production
GRAMMARLY_{DEV|STG|PROD}_CLIENT_ID=<client-id>
GRAMMARLY_{DEV|STG|PROD}_CLIENT_SECRET=<secret>
GRAMMARLY_BASE_URL={http://localhost:3100/mock|https://api.grammarly.com/sandbox|https://api.grammarly.com}
GRAMMARLY_TEAM_ID=<team-id>          # staging + production only
```

## Environment Validation

```typescript
function validateGrammarlyEnv(env: string): void {
  const suffix = { development: "_DEV", staging: "_STG", production: "_PROD" }[env];
  const required = [`GRAMMARLY${suffix}_CLIENT_ID`, `GRAMMARLY${suffix}_CLIENT_SECRET`];
  if (env === "production") required.push("GRAMMARLY_TEAM_ID");
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length) throw new Error(`Missing Grammarly vars for ${env}: ${missing.join(", ")}`);
}
```

## Promotion Workflow

```bash
# 1. Verify mock API coverage in dev
npm test -- --grep "grammarly" --env development

# 2. Run style guide checks against Grammarly sandbox
curl -X POST "https://api.grammarly.com/sandbox/check" \
  -H "Authorization: Bearer $GRAMMARLY_STG_TOKEN" -d @test-content.json

# 3. Compare suggestion quality between staging and baseline
node scripts/grammarly-diff.js --env staging --baseline expected-suggestions.json

# 4. Rotate credentials and deploy to production
GRAMMARLY_PROD_CLIENT_SECRET=$(vault read -field=secret grammarly/prod)
npm run deploy -- --env production
```

## Environment Matrix

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| API Endpoint | Mock (localhost) | Grammarly Sandbox | Live API |
| Team Style Guide | None | Test guide | Production guide |
| Rate Limit | 1 concurrent / 2 per interval | 2 / 5 | 5 / 10 |
| Quota Tracking | Disabled | Enabled | Enabled + alerts |
| User Scope | Developer only | QA team | All team members |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Client credentials expired or wrong env | Rotate credentials in Grammarly developer console for target env |
| Rate limit 429 | Concurrency exceeds tier plan | Lower `intervalCap` or upgrade Grammarly plan |
| Mock API returns empty | Local mock server not running | Start mock with `npm run mock:grammarly` before dev tests |
| Style guide mismatch | Team ID points to wrong guide | Verify `GRAMMARLY_TEAM_ID` matches the intended style guide |
| Suggestions differ across envs | Sandbox uses older model version | Expected behavior; validate core rules only in staging |

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

See `grammarly-deploy-integration`.

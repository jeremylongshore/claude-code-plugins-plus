---
name: juicebox-multi-env-setup
description: 'Configure Juicebox multi-environment.

  Trigger: "juicebox environments", "juicebox staging".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Multi-Environment Setup

## Overview

Juicebox AI analysis requires environment separation to enforce workspace isolation, control data access, and prevent accidental exports of sensitive datasets. Development works with sample datasets and strict result limits for fast iteration, staging connects to full production data but disables export functionality, and production enables all features with full export capabilities. Each environment uses isolated workspaces so analysis experiments in dev never affect production workspace state or user-facing reports.

## Environment Configuration

```typescript
const juiceboxConfig = (env: string) => ({
  development: {
    apiKey: process.env.JB_KEY_DEV!, baseUrl: "https://api.dev.juicebox.work/v1",
    workspaceId: process.env.JB_WORKSPACE_DEV!, resultLimit: 5, exportEnabled: false,
  },
  staging: {
    apiKey: process.env.JB_KEY_STG!, baseUrl: "https://api.staging.juicebox.work/v1",
    workspaceId: process.env.JB_WORKSPACE_STG!, resultLimit: 20, exportEnabled: false,
  },
  production: {
    apiKey: process.env.JB_KEY_PROD!, baseUrl: "https://api.juicebox.work/v1",
    workspaceId: process.env.JB_WORKSPACE_PROD!, resultLimit: 50, exportEnabled: true,
  },
}[env]);
```

## Environment Files

```bash
# Per-env files: .env.development, .env.staging, .env.production
JB_KEY_{DEV|STG|PROD}=<api-key>
JB_WORKSPACE_{DEV|STG|PROD}=<workspace-id>
JB_BASE_URL=https://api.{dev.|staging.|""}juicebox.work/v1
JB_EXPORT_ENABLED={false|false|true}
JB_DATASET_SCOPE={sample|full|full}
```

## Environment Validation

```typescript
function validateJuiceboxEnv(env: string): void {
  const suffix = { development: "_DEV", staging: "_STG", production: "_PROD" }[env];
  const required = [`JB_KEY${suffix}`, `JB_WORKSPACE${suffix}`, "JB_BASE_URL"];
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length) throw new Error(`Missing Juicebox vars for ${env}: ${missing.join(", ")}`);
}
```

## Promotion Workflow

```bash
# 1. Run analysis queries against sample data in dev
curl -X POST "$JB_BASE_URL/analyze" \
  -H "Authorization: Bearer $JB_KEY_DEV" -d @test-query.json

# 2. Validate same queries against full dataset in staging (exports blocked)
curl -X POST "$JB_BASE_URL/analyze" \
  -H "Authorization: Bearer $JB_KEY_STG" -d @test-query.json | jq '.resultCount'

# 3. Verify workspace isolation — staging results don't appear in prod
curl "$JB_BASE_URL/workspaces/$JB_WORKSPACE_PROD/reports" \
  -H "Authorization: Bearer $JB_KEY_PROD" | jq 'length'

# 4. Deploy to production with export capabilities enabled
JB_EXPORT_ENABLED=true npm run deploy -- --env production
```

## Environment Matrix

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Dataset | Sample (100 records) | Full dataset | Full dataset |
| Result Limit | 5 | 20 | 50 |
| Export Enabled | No | No | Yes |
| Workspace | Isolated dev | Isolated staging | Production |
| API Tier | Free | Standard | Enterprise |
| Report Sharing | Disabled | Internal only | Full access |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 403 on export endpoint | Export disabled in non-prod env | Expected; exports only work in production |
| Workspace not found | Workspace ID mismatch for env | Verify `JB_WORKSPACE_*` matches Juicebox admin panel |
| Result limit exceeded | Query returns more than env cap | Reduce query scope or increase limit in config |
| Stale sample data in dev | Dev dataset not refreshed | Run `npm run seed:dev` to reload sample data |
| API key scope error | Key generated for wrong workspace | Regenerate API key in correct workspace settings |

## Resources

- [Juicebox Docs](https://docs.juicebox.work)
- [Juicebox API Reference](https://docs.juicebox.work/api)

## Next Steps

See `juicebox-deploy-integration`.

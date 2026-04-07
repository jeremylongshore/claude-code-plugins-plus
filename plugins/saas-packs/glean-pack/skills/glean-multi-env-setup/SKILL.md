---
name: glean-multi-env-setup
description: |
  Use separate datasource names per environment (wiki_staging vs wiki_prod).
  Trigger: "glean multi env setup", "multi-env-setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Multi-Environment Setup

## Overview

Glean enterprise search requires environment isolation to prevent test data from polluting production search results. Each environment uses its own datasource names, API tokens, and connector configurations. Sandbox indexes synthetic test documents, staging indexes a curated subset of real documents for search quality validation, and production indexes the full corpus. Connector changes must be tested in staging before promotion to avoid breaking search relevance for end users.

## Environment Configuration

```typescript
const gleanConfig = (env: string) => ({
  development: {
    apiToken: process.env.GLEAN_API_TOKEN_DEV!, baseUrl: "https://sandbox.glean.com/api/v1",
    datasourceSuffix: "_sandbox", indexingEnabled: true, searchQualityChecks: false,
  },
  staging: {
    apiToken: process.env.GLEAN_API_TOKEN_STG!, baseUrl: "https://staging.glean.com/api/v1",
    datasourceSuffix: "_staging", indexingEnabled: true, searchQualityChecks: true,
  },
  production: {
    apiToken: process.env.GLEAN_API_TOKEN_PROD!, baseUrl: "https://app.glean.com/api/v1",
    datasourceSuffix: "_prod", indexingEnabled: true, searchQualityChecks: false,
  },
}[env]);
```

## Environment Files

```bash
# Per-env files: .env.development, .env.staging, .env.production
GLEAN_API_TOKEN_{DEV|STG|PROD}=<token>
GLEAN_BASE_URL=https://{sandbox|staging|app}.glean.com/api/v1
GLEAN_DATASOURCE_SUFFIX={_sandbox|_staging|_prod}
GLEAN_INSTANCE={sandbox|staging|production}
```

## Environment Validation

```typescript
function validateGleanEnv(env: string): void {
  const suffix = { development: "_DEV", staging: "_STG", production: "_PROD" }[env];
  const required = [`GLEAN_API_TOKEN${suffix}`, "GLEAN_BASE_URL", "GLEAN_INSTANCE"];
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length) throw new Error(`Missing Glean env vars for ${env}: ${missing.join(", ")}`);
}
```

## Promotion Workflow

```bash
# 1. Index test documents in sandbox
curl -X POST "$GLEAN_BASE_URL/indexing/datasources/wiki_sandbox/documents" \
  -H "Authorization: Bearer $GLEAN_API_TOKEN_DEV" -d @test-docs.json

# 2. Validate search quality in staging
curl "$GLEAN_BASE_URL/search" -H "Authorization: Bearer $GLEAN_API_TOKEN_STG" \
  -d '{"query": "onboarding guide"}' | jq '.results[:3].title'

# 3. Compare relevance scores against baseline
node scripts/compare-search-quality.js --env staging --baseline baseline.json

# 4. Promote connector config to production
cp connectors/staging/*.json connectors/production/
curl -X POST "$GLEAN_BASE_URL/indexing/datasources/wiki_prod/crawl" \
  -H "Authorization: Bearer $GLEAN_API_TOKEN_PROD"
```

## Environment Matrix

| Setting | Dev (Sandbox) | Staging | Prod |
|---------|---------------|---------|------|
| Data Source | Synthetic test docs | Subset of real docs | Full document index |
| Datasource Suffix | `_sandbox` | `_staging` | `_prod` |
| Connectors | Mock connectors | Real connectors | Real connectors |
| User Access | Developers only | QA + developers | All employees |
| Crawl Frequency | Manual | Daily | Continuous |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Datasource not found | Suffix mismatch between env and config | Verify `GLEAN_DATASOURCE_SUFFIX` matches connector registration |
| 401 on indexing API | Token scoped to wrong instance | Regenerate token in the correct Glean admin console |
| Search returns stale results | Crawl not triggered after promotion | Manually trigger crawl via indexing API |
| Connector sync fails | OAuth credentials expired for data source | Re-authorize connector in Glean admin for the target env |
| Staging indexes prod data | Connector config copied without suffix update | Always update datasource names when promoting configs |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-deploy-integration`.

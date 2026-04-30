---
name: openevidence-multi-env-setup
description: 'Multi Env Setup for OpenEvidence.

  Trigger: "openevidence multi env setup".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Multi-Environment Setup

## Overview

OpenEvidence clinical AI requires strict environment separation to maintain HIPAA compliance across the data lifecycle. Development uses only synthetic patient data with no PHI access, staging operates on de-identified datasets for clinical validation, and production handles full PHI under BAA-covered infrastructure. Each environment enforces its own audit logging, encryption, and access control policies. Misconfigured environments risk PHI exposure and regulatory violations, making environment validation a hard requirement at startup.

## Environment Configuration

```typescript
const openEvidenceConfig = (env: string) => ({
  development: {
    apiKey: process.env.OPENEVIDENCE_API_KEY_DEV!, baseUrl: "https://api.dev.openevidence.com/v1",
    dataClassification: "synthetic", phiEnabled: false, auditLevel: "basic", encryptionRequired: false,
  },
  staging: {
    apiKey: process.env.OPENEVIDENCE_API_KEY_STG!, baseUrl: "https://api.staging.openevidence.com/v1",
    dataClassification: "de-identified", phiEnabled: false, auditLevel: "full", encryptionRequired: true,
  },
  production: {
    apiKey: process.env.OPENEVIDENCE_API_KEY_PROD!, baseUrl: "https://api.openevidence.com/v1",
    dataClassification: "phi", phiEnabled: true, auditLevel: "full", encryptionRequired: true,
  },
}[env]);
```

## Environment Files

```bash
# Per-env files: .env.development, .env.staging, .env.production
OPENEVIDENCE_API_KEY_{DEV|STG|PROD}=<api-key>
OPENEVIDENCE_BASE_URL=https://api.{dev.|staging.|""}openevidence.com/v1
OPENEVIDENCE_DATA_CLASS={synthetic|de-identified|phi}
OPENEVIDENCE_PHI_ENABLED={false|false|true}
OPENEVIDENCE_AUDIT_LEVEL={basic|full|full}
OPENEVIDENCE_BAA_ID=<baa-id>          # production only
```

## Environment Validation

```typescript
function validateOpenEvidenceEnv(env: string): void {
  const suffix = { development: "_DEV", staging: "_STG", production: "_PROD" }[env];
  const required = [`OPENEVIDENCE_API_KEY${suffix}`, "OPENEVIDENCE_BASE_URL", "OPENEVIDENCE_DATA_CLASS"];
  if (env === "production") required.push("OPENEVIDENCE_BAA_ID");
  if (env !== "development") required.push("OPENEVIDENCE_AUDIT_LEVEL");
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length) throw new Error(`Missing OpenEvidence vars for ${env}: ${missing.join(", ")}`);
  if (env === "production" && process.env.OPENEVIDENCE_PHI_ENABLED !== "true")
    throw new Error("HIPAA violation: PHI must be enabled in production");
}
```

## Promotion Workflow

```bash
# 1. Run clinical queries against synthetic data in dev
curl -X POST "$OPENEVIDENCE_BASE_URL/query" \
  -H "Authorization: Bearer $OPENEVIDENCE_API_KEY_DEV" -d @synthetic-query.json

# 2. Validate with de-identified data in staging (audit logs required)
curl -X POST "$OPENEVIDENCE_BASE_URL/query" \
  -H "Authorization: Bearer $OPENEVIDENCE_API_KEY_STG" -d @staging-query.json

# 3. Verify HIPAA audit trail exists for all staging queries
curl "$OPENEVIDENCE_BASE_URL/audit/logs?env=staging" \
  -H "Authorization: Bearer $OPENEVIDENCE_API_KEY_STG" | jq '.totalEntries'

# 4. Deploy to production (requires BAA verification)
OPENEVIDENCE_BAA_ID=baa-2026-001 npm run deploy -- --env production --hipaa-check
```

## Environment Matrix

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Data Type | Synthetic only | De-identified | Full PHI |
| PHI Access | No | No | Yes (BAA required) |
| Audit Logging | Basic | Full | Full + HIPAA trail |
| Encryption at Rest | Optional | Required | Required (AES-256) |
| Access Control | Developer only | Clinical QA team | Authorized clinicians |
| BAA Required | No | No | Yes |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| HIPAA validation failed at startup | `PHI_ENABLED` not set in production | Set `OPENEVIDENCE_PHI_ENABLED=true` in prod env file |
| BAA ID missing | Production deploy without BAA reference | Add `OPENEVIDENCE_BAA_ID` from compliance team |
| 403 on PHI endpoint | Dev/staging key used against prod API | Use environment-specific API key with correct scope |
| Audit log gap detected | Staging queries not logged | Verify `OPENEVIDENCE_AUDIT_LEVEL=full` in staging env |

## Resources

- [OpenEvidence Docs](https://www.openevidence.com)
## Next Steps

See `openevidence-deploy-integration`.

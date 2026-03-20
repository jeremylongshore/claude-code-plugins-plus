---
name: lokalise-multi-env-setup
description: |
  Configure Lokalise across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Lokalise configurations.
  Trigger with phrases like "lokalise environments", "lokalise staging",
  "lokalise dev prod", "lokalise environment setup", "lokalise config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Multi-Environment Setup

## Overview

Configure Lokalise for isolated development, staging, and production environments. Two strategies are covered: separate Lokalise projects per environment (strongest isolation) and Lokalise branching within a single project (simpler management). Both approaches include secret management, environment-aware configuration, and a promotion workflow that moves translations through the pipeline from dev to production without cross-contamination.

## Prerequisites

- Lokalise Team or Enterprise plan (branching requires Team plan or higher)
- One Lokalise API token per environment, each scoped to minimum required permissions
- Secret management system: GitHub Secrets, AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault
- Node.js 18+ with `@lokalise/node-api` SDK installed
- Environment variable `NODE_ENV` (or equivalent) set in each deployment target

## Instructions

### Step 1: Choose Your Strategy

**Option A — Separate projects per environment** (recommended for teams > 5 translators or strict compliance):

| Environment | Lokalise Project | Purpose |
|-------------|-----------------|---------|
| Development | `MyApp (Dev)` | Rapid iteration, machine translations OK |
| Staging | `MyApp (Staging)` | QA review, translator proofing |
| Production | `MyApp (Prod)` | Approved translations only |

**Option B — Single project with Lokalise branching** (simpler for small teams):

| Branch | Purpose |
|--------|---------|
| `main` | Production translations |
| `staging` | QA translations under review |
| `dev` | Work-in-progress translations |

### Step 2: Environment-Aware Configuration

Create a configuration module that selects the correct Lokalise project and credentials based on the runtime environment:

```typescript
// src/config/lokalise.ts
interface LokaliseEnvConfig {
  environment: string;
  apiToken: string;
  projectId: string;
  branch?: string;           // Only used with Option B (branching)
  cacheTtlMs: number;
  enableOta: boolean;
  fallbackLocale: string;
  rateLimitPerSec: number;
}

const ENV_CONFIGS: Record<string, Omit<LokaliseEnvConfig, 'apiToken' | 'projectId'>> = {
  development: {
    environment: 'development',
    cacheTtlMs: 0,            // No cache in dev — always fetch fresh
    enableOta: false,
    fallbackLocale: 'en',
    rateLimitPerSec: 6,
  },
  staging: {
    environment: 'staging',
    cacheTtlMs: 5 * 60_000,  // 5 minutes
    enableOta: true,
    fallbackLocale: 'en',
    rateLimitPerSec: 6,
  },
  production: {
    environment: 'production',
    cacheTtlMs: 30 * 60_000, // 30 minutes
    enableOta: true,
    fallbackLocale: 'en',
    rateLimitPerSec: 4,       // Conservative — leave headroom for other integrations
  },
};

export function getLokaliseConfig(): LokaliseEnvConfig {
  const env = process.env.NODE_ENV || 'development';
  const base = ENV_CONFIGS[env];

  if (!base) {
    throw new Error(`Unknown environment: ${env}. Expected: ${Object.keys(ENV_CONFIGS).join(', ')}`);
  }

  const apiToken = process.env.LOKALISE_API_TOKEN;
  const projectId = process.env.LOKALISE_PROJECT_ID;

  if (!apiToken) {
    throw new Error('LOKALISE_API_TOKEN is not set');
  }
  if (!projectId) {
    throw new Error('LOKALISE_PROJECT_ID is not set');
  }

  return {
    ...base,
    apiToken,
    projectId,
    branch: process.env.LOKALISE_BRANCH,  // Optional: for branching strategy
  };
}
```

### Step 3: Secret Management

Store API tokens securely in each environment. Never commit tokens to source control.

**GitHub Actions (CI/CD):**

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN_STAGING }}
      LOKALISE_PROJECT_ID: ${{ vars.LOKALISE_PROJECT_ID_STAGING }}
    steps:
      - run: npm run build

  deploy-production:
    environment: production
    env:
      LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN_PROD }}
      LOKALISE_PROJECT_ID: ${{ vars.LOKALISE_PROJECT_ID_PROD }}
    steps:
      - run: npm run build
```

**AWS Secrets Manager:**

```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

async function getLokaliseToken(environment: string): Promise<string> {
  const client = new SecretsManagerClient({ region: 'us-east-1' });
  const command = new GetSecretValueCommand({
    SecretId: `lokalise/${environment}/api-token`,
  });
  const response = await client.send(command);
  return response.SecretString!;
}
```

**GCP Secret Manager:**

```typescript
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getLokaliseToken(environment: string): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/lokalise-token-${environment}/versions/latest`,
  });
  return version.payload!.data!.toString();
}
```

**HashiCorp Vault:**

```bash
# Read token from Vault
vault kv get -field=api_token secret/lokalise/production
```

### Step 4: Lokalise Branching (Option B Alternative)

If using a single project with branching instead of separate projects:

```typescript
import { LokaliseApi } from '@lokalise/node-api';

const lokalise = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const projectId = process.env.LOKALISE_PROJECT_ID!;

// Create a branch for a new environment or feature
async function createBranch(branchName: string): Promise<void> {
  await lokalise.branches().create({ name: branchName }, { project_id: projectId });
  console.log(`Created branch: ${branchName}`);
}

// Download translations from a specific branch
async function downloadFromBranch(branchName: string, outputDir: string): Promise<void> {
  const response = await lokalise.files().download(`${projectId}:${branchName}`, {
    format: 'json',
    original_filenames: true,
    directory_prefix: '',
    export_empty_as: 'base',
  });

  console.log(`Download URL: ${response.bundle_url}`);
  // Fetch and extract the zip from response.bundle_url into outputDir
}

// Merge a branch into main after QA approval
async function mergeBranch(sourceBranch: string, targetBranch = 'main'): Promise<void> {
  await lokalise.branches().merge(
    { project_id: projectId },
    {
      source_branch_id: sourceBranch,
      target_branch_id: targetBranch,
      force_conflict_resolve_using: 'source',
    }
  );
  console.log(`Merged ${sourceBranch} → ${targetBranch}`);
}
```

### Step 5: Promotion Workflow (Dev to Staging to Production)

Promote translations through environments with validation at each gate:

```bash
#!/bin/bash
# scripts/promote-translations.sh
# Usage: ./promote-translations.sh staging   (promote dev → staging)
# Usage: ./promote-translations.sh production (promote staging → production)
set -euo pipefail

TARGET_ENV="${1:?Usage: promote-translations.sh <staging|production>}"

case "$TARGET_ENV" in
  staging)
    SOURCE_TOKEN="$LOKALISE_API_TOKEN_DEV"
    SOURCE_PROJECT="$LOKALISE_PROJECT_ID_DEV"
    TARGET_TOKEN="$LOKALISE_API_TOKEN_STAGING"
    TARGET_PROJECT="$LOKALISE_PROJECT_ID_STAGING"
    ;;
  production)
    SOURCE_TOKEN="$LOKALISE_API_TOKEN_STAGING"
    SOURCE_PROJECT="$LOKALISE_PROJECT_ID_STAGING"
    TARGET_TOKEN="$LOKALISE_API_TOKEN_PROD"
    TARGET_PROJECT="$LOKALISE_PROJECT_ID_PROD"
    ;;
  *)
    echo "Invalid target: $TARGET_ENV (expected staging or production)"
    exit 1
    ;;
esac

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "=== Step 1: Download from source ==="
lokalise2 file download \
  --token "$SOURCE_TOKEN" \
  --project-id "$SOURCE_PROJECT" \
  --format json \
  --original-filenames=true \
  --directory-prefix="" \
  --export-empty-as=skip \
  --unzip-to "$TEMP_DIR/"

echo "=== Step 2: Validate completeness ==="
SOURCE_FILE="$TEMP_DIR/en.json"
if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "ERROR: Source locale file not found"
  exit 1
fi

SOURCE_KEY_COUNT=$(jq '[paths(scalars)] | length' "$SOURCE_FILE")
echo "Source has $SOURCE_KEY_COUNT keys"

for locale_file in "$TEMP_DIR"/*.json; do
  locale=$(basename "$locale_file" .json)
  key_count=$(jq '[paths(scalars)] | length' "$locale_file")
  coverage=$((key_count * 100 / SOURCE_KEY_COUNT))

  if [[ "$TARGET_ENV" == "production" && $coverage -lt 100 ]]; then
    echo "BLOCKED: ${locale} is ${coverage}% translated (production requires 100%)"
    exit 1
  elif [[ "$TARGET_ENV" == "staging" && $coverage -lt 80 ]]; then
    echo "WARNING: ${locale} is ${coverage}% translated"
  fi
  echo "  ${locale}: ${coverage}% (${key_count}/${SOURCE_KEY_COUNT} keys)"
done

echo "=== Step 3: Upload to target ==="
for locale_file in "$TEMP_DIR"/*.json; do
  locale=$(basename "$locale_file" .json)
  lokalise2 file upload \
    --token "$TARGET_TOKEN" \
    --project-id "$TARGET_PROJECT" \
    --file "$locale_file" \
    --lang-iso "$locale" \
    --replace-modified \
    --poll \
    --poll-timeout 120s
  echo "  Uploaded ${locale}"
  sleep 0.2  # Stay under 6 req/sec rate limit
done

echo "=== Promotion to ${TARGET_ENV} complete ==="
```

## Output

After applying this skill, the project will have:
- Environment-aware Lokalise configuration module (`src/config/lokalise.ts`)
- Per-environment API tokens stored in the chosen secret manager
- GitHub Actions workflows with environment-specific secrets
- Promotion script for moving translations through the dev/staging/prod pipeline
- (If using branching) Branch management utilities for the single-project approach

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `LOKALISE_API_TOKEN is not set` | Missing environment variable | Verify secret injection in deployment config |
| Wrong translations in production | Using dev project ID | Audit `LOKALISE_PROJECT_ID` per environment; never share project IDs across environments |
| Cross-env data leak | Shared API token with write access to multiple projects | Create separate tokens per environment with project-scoped permissions |
| Secret rotation breaks CI | Old token in GitHub Secrets | Rotate in Lokalise first, update GitHub Secret, verify CI run |
| Branch merge conflict | Same key edited in multiple branches | Resolve in Lokalise UI or use `force_conflict_resolve_using` |
| Promotion blocked at 80% | Coverage gate in staging | Expected — translate remaining keys in dev before promoting |
| Rate limit during promotion | Uploading many files sequentially | Add `sleep 0.2` between uploads; batch files if possible |

## Examples

### Quick Environment Check

```typescript
import { getLokaliseConfig } from './config/lokalise';

const config = getLokaliseConfig();
console.log(`Environment: ${config.environment}`);
console.log(`Project ID:  ${config.projectId}`);
console.log(`Cache TTL:   ${config.cacheTtlMs}ms`);
console.log(`OTA enabled: ${config.enableOta}`);
// Never log apiToken
```

### Startup Validation with Zod

```typescript
import { z } from 'zod';
import { getLokaliseConfig } from './config/lokalise';

const configSchema = z.object({
  environment: z.enum(['development', 'staging', 'production']),
  apiToken: z.string().min(30, 'LOKALISE_API_TOKEN looks too short — check the value'),
  projectId: z.string().regex(/^\w+\.\w+$/, 'LOKALISE_PROJECT_ID should be in format: projectId.branchSuffix'),
  cacheTtlMs: z.number().min(0),
  enableOta: z.boolean(),
  fallbackLocale: z.string().min(2),
  rateLimitPerSec: z.number().min(1).max(6),
});

// Validate at startup — fail fast if misconfigured
const config = configSchema.parse(getLokaliseConfig());
```

### Environment Matrix for `.env` Files

```bash
# .env.development
LOKALISE_API_TOKEN=dev-token-here
LOKALISE_PROJECT_ID=123456789.dev
LOKALISE_BRANCH=dev

# .env.staging
LOKALISE_API_TOKEN=staging-token-here
LOKALISE_PROJECT_ID=123456789.staging
LOKALISE_BRANCH=staging

# .env.production
LOKALISE_API_TOKEN=prod-token-here
LOKALISE_PROJECT_ID=987654321.prod
# No branch — production uses project root
```

> Add `.env.*` to `.gitignore`. Never commit tokens.

## Resources

- [Lokalise API — Projects](https://developers.lokalise.com/reference/list-all-projects)
- [Lokalise Branching](https://docs.lokalise.com/en/articles/3181040-branching)
- [Lokalise Team Permissions](https://docs.lokalise.com/en/articles/1400870-team-roles-and-permissions)
- [12-Factor App — Config](https://12factor.net/config)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)

## Next Steps

- Set up `lokalise-ci-integration` for automated upload/download in CI
- Run `lokalise-prod-checklist` before your first production deployment
- Use `lokalise-reference-architecture` to establish the full i18n project structure

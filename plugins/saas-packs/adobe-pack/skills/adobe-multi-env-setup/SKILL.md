---
name: adobe-multi-env-setup
description: |
  Configure Adobe OAuth credentials and API access across development,
  staging, and production environments with separate Developer Console
  projects, secret managers, and environment-specific scoping.
  Trigger with phrases like "adobe environments", "adobe staging",
  "adobe dev prod", "adobe environment setup", "adobe config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Multi-Environment Setup

## Overview

Configure Adobe APIs across development, staging, and production environments using separate Developer Console projects, environment-specific OAuth credentials, and cloud-native secret management.

## Prerequisites

- Adobe Developer Console access (admin or developer role)
- Secret management solution (GCP Secret Manager, AWS Secrets Manager, or Vault)
- CI/CD pipeline with environment variable injection

## Instructions

### Step 1: Create Separate Developer Console Projects

Adobe best practice: one Developer Console **project** per environment with separate OAuth credentials.

| Environment | Console Project | Scopes | Product Profile |
|-------------|----------------|--------|-----------------|
| Development | `my-app-dev` | `openid,AdobeID` | Dev sandbox |
| Staging | `my-app-staging` | `openid,AdobeID,firefly_api` | Staging profile |
| Production | `my-app-prod` | `openid,AdobeID,firefly_api,ff_apis` | Production profile |

### Step 2: Environment Configuration Files

```typescript
// src/config/adobe.ts
interface AdobeEnvConfig {
  imsEndpoint: string;       // Same across all envs
  fireflyEndpoint: string;   // Same across all envs
  photoshopEndpoint: string; // Same across all envs
  scopes: string;            // Different per env (least privilege)
  retries: number;
  timeoutMs: number;
  cache: { enabled: boolean; ttlMs: number };
}

const configs: Record<string, AdobeEnvConfig> = {
  development: {
    imsEndpoint: 'https://ims-na1.adobelogin.com',
    fireflyEndpoint: 'https://firefly-api.adobe.io',
    photoshopEndpoint: 'https://image.adobe.io',
    scopes: 'openid,AdobeID',        // Minimal scopes for dev
    retries: 1,                       // Fast failure in dev
    timeoutMs: 15_000,
    cache: { enabled: false, ttlMs: 0 },  // No cache in dev
  },
  staging: {
    imsEndpoint: 'https://ims-na1.adobelogin.com',
    fireflyEndpoint: 'https://firefly-api.adobe.io',
    photoshopEndpoint: 'https://image.adobe.io',
    scopes: 'openid,AdobeID,firefly_api',
    retries: 3,
    timeoutMs: 30_000,
    cache: { enabled: true, ttlMs: 60_000 },
  },
  production: {
    imsEndpoint: 'https://ims-na1.adobelogin.com',
    fireflyEndpoint: 'https://firefly-api.adobe.io',
    photoshopEndpoint: 'https://image.adobe.io',
    scopes: 'openid,AdobeID,firefly_api,ff_apis',
    retries: 5,
    timeoutMs: 60_000,
    cache: { enabled: true, ttlMs: 300_000 },
  },
};

export function getAdobeConfig(): AdobeEnvConfig & { clientId: string; clientSecret: string } {
  const env = process.env.NODE_ENV || 'development';
  const config = configs[env] || configs.development;

  return {
    ...config,
    clientId: process.env.ADOBE_CLIENT_ID!,
    clientSecret: process.env.ADOBE_CLIENT_SECRET!,
  };
}
```

### Step 3: Secret Management per Environment

```bash
# --- Local Development ---
# .env.local (git-ignored)
ADOBE_CLIENT_ID=dev-client-id-from-console
ADOBE_CLIENT_SECRET=p8_dev_secret
ADOBE_SCOPES=openid,AdobeID

# --- GCP Secret Manager ---
# Create secrets for staging and production
gcloud secrets create adobe-client-id-staging --data-file=- <<< "staging-client-id"
gcloud secrets create adobe-client-secret-staging --data-file=- <<< "p8_staging_secret"
gcloud secrets create adobe-client-id-prod --data-file=- <<< "prod-client-id"
gcloud secrets create adobe-client-secret-prod --data-file=- <<< "p8_prod_secret"

# Grant service account access
gcloud secrets add-iam-policy-binding adobe-client-secret-prod \
  --member="serviceAccount:my-app@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# --- AWS Secrets Manager ---
aws secretsmanager create-secret \
  --name adobe/staging/credentials \
  --secret-string '{"client_id":"...","client_secret":"p8_staging_..."}'

aws secretsmanager create-secret \
  --name adobe/production/credentials \
  --secret-string '{"client_id":"...","client_secret":"p8_prod_..."}'

# --- HashiCorp Vault ---
vault kv put secret/adobe/staging client_id="..." client_secret="p8_staging_..."
vault kv put secret/adobe/production client_id="..." client_secret="p8_prod_..."
```

### Step 4: CI/CD Environment Matrix

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    strategy:
      matrix:
        environment: [staging, production]
    environment: ${{ matrix.environment }}
    runs-on: ubuntu-latest
    env:
      NODE_ENV: ${{ matrix.environment }}
      ADOBE_CLIENT_ID: ${{ secrets[format('ADOBE_CLIENT_ID_{0}', matrix.environment)] }}
      ADOBE_CLIENT_SECRET: ${{ secrets[format('ADOBE_CLIENT_SECRET_{0}', matrix.environment)] }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
      - name: Verify Adobe credentials for ${{ matrix.environment }}
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            'https://ims-na1.adobelogin.com/ims/token/v3' \
            -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=openid,AdobeID")
          if [ "$HTTP_CODE" != "200" ]; then
            echo "::error::Adobe credential validation failed for ${{ matrix.environment }}"
            exit 1
          fi
      - run: npm run deploy:${{ matrix.environment }}
```

### Step 5: Environment Safety Guard

```typescript
// Prevent accidental production operations in non-prod
function requireEnvironment(required: string): void {
  const current = process.env.NODE_ENV || 'development';
  if (current !== required) {
    throw new Error(
      `Operation requires ${required} environment, currently running in ${current}`
    );
  }
}

// Usage: guard dangerous operations
async function deleteAllCachedAssets() {
  requireEnvironment('production');
  // ... actual deletion logic
}
```

## Output

- Separate Developer Console projects per environment
- Environment-aware configuration with least-privilege scoping
- Cloud-native secret management for credentials
- CI/CD pipeline with per-environment credential injection
- Safety guards preventing cross-environment operations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `invalid_scope` in staging | Scope not in staging project | Add API to staging Console project |
| Wrong credentials deployed | Environment mismatch | Verify `NODE_ENV` matches secret path |
| Secret access denied | Missing IAM binding | Grant secretAccessor role |
| Config merge fails | Missing env config file | Ensure all environments defined |

## Resources

- [Adobe Developer Console](https://developer.adobe.com/console)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `adobe-observability`.

---
name: webflow-multi-env-setup
description: |
  Configure Webflow across development, staging, and production environments with
  per-environment API tokens, site IDs, and secret management via Vault/AWS/GCP.
  Trigger with phrases like "webflow environments", "webflow staging",
  "webflow dev prod", "webflow environment setup", "webflow config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Multi-Environment Setup

## Overview

Configure Webflow Data API v2 integrations across development, staging, and production
with separate API tokens, site IDs, and secret management. Each environment targets
a different Webflow site for complete isolation.

## Prerequisites

- Separate Webflow sites for each environment (or at minimum, separate API tokens)
- Secret management solution (Vault, AWS Secrets Manager, or GCP Secret Manager)
- CI/CD pipeline with environment variable support

## Environment Strategy

| Environment | Webflow Site | API Token | CMS Data | Purpose |
|-------------|-------------|-----------|----------|---------|
| Development | Dev site | Dev token | Test/seed data | Local development |
| Staging | Staging site | Staging token | Copy of prod data | Pre-prod validation |
| Production | Production site | Prod token | Real data | Live traffic |

## Instructions

### Step 1: Environment Configuration

```typescript
// src/config/webflow.ts
type Environment = "development" | "staging" | "production";

interface WebflowEnvConfig {
  accessToken: string;
  siteId: string;
  maxRetries: number;
  webhookSecret: string;
  debug: boolean;
}

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || "development";
  const valid: Environment[] = ["development", "staging", "production"];
  return valid.includes(env as Environment) ? (env as Environment) : "development";
}

export function getWebflowConfig(): WebflowEnvConfig {
  const env = detectEnvironment();

  // Each environment has its own token and site
  const configs: Record<Environment, () => WebflowEnvConfig> = {
    development: () => ({
      accessToken: requireEnv("WEBFLOW_API_TOKEN"),
      siteId: requireEnv("WEBFLOW_SITE_ID"),
      maxRetries: 1,
      webhookSecret: process.env.WEBFLOW_WEBHOOK_SECRET || "",
      debug: true,
    }),
    staging: () => ({
      accessToken: requireEnv("WEBFLOW_API_TOKEN_STAGING"),
      siteId: requireEnv("WEBFLOW_SITE_ID_STAGING"),
      maxRetries: 2,
      webhookSecret: requireEnv("WEBFLOW_WEBHOOK_SECRET_STAGING"),
      debug: false,
    }),
    production: () => ({
      accessToken: requireEnv("WEBFLOW_API_TOKEN_PROD"),
      siteId: requireEnv("WEBFLOW_SITE_ID_PROD"),
      maxRetries: 3,
      webhookSecret: requireEnv("WEBFLOW_WEBHOOK_SECRET_PROD"),
      debug: false,
    }),
  };

  const config = configs[env]();
  console.log(`[webflow] Environment: ${env}, Site: ${config.siteId.substring(0, 8)}...`);
  return config;
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var: ${name}`);
  return value;
}
```

### Step 2: Environment Files

```bash
# .env.development (local, git-ignored)
WEBFLOW_API_TOKEN=dev-token-here
WEBFLOW_SITE_ID=dev-site-id-here
WEBFLOW_WEBHOOK_SECRET=dev-webhook-secret

# .env.staging (stored in CI/deployment platform, never committed)
WEBFLOW_API_TOKEN_STAGING=staging-token-here
WEBFLOW_SITE_ID_STAGING=staging-site-id-here
WEBFLOW_WEBHOOK_SECRET_STAGING=staging-webhook-secret

# .env.production (stored in vault/secret manager, never committed)
WEBFLOW_API_TOKEN_PROD=prod-token-here
WEBFLOW_SITE_ID_PROD=prod-site-id-here
WEBFLOW_WEBHOOK_SECRET_PROD=prod-webhook-secret

# .env.example (committed to repo, no real values)
WEBFLOW_API_TOKEN=your-token-here
WEBFLOW_SITE_ID=your-site-id-here
WEBFLOW_WEBHOOK_SECRET=your-webhook-secret
```

### Step 3: Secret Management

#### AWS Secrets Manager

```bash
# Store secrets
aws secretsmanager create-secret \
  --name webflow/production \
  --secret-string '{
    "WEBFLOW_API_TOKEN": "prod-token",
    "WEBFLOW_SITE_ID": "prod-site-id",
    "WEBFLOW_WEBHOOK_SECRET": "prod-webhook-secret"
  }'

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id webflow/production \
  --query SecretString --output text | jq .
```

```typescript
// Load from AWS at startup
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";

async function loadWebflowSecrets(env: string) {
  const client = new SecretsManagerClient({});
  const command = new GetSecretValueCommand({
    SecretId: `webflow/${env}`,
  });
  const response = await client.send(command);
  const secrets = JSON.parse(response.SecretString!);

  process.env.WEBFLOW_API_TOKEN_PROD = secrets.WEBFLOW_API_TOKEN;
  process.env.WEBFLOW_SITE_ID_PROD = secrets.WEBFLOW_SITE_ID;
}
```

#### GCP Secret Manager

```bash
# Store secrets
echo -n "prod-token" | gcloud secrets create webflow-api-token-prod --data-file=-
echo -n "prod-site-id" | gcloud secrets create webflow-site-id-prod --data-file=-

# Use in Cloud Run
gcloud run deploy webflow-service \
  --set-secrets="WEBFLOW_API_TOKEN_PROD=webflow-api-token-prod:latest,WEBFLOW_SITE_ID_PROD=webflow-site-id-prod:latest"
```

#### HashiCorp Vault

```bash
# Store secrets
vault kv put secret/webflow/production \
  api_token="prod-token" \
  site_id="prod-site-id" \
  webhook_secret="prod-webhook-secret"

# Retrieve
vault kv get -field=api_token secret/webflow/production
```

### Step 4: Environment Guards

Prevent destructive operations in wrong environment:

```typescript
function requireProduction(operation: string): void {
  const config = getWebflowConfig();
  if (config.debug) {
    throw new Error(
      `${operation} is production-only. Current: ${detectEnvironment()}`
    );
  }
}

function blockProduction(operation: string): void {
  const env = detectEnvironment();
  if (env === "production") {
    throw new Error(
      `${operation} is blocked in production. Use staging for testing.`
    );
  }
}

// Usage
async function publishSite(siteId: string) {
  requireProduction("publishSite"); // Only in production
  await webflow.sites.publish(siteId, { publishToWebflowSubdomain: true });
}

async function deleteAllItems(collectionId: string) {
  blockProduction("deleteAllItems"); // Never in production
  const { items } = await webflow.collections.items.listItems(collectionId);
  const ids = items!.map(i => i.id!);
  await webflow.collections.items.deleteItemsBulk(collectionId, { itemIds: ids });
}
```

### Step 5: CI/CD Environment Matrix

```yaml
# .github/workflows/webflow-deploy.yml
name: Deploy Webflow Integration

on:
  push:
    branches: [main, staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - branch: staging
            env: staging
            token_secret: WEBFLOW_API_TOKEN_STAGING
            site_secret: WEBFLOW_SITE_ID_STAGING
          - branch: main
            env: production
            token_secret: WEBFLOW_API_TOKEN_PROD
            site_secret: WEBFLOW_SITE_ID_PROD

    if: github.ref == format('refs/heads/{0}', matrix.branch)
    environment: ${{ matrix.env }}
    env:
      NODE_ENV: ${{ matrix.env }}
      WEBFLOW_API_TOKEN: ${{ secrets[matrix.token_secret] }}
      WEBFLOW_SITE_ID: ${{ secrets[matrix.site_secret] }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
      - name: Verify Webflow connectivity
        run: |
          curl -sf -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
            https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID > /dev/null
      - run: npm run deploy
```

### Step 6: Environment Status Dashboard

```typescript
async function environmentReport() {
  for (const env of ["development", "staging", "production"]) {
    try {
      process.env.NODE_ENV = env;
      const config = getWebflowConfig();
      const webflow = new WebflowClient({ accessToken: config.accessToken });

      const site = await webflow.sites.get(config.siteId);
      console.log(`[${env}] ${site.displayName} — last published: ${site.lastPublished}`);
    } catch (error: any) {
      console.log(`[${env}] ERROR: ${error.message}`);
    }
  }
}
```

## Output

- Per-environment configuration with separate tokens and site IDs
- Secret management via AWS/GCP/Vault
- Environment guards preventing dangerous cross-environment operations
- CI/CD matrix deploying to correct environment per branch
- Environment status reporting

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong site in production | Token/site mismatch | Verify WEBFLOW_SITE_ID matches expected site |
| Secret not found | Wrong path/name | Check secret manager path matches env |
| Guard triggered | Running prod operation in dev | Set NODE_ENV correctly |
| Missing env var | .env not loaded | `dotenv.config({ path: ".env.development" })` |

## Resources

- [Webflow Authentication](https://developers.webflow.com/data/reference/authentication)
- [12-Factor App Config](https://12factor.net/config)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For observability setup, see `webflow-observability`.

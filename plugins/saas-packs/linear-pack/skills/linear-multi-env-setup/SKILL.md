---
name: linear-multi-env-setup
description: |
  Configure Linear across development, staging, and production environments.
  Use when setting up per-environment API keys, secret management,
  or environment-specific Linear configurations.
  Trigger: "linear environments", "linear staging", "linear dev prod",
  "linear environment setup", "multi-environment linear".
allowed-tools: Read, Write, Edit, Bash(vault:*), Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, deployment, api]

---
# Linear Multi-Environment Setup

## Overview
Configure Linear integrations across dev, staging, and production with isolated API keys, secret management, environment guards, and per-environment webhook routing. Use separate Linear workspaces or at minimum separate API keys per environment.

## Prerequisites
- Separate Linear API keys per environment (dev, staging, prod)
- Secret management (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment support
- Node.js 18+

## Instructions

### Step 1: Environment Configuration
```typescript
// src/config/linear.ts
import { LinearClient } from "@linear/sdk";

interface LinearEnvConfig {
  apiKey: string;
  webhookSecret: string;
  defaultTeamKey: string;
  enableWebhooks: boolean;
  enableDebugLogging: boolean;
  cacheEnabled: boolean;
}

type Environment = "development" | "staging" | "production" | "test";

function getEnvironment(): Environment {
  const env = process.env.NODE_ENV ?? "development";
  if (!["development", "staging", "production", "test"].includes(env)) {
    throw new Error(`Unknown NODE_ENV: ${env}`);
  }
  return env as Environment;
}

async function loadConfig(): Promise<LinearEnvConfig> {
  const env = getEnvironment();

  // In production, use secret manager instead of env vars
  if (env === "production" || env === "staging") {
    return {
      apiKey: await getSecret(`linear-api-key-${env}`),
      webhookSecret: await getSecret(`linear-webhook-secret-${env}`),
      defaultTeamKey: process.env.LINEAR_DEFAULT_TEAM_KEY ?? "ENG",
      enableWebhooks: true,
      enableDebugLogging: env === "staging",
      cacheEnabled: true,
    };
  }

  // Dev/test: use environment variables
  return {
    apiKey: process.env.LINEAR_API_KEY ?? "",
    webhookSecret: process.env.LINEAR_WEBHOOK_SECRET ?? "",
    defaultTeamKey: process.env.LINEAR_DEV_TEAM_KEY ?? "DEV",
    enableWebhooks: false, // No webhook server in local dev
    enableDebugLogging: true,
    cacheEnabled: false,
  };
}
```

### Step 2: Secret Manager Integration
```typescript
// GCP Secret Manager
import { SecretManagerServiceClient } from "@google-cloud/secret-manager";

async function getSecret(name: string): Promise<string> {
  const client = new SecretManagerServiceClient();
  const projectId = process.env.GCP_PROJECT_ID!;
  const [version] = await client.accessSecretVersion({
    name: `projects/${projectId}/secrets/${name}/versions/latest`,
  });
  return version.payload?.data?.toString() ?? "";
}

// AWS Secrets Manager
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";

async function getSecretAWS(name: string): Promise<string> {
  const client = new SecretsManagerClient({});
  const result = await client.send(new GetSecretValueCommand({ SecretId: name }));
  return result.SecretString ?? "";
}

// HashiCorp Vault
async function getSecretVault(path: string): Promise<string> {
  const response = await fetch(`${process.env.VAULT_ADDR}/v1/${path}`, {
    headers: { "X-Vault-Token": process.env.VAULT_TOKEN! },
  });
  const data = await response.json();
  return data.data.data.value;
}
```

### Step 3: Environment-Aware Client Factory
```typescript
let _client: LinearClient | null = null;
let _config: LinearEnvConfig | null = null;

export async function getLinearClient(): Promise<LinearClient> {
  if (!_client) {
    _config = await loadConfig();
    if (!_config.apiKey) {
      throw new Error(`LINEAR_API_KEY not configured for ${getEnvironment()}`);
    }
    _client = new LinearClient({ apiKey: _config.apiKey });
  }
  return _client;
}

export async function getConfig(): Promise<LinearEnvConfig> {
  if (!_config) await getLinearClient(); // Triggers config load
  return _config!;
}

// For tests: inject a mock or test client
export function setTestClient(client: LinearClient) {
  _client = client;
}
```

### Step 4: Environment Guards
Prevent dangerous operations from running in the wrong environment.

```typescript
function requireProduction(operation: string) {
  if (getEnvironment() !== "production") {
    throw new Error(`${operation} is production-only (current: ${getEnvironment()})`);
  }
}

function preventProduction(operation: string) {
  if (getEnvironment() === "production") {
    throw new Error(`${operation} is forbidden in production`);
  }
}

// Usage
async function deleteAllTestIssues(teamKey: string) {
  preventProduction("deleteAllTestIssues"); // Safety guard

  const client = await getLinearClient();
  const issues = await client.issues({
    filter: {
      team: { key: { eq: teamKey } },
      title: { startsWith: "[TEST]" },
    },
  });

  for (const issue of issues.nodes) {
    await issue.delete();
  }
}

// Safe delete: archives in prod, deletes in dev
async function safeRemoveIssue(issueId: string) {
  const client = await getLinearClient();
  if (getEnvironment() === "production") {
    await client.archiveIssue(issueId);
  } else {
    await client.deleteIssue(issueId);
  }
}
```

### Step 5: Per-Environment Webhooks
```typescript
// Different webhook configs per environment
const webhookConfigs: Record<Environment, {
  resourceTypes: string[];
  enabled: boolean;
}> = {
  development: {
    resourceTypes: [], // No webhooks in dev — use polling/ngrok manually
    enabled: false,
  },
  staging: {
    resourceTypes: ["Issue", "Comment", "Project", "Cycle"],
    enabled: true,
  },
  production: {
    resourceTypes: ["Issue", "Comment", "Project", "Cycle", "IssueLabel", "ProjectUpdate"],
    enabled: true,
  },
  test: {
    resourceTypes: [],
    enabled: false,
  },
};
```

### Step 6: CI/CD with Environment Secrets
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, release/*]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm run deploy:staging
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_WEBHOOK_SECRET: ${{ secrets.LINEAR_WEBHOOK_SECRET }}

  deploy-production:
    if: startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm run deploy:production
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_WEBHOOK_SECRET: ${{ secrets.LINEAR_WEBHOOK_SECRET }}
```

### Step 7: Environment Validation Script
```typescript
// scripts/validate-environment.ts
async function validateEnvironment() {
  const env = getEnvironment();
  console.log(`Validating Linear config for: ${env}\n`);

  const config = await loadConfig();

  const checks = [
    { name: "API Key", ok: config.apiKey.startsWith("lin_api_") },
    { name: "Webhook Secret", ok: !config.enableWebhooks || config.webhookSecret.length > 10 },
    { name: "Default Team", ok: config.defaultTeamKey.length > 0 },
  ];

  // Test API connectivity
  try {
    const client = new LinearClient({ apiKey: config.apiKey });
    const viewer = await client.viewer;
    const teams = await client.teams();
    const team = teams.nodes.find(t => t.key === config.defaultTeamKey);

    checks.push({ name: "API Auth", ok: true });
    checks.push({ name: "Default Team Exists", ok: !!team });

    console.log(`  User: ${viewer.name} (${viewer.email})`);
    console.log(`  Teams: ${teams.nodes.map(t => t.key).join(", ")}`);
  } catch (e: any) {
    checks.push({ name: "API Auth", ok: false });
    console.error(`  Auth failed: ${e.message}`);
  }

  for (const { name, ok } of checks) {
    console.log(`  ${ok ? "PASS" : "FAIL"}: ${name}`);
  }

  const failed = checks.filter(c => !c.ok).length;
  if (failed > 0) process.exit(1);
}

validateEnvironment();
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment data | API key for wrong workspace | Verify secrets per environment |
| Secret not found | Missing in secret manager | Add secret for the target environment |
| Team not found | Wrong `defaultTeamKey` | Check team key matches the environment's workspace |
| Permission denied | Insufficient API key scope | Regenerate with correct scopes |

## Examples

### Quick Validation
```bash
NODE_ENV=staging npx tsx scripts/validate-environment.ts
# Output:
# Validating Linear config for: staging
#   User: CI Bot (ci@company.com)
#   Teams: ENG, PRODUCT, DESIGN
#   PASS: API Key
#   PASS: Webhook Secret
#   PASS: Default Team
#   PASS: API Auth
#   PASS: Default Team Exists
```

## Resources
- [Linear API Authentication](https://linear.app/developers/graphql)
- [12-Factor Config](https://12factor.net/config)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

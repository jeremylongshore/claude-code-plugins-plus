# Linear Multi-Environment Setup - Implementation Details

## Environment Configuration Structure

```typescript
// config/environments.ts
interface LinearEnvironmentConfig {
  apiKey: string;
  webhookSecret: string;
  defaultTeamKey: string;
  features: {
    syncEnabled: boolean;
    webhooksEnabled: boolean;
    debugMode: boolean;
  };
}

const configs = {
  development: {
    apiKey: process.env.LINEAR_API_KEY_DEV!,
    webhookSecret: process.env.LINEAR_WEBHOOK_SECRET_DEV!,
    defaultTeamKey: "DEV",
    features: { syncEnabled: true, webhooksEnabled: false, debugMode: true },
  },
  staging: {
    apiKey: process.env.LINEAR_API_KEY_STAGING!,
    webhookSecret: process.env.LINEAR_WEBHOOK_SECRET_STAGING!,
    defaultTeamKey: "STG",
    features: { syncEnabled: true, webhooksEnabled: true, debugMode: true },
  },
  production: {
    apiKey: process.env.LINEAR_API_KEY_PROD!,
    webhookSecret: process.env.LINEAR_WEBHOOK_SECRET_PROD!,
    defaultTeamKey: "PROD",
    features: { syncEnabled: true, webhooksEnabled: true, debugMode: false },
  },
};

export function getConfig(): LinearEnvironmentConfig {
  const env = process.env.NODE_ENV || "development";
  return configs[env as keyof typeof configs];
}
```

## Secret Management

### HashiCorp Vault
```typescript
import Vault from "node-vault";
const vault = Vault({ endpoint: process.env.VAULT_ADDR, token: process.env.VAULT_TOKEN });

export async function getLinearSecrets(environment: string) {
  const { data } = await vault.read(`secret/data/linear/${environment}`);
  return { apiKey: data.data.api_key, webhookSecret: data.data.webhook_secret };
}
```

### AWS Secrets Manager
```typescript
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";
const client = new SecretsManagerClient({ region: "us-east-1" });

export async function getLinearSecrets(environment: string) {
  const response = await client.send(new GetSecretValueCommand({ SecretId: `linear/${environment}` }));
  return JSON.parse(response.SecretString!);
}
```

### GCP Secret Manager
```typescript
import { SecretManagerServiceClient } from "@google-cloud/secret-manager";
const client = new SecretManagerServiceClient();

export async function getLinearSecrets(environment: string) {
  const [version] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT_ID}/secrets/linear-${environment}/versions/latest`,
  });
  return JSON.parse(version.payload!.data!.toString());
}
```

## Environment-Aware Client Factory

```typescript
import { LinearClient } from "@linear/sdk";

let clientInstance: LinearClient | null = null;

export async function getLinearClient(): Promise<LinearClient> {
  if (clientInstance) return clientInstance;
  const config = getConfig();
  let apiKey = config.apiKey;
  if (process.env.NODE_ENV === "production") {
    const secrets = await getLinearSecrets("production");
    apiKey = secrets.apiKey;
  }
  clientInstance = new LinearClient({ apiKey });
  return clientInstance;
}

export function setLinearClient(client: LinearClient): void { clientInstance = client; }
export function resetLinearClient(): void { clientInstance = null; }
```

## Environment Guards

```typescript
export function requireProduction(): void {
  if (process.env.NODE_ENV !== "production") {
    throw new Error("This operation requires production environment");
  }
}

export function preventProduction(): void {
  if (process.env.NODE_ENV === "production") {
    throw new Error("This operation is not allowed in production");
  }
}

// Safe issue deletion (prevents accidental production deletes)
export async function safeDeleteIssue(client: LinearClient, issueId: string): Promise<void> {
  if (process.env.NODE_ENV === "production") {
    await client.archiveIssue(issueId);
    console.log(`Archived issue ${issueId} (production safe mode)`);
  } else {
    await client.deleteIssue(issueId);
    console.log(`Deleted issue ${issueId}`);
  }
}
```

## Environment-Specific Webhook Configuration

```typescript
const webhookConfigs = {
  development: {
    url: "http://localhost:3000/api/webhooks/linear",
    events: ["Issue", "IssueComment"],
    enabled: false,
  },
  staging: {
    url: "https://staging.yourapp.com/api/webhooks/linear",
    events: ["Issue", "IssueComment", "Project", "Cycle"],
    enabled: true,
  },
  production: {
    url: "https://yourapp.com/api/webhooks/linear",
    events: ["Issue", "IssueComment", "Project", "Cycle", "Label"],
    enabled: true,
  },
};
```

## CI/CD Configuration

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches:
      - main      # Deploy to staging
      - release/* # Deploy to production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref == 'refs/heads/main' && 'staging' || 'production' }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: npm run deploy
        env:
          NODE_ENV: ${{ github.ref == 'refs/heads/main' && 'staging' || 'production' }}
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_WEBHOOK_SECRET: ${{ secrets.LINEAR_WEBHOOK_SECRET }}
```

## Environment Validation Script

```typescript
async function validateEnvironment(): Promise<void> {
  const config = getConfig();
  console.log(`Validating ${process.env.NODE_ENV} environment...`);

  const client = await getLinearClient();
  const viewer = await client.viewer;
  console.log(`  API Key: Valid (${viewer.email})`);

  const teams = await client.teams();
  const hasDefaultTeam = teams.nodes.some(t => t.key === config.defaultTeamKey);
  console.log(`  Default Team (${config.defaultTeamKey}): ${hasDefaultTeam ? "Found" : "NOT FOUND"}`);
  console.log(`  Webhook Secret: ${config.webhookSecret ? "Set" : "NOT SET"}`);
}
```

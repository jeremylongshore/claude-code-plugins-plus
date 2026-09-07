# Intercom Multi-Environment Setup — Full Implementation

The complete, step-by-step build for configuring Intercom across development,
staging, and production. SKILL.md carries the high-level workflow and the Step 1
skeleton; this file holds the full code for every step.

## Step 1: Environment Configuration

```typescript
// src/config/intercom.ts
interface IntercomEnvironmentConfig {
  accessToken: string;
  webhookSecret: string;
  identitySecret: string;
  environment: "development" | "staging" | "production";
  baseUrl: string;
  debug: boolean;
  cache: { enabled: boolean; ttlSeconds: number };
  rateLimit: { maxConcurrency: number };
}

function loadConfig(): IntercomEnvironmentConfig {
  const env = (process.env.NODE_ENV || "development") as IntercomEnvironmentConfig["environment"];

  const shared = {
    accessToken: process.env.INTERCOM_ACCESS_TOKEN!,
    webhookSecret: process.env.INTERCOM_WEBHOOK_SECRET!,
    identitySecret: process.env.INTERCOM_IDENTITY_SECRET || "",
    environment: env,
    baseUrl: "https://api.intercom.io",
  };

  const envDefaults: Record<string, Partial<IntercomEnvironmentConfig>> = {
    development: {
      debug: true,
      cache: { enabled: false, ttlSeconds: 0 },
      rateLimit: { maxConcurrency: 2 },
    },
    staging: {
      debug: false,
      cache: { enabled: true, ttlSeconds: 60 },
      rateLimit: { maxConcurrency: 5 },
    },
    production: {
      debug: false,
      cache: { enabled: true, ttlSeconds: 300 },
      rateLimit: { maxConcurrency: 10 },
    },
  };

  return { ...shared, ...envDefaults[env] } as IntercomEnvironmentConfig;
}

export const intercomConfig = loadConfig();
```

## Step 2: Environment-Aware Client Factory

```typescript
// src/intercom/client.ts
import { IntercomClient } from "intercom-client";
import { intercomConfig } from "../config/intercom";

let client: IntercomClient | null = null;

export function getClient(): IntercomClient {
  if (!client) {
    if (!intercomConfig.accessToken) {
      throw new Error(
        `INTERCOM_ACCESS_TOKEN not set for ${intercomConfig.environment}. ` +
        `Create a .env.${intercomConfig.environment} file.`
      );
    }

    client = new IntercomClient({
      token: intercomConfig.accessToken,
    });

    if (intercomConfig.debug) {
      console.log(`[Intercom] Connected to ${intercomConfig.environment} workspace`);
    }
  }
  return client;
}
```

## Step 3: Secret Management by Platform

```bash
# Local development (.env.development - git-ignored)
INTERCOM_ACCESS_TOKEN=dG9rOmRldl90b2tlbg==
INTERCOM_WEBHOOK_SECRET=dev-webhook-secret
NODE_ENV=development

# GitHub Actions (for CI)
gh secret set INTERCOM_DEV_TOKEN --body "dev-token"
gh secret set INTERCOM_STAGING_TOKEN --body "staging-token"
gh secret set INTERCOM_PROD_TOKEN --body "prod-token"

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name intercom/production/access-token \
  --secret-string "prod-token"

# GCP Secret Manager
echo -n "prod-token" | gcloud secrets create intercom-prod-token --data-file=-

# HashiCorp Vault
vault kv put secret/intercom/production \
  access_token="prod-token" \
  webhook_secret="prod-webhook-secret"
```

## Step 4: Production Safety Guards

```typescript
// Prevent destructive operations in wrong environment
class EnvironmentGuard {
  constructor(private env: string) {}

  requireProduction(operation: string): void {
    if (this.env !== "production") {
      throw new Error(
        `${operation} is only allowed in production (current: ${this.env})`
      );
    }
  }

  preventProduction(operation: string): void {
    if (this.env === "production") {
      throw new Error(
        `${operation} is blocked in production for safety`
      );
    }
  }
}

const guard = new EnvironmentGuard(intercomConfig.environment);

// Usage
async function deleteAllTestContacts() {
  guard.preventProduction("deleteAllTestContacts"); // Blocks in prod

  const contacts = await client.contacts.search({
    query: { field: "custom_attributes.is_test", operator: "=", value: true },
  });

  for (const contact of contacts.data) {
    await client.contacts.delete({ contactId: contact.id });
  }
}

async function sendBulkMessages(contactIds: string[], message: string) {
  guard.requireProduction("sendBulkMessages"); // Only works in prod
  // ... send messages
}
```

## Step 5: Webhook URL per Environment

```typescript
// CI/CD: Set webhook URL based on environment
const webhookUrls: Record<string, string> = {
  development: "https://dev-abc123.ngrok.io/webhooks/intercom",
  staging: "https://staging.example.com/webhooks/intercom",
  production: "https://api.example.com/webhooks/intercom",
};

// In your webhook handler, log the environment for debugging
app.post("/webhooks/intercom", (req, res) => {
  console.log(`[${intercomConfig.environment}] Webhook received: ${req.body.topic}`);
  // ... process webhook
});
```

## Step 6: Environment Validation on Startup

```typescript
async function validateIntercomSetup(): Promise<void> {
  const client = getClient();
  const config = intercomConfig;

  console.log(`[Intercom] Validating ${config.environment} setup...`);

  try {
    const admins = await client.admins.list();
    const appName = admins.admins[0]?.name || "Unknown";
    console.log(`[Intercom] Connected to workspace (admin: ${appName})`);

    // Verify we're in the right workspace
    if (config.environment === "production") {
      // In production, verify the token has expected permissions
      try {
        await client.contacts.list({ perPage: 1 });
        console.log("[Intercom] Contact access: OK");
      } catch {
        console.error("[Intercom] WARNING: Cannot access contacts");
      }
    }
  } catch (err) {
    console.error(`[Intercom] Setup validation FAILED for ${config.environment}:`, err);
    if (config.environment === "production") {
      throw err; // Fail fast in production
    }
  }
}

// Call during application startup
validateIntercomSetup().catch(console.error);
```

## GitHub Actions Environment Matrix

```yaml
jobs:
  test:
    strategy:
      matrix:
        environment: [development, staging]
    runs-on: ubuntu-latest
    env:
      NODE_ENV: ${{ matrix.environment }}
      INTERCOM_ACCESS_TOKEN: ${{ secrets[format('INTERCOM_{0}_TOKEN', matrix.environment)] }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
```

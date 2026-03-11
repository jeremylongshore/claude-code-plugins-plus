# Documenso Multi-Environment Setup - Implementation Guide

## Environment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Development                           │
│  API: stg-app.documenso.com (staging)                   │
│  Key: DOCUMENSO_API_KEY_DEV                             │
│  Purpose: Local development, testing                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      Staging                             │
│  API: stg-app.documenso.com                             │
│  Key: DOCUMENSO_API_KEY_STAGING                         │
│  Purpose: Integration testing, QA                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     Production                           │
│  API: app.documenso.com                                 │
│  Key: DOCUMENSO_API_KEY_PRODUCTION                      │
│  Purpose: Live customer traffic                          │
└─────────────────────────────────────────────────────────┘
```

## Configuration Files

### Environment-Specific Configs

```typescript
// config/documenso.development.json
{
  "baseUrl": "https://stg-app.documenso.com/api/v2/",
  "timeout": 30000,
  "debug": true,
  "mockEnabled": true,
  "testRecipients": ["dev@yourcompany.com"],
  "cacheOptions": {
    "enabled": false,
    "ttl": 60
  }
}

// config/documenso.staging.json
{
  "baseUrl": "https://stg-app.documenso.com/api/v2/",
  "timeout": 30000,
  "debug": true,
  "mockEnabled": false,
  "testRecipients": ["staging-test@yourcompany.com"],
  "cacheOptions": {
    "enabled": true,
    "ttl": 300
  }
}

// config/documenso.production.json
{
  "baseUrl": "https://app.documenso.com/api/v2/",
  "timeout": 30000,
  "debug": false,
  "mockEnabled": false,
  "testRecipients": [],
  "cacheOptions": {
    "enabled": true,
    "ttl": 600
  }
}
```

### Configuration Loader

```typescript
// src/config/documenso.ts
import { z } from "zod";

const EnvironmentSchema = z.enum(["development", "staging", "production"]);
type Environment = z.infer<typeof EnvironmentSchema>;

const ConfigSchema = z.object({
  baseUrl: z.string().url(),
  timeout: z.number().default(30000),
  debug: z.boolean().default(false),
  mockEnabled: z.boolean().default(false),
  testRecipients: z.array(z.string().email()).default([]),
  cacheOptions: z.object({
    enabled: z.boolean(),
    ttl: z.number(),
  }),
});

export type DocumensoConfig = z.infer<typeof ConfigSchema>;

export function getEnvironment(): Environment {
  const env = process.env.NODE_ENV ?? "development";
  return EnvironmentSchema.parse(env);
}

export function loadConfig(): DocumensoConfig & { apiKey: string } {
  const env = getEnvironment();

  // Load file config
  const fileConfig = require(`../../config/documenso.${env}.json`);

  // Get API key from environment variable
  const apiKeyVar = `DOCUMENSO_API_KEY_${env.toUpperCase()}`;
  const apiKey = process.env[apiKeyVar] ?? process.env.DOCUMENSO_API_KEY;

  if (!apiKey) {
    throw new Error(`Missing API key: ${apiKeyVar}`);
  }

  // Allow environment variable overrides
  const config = {
    ...ConfigSchema.parse(fileConfig),
    apiKey,
    baseUrl: process.env.DOCUMENSO_BASE_URL ?? fileConfig.baseUrl,
  };

  return config;
}
```

## Environment Variables

### .env.development

```bash
NODE_ENV=development
DOCUMENSO_API_KEY_DEVELOPMENT=dcs_dev_xxx
# Or use alias
DOCUMENSO_API_KEY=${DOCUMENSO_API_KEY_DEVELOPMENT}

# Optional overrides
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2/
DOCUMENSO_WEBHOOK_SECRET=dev-webhook-secret
```

### .env.staging

```bash
NODE_ENV=staging
DOCUMENSO_API_KEY_STAGING=dcs_staging_xxx
DOCUMENSO_WEBHOOK_SECRET=staging-webhook-secret
```

### .env.production

```bash
NODE_ENV=production
DOCUMENSO_API_KEY_PRODUCTION=dcs_prod_xxx
DOCUMENSO_WEBHOOK_SECRET=prod-webhook-secret
```

## Client Factory

```typescript
// src/documenso/factory.ts
import { Documenso } from "@documenso/sdk-typescript";
import { loadConfig, getEnvironment } from "../config/documenso";

interface ClientOptions {
  forceEnvironment?: "development" | "staging" | "production";
  mockMode?: boolean;
}

const clients = new Map<string, Documenso>();

export function getDocumensoClient(options?: ClientOptions): Documenso {
  const env = options?.forceEnvironment ?? getEnvironment();
  const cacheKey = `${env}-${options?.mockMode ?? false}`;

  if (clients.has(cacheKey)) {
    return clients.get(cacheKey)!;
  }

  const config = loadConfig();

  // Use mock client in development if enabled
  if (options?.mockMode && config.mockEnabled) {
    console.log(`[Documenso] Using mock client for ${env}`);
    return createMockClient();
  }

  const client = new Documenso({
    apiKey: config.apiKey,
    serverURL: config.baseUrl,
    timeoutMs: config.timeout,
    debugLogger: config.debug ? console : undefined,
  });

  clients.set(cacheKey, client);

  console.log(`[Documenso] Client initialized for ${env}`);
  console.log(`[Documenso] Base URL: ${config.baseUrl}`);

  return client;
}

// Reset clients (useful for testing)
export function resetClients(): void {
  clients.clear();
}
```

## Mock Client for Development

```typescript
// src/documenso/mock.ts
import { Documenso } from "@documenso/sdk-typescript";

let mockDocumentCounter = 0;

export function createMockClient(): Documenso {
  // Create a proxy that intercepts all method calls
  const mockClient = {
    documents: {
      createV0: async (input: any) => {
        mockDocumentCounter++;
        console.log(`[MOCK] Creating document: ${input.title}`);
        return {
          documentId: `mock_doc_${mockDocumentCounter}`,
          title: input.title,
          status: "DRAFT",
        };
      },
      getV0: async ({ documentId }: any) => {
        console.log(`[MOCK] Getting document: ${documentId}`);
        return {
          id: documentId,
          title: "Mock Document",
          status: "PENDING",
          recipients: [],
        };
      },
      findV0: async () => {
        console.log(`[MOCK] Finding documents`);
        return { documents: [], totalPages: 0 };
      },
      deleteV0: async ({ documentId }: any) => {
        console.log(`[MOCK] Deleting document: ${documentId}`);
        return { success: true };
      },
    },
    templates: {
      getV0: async ({ templateId }: any) => {
        console.log(`[MOCK] Getting template: ${templateId}`);
        return {
          id: templateId,
          title: "Mock Template",
          recipients: [],
        };
      },
    },
    // Add more mock methods as needed
  };

  return mockClient as unknown as Documenso;
}
```

## Environment Promotion

```typescript
// scripts/promote-templates.ts
/**
 * Promote templates from staging to production.
 * Templates are recreated in production with same configuration.
 */

import { getDocumensoClient } from "../src/documenso/factory";

interface TemplateMapping {
  stagingId: string;
  productionId?: string;
  name: string;
}

const TEMPLATE_MAPPINGS: TemplateMapping[] = [
  { stagingId: "tmpl_stg_nda", name: "NDA Template" },
  { stagingId: "tmpl_stg_contract", name: "Contract Template" },
];

async function promoteTemplates() {
  const stagingClient = getDocumensoClient({ forceEnvironment: "staging" });
  const prodClient = getDocumensoClient({ forceEnvironment: "production" });

  console.log("Promoting templates from staging to production...\n");

  for (const mapping of TEMPLATE_MAPPINGS) {
    try {
      // Get staging template
      const stagingTemplate = await stagingClient.templates.getV0({
        templateId: mapping.stagingId,
      });

      console.log(`Template: ${mapping.name}`);
      console.log(`  Staging ID: ${mapping.stagingId}`);

      // Note: In practice, you'd need to download the PDF and recreate
      // the template in production. This is a simplified example.
      console.log(`  Status: Ready for manual creation in production`);
      console.log(`  Fields: ${stagingTemplate.fields?.length ?? 0}`);
      console.log(`  Recipients: ${stagingTemplate.recipients?.length ?? 0}`);
      console.log("");
    } catch (error: any) {
      console.error(`  Error: ${error.message}`);
    }
  }
}

promoteTemplates().catch(console.error);
```

## Webhook Configuration Per Environment

```typescript
// src/webhooks/config.ts
import { getEnvironment } from "../config/documenso";

interface WebhookConfig {
  url: string;
  secret: string;
  events: string[];
}

export function getWebhookConfig(): WebhookConfig {
  const env = getEnvironment();

  const configs: Record<string, WebhookConfig> = {
    development: {
      url: "https://dev.yourapp.com/webhooks/documenso",
      secret: process.env.DOCUMENSO_WEBHOOK_SECRET_DEV ?? "",
      events: ["document.created", "document.completed"],
    },
    staging: {
      url: "https://staging.yourapp.com/webhooks/documenso",
      secret: process.env.DOCUMENSO_WEBHOOK_SECRET_STAGING ?? "",
      events: [
        "document.created",
        "document.sent",
        "document.signed",
        "document.completed",
      ],
    },
    production: {
      url: "https://app.yourapp.com/webhooks/documenso",
      secret: process.env.DOCUMENSO_WEBHOOK_SECRET_PRODUCTION ?? "",
      events: [
        "document.created",
        "document.sent",
        "document.opened",
        "document.signed",
        "document.completed",
        "document.rejected",
        "document.cancelled",
      ],
    },
  };

  return configs[env];
}
```

## Testing Across Environments

```typescript
// tests/integration/environment.test.ts
import { describe, it, expect, beforeAll } from "vitest";
import { getDocumensoClient, resetClients } from "../../src/documenso/factory";

describe("Multi-Environment Configuration", () => {
  beforeAll(() => {
    resetClients();
  });

  it("connects to staging environment", async () => {
    const client = getDocumensoClient({ forceEnvironment: "staging" });
    const result = await client.documents.findV0({ perPage: 1 });
    expect(result).toBeDefined();
  });

  it("uses mock client in development with mockMode", async () => {
    const client = getDocumensoClient({
      forceEnvironment: "development",
      mockMode: true,
    });
    const doc = await client.documents.createV0({ title: "Test" });
    expect(doc.documentId).toMatch(/^mock_doc_/);
  });

  it("production requires production API key", async () => {
    // This test verifies production config is properly isolated
    const config = loadConfigForEnv("production");
    expect(config.baseUrl).toBe("https://app.documenso.com/api/v2/");
    expect(config.debug).toBe(false);
  });
});
```

## Environment Checklist

### Development
- [ ] Using staging Documenso API
- [ ] Mock mode available for offline development
- [ ] Debug logging enabled
- [ ] Test recipients configured
- [ ] Caching disabled for fresh data

### Staging
- [ ] Separate API key from production
- [ ] All webhooks configured
- [ ] Integration tests passing
- [ ] Template parity with production
- [ ] Monitoring configured

### Production
- [ ] Production API key secured
- [ ] Webhooks verified
- [ ] Caching enabled
- [ ] Debug logging disabled
- [ ] Alerting configured

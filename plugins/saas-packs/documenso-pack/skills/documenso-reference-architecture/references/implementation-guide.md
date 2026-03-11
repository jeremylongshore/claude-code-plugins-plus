# Documenso Reference Architecture - Implementation Guide

## Project Structure

```
my-signing-app/
├── src/
│   ├── documenso/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── signing/
│   │       ├── index.ts        # Service facade
│   │       ├── documents.ts    # Document operations
│   │       ├── templates.ts    # Template operations
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── signing/
│   │       ├── routes.ts       # API routes
│   │       └── webhook.ts      # Webhook endpoint
│   ├── jobs/
│   │   └── signing/
│   │       ├── cleanup.ts      # Draft cleanup job
│   │       └── sync.ts         # Status sync job
│   └── utils/
│       ├── pdf.ts              # PDF utilities
│       └── validation.ts       # Input validation
├── tests/
│   ├── unit/
│   │   └── signing/
│   │       ├── documents.test.ts
│   │       └── templates.test.ts
│   └── integration/
│       └── signing/
│           └── workflows.test.ts
├── config/
│   ├── documenso.development.json
│   ├── documenso.staging.json
│   └── documenso.production.json
├── templates/
│   └── pdf/                    # PDF template files
│       ├── nda.pdf
│       ├── contract.pdf
│       └── agreement.pdf
└── docs/
    └── signing/
        ├── SETUP.md
        └── RUNBOOK.md
```

## Layer Architecture

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (Controllers, Routes, Webhooks)        │
├─────────────────────────────────────────┤
│           Service Layer                  │
│  (Business Logic, Orchestration)         │
├─────────────────────────────────────────┤
│          Documenso Layer                 │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Documenso Client Wrapper

```typescript
// src/documenso/client.ts
import { Documenso } from "@documenso/sdk-typescript";
import { DocumensoConfig, loadDocumensoConfig } from "./config";
import { CacheService } from "../services/signing/cache";
import { MetricsService } from "../utils/metrics";

export class DocumensoService {
  private client: Documenso;
  private cache: CacheService;
  private metrics: MetricsService;

  constructor(config: DocumensoConfig) {
    this.client = new Documenso({
      apiKey: config.apiKey,
      serverURL: config.baseUrl,
      timeoutMs: config.timeout,
    });
    this.cache = new CacheService(config.cacheOptions);
    this.metrics = new MetricsService("documenso");
  }

  async getDocument(documentId: string) {
    return this.cache.getOrFetch(
      `doc:${documentId}`,
      () => this.metrics.track("getDocument", () =>
        this.client.documents.getV0({ documentId })
      ),
      { ttl: 300 }
    );
  }

  async createDocument(input: CreateDocumentInput) {
    return this.metrics.track("createDocument", () =>
      this.client.documents.createV0(input)
    );
  }

  // Expose raw client for advanced use cases
  getRawClient(): Documenso {
    return this.client;
  }
}

// Singleton instance
let service: DocumensoService | null = null;

export function getDocumensoService(): DocumensoService {
  if (!service) {
    const config = loadDocumensoConfig();
    service = new DocumensoService(config);
  }
  return service;
}
```

### Configuration Management

```typescript
// src/documenso/config.ts
import { z } from "zod";

const ConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseUrl: z.string().url().optional(),
  timeout: z.number().default(30000),
  cacheOptions: z.object({
    enabled: z.boolean().default(true),
    ttl: z.number().default(300),
  }).default({}),
});

export type DocumensoConfig = z.infer<typeof ConfigSchema>;

export function loadDocumensoConfig(): DocumensoConfig {
  const env = process.env.NODE_ENV ?? "development";

  // Load environment-specific config
  let fileConfig = {};
  try {
    fileConfig = require(`../../config/documenso.${env}.json`);
  } catch {
    console.warn(`No config file for environment: ${env}`);
  }

  // Merge with environment variables
  const config = {
    apiKey: process.env.DOCUMENSO_API_KEY ?? "",
    baseUrl: process.env.DOCUMENSO_BASE_URL,
    ...fileConfig,
  };

  return ConfigSchema.parse(config);
}
```

### Error Boundary

```typescript
// src/documenso/errors.ts
export class DocumensoServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "DocumensoServiceError";
  }

  static fromSdkError(error: any): DocumensoServiceError {
    const statusCode = error.statusCode ?? error.status ?? 0;
    const retryable = statusCode === 429 || statusCode >= 500;

    return new DocumensoServiceError(
      error.message,
      `DOCUMENSO_${statusCode}`,
      statusCode,
      retryable,
      error
    );
  }
}

export async function withErrorHandling<T>(
  operation: () => Promise<T>
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    throw DocumensoServiceError.fromSdkError(error);
  }
}
```

### Service Facade

```typescript
// src/services/signing/index.ts
import { getDocumensoService } from "../../documenso/client";
import { withErrorHandling } from "../../documenso/errors";
import { validateCreateDocumentInput } from "../../utils/validation";

export interface SigningService {
  createAndSendDocument(input: CreateDocumentInput): Promise<DocumentResult>;
  getDocumentStatus(documentId: string): Promise<DocumentStatus>;
  downloadSignedDocument(documentId: string): Promise<Buffer>;
}

export class SigningServiceImpl implements SigningService {
  private documenso = getDocumensoService();

  async createAndSendDocument(
    input: CreateDocumentInput
  ): Promise<DocumentResult> {
    // Validate input
    const validated = validateCreateDocumentInput(input);

    return withErrorHandling(async () => {
      // Create from template
      const envelope = await this.documenso.getRawClient().envelopes.useV0({
        templateId: validated.templateId,
        title: validated.title,
        recipients: validated.recipients.map((r, i) => ({
          email: r.email,
          name: r.name,
          signerIndex: i,
        })),
      });

      // Send immediately
      await this.documenso.getRawClient().envelopes.distributeV0({
        envelopeId: envelope.envelopeId!,
      });

      return {
        documentId: envelope.envelopeId!,
        status: "SENT",
      };
    });
  }

  async getDocumentStatus(documentId: string): Promise<DocumentStatus> {
    const doc = await this.documenso.getDocument(documentId);
    return {
      id: doc.id!,
      status: doc.status!,
      recipients: doc.recipients?.map((r) => ({
        email: r.email!,
        status: r.signingStatus!,
      })) ?? [],
    };
  }

  async downloadSignedDocument(documentId: string): Promise<Buffer> {
    return withErrorHandling(async () => {
      const result = await this.documenso.getRawClient().documents.downloadV0({
        documentId,
      });
      // Handle the download response
      return Buffer.from(result as any);
    });
  }
}

// Export singleton
let signingService: SigningService | null = null;

export function getSigningService(): SigningService {
  if (!signingService) {
    signingService = new SigningServiceImpl();
  }
  return signingService;
}
```

### Health Check

```typescript
// src/documenso/health.ts
import { getDocumensoService } from "./client";

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  error?: string;
}

export async function checkDocumensoHealth(): Promise<HealthStatus> {
  const service = getDocumensoService();
  const start = Date.now();

  try {
    await service.getRawClient().documents.findV0({ perPage: 1 });
    return {
      status: "healthy",
      latencyMs: Date.now() - start,
    };
  } catch (error: any) {
    return {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      error: error.message,
    };
  }
}
```

## Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────┐
│   API       │
│   Layer     │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│  Service    │───▶│   Cache     │
│   Layer     │    │  (Redis)    │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│ Documenso   │───▶│   Queue     │
│   Layer     │    │  (Bull)     │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ Documenso   │
│   API       │
└─────────────┘
```

## Webhook Architecture

```
Documenso
    │
    ▼ POST /webhooks/documenso
┌─────────────┐
│  Webhook    │
│  Handler    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Event      │
│  Queue      │
└──────┬──────┘
       │
       ├──▶ Update Database
       ├──▶ Send Notifications
       ├──▶ Trigger Workflows
       └──▶ Update Cache
```

## Setup Script

```bash
#!/bin/bash
# scripts/setup-documenso-structure.sh

# Create directory structure
mkdir -p src/documenso/handlers
mkdir -p src/services/signing
mkdir -p src/api/signing
mkdir -p src/jobs/signing
mkdir -p src/utils
mkdir -p tests/unit/signing
mkdir -p tests/integration/signing
mkdir -p config
mkdir -p templates/pdf
mkdir -p docs/signing

# Create placeholder files
touch src/documenso/{client,config,types,errors}.ts
touch src/documenso/handlers/{webhooks,events}.ts
touch src/services/signing/{index,documents,templates,cache}.ts
touch src/api/signing/{routes,webhook}.ts
touch config/documenso.{development,staging,production}.json

echo "Documenso project structure created!"
```

---
name: adobe-reference-architecture
description: |
  Implement Adobe reference architecture for production integrations covering
  Firefly Services, PDF Services, I/O Events, and App Builder with layered
  project layout, error boundaries, and health monitoring.
  Trigger with phrases like "adobe architecture", "adobe project structure",
  "how to organize adobe", "adobe layout", "adobe best practices".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Reference Architecture

## Overview

Production-ready architecture patterns for Adobe API integrations, designed around the three main API families: Firefly Services (creative AI), PDF Services (document automation), and I/O Events (event-driven).

## Prerequisites

- Understanding of layered architecture
- TypeScript project setup
- Decision on which Adobe APIs to integrate

## Instructions

### Step 1: Project Structure

```
my-adobe-project/
├── src/
│   ├── adobe/                     # Adobe client layer
│   │   ├── auth.ts                # OAuth Server-to-Server token management
│   │   ├── firefly-client.ts      # Firefly API wrapper (generate, fill, expand)
│   │   ├── pdf-client.ts          # PDF Services wrapper (create, extract, merge)
│   │   ├── photoshop-client.ts    # Photoshop API wrapper (cutout, actions)
│   │   ├── events-client.ts       # I/O Events registration and verification
│   │   ├── types.ts               # Shared Adobe types
│   │   └── errors.ts              # Error classification (retryable vs permanent)
│   ├── services/                  # Business logic layer
│   │   ├── image-generation.ts    # Orchestrates Firefly + Photoshop workflows
│   │   ├── document-pipeline.ts   # Orchestrates PDF create/extract/merge
│   │   └── event-processor.ts     # Routes and processes I/O Events
│   ├── api/                       # API layer (routes, controllers)
│   │   ├── health.ts              # Health check including Adobe IMS
│   │   ├── webhooks/adobe.ts      # I/O Events webhook endpoint
│   │   └── routes/
│   │       ├── images.ts          # Image generation endpoints
│   │       └── documents.ts       # Document processing endpoints
│   ├── jobs/                      # Background job layer
│   │   ├── firefly-batch.ts       # Batch image generation queue
│   │   └── pdf-extraction.ts      # Async PDF extraction worker
│   └── index.ts
├── tests/
│   ├── unit/
│   │   ├── adobe/auth.test.ts
│   │   └── services/
│   └── integration/
│       └── adobe/
│           ├── firefly.test.ts
│           └── pdf-services.test.ts
├── config/
│   ├── adobe.development.json
│   ├── adobe.staging.json
│   └── adobe.production.json
└── package.json
```

### Step 2: Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                    API Layer                         │
│   Routes, Controllers, Webhook Endpoints            │
├─────────────────────────────────────────────────────┤
│                  Service Layer                       │
│   Business Logic, Workflow Orchestration             │
│   (image-generation.ts, document-pipeline.ts)       │
├─────────────────────────────────────────────────────┤
│                Adobe Client Layer                    │
│   auth.ts, firefly-client.ts, pdf-client.ts         │
│   Token caching, retry, error classification        │
├─────────────────────────────────────────────────────┤
│              Infrastructure Layer                    │
│   Cache (LRU/Redis), Queue (BullMQ), Monitoring     │
└─────────────────────────────────────────────────────┘
```

**Rules:**
- API layer never calls Adobe APIs directly — always through Service layer
- Service layer orchestrates multiple Adobe clients (e.g., Firefly + Photoshop)
- Adobe Client layer handles auth, retry, error classification
- Infrastructure layer is swappable (in-memory cache for dev, Redis for prod)

### Step 3: Error Boundary

```typescript
// src/adobe/errors.ts
export class AdobeServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly httpStatus: number,
    public readonly retryable: boolean,
    public readonly api: 'firefly' | 'pdf-services' | 'photoshop' | 'events',
    public readonly retryAfter?: number,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AdobeServiceError';
  }

  static fromResponse(api: string, status: number, body: string, headers?: Headers): AdobeServiceError {
    const retryAfter = headers?.get('Retry-After');
    return new AdobeServiceError(
      `Adobe ${api} API error (${status}): ${body.slice(0, 200)}`,
      status === 429 ? 'RATE_LIMITED' :
      status === 401 ? 'AUTH_EXPIRED' :
      status >= 500 ? 'SERVER_ERROR' : 'CLIENT_ERROR',
      status,
      status === 429 || status >= 500,
      api as any,
      retryAfter ? parseInt(retryAfter) : undefined,
    );
  }
}
```

### Step 4: Configuration Management

```typescript
// config/adobe.ts
export interface AdobeConfig {
  clientId: string;
  clientSecret: string;
  scopes: string;
  environment: 'development' | 'staging' | 'production';
  apis: {
    firefly: { enabled: boolean; baseUrl: string };
    pdfServices: { enabled: boolean };
    photoshop: { enabled: boolean; baseUrl: string };
    events: { enabled: boolean; webhookUrl: string };
  };
  retry: { maxRetries: number; baseDelayMs: number };
  cache: { enabled: boolean; ttlSeconds: number };
}

export function loadConfig(): AdobeConfig {
  const env = process.env.NODE_ENV || 'development';
  const base = require(`./adobe.${env}.json`);
  return {
    ...base,
    clientId: process.env.ADOBE_CLIENT_ID!,
    clientSecret: process.env.ADOBE_CLIENT_SECRET!,
    scopes: process.env.ADOBE_SCOPES!,
    environment: env as any,
  };
}
```

### Step 5: Health Check

```typescript
// src/api/health.ts
export async function adobeHealthCheck(config: AdobeConfig) {
  const checks: Record<string, any> = {};

  // Always check IMS auth
  try {
    const start = Date.now();
    await getCachedToken();
    checks.ims = { status: 'healthy', latencyMs: Date.now() - start };
  } catch (e: any) {
    checks.ims = { status: 'unhealthy', error: e.message };
  }

  // Check enabled APIs
  if (config.apis.firefly.enabled) {
    checks.firefly = await pingEndpoint('https://firefly-api.adobe.io');
  }
  if (config.apis.photoshop.enabled) {
    checks.photoshop = await pingEndpoint('https://image.adobe.io');
  }

  const overall = Object.values(checks).every(
    (c: any) => c.status === 'healthy'
  ) ? 'healthy' : 'degraded';

  return { status: overall, services: checks };
}
```

## Data Flow

```
User Request
     │
     ▼
┌─────────────┐
│   Express    │ ← Webhook from Adobe I/O Events
│   Router     │
└──────┬───┬──┘
       │   │
       ▼   ▼
┌────────┐ ┌────────────┐
│Service │ │Event       │
│Layer   │ │Processor   │
└───┬────┘ └──────┬─────┘
    │              │
    ▼              ▼
┌──────────────────────┐    ┌─────────┐
│  Adobe Client Layer  │───▶│  Cache   │
│  (auth + API calls)  │    │ LRU/Redis│
└──────────┬───────────┘    └─────────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐
│Firefly││PDF   ││Photo │
│API   ││Svc   ││shop  │
└──────┘└──────┘└──────┘
```

## Output

- Layered project structure separating concerns
- Error boundary with classification and retry logic
- Per-environment configuration with secret injection
- Health check covering IMS and all enabled APIs

## Resources

- [Adobe Developer Console](https://developer.adobe.com/console)
- [Firefly Services SDK](https://developer.adobe.com/firefly-services/docs/guides/sdks/)
- [PDF Services Node SDK](https://www.npmjs.com/package/@adobe/pdfservices-node-sdk)
- [App Builder Architecture](https://developer.adobe.com/app-builder/docs/guides/)

## Next Steps

For multi-environment setup, see `adobe-multi-env-setup`.

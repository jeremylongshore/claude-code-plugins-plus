---
name: shopify-reference-architecture
description: |
  Implement Shopify reference architecture with best-practice project layout.
  Use when designing new Shopify integrations, reviewing project structure,
  or establishing architecture standards for Shopify applications.
  Trigger with phrases like "shopify architecture", "shopify best practices",
  "shopify project structure", "how to organize shopify", "shopify layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, shopify]
---

# Shopify Reference Architecture

## Overview
Production-ready architecture patterns for Shopify integrations.

## Prerequisites
- Understanding of layered architecture
- Shopify SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-shopify-project/
├── src/
│   ├── shopify/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── shopify/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── shopify/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── shopify/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── shopify/
│   └── integration/
│       └── shopify/
├── config/
│   ├── shopify.development.json
│   ├── shopify.staging.json
│   └── shopify.production.json
└── docs/
    └── shopify/
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
│          Shopify Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/shopify/client.ts
export class ShopifyService {
  private client: ShopifyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ShopifyConfig) {
    this.client = new ShopifyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('shopify');
  }

  async get(id: string): Promise<Resource> {
    return this.cache.getOrFetch(id, () =>
      this.monitor.track('get', () => this.client.get(id))
    );
  }
}
```

### Step 2: Error Boundary
```typescript
// src/shopify/errors.ts
export class ShopifyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ShopifyServiceError';
  }
}

export function wrapShopifyError(error: unknown): ShopifyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/shopify/health.ts
export async function checkShopifyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await shopifyClient.ping();
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
    };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
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
│   Gateway   │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│   Service   │───▶│   Cache     │
│   Layer     │    │   (Redis)   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ Shopify    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Shopify    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/shopify.ts
export interface ShopifyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadShopifyConfig(): ShopifyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./shopify.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Shopify operations.

### Step 4: Configure Health Checks
Add health check endpoint for Shopify connectivity.

## Output
- Structured project layout
- Client wrapper with caching
- Error boundary implemented
- Health checks configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns by layer |
| Config not loading | Wrong paths | Verify config file locations |
| Type errors | Missing types | Add Shopify types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/shopify/{handlers} src/services/shopify src/api/shopify
touch src/shopify/{client,config,types,errors}.ts
touch src/services/shopify/{index,sync,cache}.ts
```

## Resources
- [Shopify SDK Documentation](https://docs.shopify.com/sdk)
- [Shopify Best Practices](https://docs.shopify.com/best-practices)

## Flagship Skills
For multi-environment setup, see `shopify-multi-env-setup`.
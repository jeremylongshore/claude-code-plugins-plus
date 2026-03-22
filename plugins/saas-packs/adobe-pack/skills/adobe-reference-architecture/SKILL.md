---
name: adobe-reference-architecture
description: |
  Implement Adobe reference architecture with best-practice project layout.
  Use when designing new Adobe integrations, reviewing project structure,
  or establishing architecture standards for Adobe applications.
  Trigger with phrases like "adobe architecture", "adobe best practices",
  "adobe project structure", "how to organize adobe", "adobe layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, adobe]
---

# Adobe Reference Architecture

## Overview
Production-ready architecture patterns for Adobe integrations.

## Prerequisites
- Understanding of layered architecture
- Adobe SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-adobe-project/
├── src/
│   ├── adobe/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── adobe/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── adobe/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── adobe/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── adobe/
│   └── integration/
│       └── adobe/
├── config/
│   ├── adobe.development.json
│   ├── adobe.staging.json
│   └── adobe.production.json
└── docs/
    └── adobe/
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
│          Adobe Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/adobe/client.ts
export class AdobeService {
  private client: AdobeClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AdobeConfig) {
    this.client = new AdobeClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('adobe');
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
// src/adobe/errors.ts
export class AdobeServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AdobeServiceError';
  }
}

export function wrapAdobeError(error: unknown): AdobeServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/adobe/health.ts
export async function checkAdobeHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await adobeClient.ping();
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
│ Adobe    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Adobe    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/adobe.ts
export interface AdobeConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAdobeConfig(): AdobeConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./adobe.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Adobe operations.

### Step 4: Configure Health Checks
Add health check endpoint for Adobe connectivity.

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
| Type errors | Missing types | Add Adobe types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/adobe/{handlers} src/services/adobe src/api/adobe
touch src/adobe/{client,config,types,errors}.ts
touch src/services/adobe/{index,sync,cache}.ts
```

## Resources
- [Adobe SDK Documentation](https://docs.adobe.com/sdk)
- [Adobe Best Practices](https://docs.adobe.com/best-practices)

## Flagship Skills
For multi-environment setup, see `adobe-multi-env-setup`.
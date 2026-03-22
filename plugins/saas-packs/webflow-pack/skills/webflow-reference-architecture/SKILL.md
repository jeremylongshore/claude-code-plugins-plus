---
name: webflow-reference-architecture
description: |
  Implement Webflow reference architecture with best-practice project layout.
  Use when designing new Webflow integrations, reviewing project structure,
  or establishing architecture standards for Webflow applications.
  Trigger with phrases like "webflow architecture", "webflow best practices",
  "webflow project structure", "how to organize webflow", "webflow layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, webflow]
---

# Webflow Reference Architecture

## Overview
Production-ready architecture patterns for Webflow integrations.

## Prerequisites
- Understanding of layered architecture
- Webflow SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-webflow-project/
├── src/
│   ├── webflow/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── webflow/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── webflow/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── webflow/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── webflow/
│   └── integration/
│       └── webflow/
├── config/
│   ├── webflow.development.json
│   ├── webflow.staging.json
│   └── webflow.production.json
└── docs/
    └── webflow/
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
│          Webflow Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/webflow/client.ts
export class WebflowService {
  private client: WebflowClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: WebflowConfig) {
    this.client = new WebflowClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('webflow');
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
// src/webflow/errors.ts
export class WebflowServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'WebflowServiceError';
  }
}

export function wrapWebflowError(error: unknown): WebflowServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/webflow/health.ts
export async function checkWebflowHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await webflowClient.ping();
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
│ Webflow    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Webflow    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/webflow.ts
export interface WebflowConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadWebflowConfig(): WebflowConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./webflow.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Webflow operations.

### Step 4: Configure Health Checks
Add health check endpoint for Webflow connectivity.

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
| Type errors | Missing types | Add Webflow types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/webflow/{handlers} src/services/webflow src/api/webflow
touch src/webflow/{client,config,types,errors}.ts
touch src/services/webflow/{index,sync,cache}.ts
```

## Resources
- [Webflow SDK Documentation](https://docs.webflow.com/sdk)
- [Webflow Best Practices](https://docs.webflow.com/best-practices)

## Flagship Skills
For multi-environment setup, see `webflow-multi-env-setup`.
---
name: flexport-reference-architecture
description: |
  Implement Flexport reference architecture with best-practice project layout.
  Use when designing new Flexport integrations, reviewing project structure,
  or establishing architecture standards for Flexport applications.
  Trigger with phrases like "flexport architecture", "flexport best practices",
  "flexport project structure", "how to organize flexport", "flexport layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flexport]
---

# Flexport Reference Architecture

## Overview
Production-ready architecture patterns for Flexport integrations.

## Prerequisites
- Understanding of layered architecture
- Flexport SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-flexport-project/
├── src/
│   ├── flexport/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── flexport/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── flexport/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── flexport/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── flexport/
│   └── integration/
│       └── flexport/
├── config/
│   ├── flexport.development.json
│   ├── flexport.staging.json
│   └── flexport.production.json
└── docs/
    └── flexport/
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
│          Flexport Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/flexport/client.ts
export class FlexportService {
  private client: FlexportClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FlexportConfig) {
    this.client = new FlexportClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('flexport');
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
// src/flexport/errors.ts
export class FlexportServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FlexportServiceError';
  }
}

export function wrapFlexportError(error: unknown): FlexportServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/flexport/health.ts
export async function checkFlexportHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await flexportClient.ping();
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
│ Flexport    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Flexport    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/flexport.ts
export interface FlexportConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFlexportConfig(): FlexportConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./flexport.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Flexport operations.

### Step 4: Configure Health Checks
Add health check endpoint for Flexport connectivity.

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
| Type errors | Missing types | Add Flexport types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/flexport/{handlers} src/services/flexport src/api/flexport
touch src/flexport/{client,config,types,errors}.ts
touch src/services/flexport/{index,sync,cache}.ts
```

## Resources
- [Flexport SDK Documentation](https://docs.flexport.com/sdk)
- [Flexport Best Practices](https://docs.flexport.com/best-practices)

## Flagship Skills
For multi-environment setup, see `flexport-multi-env-setup`.
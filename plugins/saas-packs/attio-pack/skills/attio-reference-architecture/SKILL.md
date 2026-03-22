---
name: attio-reference-architecture
description: |
  Implement Attio reference architecture with best-practice project layout.
  Use when designing new Attio integrations, reviewing project structure,
  or establishing architecture standards for Attio applications.
  Trigger with phrases like "attio architecture", "attio best practices",
  "attio project structure", "how to organize attio", "attio layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, attio]
---

# Attio Reference Architecture

## Overview
Production-ready architecture patterns for Attio integrations.

## Prerequisites
- Understanding of layered architecture
- Attio SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-attio-project/
├── src/
│   ├── attio/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── attio/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── attio/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── attio/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── attio/
│   └── integration/
│       └── attio/
├── config/
│   ├── attio.development.json
│   ├── attio.staging.json
│   └── attio.production.json
└── docs/
    └── attio/
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
│          Attio Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/attio/client.ts
export class AttioService {
  private client: AttioClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AttioConfig) {
    this.client = new AttioClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('attio');
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
// src/attio/errors.ts
export class AttioServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AttioServiceError';
  }
}

export function wrapAttioError(error: unknown): AttioServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/attio/health.ts
export async function checkAttioHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await attioClient.ping();
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
│ Attio    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Attio    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/attio.ts
export interface AttioConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAttioConfig(): AttioConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./attio.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Attio operations.

### Step 4: Configure Health Checks
Add health check endpoint for Attio connectivity.

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
| Type errors | Missing types | Add Attio types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/attio/{handlers} src/services/attio src/api/attio
touch src/attio/{client,config,types,errors}.ts
touch src/services/attio/{index,sync,cache}.ts
```

## Resources
- [Attio SDK Documentation](https://docs.attio.com/sdk)
- [Attio Best Practices](https://docs.attio.com/best-practices)

## Flagship Skills
For multi-environment setup, see `attio-multi-env-setup`.
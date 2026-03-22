---
name: abridge-reference-architecture
description: |
  Implement Abridge reference architecture with best-practice project layout.
  Use when designing new Abridge integrations, reviewing project structure,
  or establishing architecture standards for Abridge applications.
  Trigger with phrases like "abridge architecture", "abridge best practices",
  "abridge project structure", "how to organize abridge", "abridge layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, abridge]
---

# Abridge Reference Architecture

## Overview
Production-ready architecture patterns for Abridge integrations.

## Prerequisites
- Understanding of layered architecture
- Abridge SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-abridge-project/
├── src/
│   ├── abridge/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── abridge/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── abridge/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── abridge/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── abridge/
│   └── integration/
│       └── abridge/
├── config/
│   ├── abridge.development.json
│   ├── abridge.staging.json
│   └── abridge.production.json
└── docs/
    └── abridge/
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
│          Abridge Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/abridge/client.ts
export class AbridgeService {
  private client: AbridgeClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AbridgeConfig) {
    this.client = new AbridgeClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('abridge');
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
// src/abridge/errors.ts
export class AbridgeServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AbridgeServiceError';
  }
}

export function wrapAbridgeError(error: unknown): AbridgeServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/abridge/health.ts
export async function checkAbridgeHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await abridgeClient.ping();
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
│ Abridge    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Abridge    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/abridge.ts
export interface AbridgeConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAbridgeConfig(): AbridgeConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./abridge.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Abridge operations.

### Step 4: Configure Health Checks
Add health check endpoint for Abridge connectivity.

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
| Type errors | Missing types | Add Abridge types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/abridge/{handlers} src/services/abridge src/api/abridge
touch src/abridge/{client,config,types,errors}.ts
touch src/services/abridge/{index,sync,cache}.ts
```

## Resources
- [Abridge SDK Documentation](https://docs.abridge.com/sdk)
- [Abridge Best Practices](https://docs.abridge.com/best-practices)

## Flagship Skills
For multi-environment setup, see `abridge-multi-env-setup`.
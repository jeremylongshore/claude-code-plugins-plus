---
name: guidewire-reference-architecture
description: |
  Implement Guidewire reference architecture with best-practice project layout.
  Use when designing new Guidewire integrations, reviewing project structure,
  or establishing architecture standards for Guidewire applications.
  Trigger with phrases like "guidewire architecture", "guidewire best practices",
  "guidewire project structure", "how to organize guidewire", "guidewire layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, guidewire]
---

# Guidewire Reference Architecture

## Overview
Production-ready architecture patterns for Guidewire integrations.

## Prerequisites
- Understanding of layered architecture
- Guidewire SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-guidewire-project/
├── src/
│   ├── guidewire/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── guidewire/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── guidewire/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── guidewire/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── guidewire/
│   └── integration/
│       └── guidewire/
├── config/
│   ├── guidewire.development.json
│   ├── guidewire.staging.json
│   └── guidewire.production.json
└── docs/
    └── guidewire/
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
│          Guidewire Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/guidewire/client.ts
export class GuidewireService {
  private client: GuidewireClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GuidewireConfig) {
    this.client = new GuidewireClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('guidewire');
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
// src/guidewire/errors.ts
export class GuidewireServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GuidewireServiceError';
  }
}

export function wrapGuidewireError(error: unknown): GuidewireServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/guidewire/health.ts
export async function checkGuidewireHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await guidewireClient.ping();
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
│ Guidewire    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Guidewire    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/guidewire.ts
export interface GuidewireConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGuidewireConfig(): GuidewireConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./guidewire.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Guidewire operations.

### Step 4: Configure Health Checks
Add health check endpoint for Guidewire connectivity.

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
| Type errors | Missing types | Add Guidewire types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/guidewire/{handlers} src/services/guidewire src/api/guidewire
touch src/guidewire/{client,config,types,errors}.ts
touch src/services/guidewire/{index,sync,cache}.ts
```

## Resources
- [Guidewire SDK Documentation](https://docs.guidewire.com/sdk)
- [Guidewire Best Practices](https://docs.guidewire.com/best-practices)

## Flagship Skills
For multi-environment setup, see `guidewire-multi-env-setup`.
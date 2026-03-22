---
name: grammarly-reference-architecture
description: |
  Implement Grammarly reference architecture with best-practice project layout.
  Use when designing new Grammarly integrations, reviewing project structure,
  or establishing architecture standards for Grammarly applications.
  Trigger with phrases like "grammarly architecture", "grammarly best practices",
  "grammarly project structure", "how to organize grammarly", "grammarly layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, grammarly]
---

# Grammarly Reference Architecture

## Overview
Production-ready architecture patterns for Grammarly integrations.

## Prerequisites
- Understanding of layered architecture
- Grammarly SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-grammarly-project/
├── src/
│   ├── grammarly/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── grammarly/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── grammarly/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── grammarly/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── grammarly/
│   └── integration/
│       └── grammarly/
├── config/
│   ├── grammarly.development.json
│   ├── grammarly.staging.json
│   └── grammarly.production.json
└── docs/
    └── grammarly/
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
│          Grammarly Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/grammarly/client.ts
export class GrammarlyService {
  private client: GrammarlyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GrammarlyConfig) {
    this.client = new GrammarlyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('grammarly');
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
// src/grammarly/errors.ts
export class GrammarlyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GrammarlyServiceError';
  }
}

export function wrapGrammarlyError(error: unknown): GrammarlyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/grammarly/health.ts
export async function checkGrammarlyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await grammarlyClient.ping();
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
│ Grammarly    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Grammarly    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/grammarly.ts
export interface GrammarlyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGrammarlyConfig(): GrammarlyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./grammarly.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Grammarly operations.

### Step 4: Configure Health Checks
Add health check endpoint for Grammarly connectivity.

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
| Type errors | Missing types | Add Grammarly types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/grammarly/{handlers} src/services/grammarly src/api/grammarly
touch src/grammarly/{client,config,types,errors}.ts
touch src/services/grammarly/{index,sync,cache}.ts
```

## Resources
- [Grammarly SDK Documentation](https://docs.grammarly.com/sdk)
- [Grammarly Best Practices](https://docs.grammarly.com/best-practices)

## Flagship Skills
For multi-environment setup, see `grammarly-multi-env-setup`.
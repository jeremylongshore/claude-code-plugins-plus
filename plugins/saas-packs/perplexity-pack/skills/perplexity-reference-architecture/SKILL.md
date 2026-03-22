---
name: perplexity-reference-architecture
description: |
  Implement Perplexity reference architecture with best-practice project layout.
  Use when designing new Perplexity integrations, reviewing project structure,
  or establishing architecture standards for Perplexity applications.
  Trigger with phrases like "perplexity architecture", "perplexity best practices",
  "perplexity project structure", "how to organize perplexity", "perplexity layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, perplexity]
---

# Perplexity Reference Architecture

## Overview
Production-ready architecture patterns for Perplexity integrations.

## Prerequisites
- Understanding of layered architecture
- Perplexity SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-perplexity-project/
├── src/
│   ├── perplexity/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── perplexity/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── perplexity/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── perplexity/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── perplexity/
│   └── integration/
│       └── perplexity/
├── config/
│   ├── perplexity.development.json
│   ├── perplexity.staging.json
│   └── perplexity.production.json
└── docs/
    └── perplexity/
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
│          Perplexity Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/perplexity/client.ts
export class PerplexityService {
  private client: PerplexityClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: PerplexityConfig) {
    this.client = new PerplexityClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('perplexity');
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
// src/perplexity/errors.ts
export class PerplexityServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'PerplexityServiceError';
  }
}

export function wrapPerplexityError(error: unknown): PerplexityServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/perplexity/health.ts
export async function checkPerplexityHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await perplexityClient.ping();
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
│ Perplexity    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Perplexity    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/perplexity.ts
export interface PerplexityConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadPerplexityConfig(): PerplexityConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./perplexity.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Perplexity operations.

### Step 4: Configure Health Checks
Add health check endpoint for Perplexity connectivity.

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
| Type errors | Missing types | Add Perplexity types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/perplexity/{handlers} src/services/perplexity src/api/perplexity
touch src/perplexity/{client,config,types,errors}.ts
touch src/services/perplexity/{index,sync,cache}.ts
```

## Resources
- [Perplexity SDK Documentation](https://docs.perplexity.com/sdk)
- [Perplexity Best Practices](https://docs.perplexity.com/best-practices)

## Flagship Skills
For multi-environment setup, see `perplexity-multi-env-setup`.
---
name: vastai-reference-architecture
description: |
  Implement Vast.ai reference architecture with best-practice project layout.
  Use when designing new Vast.ai integrations, reviewing project structure,
  or establishing architecture standards for Vast.ai applications.
  Trigger with phrases like "vastai architecture", "vastai best practices",
  "vastai project structure", "how to organize vastai", "vastai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, vastai]
---

# Vast.ai Reference Architecture

## Overview
Production-ready architecture patterns for Vast.ai integrations.

## Prerequisites
- Understanding of layered architecture
- Vast.ai SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-vastai-project/
├── src/
│   ├── vastai/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── vastai/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── vastai/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── vastai/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── vastai/
│   └── integration/
│       └── vastai/
├── config/
│   ├── vastai.development.json
│   ├── vastai.staging.json
│   └── vastai.production.json
└── docs/
    └── vastai/
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
│          Vast.ai Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/vastai/client.ts
export class Vast.aiService {
  private client: Vast.aiClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Vast.aiConfig) {
    this.client = new Vast.aiClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('vastai');
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
// src/vastai/errors.ts
export class Vast.aiServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Vast.aiServiceError';
  }
}

export function wrapVast.aiError(error: unknown): Vast.aiServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/vastai/health.ts
export async function checkVast.aiHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await vastaiClient.ping();
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
│ Vast.ai    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Vast.ai    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/vastai.ts
export interface Vast.aiConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadVast.aiConfig(): Vast.aiConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./vastai.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Vast.ai operations.

### Step 4: Configure Health Checks
Add health check endpoint for Vast.ai connectivity.

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
| Type errors | Missing types | Add Vast.ai types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/vastai/{handlers} src/services/vastai src/api/vastai
touch src/vastai/{client,config,types,errors}.ts
touch src/services/vastai/{index,sync,cache}.ts
```

## Resources
- [Vast.ai SDK Documentation](https://docs.vastai.com/sdk)
- [Vast.ai Best Practices](https://docs.vastai.com/best-practices)

## Flagship Skills
For multi-environment setup, see `vastai-multi-env-setup`.
---
name: framer-reference-architecture
description: |
  Implement Framer reference architecture with best-practice project layout.
  Use when designing new Framer integrations, reviewing project structure,
  or establishing architecture standards for Framer applications.
  Trigger with phrases like "framer architecture", "framer best practices",
  "framer project structure", "how to organize framer", "framer layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Reference Architecture

## Overview
Production-ready architecture patterns for Framer integrations.

## Prerequisites
- Understanding of layered architecture
- Framer SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-framer-project/
├── src/
│   ├── framer/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── framer/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── framer/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── framer/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── framer/
│   └── integration/
│       └── framer/
├── config/
│   ├── framer.development.json
│   ├── framer.staging.json
│   └── framer.production.json
└── docs/
    └── framer/
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
│          Framer Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/framer/client.ts
export class FramerService {
  private client: FramerClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FramerConfig) {
    this.client = new FramerClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('framer');
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
// src/framer/errors.ts
export class FramerServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FramerServiceError';
  }
}

export function wrapFramerError(error: unknown): FramerServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/framer/health.ts
export async function checkFramerHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await framerClient.ping();
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
│ Framer    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Framer    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/framer.ts
export interface FramerConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFramerConfig(): FramerConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./framer.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Framer operations.

### Step 4: Configure Health Checks
Add health check endpoint for Framer connectivity.

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
| Type errors | Missing types | Add Framer types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/framer/{handlers} src/services/framer src/api/framer
touch src/framer/{client,config,types,errors}.ts
touch src/services/framer/{index,sync,cache}.ts
```

## Resources
- [Framer SDK Documentation](https://docs.framer.com/sdk)
- [Framer Best Practices](https://docs.framer.com/best-practices)

## Flagship Skills
For multi-environment setup, see `framer-multi-env-setup`.
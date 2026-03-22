---
name: runway-reference-architecture
description: |
  Implement Runway reference architecture with best-practice project layout.
  Use when designing new Runway integrations, reviewing project structure,
  or establishing architecture standards for Runway applications.
  Trigger with phrases like "runway architecture", "runway best practices",
  "runway project structure", "how to organize runway", "runway layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, runway]
---

# Runway Reference Architecture

## Overview
Production-ready architecture patterns for Runway integrations.

## Prerequisites
- Understanding of layered architecture
- Runway SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-runway-project/
├── src/
│   ├── runway/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── runway/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── runway/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── runway/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── runway/
│   └── integration/
│       └── runway/
├── config/
│   ├── runway.development.json
│   ├── runway.staging.json
│   └── runway.production.json
└── docs/
    └── runway/
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
│          Runway Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/runway/client.ts
export class RunwayService {
  private client: RunwayClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: RunwayConfig) {
    this.client = new RunwayClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('runway');
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
// src/runway/errors.ts
export class RunwayServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'RunwayServiceError';
  }
}

export function wrapRunwayError(error: unknown): RunwayServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/runway/health.ts
export async function checkRunwayHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await runwayClient.ping();
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
│ Runway    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Runway    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/runway.ts
export interface RunwayConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadRunwayConfig(): RunwayConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./runway.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Runway operations.

### Step 4: Configure Health Checks
Add health check endpoint for Runway connectivity.

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
| Type errors | Missing types | Add Runway types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/runway/{handlers} src/services/runway src/api/runway
touch src/runway/{client,config,types,errors}.ts
touch src/services/runway/{index,sync,cache}.ts
```

## Resources
- [Runway SDK Documentation](https://docs.runway.com/sdk)
- [Runway Best Practices](https://docs.runway.com/best-practices)

## Flagship Skills
For multi-environment setup, see `runway-multi-env-setup`.
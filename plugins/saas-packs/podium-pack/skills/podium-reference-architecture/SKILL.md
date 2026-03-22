---
name: podium-reference-architecture
description: |
  Implement Podium reference architecture with best-practice project layout.
  Use when designing new Podium integrations, reviewing project structure,
  or establishing architecture standards for Podium applications.
  Trigger with phrases like "podium architecture", "podium best practices",
  "podium project structure", "how to organize podium", "podium layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, podium]
---

# Podium Reference Architecture

## Overview
Production-ready architecture patterns for Podium integrations.

## Prerequisites
- Understanding of layered architecture
- Podium SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-podium-project/
├── src/
│   ├── podium/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── podium/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── podium/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── podium/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── podium/
│   └── integration/
│       └── podium/
├── config/
│   ├── podium.development.json
│   ├── podium.staging.json
│   └── podium.production.json
└── docs/
    └── podium/
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
│          Podium Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/podium/client.ts
export class PodiumService {
  private client: PodiumClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: PodiumConfig) {
    this.client = new PodiumClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('podium');
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
// src/podium/errors.ts
export class PodiumServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'PodiumServiceError';
  }
}

export function wrapPodiumError(error: unknown): PodiumServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/podium/health.ts
export async function checkPodiumHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await podiumClient.ping();
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
│ Podium    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Podium    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/podium.ts
export interface PodiumConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadPodiumConfig(): PodiumConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./podium.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Podium operations.

### Step 4: Configure Health Checks
Add health check endpoint for Podium connectivity.

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
| Type errors | Missing types | Add Podium types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/podium/{handlers} src/services/podium src/api/podium
touch src/podium/{client,config,types,errors}.ts
touch src/services/podium/{index,sync,cache}.ts
```

## Resources
- [Podium SDK Documentation](https://docs.podium.com/sdk)
- [Podium Best Practices](https://docs.podium.com/best-practices)

## Flagship Skills
For multi-environment setup, see `podium-multi-env-setup`.
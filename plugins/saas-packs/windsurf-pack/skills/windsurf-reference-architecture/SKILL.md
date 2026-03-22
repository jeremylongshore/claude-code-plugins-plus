---
name: windsurf-reference-architecture
description: |
  Implement Windsurf reference architecture with best-practice project layout.
  Use when designing new Windsurf integrations, reviewing project structure,
  or establishing architecture standards for Windsurf applications.
  Trigger with phrases like "windsurf architecture", "windsurf best practices",
  "windsurf project structure", "how to organize windsurf", "windsurf layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, windsurf]
---

# Windsurf Reference Architecture

## Overview
Production-ready architecture patterns for Windsurf integrations.

## Prerequisites
- Understanding of layered architecture
- Windsurf SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-windsurf-project/
├── src/
│   ├── windsurf/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── windsurf/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── windsurf/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── windsurf/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── windsurf/
│   └── integration/
│       └── windsurf/
├── config/
│   ├── windsurf.development.json
│   ├── windsurf.staging.json
│   └── windsurf.production.json
└── docs/
    └── windsurf/
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
│          Windsurf Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/windsurf/client.ts
export class WindsurfService {
  private client: WindsurfClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: WindsurfConfig) {
    this.client = new WindsurfClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('windsurf');
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
// src/windsurf/errors.ts
export class WindsurfServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'WindsurfServiceError';
  }
}

export function wrapWindsurfError(error: unknown): WindsurfServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/windsurf/health.ts
export async function checkWindsurfHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await windsurfClient.ping();
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
│ Windsurf    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Windsurf    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/windsurf.ts
export interface WindsurfConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadWindsurfConfig(): WindsurfConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./windsurf.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Windsurf operations.

### Step 4: Configure Health Checks
Add health check endpoint for Windsurf connectivity.

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
| Type errors | Missing types | Add Windsurf types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/windsurf/{handlers} src/services/windsurf src/api/windsurf
touch src/windsurf/{client,config,types,errors}.ts
touch src/services/windsurf/{index,sync,cache}.ts
```

## Resources
- [Windsurf SDK Documentation](https://docs.windsurf.com/sdk)
- [Windsurf Best Practices](https://docs.windsurf.com/best-practices)

## Flagship Skills
For multi-environment setup, see `windsurf-multi-env-setup`.
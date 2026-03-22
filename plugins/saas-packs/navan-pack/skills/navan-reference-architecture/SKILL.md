---
name: navan-reference-architecture
description: |
  Implement Navan reference architecture with best-practice project layout.
  Use when designing new Navan integrations, reviewing project structure,
  or establishing architecture standards for Navan applications.
  Trigger with phrases like "navan architecture", "navan best practices",
  "navan project structure", "how to organize navan", "navan layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, navan]
---

# Navan Reference Architecture

## Overview
Production-ready architecture patterns for Navan integrations.

## Prerequisites
- Understanding of layered architecture
- Navan SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-navan-project/
├── src/
│   ├── navan/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── navan/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── navan/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── navan/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── navan/
│   └── integration/
│       └── navan/
├── config/
│   ├── navan.development.json
│   ├── navan.staging.json
│   └── navan.production.json
└── docs/
    └── navan/
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
│          Navan Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/navan/client.ts
export class NavanService {
  private client: NavanClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: NavanConfig) {
    this.client = new NavanClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('navan');
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
// src/navan/errors.ts
export class NavanServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'NavanServiceError';
  }
}

export function wrapNavanError(error: unknown): NavanServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/navan/health.ts
export async function checkNavanHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await navanClient.ping();
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
│ Navan    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Navan    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/navan.ts
export interface NavanConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadNavanConfig(): NavanConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./navan.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Navan operations.

### Step 4: Configure Health Checks
Add health check endpoint for Navan connectivity.

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
| Type errors | Missing types | Add Navan types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/navan/{handlers} src/services/navan src/api/navan
touch src/navan/{client,config,types,errors}.ts
touch src/services/navan/{index,sync,cache}.ts
```

## Resources
- [Navan SDK Documentation](https://docs.navan.com/sdk)
- [Navan Best Practices](https://docs.navan.com/best-practices)

## Flagship Skills
For multi-environment setup, see `navan-multi-env-setup`.
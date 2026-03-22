---
name: serpapi-reference-architecture
description: |
  Implement SerpApi reference architecture with best-practice project layout.
  Use when designing new SerpApi integrations, reviewing project structure,
  or establishing architecture standards for SerpApi applications.
  Trigger with phrases like "serpapi architecture", "serpapi best practices",
  "serpapi project structure", "how to organize serpapi", "serpapi layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi Reference Architecture

## Overview
Production-ready architecture patterns for SerpApi integrations.

## Prerequisites
- Understanding of layered architecture
- SerpApi SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-serpapi-project/
├── src/
│   ├── serpapi/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── serpapi/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── serpapi/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── serpapi/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── serpapi/
│   └── integration/
│       └── serpapi/
├── config/
│   ├── serpapi.development.json
│   ├── serpapi.staging.json
│   └── serpapi.production.json
└── docs/
    └── serpapi/
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
│          SerpApi Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/serpapi/client.ts
export class SerpApiService {
  private client: SerpApiClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SerpApiConfig) {
    this.client = new SerpApiClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('serpapi');
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
// src/serpapi/errors.ts
export class SerpApiServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SerpApiServiceError';
  }
}

export function wrapSerpApiError(error: unknown): SerpApiServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/serpapi/health.ts
export async function checkSerpApiHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await serpapiClient.ping();
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
│ SerpApi    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ SerpApi    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/serpapi.ts
export interface SerpApiConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSerpApiConfig(): SerpApiConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./serpapi.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for SerpApi operations.

### Step 4: Configure Health Checks
Add health check endpoint for SerpApi connectivity.

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
| Type errors | Missing types | Add SerpApi types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/serpapi/{handlers} src/services/serpapi src/api/serpapi
touch src/serpapi/{client,config,types,errors}.ts
touch src/services/serpapi/{index,sync,cache}.ts
```

## Resources
- [SerpApi SDK Documentation](https://docs.serpapi.com/sdk)
- [SerpApi Best Practices](https://docs.serpapi.com/best-practices)

## Flagship Skills
For multi-environment setup, see `serpapi-multi-env-setup`.
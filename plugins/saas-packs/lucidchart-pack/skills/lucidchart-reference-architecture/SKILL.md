---
name: lucidchart-reference-architecture
description: |
  Implement Lucidchart reference architecture with best-practice project layout.
  Use when designing new Lucidchart integrations, reviewing project structure,
  or establishing architecture standards for Lucidchart applications.
  Trigger with phrases like "lucidchart architecture", "lucidchart best practices",
  "lucidchart project structure", "how to organize lucidchart", "lucidchart layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart Reference Architecture

## Overview
Production-ready architecture patterns for Lucidchart integrations.

## Prerequisites
- Understanding of layered architecture
- Lucidchart SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-lucidchart-project/
├── src/
│   ├── lucidchart/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── lucidchart/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── lucidchart/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── lucidchart/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── lucidchart/
│   └── integration/
│       └── lucidchart/
├── config/
│   ├── lucidchart.development.json
│   ├── lucidchart.staging.json
│   └── lucidchart.production.json
└── docs/
    └── lucidchart/
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
│          Lucidchart Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/lucidchart/client.ts
export class LucidchartService {
  private client: LucidchartClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LucidchartConfig) {
    this.client = new LucidchartClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('lucidchart');
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
// src/lucidchart/errors.ts
export class LucidchartServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LucidchartServiceError';
  }
}

export function wrapLucidchartError(error: unknown): LucidchartServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/lucidchart/health.ts
export async function checkLucidchartHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await lucidchartClient.ping();
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
│ Lucidchart    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Lucidchart    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/lucidchart.ts
export interface LucidchartConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLucidchartConfig(): LucidchartConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./lucidchart.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Lucidchart operations.

### Step 4: Configure Health Checks
Add health check endpoint for Lucidchart connectivity.

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
| Type errors | Missing types | Add Lucidchart types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/lucidchart/{handlers} src/services/lucidchart src/api/lucidchart
touch src/lucidchart/{client,config,types,errors}.ts
touch src/services/lucidchart/{index,sync,cache}.ts
```

## Resources
- [Lucidchart SDK Documentation](https://docs.lucidchart.com/sdk)
- [Lucidchart Best Practices](https://docs.lucidchart.com/best-practices)

## Flagship Skills
For multi-environment setup, see `lucidchart-multi-env-setup`.
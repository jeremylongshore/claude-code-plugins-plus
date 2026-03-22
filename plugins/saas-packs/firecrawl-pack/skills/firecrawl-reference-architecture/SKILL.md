---
name: firecrawl-reference-architecture
description: |
  Implement FireCrawl reference architecture with best-practice project layout.
  Use when designing new FireCrawl integrations, reviewing project structure,
  or establishing architecture standards for FireCrawl applications.
  Trigger with phrases like "firecrawl architecture", "firecrawl best practices",
  "firecrawl project structure", "how to organize firecrawl", "firecrawl layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, firecrawl]
---

# FireCrawl Reference Architecture

## Overview
Production-ready architecture patterns for FireCrawl integrations.

## Prerequisites
- Understanding of layered architecture
- FireCrawl SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-firecrawl-project/
├── src/
│   ├── firecrawl/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── firecrawl/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── firecrawl/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── firecrawl/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── firecrawl/
│   └── integration/
│       └── firecrawl/
├── config/
│   ├── firecrawl.development.json
│   ├── firecrawl.staging.json
│   └── firecrawl.production.json
└── docs/
    └── firecrawl/
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
│          FireCrawl Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/firecrawl/client.ts
export class FireCrawlService {
  private client: FireCrawlClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FireCrawlConfig) {
    this.client = new FireCrawlClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('firecrawl');
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
// src/firecrawl/errors.ts
export class FireCrawlServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FireCrawlServiceError';
  }
}

export function wrapFireCrawlError(error: unknown): FireCrawlServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/firecrawl/health.ts
export async function checkFireCrawlHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await firecrawlClient.ping();
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
│ FireCrawl    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ FireCrawl    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/firecrawl.ts
export interface FireCrawlConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFireCrawlConfig(): FireCrawlConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./firecrawl.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for FireCrawl operations.

### Step 4: Configure Health Checks
Add health check endpoint for FireCrawl connectivity.

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
| Type errors | Missing types | Add FireCrawl types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/firecrawl/{handlers} src/services/firecrawl src/api/firecrawl
touch src/firecrawl/{client,config,types,errors}.ts
touch src/services/firecrawl/{index,sync,cache}.ts
```

## Resources
- [FireCrawl SDK Documentation](https://docs.firecrawl.com/sdk)
- [FireCrawl Best Practices](https://docs.firecrawl.com/best-practices)

## Flagship Skills
For multi-environment setup, see `firecrawl-multi-env-setup`.
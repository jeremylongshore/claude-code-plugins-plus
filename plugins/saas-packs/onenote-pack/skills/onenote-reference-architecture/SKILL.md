---
name: onenote-reference-architecture
description: |
  Implement OneNote reference architecture with best-practice project layout.
  Use when designing new OneNote integrations, reviewing project structure,
  or establishing architecture standards for OneNote applications.
  Trigger with phrases like "onenote architecture", "onenote best practices",
  "onenote project structure", "how to organize onenote", "onenote layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Reference Architecture

## Overview
Production-ready architecture patterns for OneNote integrations.

## Prerequisites
- Understanding of layered architecture
- OneNote SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-onenote-project/
├── src/
│   ├── onenote/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── onenote/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── onenote/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── onenote/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── onenote/
│   └── integration/
│       └── onenote/
├── config/
│   ├── onenote.development.json
│   ├── onenote.staging.json
│   └── onenote.production.json
└── docs/
    └── onenote/
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
│          OneNote Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/onenote/client.ts
export class OneNoteService {
  private client: OneNoteClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: OneNoteConfig) {
    this.client = new OneNoteClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('onenote');
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
// src/onenote/errors.ts
export class OneNoteServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'OneNoteServiceError';
  }
}

export function wrapOneNoteError(error: unknown): OneNoteServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/onenote/health.ts
export async function checkOneNoteHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await onenoteClient.ping();
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
│ OneNote    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ OneNote    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/onenote.ts
export interface OneNoteConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadOneNoteConfig(): OneNoteConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./onenote.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for OneNote operations.

### Step 4: Configure Health Checks
Add health check endpoint for OneNote connectivity.

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
| Type errors | Missing types | Add OneNote types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/onenote/{handlers} src/services/onenote src/api/onenote
touch src/onenote/{client,config,types,errors}.ts
touch src/services/onenote/{index,sync,cache}.ts
```

## Resources
- [OneNote SDK Documentation](https://docs.onenote.com/sdk)
- [OneNote Best Practices](https://docs.onenote.com/best-practices)

## Flagship Skills
For multi-environment setup, see `onenote-multi-env-setup`.
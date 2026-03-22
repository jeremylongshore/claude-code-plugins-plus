---
name: evernote-reference-architecture
description: |
  Implement Evernote reference architecture with best-practice project layout.
  Use when designing new Evernote integrations, reviewing project structure,
  or establishing architecture standards for Evernote applications.
  Trigger with phrases like "evernote architecture", "evernote best practices",
  "evernote project structure", "how to organize evernote", "evernote layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, evernote]
---

# Evernote Reference Architecture

## Overview
Production-ready architecture patterns for Evernote integrations.

## Prerequisites
- Understanding of layered architecture
- Evernote SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-evernote-project/
├── src/
│   ├── evernote/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── evernote/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── evernote/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── evernote/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── evernote/
│   └── integration/
│       └── evernote/
├── config/
│   ├── evernote.development.json
│   ├── evernote.staging.json
│   └── evernote.production.json
└── docs/
    └── evernote/
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
│          Evernote Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/evernote/client.ts
export class EvernoteService {
  private client: EvernoteClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: EvernoteConfig) {
    this.client = new EvernoteClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('evernote');
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
// src/evernote/errors.ts
export class EvernoteServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'EvernoteServiceError';
  }
}

export function wrapEvernoteError(error: unknown): EvernoteServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/evernote/health.ts
export async function checkEvernoteHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await evernoteClient.ping();
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
│ Evernote    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Evernote    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/evernote.ts
export interface EvernoteConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadEvernoteConfig(): EvernoteConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./evernote.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Evernote operations.

### Step 4: Configure Health Checks
Add health check endpoint for Evernote connectivity.

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
| Type errors | Missing types | Add Evernote types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/evernote/{handlers} src/services/evernote src/api/evernote
touch src/evernote/{client,config,types,errors}.ts
touch src/services/evernote/{index,sync,cache}.ts
```

## Resources
- [Evernote SDK Documentation](https://docs.evernote.com/sdk)
- [Evernote Best Practices](https://docs.evernote.com/best-practices)

## Flagship Skills
For multi-environment setup, see `evernote-multi-env-setup`.
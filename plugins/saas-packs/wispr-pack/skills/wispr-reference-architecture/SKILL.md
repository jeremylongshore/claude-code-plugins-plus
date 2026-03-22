---
name: wispr-reference-architecture
description: |
  Implement Wispr reference architecture with best-practice project layout.
  Use when designing new Wispr integrations, reviewing project structure,
  or establishing architecture standards for Wispr applications.
  Trigger with phrases like "wispr architecture", "wispr best practices",
  "wispr project structure", "how to organize wispr", "wispr layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr Reference Architecture

## Overview
Production-ready architecture patterns for Wispr integrations.

## Prerequisites
- Understanding of layered architecture
- Wispr SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-wispr-project/
├── src/
│   ├── wispr/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── wispr/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── wispr/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── wispr/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── wispr/
│   └── integration/
│       └── wispr/
├── config/
│   ├── wispr.development.json
│   ├── wispr.staging.json
│   └── wispr.production.json
└── docs/
    └── wispr/
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
│          Wispr Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/wispr/client.ts
export class WisprService {
  private client: WisprClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: WisprConfig) {
    this.client = new WisprClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('wispr');
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
// src/wispr/errors.ts
export class WisprServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'WisprServiceError';
  }
}

export function wrapWisprError(error: unknown): WisprServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/wispr/health.ts
export async function checkWisprHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await wisprClient.ping();
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
│ Wispr    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Wispr    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/wispr.ts
export interface WisprConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadWisprConfig(): WisprConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./wispr.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Wispr operations.

### Step 4: Configure Health Checks
Add health check endpoint for Wispr connectivity.

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
| Type errors | Missing types | Add Wispr types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/wispr/{handlers} src/services/wispr src/api/wispr
touch src/wispr/{client,config,types,errors}.ts
touch src/services/wispr/{index,sync,cache}.ts
```

## Resources
- [Wispr SDK Documentation](https://docs.wispr.com/sdk)
- [Wispr Best Practices](https://docs.wispr.com/best-practices)

## Flagship Skills
For multi-environment setup, see `wispr-multi-env-setup`.
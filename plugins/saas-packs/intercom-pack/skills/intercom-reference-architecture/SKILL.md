---
name: intercom-reference-architecture
description: |
  Implement Intercom reference architecture with best-practice project layout.
  Use when designing new Intercom integrations, reviewing project structure,
  or establishing architecture standards for Intercom applications.
  Trigger with phrases like "intercom architecture", "intercom best practices",
  "intercom project structure", "how to organize intercom", "intercom layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Reference Architecture

## Overview
Production-ready architecture patterns for Intercom integrations.

## Prerequisites
- Understanding of layered architecture
- Intercom SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-intercom-project/
├── src/
│   ├── intercom/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── intercom/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── intercom/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── intercom/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── intercom/
│   └── integration/
│       └── intercom/
├── config/
│   ├── intercom.development.json
│   ├── intercom.staging.json
│   └── intercom.production.json
└── docs/
    └── intercom/
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
│          Intercom Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/intercom/client.ts
export class IntercomService {
  private client: IntercomClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: IntercomConfig) {
    this.client = new IntercomClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('intercom');
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
// src/intercom/errors.ts
export class IntercomServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'IntercomServiceError';
  }
}

export function wrapIntercomError(error: unknown): IntercomServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/intercom/health.ts
export async function checkIntercomHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await intercomClient.ping();
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
│ Intercom    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Intercom    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/intercom.ts
export interface IntercomConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadIntercomConfig(): IntercomConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./intercom.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Intercom operations.

### Step 4: Configure Health Checks
Add health check endpoint for Intercom connectivity.

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
| Type errors | Missing types | Add Intercom types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/intercom/{handlers} src/services/intercom src/api/intercom
touch src/intercom/{client,config,types,errors}.ts
touch src/services/intercom/{index,sync,cache}.ts
```

## Resources
- [Intercom SDK Documentation](https://docs.intercom.com/sdk)
- [Intercom Best Practices](https://docs.intercom.com/best-practices)

## Flagship Skills
For multi-environment setup, see `intercom-multi-env-setup`.
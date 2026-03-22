---
name: exa-reference-architecture
description: |
  Implement Exa reference architecture with best-practice project layout.
  Use when designing new Exa integrations, reviewing project structure,
  or establishing architecture standards for Exa applications.
  Trigger with phrases like "exa architecture", "exa best practices",
  "exa project structure", "how to organize exa", "exa layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, exa]
---

# Exa Reference Architecture

## Overview
Production-ready architecture patterns for Exa integrations.

## Prerequisites
- Understanding of layered architecture
- Exa SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-exa-project/
├── src/
│   ├── exa/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── exa/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── exa/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── exa/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── exa/
│   └── integration/
│       └── exa/
├── config/
│   ├── exa.development.json
│   ├── exa.staging.json
│   └── exa.production.json
└── docs/
    └── exa/
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
│          Exa Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/exa/client.ts
export class ExaService {
  private client: ExaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ExaConfig) {
    this.client = new ExaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('exa');
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
// src/exa/errors.ts
export class ExaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ExaServiceError';
  }
}

export function wrapExaError(error: unknown): ExaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/exa/health.ts
export async function checkExaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await exaClient.ping();
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
│ Exa    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Exa    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/exa.ts
export interface ExaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadExaConfig(): ExaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./exa.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Exa operations.

### Step 4: Configure Health Checks
Add health check endpoint for Exa connectivity.

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
| Type errors | Missing types | Add Exa types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/exa/{handlers} src/services/exa src/api/exa
touch src/exa/{client,config,types,errors}.ts
touch src/services/exa/{index,sync,cache}.ts
```

## Resources
- [Exa SDK Documentation](https://docs.exa.com/sdk)
- [Exa Best Practices](https://docs.exa.com/best-practices)

## Flagship Skills
For multi-environment setup, see `exa-multi-env-setup`.
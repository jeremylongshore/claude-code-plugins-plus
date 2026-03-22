---
name: lokalise-reference-architecture
description: |
  Implement Lokalise reference architecture with best-practice project layout.
  Use when designing new Lokalise integrations, reviewing project structure,
  or establishing architecture standards for Lokalise applications.
  Trigger with phrases like "lokalise architecture", "lokalise best practices",
  "lokalise project structure", "how to organize lokalise", "lokalise layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lokalise]
---

# Lokalise Reference Architecture

## Overview
Production-ready architecture patterns for Lokalise integrations.

## Prerequisites
- Understanding of layered architecture
- Lokalise SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-lokalise-project/
├── src/
│   ├── lokalise/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── lokalise/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── lokalise/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── lokalise/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── lokalise/
│   └── integration/
│       └── lokalise/
├── config/
│   ├── lokalise.development.json
│   ├── lokalise.staging.json
│   └── lokalise.production.json
└── docs/
    └── lokalise/
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
│          Lokalise Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/lokalise/client.ts
export class LokaliseService {
  private client: LokaliseClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LokaliseConfig) {
    this.client = new LokaliseClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('lokalise');
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
// src/lokalise/errors.ts
export class LokaliseServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LokaliseServiceError';
  }
}

export function wrapLokaliseError(error: unknown): LokaliseServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/lokalise/health.ts
export async function checkLokaliseHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await lokaliseClient.ping();
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
│ Lokalise    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Lokalise    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/lokalise.ts
export interface LokaliseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLokaliseConfig(): LokaliseConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./lokalise.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Lokalise operations.

### Step 4: Configure Health Checks
Add health check endpoint for Lokalise connectivity.

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
| Type errors | Missing types | Add Lokalise types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/lokalise/{handlers} src/services/lokalise src/api/lokalise
touch src/lokalise/{client,config,types,errors}.ts
touch src/services/lokalise/{index,sync,cache}.ts
```

## Resources
- [Lokalise SDK Documentation](https://docs.lokalise.com/sdk)
- [Lokalise Best Practices](https://docs.lokalise.com/best-practices)

## Flagship Skills
For multi-environment setup, see `lokalise-multi-env-setup`.
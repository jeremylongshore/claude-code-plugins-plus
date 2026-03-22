---
name: techsmith-reference-architecture
description: |
  Implement TechSmith reference architecture with best-practice project layout.
  Use when designing new TechSmith integrations, reviewing project structure,
  or establishing architecture standards for TechSmith applications.
  Trigger with phrases like "techsmith architecture", "techsmith best practices",
  "techsmith project structure", "how to organize techsmith", "techsmith layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, techsmith]
---

# TechSmith Reference Architecture

## Overview
Production-ready architecture patterns for TechSmith integrations.

## Prerequisites
- Understanding of layered architecture
- TechSmith SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-techsmith-project/
├── src/
│   ├── techsmith/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── techsmith/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── techsmith/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── techsmith/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── techsmith/
│   └── integration/
│       └── techsmith/
├── config/
│   ├── techsmith.development.json
│   ├── techsmith.staging.json
│   └── techsmith.production.json
└── docs/
    └── techsmith/
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
│          TechSmith Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/techsmith/client.ts
export class TechSmithService {
  private client: TechSmithClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: TechSmithConfig) {
    this.client = new TechSmithClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('techsmith');
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
// src/techsmith/errors.ts
export class TechSmithServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'TechSmithServiceError';
  }
}

export function wrapTechSmithError(error: unknown): TechSmithServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/techsmith/health.ts
export async function checkTechSmithHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await techsmithClient.ping();
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
│ TechSmith    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ TechSmith    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/techsmith.ts
export interface TechSmithConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadTechSmithConfig(): TechSmithConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./techsmith.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for TechSmith operations.

### Step 4: Configure Health Checks
Add health check endpoint for TechSmith connectivity.

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
| Type errors | Missing types | Add TechSmith types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/techsmith/{handlers} src/services/techsmith src/api/techsmith
touch src/techsmith/{client,config,types,errors}.ts
touch src/services/techsmith/{index,sync,cache}.ts
```

## Resources
- [TechSmith SDK Documentation](https://docs.techsmith.com/sdk)
- [TechSmith Best Practices](https://docs.techsmith.com/best-practices)

## Flagship Skills
For multi-environment setup, see `techsmith-multi-env-setup`.
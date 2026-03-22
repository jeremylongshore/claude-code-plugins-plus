---
name: obsidian-reference-architecture
description: |
  Implement Obsidian reference architecture with best-practice project layout.
  Use when designing new Obsidian integrations, reviewing project structure,
  or establishing architecture standards for Obsidian applications.
  Trigger with phrases like "obsidian architecture", "obsidian best practices",
  "obsidian project structure", "how to organize obsidian", "obsidian layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, obsidian]
---

# Obsidian Reference Architecture

## Overview
Production-ready architecture patterns for Obsidian integrations.

## Prerequisites
- Understanding of layered architecture
- Obsidian SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-obsidian-project/
├── src/
│   ├── obsidian/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── obsidian/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── obsidian/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── obsidian/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── obsidian/
│   └── integration/
│       └── obsidian/
├── config/
│   ├── obsidian.development.json
│   ├── obsidian.staging.json
│   └── obsidian.production.json
└── docs/
    └── obsidian/
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
│          Obsidian Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/obsidian/client.ts
export class ObsidianService {
  private client: ObsidianClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ObsidianConfig) {
    this.client = new ObsidianClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('obsidian');
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
// src/obsidian/errors.ts
export class ObsidianServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ObsidianServiceError';
  }
}

export function wrapObsidianError(error: unknown): ObsidianServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/obsidian/health.ts
export async function checkObsidianHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await obsidianClient.ping();
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
│ Obsidian    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Obsidian    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/obsidian.ts
export interface ObsidianConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadObsidianConfig(): ObsidianConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./obsidian.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Obsidian operations.

### Step 4: Configure Health Checks
Add health check endpoint for Obsidian connectivity.

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
| Type errors | Missing types | Add Obsidian types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/obsidian/{handlers} src/services/obsidian src/api/obsidian
touch src/obsidian/{client,config,types,errors}.ts
touch src/services/obsidian/{index,sync,cache}.ts
```

## Resources
- [Obsidian SDK Documentation](https://docs.obsidian.com/sdk)
- [Obsidian Best Practices](https://docs.obsidian.com/best-practices)

## Flagship Skills
For multi-environment setup, see `obsidian-multi-env-setup`.
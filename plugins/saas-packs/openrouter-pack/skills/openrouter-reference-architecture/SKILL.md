---
name: openrouter-reference-architecture
description: |
  Implement OpenRouter reference architecture with best-practice project layout.
  Use when designing new OpenRouter integrations, reviewing project structure,
  or establishing architecture standards for OpenRouter applications.
  Trigger with phrases like "openrouter architecture", "openrouter best practices",
  "openrouter project structure", "how to organize openrouter", "openrouter layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter Reference Architecture

## Overview
Production-ready architecture patterns for OpenRouter integrations.

## Prerequisites
- Understanding of layered architecture
- OpenRouter SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-openrouter-project/
├── src/
│   ├── openrouter/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── openrouter/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── openrouter/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── openrouter/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── openrouter/
│   └── integration/
│       └── openrouter/
├── config/
│   ├── openrouter.development.json
│   ├── openrouter.staging.json
│   └── openrouter.production.json
└── docs/
    └── openrouter/
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
│          OpenRouter Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/openrouter/client.ts
export class OpenRouterService {
  private client: OpenRouterClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: OpenRouterConfig) {
    this.client = new OpenRouterClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('openrouter');
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
// src/openrouter/errors.ts
export class OpenRouterServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'OpenRouterServiceError';
  }
}

export function wrapOpenRouterError(error: unknown): OpenRouterServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/openrouter/health.ts
export async function checkOpenRouterHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await openrouterClient.ping();
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
│ OpenRouter    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ OpenRouter    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/openrouter.ts
export interface OpenRouterConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadOpenRouterConfig(): OpenRouterConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./openrouter.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for OpenRouter operations.

### Step 4: Configure Health Checks
Add health check endpoint for OpenRouter connectivity.

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
| Type errors | Missing types | Add OpenRouter types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/openrouter/{handlers} src/services/openrouter src/api/openrouter
touch src/openrouter/{client,config,types,errors}.ts
touch src/services/openrouter/{index,sync,cache}.ts
```

## Resources
- [OpenRouter SDK Documentation](https://docs.openrouter.com/sdk)
- [OpenRouter Best Practices](https://docs.openrouter.com/best-practices)

## Flagship Skills
For multi-environment setup, see `openrouter-multi-env-setup`.
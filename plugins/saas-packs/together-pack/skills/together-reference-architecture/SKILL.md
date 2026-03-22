---
name: together-reference-architecture
description: |
  Implement Together AI reference architecture with best-practice project layout.
  Use when designing new Together AI integrations, reviewing project structure,
  or establishing architecture standards for Together AI applications.
  Trigger with phrases like "together architecture", "together best practices",
  "together project structure", "how to organize together", "together layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, together]
---

# Together AI Reference Architecture

## Overview
Production-ready architecture patterns for Together AI integrations.

## Prerequisites
- Understanding of layered architecture
- Together AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-together-project/
├── src/
│   ├── together/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── together/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── together/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── together/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── together/
│   └── integration/
│       └── together/
├── config/
│   ├── together.development.json
│   ├── together.staging.json
│   └── together.production.json
└── docs/
    └── together/
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
│          Together AI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/together/client.ts
export class Together AIService {
  private client: TogetherAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Together AIConfig) {
    this.client = new TogetherAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('together');
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
// src/together/errors.ts
export class Together AIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Together AIServiceError';
  }
}

export function wrapTogether AIError(error: unknown): Together AIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/together/health.ts
export async function checkTogether AIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await togetherClient.ping();
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
│ Together AI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Together AI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/together.ts
export interface Together AIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadTogether AIConfig(): Together AIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./together.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Together AI operations.

### Step 4: Configure Health Checks
Add health check endpoint for Together AI connectivity.

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
| Type errors | Missing types | Add Together AI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/together/{handlers} src/services/together src/api/together
touch src/together/{client,config,types,errors}.ts
touch src/services/together/{index,sync,cache}.ts
```

## Resources
- [Together AI SDK Documentation](https://docs.together.com/sdk)
- [Together AI Best Practices](https://docs.together.com/best-practices)

## Flagship Skills
For multi-environment setup, see `together-multi-env-setup`.
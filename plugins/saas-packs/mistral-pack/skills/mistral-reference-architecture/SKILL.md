---
name: mistral-reference-architecture
description: |
  Implement Mistral AI reference architecture with best-practice project layout.
  Use when designing new Mistral AI integrations, reviewing project structure,
  or establishing architecture standards for Mistral AI applications.
  Trigger with phrases like "mistral architecture", "mistral best practices",
  "mistral project structure", "how to organize mistral", "mistral layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mistral]
---

# Mistral AI Reference Architecture

## Overview
Production-ready architecture patterns for Mistral AI integrations.

## Prerequisites
- Understanding of layered architecture
- Mistral AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-mistral-project/
├── src/
│   ├── mistral/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── mistral/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── mistral/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── mistral/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── mistral/
│   └── integration/
│       └── mistral/
├── config/
│   ├── mistral.development.json
│   ├── mistral.staging.json
│   └── mistral.production.json
└── docs/
    └── mistral/
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
│          Mistral AI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/mistral/client.ts
export class Mistral AIService {
  private client: MistralAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Mistral AIConfig) {
    this.client = new MistralAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('mistral');
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
// src/mistral/errors.ts
export class Mistral AIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Mistral AIServiceError';
  }
}

export function wrapMistral AIError(error: unknown): Mistral AIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/mistral/health.ts
export async function checkMistral AIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await mistralClient.ping();
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
│ Mistral AI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Mistral AI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/mistral.ts
export interface Mistral AIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadMistral AIConfig(): Mistral AIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./mistral.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Mistral AI operations.

### Step 4: Configure Health Checks
Add health check endpoint for Mistral AI connectivity.

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
| Type errors | Missing types | Add Mistral AI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/mistral/{handlers} src/services/mistral src/api/mistral
touch src/mistral/{client,config,types,errors}.ts
touch src/services/mistral/{index,sync,cache}.ts
```

## Resources
- [Mistral AI SDK Documentation](https://docs.mistral.com/sdk)
- [Mistral AI Best Practices](https://docs.mistral.com/best-practices)

## Flagship Skills
For multi-environment setup, see `mistral-multi-env-setup`.
---
name: castai-reference-architecture
description: |
  Implement Cast AI reference architecture with best-practice project layout.
  Use when designing new Cast AI integrations, reviewing project structure,
  or establishing architecture standards for Cast AI applications.
  Trigger with phrases like "castai architecture", "castai best practices",
  "castai project structure", "how to organize castai", "castai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI Reference Architecture

## Overview
Production-ready architecture patterns for Cast AI integrations.

## Prerequisites
- Understanding of layered architecture
- Cast AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-castai-project/
├── src/
│   ├── castai/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── castai/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── castai/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── castai/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── castai/
│   └── integration/
│       └── castai/
├── config/
│   ├── castai.development.json
│   ├── castai.staging.json
│   └── castai.production.json
└── docs/
    └── castai/
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
│          Cast AI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/castai/client.ts
export class Cast AIService {
  private client: CastAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Cast AIConfig) {
    this.client = new CastAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('castai');
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
// src/castai/errors.ts
export class Cast AIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Cast AIServiceError';
  }
}

export function wrapCast AIError(error: unknown): Cast AIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/castai/health.ts
export async function checkCast AIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await castaiClient.ping();
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
│ Cast AI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cast AI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/castai.ts
export interface Cast AIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCast AIConfig(): Cast AIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./castai.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Cast AI operations.

### Step 4: Configure Health Checks
Add health check endpoint for Cast AI connectivity.

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
| Type errors | Missing types | Add Cast AI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/castai/{handlers} src/services/castai src/api/castai
touch src/castai/{client,config,types,errors}.ts
touch src/services/castai/{index,sync,cache}.ts
```

## Resources
- [Cast AI SDK Documentation](https://docs.castai.com/sdk)
- [Cast AI Best Practices](https://docs.castai.com/best-practices)

## Flagship Skills
For multi-environment setup, see `castai-multi-env-setup`.
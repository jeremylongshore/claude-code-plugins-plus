---
name: klingai-reference-architecture
description: |
  Implement Kling AI reference architecture with best-practice project layout.
  Use when designing new Kling AI integrations, reviewing project structure,
  or establishing architecture standards for Kling AI applications.
  Trigger with phrases like "klingai architecture", "klingai best practices",
  "klingai project structure", "how to organize klingai", "klingai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Reference Architecture

## Overview
Production-ready architecture patterns for Kling AI integrations.

## Prerequisites
- Understanding of layered architecture
- Kling AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-klingai-project/
├── src/
│   ├── klingai/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── klingai/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── klingai/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── klingai/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── klingai/
│   └── integration/
│       └── klingai/
├── config/
│   ├── klingai.development.json
│   ├── klingai.staging.json
│   └── klingai.production.json
└── docs/
    └── klingai/
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
│          Kling AI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/klingai/client.ts
export class Kling AIService {
  private client: KlingAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Kling AIConfig) {
    this.client = new KlingAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('klingai');
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
// src/klingai/errors.ts
export class Kling AIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Kling AIServiceError';
  }
}

export function wrapKling AIError(error: unknown): Kling AIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/klingai/health.ts
export async function checkKling AIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await klingaiClient.ping();
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
│ Kling AI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Kling AI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/klingai.ts
export interface Kling AIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadKling AIConfig(): Kling AIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./klingai.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Kling AI operations.

### Step 4: Configure Health Checks
Add health check endpoint for Kling AI connectivity.

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
| Type errors | Missing types | Add Kling AI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/klingai/{handlers} src/services/klingai src/api/klingai
touch src/klingai/{client,config,types,errors}.ts
touch src/services/klingai/{index,sync,cache}.ts
```

## Resources
- [Kling AI SDK Documentation](https://docs.klingai.com/sdk)
- [Kling AI Best Practices](https://docs.klingai.com/best-practices)

## Flagship Skills
For multi-environment setup, see `klingai-multi-env-setup`.
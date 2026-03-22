---
name: coderabbit-reference-architecture
description: |
  Implement CodeRabbit reference architecture with best-practice project layout.
  Use when designing new CodeRabbit integrations, reviewing project structure,
  or establishing architecture standards for CodeRabbit applications.
  Trigger with phrases like "coderabbit architecture", "coderabbit best practices",
  "coderabbit project structure", "how to organize coderabbit", "coderabbit layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coderabbit]
---

# CodeRabbit Reference Architecture

## Overview
Production-ready architecture patterns for CodeRabbit integrations.

## Prerequisites
- Understanding of layered architecture
- CodeRabbit SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-coderabbit-project/
├── src/
│   ├── coderabbit/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── coderabbit/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── coderabbit/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── coderabbit/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── coderabbit/
│   └── integration/
│       └── coderabbit/
├── config/
│   ├── coderabbit.development.json
│   ├── coderabbit.staging.json
│   └── coderabbit.production.json
└── docs/
    └── coderabbit/
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
│          CodeRabbit Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/coderabbit/client.ts
export class CodeRabbitService {
  private client: CodeRabbitClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: CodeRabbitConfig) {
    this.client = new CodeRabbitClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('coderabbit');
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
// src/coderabbit/errors.ts
export class CodeRabbitServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CodeRabbitServiceError';
  }
}

export function wrapCodeRabbitError(error: unknown): CodeRabbitServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/coderabbit/health.ts
export async function checkCodeRabbitHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await coderabbitClient.ping();
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
│ CodeRabbit    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CodeRabbit    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/coderabbit.ts
export interface CodeRabbitConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCodeRabbitConfig(): CodeRabbitConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./coderabbit.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for CodeRabbit operations.

### Step 4: Configure Health Checks
Add health check endpoint for CodeRabbit connectivity.

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
| Type errors | Missing types | Add CodeRabbit types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/coderabbit/{handlers} src/services/coderabbit src/api/coderabbit
touch src/coderabbit/{client,config,types,errors}.ts
touch src/services/coderabbit/{index,sync,cache}.ts
```

## Resources
- [CodeRabbit SDK Documentation](https://docs.coderabbit.com/sdk)
- [CodeRabbit Best Practices](https://docs.coderabbit.com/best-practices)

## Flagship Skills
For multi-environment setup, see `coderabbit-multi-env-setup`.
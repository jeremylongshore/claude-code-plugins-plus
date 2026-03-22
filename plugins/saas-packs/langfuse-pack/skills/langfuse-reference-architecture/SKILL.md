---
name: langfuse-reference-architecture
description: |
  Implement Langfuse reference architecture with best-practice project layout.
  Use when designing new Langfuse integrations, reviewing project structure,
  or establishing architecture standards for Langfuse applications.
  Trigger with phrases like "langfuse architecture", "langfuse best practices",
  "langfuse project structure", "how to organize langfuse", "langfuse layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langfuse]
---

# Langfuse Reference Architecture

## Overview
Production-ready architecture patterns for Langfuse integrations.

## Prerequisites
- Understanding of layered architecture
- Langfuse SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-langfuse-project/
├── src/
│   ├── langfuse/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── langfuse/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── langfuse/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── langfuse/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── langfuse/
│   └── integration/
│       └── langfuse/
├── config/
│   ├── langfuse.development.json
│   ├── langfuse.staging.json
│   └── langfuse.production.json
└── docs/
    └── langfuse/
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
│          Langfuse Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/langfuse/client.ts
export class LangfuseService {
  private client: LangfuseClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LangfuseConfig) {
    this.client = new LangfuseClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('langfuse');
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
// src/langfuse/errors.ts
export class LangfuseServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LangfuseServiceError';
  }
}

export function wrapLangfuseError(error: unknown): LangfuseServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/langfuse/health.ts
export async function checkLangfuseHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await langfuseClient.ping();
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
│ Langfuse    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Langfuse    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/langfuse.ts
export interface LangfuseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLangfuseConfig(): LangfuseConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./langfuse.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Langfuse operations.

### Step 4: Configure Health Checks
Add health check endpoint for Langfuse connectivity.

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
| Type errors | Missing types | Add Langfuse types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/langfuse/{handlers} src/services/langfuse src/api/langfuse
touch src/langfuse/{client,config,types,errors}.ts
touch src/services/langfuse/{index,sync,cache}.ts
```

## Resources
- [Langfuse SDK Documentation](https://docs.langfuse.com/sdk)
- [Langfuse Best Practices](https://docs.langfuse.com/best-practices)

## Flagship Skills
For multi-environment setup, see `langfuse-multi-env-setup`.
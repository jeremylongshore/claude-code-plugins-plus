---
name: retellai-reference-architecture
description: |
  Implement Retell AI reference architecture with best-practice project layout.
  Use when designing new Retell AI integrations, reviewing project structure,
  or establishing architecture standards for Retell AI applications.
  Trigger with phrases like "retellai architecture", "retellai best practices",
  "retellai project structure", "how to organize retellai", "retellai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, retellai]
---

# Retell AI Reference Architecture

## Overview
Production-ready architecture patterns for Retell AI integrations.

## Prerequisites
- Understanding of layered architecture
- Retell AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-retellai-project/
├── src/
│   ├── retellai/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── retellai/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── retellai/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── retellai/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── retellai/
│   └── integration/
│       └── retellai/
├── config/
│   ├── retellai.development.json
│   ├── retellai.staging.json
│   └── retellai.production.json
└── docs/
    └── retellai/
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
│          Retell AI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/retellai/client.ts
export class Retell AIService {
  private client: RetellAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Retell AIConfig) {
    this.client = new RetellAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('retellai');
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
// src/retellai/errors.ts
export class Retell AIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Retell AIServiceError';
  }
}

export function wrapRetell AIError(error: unknown): Retell AIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/retellai/health.ts
export async function checkRetell AIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await retellaiClient.ping();
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
│ Retell AI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Retell AI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/retellai.ts
export interface Retell AIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadRetell AIConfig(): Retell AIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./retellai.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Retell AI operations.

### Step 4: Configure Health Checks
Add health check endpoint for Retell AI connectivity.

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
| Type errors | Missing types | Add Retell AI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/retellai/{handlers} src/services/retellai src/api/retellai
touch src/retellai/{client,config,types,errors}.ts
touch src/services/retellai/{index,sync,cache}.ts
```

## Resources
- [Retell AI SDK Documentation](https://docs.retellai.com/sdk)
- [Retell AI Best Practices](https://docs.retellai.com/best-practices)

## Flagship Skills
For multi-environment setup, see `retellai-multi-env-setup`.
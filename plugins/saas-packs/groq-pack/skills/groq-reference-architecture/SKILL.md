---
name: groq-reference-architecture
description: |
  Implement Groq reference architecture with best-practice project layout.
  Use when designing new Groq integrations, reviewing project structure,
  or establishing architecture standards for Groq applications.
  Trigger with phrases like "groq architecture", "groq best practices",
  "groq project structure", "how to organize groq", "groq layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, groq]
---

# Groq Reference Architecture

## Overview
Production-ready architecture patterns for Groq integrations.

## Prerequisites
- Understanding of layered architecture
- Groq SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-groq-project/
├── src/
│   ├── groq/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── groq/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── groq/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── groq/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── groq/
│   └── integration/
│       └── groq/
├── config/
│   ├── groq.development.json
│   ├── groq.staging.json
│   └── groq.production.json
└── docs/
    └── groq/
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
│          Groq Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/groq/client.ts
export class GroqService {
  private client: GroqClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GroqConfig) {
    this.client = new GroqClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('groq');
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
// src/groq/errors.ts
export class GroqServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GroqServiceError';
  }
}

export function wrapGroqError(error: unknown): GroqServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/groq/health.ts
export async function checkGroqHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await groqClient.ping();
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
│ Groq    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Groq    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/groq.ts
export interface GroqConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGroqConfig(): GroqConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./groq.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Groq operations.

### Step 4: Configure Health Checks
Add health check endpoint for Groq connectivity.

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
| Type errors | Missing types | Add Groq types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/groq/{handlers} src/services/groq src/api/groq
touch src/groq/{client,config,types,errors}.ts
touch src/services/groq/{index,sync,cache}.ts
```

## Resources
- [Groq SDK Documentation](https://docs.groq.com/sdk)
- [Groq Best Practices](https://docs.groq.com/best-practices)

## Flagship Skills
For multi-environment setup, see `groq-multi-env-setup`.
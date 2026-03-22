---
name: juicebox-reference-architecture
description: |
  Implement Juicebox reference architecture with best-practice project layout.
  Use when designing new Juicebox integrations, reviewing project structure,
  or establishing architecture standards for Juicebox applications.
  Trigger with phrases like "juicebox architecture", "juicebox best practices",
  "juicebox project structure", "how to organize juicebox", "juicebox layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Reference Architecture

## Overview
Production-ready architecture patterns for Juicebox integrations.

## Prerequisites
- Understanding of layered architecture
- Juicebox SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-juicebox-project/
├── src/
│   ├── juicebox/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── juicebox/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── juicebox/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── juicebox/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── juicebox/
│   └── integration/
│       └── juicebox/
├── config/
│   ├── juicebox.development.json
│   ├── juicebox.staging.json
│   └── juicebox.production.json
└── docs/
    └── juicebox/
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
│          Juicebox Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/juicebox/client.ts
export class JuiceboxService {
  private client: JuiceboxClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: JuiceboxConfig) {
    this.client = new JuiceboxClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('juicebox');
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
// src/juicebox/errors.ts
export class JuiceboxServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'JuiceboxServiceError';
  }
}

export function wrapJuiceboxError(error: unknown): JuiceboxServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/juicebox/health.ts
export async function checkJuiceboxHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await juiceboxClient.ping();
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
│ Juicebox    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Juicebox    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/juicebox.ts
export interface JuiceboxConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadJuiceboxConfig(): JuiceboxConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./juicebox.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Juicebox operations.

### Step 4: Configure Health Checks
Add health check endpoint for Juicebox connectivity.

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
| Type errors | Missing types | Add Juicebox types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/juicebox/{handlers} src/services/juicebox src/api/juicebox
touch src/juicebox/{client,config,types,errors}.ts
touch src/services/juicebox/{index,sync,cache}.ts
```

## Resources
- [Juicebox SDK Documentation](https://docs.juicebox.com/sdk)
- [Juicebox Best Practices](https://docs.juicebox.com/best-practices)

## Flagship Skills
For multi-environment setup, see `juicebox-multi-env-setup`.
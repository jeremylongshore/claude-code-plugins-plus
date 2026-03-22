---
name: apollo-reference-architecture
description: |
  Implement Apollo reference architecture with best-practice project layout.
  Use when designing new Apollo integrations, reviewing project structure,
  or establishing architecture standards for Apollo applications.
  Trigger with phrases like "apollo architecture", "apollo best practices",
  "apollo project structure", "how to organize apollo", "apollo layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo Reference Architecture

## Overview
Production-ready architecture patterns for Apollo integrations.

## Prerequisites
- Understanding of layered architecture
- Apollo SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-apollo-project/
├── src/
│   ├── apollo/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── apollo/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── apollo/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── apollo/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── apollo/
│   └── integration/
│       └── apollo/
├── config/
│   ├── apollo.development.json
│   ├── apollo.staging.json
│   └── apollo.production.json
└── docs/
    └── apollo/
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
│          Apollo Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/apollo/client.ts
export class ApolloService {
  private client: ApolloClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ApolloConfig) {
    this.client = new ApolloClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('apollo');
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
// src/apollo/errors.ts
export class ApolloServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ApolloServiceError';
  }
}

export function wrapApolloError(error: unknown): ApolloServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/apollo/health.ts
export async function checkApolloHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await apolloClient.ping();
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
│ Apollo    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Apollo    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/apollo.ts
export interface ApolloConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadApolloConfig(): ApolloConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./apollo.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Apollo operations.

### Step 4: Configure Health Checks
Add health check endpoint for Apollo connectivity.

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
| Type errors | Missing types | Add Apollo types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/apollo/{handlers} src/services/apollo src/api/apollo
touch src/apollo/{client,config,types,errors}.ts
touch src/services/apollo/{index,sync,cache}.ts
```

## Resources
- [Apollo SDK Documentation](https://docs.apollo.com/sdk)
- [Apollo Best Practices](https://docs.apollo.com/best-practices)

## Flagship Skills
For multi-environment setup, see `apollo-multi-env-setup`.
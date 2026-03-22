---
name: clerk-reference-architecture
description: |
  Implement Clerk reference architecture with best-practice project layout.
  Use when designing new Clerk integrations, reviewing project structure,
  or establishing architecture standards for Clerk applications.
  Trigger with phrases like "clerk architecture", "clerk best practices",
  "clerk project structure", "how to organize clerk", "clerk layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk Reference Architecture

## Overview
Production-ready architecture patterns for Clerk integrations.

## Prerequisites
- Understanding of layered architecture
- Clerk SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-clerk-project/
├── src/
│   ├── clerk/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── clerk/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── clerk/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── clerk/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── clerk/
│   └── integration/
│       └── clerk/
├── config/
│   ├── clerk.development.json
│   ├── clerk.staging.json
│   └── clerk.production.json
└── docs/
    └── clerk/
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
│          Clerk Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/clerk/client.ts
export class ClerkService {
  private client: ClerkClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ClerkConfig) {
    this.client = new ClerkClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('clerk');
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
// src/clerk/errors.ts
export class ClerkServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ClerkServiceError';
  }
}

export function wrapClerkError(error: unknown): ClerkServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/clerk/health.ts
export async function checkClerkHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await clerkClient.ping();
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
│ Clerk    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Clerk    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/clerk.ts
export interface ClerkConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadClerkConfig(): ClerkConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./clerk.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Clerk operations.

### Step 4: Configure Health Checks
Add health check endpoint for Clerk connectivity.

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
| Type errors | Missing types | Add Clerk types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/clerk/{handlers} src/services/clerk src/api/clerk
touch src/clerk/{client,config,types,errors}.ts
touch src/services/clerk/{index,sync,cache}.ts
```

## Resources
- [Clerk SDK Documentation](https://docs.clerk.com/sdk)
- [Clerk Best Practices](https://docs.clerk.com/best-practices)

## Flagship Skills
For multi-environment setup, see `clerk-multi-env-setup`.
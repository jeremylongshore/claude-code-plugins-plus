---
name: ideogram-reference-architecture
description: |
  Implement Ideogram reference architecture with best-practice project layout.
  Use when designing new Ideogram integrations, reviewing project structure,
  or establishing architecture standards for Ideogram applications.
  Trigger with phrases like "ideogram architecture", "ideogram best practices",
  "ideogram project structure", "how to organize ideogram", "ideogram layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ideogram]
---

# Ideogram Reference Architecture

## Overview
Production-ready architecture patterns for Ideogram integrations.

## Prerequisites
- Understanding of layered architecture
- Ideogram SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-ideogram-project/
├── src/
│   ├── ideogram/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── ideogram/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── ideogram/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── ideogram/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── ideogram/
│   └── integration/
│       └── ideogram/
├── config/
│   ├── ideogram.development.json
│   ├── ideogram.staging.json
│   └── ideogram.production.json
└── docs/
    └── ideogram/
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
│          Ideogram Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/ideogram/client.ts
export class IdeogramService {
  private client: IdeogramClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: IdeogramConfig) {
    this.client = new IdeogramClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('ideogram');
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
// src/ideogram/errors.ts
export class IdeogramServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'IdeogramServiceError';
  }
}

export function wrapIdeogramError(error: unknown): IdeogramServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/ideogram/health.ts
export async function checkIdeogramHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await ideogramClient.ping();
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
│ Ideogram    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Ideogram    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/ideogram.ts
export interface IdeogramConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadIdeogramConfig(): IdeogramConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./ideogram.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Ideogram operations.

### Step 4: Configure Health Checks
Add health check endpoint for Ideogram connectivity.

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
| Type errors | Missing types | Add Ideogram types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/ideogram/{handlers} src/services/ideogram src/api/ideogram
touch src/ideogram/{client,config,types,errors}.ts
touch src/services/ideogram/{index,sync,cache}.ts
```

## Resources
- [Ideogram SDK Documentation](https://docs.ideogram.com/sdk)
- [Ideogram Best Practices](https://docs.ideogram.com/best-practices)

## Flagship Skills
For multi-environment setup, see `ideogram-multi-env-setup`.
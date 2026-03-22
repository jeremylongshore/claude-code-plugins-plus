---
name: bamboohr-reference-architecture
description: |
  Implement BambooHR reference architecture with best-practice project layout.
  Use when designing new BambooHR integrations, reviewing project structure,
  or establishing architecture standards for BambooHR applications.
  Trigger with phrases like "bamboohr architecture", "bamboohr best practices",
  "bamboohr project structure", "how to organize bamboohr", "bamboohr layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, bamboohr]
---

# BambooHR Reference Architecture

## Overview
Production-ready architecture patterns for BambooHR integrations.

## Prerequisites
- Understanding of layered architecture
- BambooHR SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-bamboohr-project/
├── src/
│   ├── bamboohr/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── bamboohr/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── bamboohr/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── bamboohr/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── bamboohr/
│   └── integration/
│       └── bamboohr/
├── config/
│   ├── bamboohr.development.json
│   ├── bamboohr.staging.json
│   └── bamboohr.production.json
└── docs/
    └── bamboohr/
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
│          BambooHR Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/bamboohr/client.ts
export class BambooHRService {
  private client: BambooHRClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: BambooHRConfig) {
    this.client = new BambooHRClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('bamboohr');
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
// src/bamboohr/errors.ts
export class BambooHRServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'BambooHRServiceError';
  }
}

export function wrapBambooHRError(error: unknown): BambooHRServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/bamboohr/health.ts
export async function checkBambooHRHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await bamboohrClient.ping();
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
│ BambooHR    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ BambooHR    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/bamboohr.ts
export interface BambooHRConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadBambooHRConfig(): BambooHRConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./bamboohr.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for BambooHR operations.

### Step 4: Configure Health Checks
Add health check endpoint for BambooHR connectivity.

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
| Type errors | Missing types | Add BambooHR types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/bamboohr/{handlers} src/services/bamboohr src/api/bamboohr
touch src/bamboohr/{client,config,types,errors}.ts
touch src/services/bamboohr/{index,sync,cache}.ts
```

## Resources
- [BambooHR SDK Documentation](https://docs.bamboohr.com/sdk)
- [BambooHR Best Practices](https://docs.bamboohr.com/best-practices)

## Flagship Skills
For multi-environment setup, see `bamboohr-multi-env-setup`.
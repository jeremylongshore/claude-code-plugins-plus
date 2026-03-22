---
name: customerio-reference-architecture
description: |
  Implement Customer.io reference architecture with best-practice project layout.
  Use when designing new Customer.io integrations, reviewing project structure,
  or establishing architecture standards for Customer.io applications.
  Trigger with phrases like "customerio architecture", "customerio best practices",
  "customerio project structure", "how to organize customerio", "customerio layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Reference Architecture

## Overview
Production-ready architecture patterns for Customer.io integrations.

## Prerequisites
- Understanding of layered architecture
- Customer.io SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-customerio-project/
├── src/
│   ├── customerio/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── customerio/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── customerio/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── customerio/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── customerio/
│   └── integration/
│       └── customerio/
├── config/
│   ├── customerio.development.json
│   ├── customerio.staging.json
│   └── customerio.production.json
└── docs/
    └── customerio/
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
│          Customer.io Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/customerio/client.ts
export class Customer.ioService {
  private client: Customer.ioClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Customer.ioConfig) {
    this.client = new Customer.ioClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('customerio');
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
// src/customerio/errors.ts
export class Customer.ioServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Customer.ioServiceError';
  }
}

export function wrapCustomer.ioError(error: unknown): Customer.ioServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/customerio/health.ts
export async function checkCustomer.ioHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await customerioClient.ping();
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
│ Customer.io    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Customer.io    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/customerio.ts
export interface Customer.ioConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCustomer.ioConfig(): Customer.ioConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./customerio.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Customer.io operations.

### Step 4: Configure Health Checks
Add health check endpoint for Customer.io connectivity.

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
| Type errors | Missing types | Add Customer.io types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/customerio/{handlers} src/services/customerio src/api/customerio
touch src/customerio/{client,config,types,errors}.ts
touch src/services/customerio/{index,sync,cache}.ts
```

## Resources
- [Customer.io SDK Documentation](https://docs.customerio.com/sdk)
- [Customer.io Best Practices](https://docs.customerio.com/best-practices)

## Flagship Skills
For multi-environment setup, see `customerio-multi-env-setup`.
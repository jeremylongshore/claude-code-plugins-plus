---
name: salesforce-reference-architecture
description: |
  Implement Salesforce reference architecture with best-practice project layout.
  Use when designing new Salesforce integrations, reviewing project structure,
  or establishing architecture standards for Salesforce applications.
  Trigger with phrases like "salesforce architecture", "salesforce best practices",
  "salesforce project structure", "how to organize salesforce", "salesforce layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Reference Architecture

## Overview
Production-ready architecture patterns for Salesforce integrations.

## Prerequisites
- Understanding of layered architecture
- Salesforce SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-salesforce-project/
├── src/
│   ├── salesforce/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── salesforce/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── salesforce/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── salesforce/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── salesforce/
│   └── integration/
│       └── salesforce/
├── config/
│   ├── salesforce.development.json
│   ├── salesforce.staging.json
│   └── salesforce.production.json
└── docs/
    └── salesforce/
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
│          Salesforce Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/salesforce/client.ts
export class SalesforceService {
  private client: SalesforceClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SalesforceConfig) {
    this.client = new SalesforceClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('salesforce');
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
// src/salesforce/errors.ts
export class SalesforceServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SalesforceServiceError';
  }
}

export function wrapSalesforceError(error: unknown): SalesforceServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/salesforce/health.ts
export async function checkSalesforceHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await salesforceClient.ping();
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
│ Salesforce    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Salesforce    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/salesforce.ts
export interface SalesforceConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSalesforceConfig(): SalesforceConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./salesforce.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Salesforce operations.

### Step 4: Configure Health Checks
Add health check endpoint for Salesforce connectivity.

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
| Type errors | Missing types | Add Salesforce types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/salesforce/{handlers} src/services/salesforce src/api/salesforce
touch src/salesforce/{client,config,types,errors}.ts
touch src/services/salesforce/{index,sync,cache}.ts
```

## Resources
- [Salesforce SDK Documentation](https://docs.salesforce.com/sdk)
- [Salesforce Best Practices](https://docs.salesforce.com/best-practices)

## Flagship Skills
For multi-environment setup, see `salesforce-multi-env-setup`.
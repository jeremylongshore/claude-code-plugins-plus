---
name: hubspot-reference-architecture
description: |
  Implement HubSpot reference architecture with best-practice project layout.
  Use when designing new HubSpot integrations, reviewing project structure,
  or establishing architecture standards for HubSpot applications.
  Trigger with phrases like "hubspot architecture", "hubspot best practices",
  "hubspot project structure", "how to organize hubspot", "hubspot layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hubspot]
---

# HubSpot Reference Architecture

## Overview
Production-ready architecture patterns for HubSpot integrations.

## Prerequisites
- Understanding of layered architecture
- HubSpot SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-hubspot-project/
├── src/
│   ├── hubspot/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── hubspot/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── hubspot/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── hubspot/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── hubspot/
│   └── integration/
│       └── hubspot/
├── config/
│   ├── hubspot.development.json
│   ├── hubspot.staging.json
│   └── hubspot.production.json
└── docs/
    └── hubspot/
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
│          HubSpot Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/hubspot/client.ts
export class HubSpotService {
  private client: HubSpotClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: HubSpotConfig) {
    this.client = new HubSpotClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('hubspot');
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
// src/hubspot/errors.ts
export class HubSpotServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'HubSpotServiceError';
  }
}

export function wrapHubSpotError(error: unknown): HubSpotServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/hubspot/health.ts
export async function checkHubSpotHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await hubspotClient.ping();
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
│ HubSpot    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ HubSpot    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/hubspot.ts
export interface HubSpotConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadHubSpotConfig(): HubSpotConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./hubspot.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for HubSpot operations.

### Step 4: Configure Health Checks
Add health check endpoint for HubSpot connectivity.

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
| Type errors | Missing types | Add HubSpot types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/hubspot/{handlers} src/services/hubspot src/api/hubspot
touch src/hubspot/{client,config,types,errors}.ts
touch src/services/hubspot/{index,sync,cache}.ts
```

## Resources
- [HubSpot SDK Documentation](https://docs.hubspot.com/sdk)
- [HubSpot Best Practices](https://docs.hubspot.com/best-practices)

## Flagship Skills
For multi-environment setup, see `hubspot-multi-env-setup`.
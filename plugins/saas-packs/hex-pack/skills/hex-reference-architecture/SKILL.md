---
name: hex-reference-architecture
description: |
  Implement Hex reference architecture with best-practice project layout.
  Use when designing new Hex integrations, reviewing project structure,
  or establishing architecture standards for Hex applications.
  Trigger with phrases like "hex architecture", "hex best practices",
  "hex project structure", "how to organize hex", "hex layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hex]
---

# Hex Reference Architecture

## Overview
Production-ready architecture patterns for Hex integrations.

## Prerequisites
- Understanding of layered architecture
- Hex SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-hex-project/
├── src/
│   ├── hex/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── hex/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── hex/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── hex/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── hex/
│   └── integration/
│       └── hex/
├── config/
│   ├── hex.development.json
│   ├── hex.staging.json
│   └── hex.production.json
└── docs/
    └── hex/
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
│          Hex Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/hex/client.ts
export class HexService {
  private client: HexClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: HexConfig) {
    this.client = new HexClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('hex');
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
// src/hex/errors.ts
export class HexServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'HexServiceError';
  }
}

export function wrapHexError(error: unknown): HexServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/hex/health.ts
export async function checkHexHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await hexClient.ping();
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
│ Hex    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Hex    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/hex.ts
export interface HexConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadHexConfig(): HexConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./hex.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Hex operations.

### Step 4: Configure Health Checks
Add health check endpoint for Hex connectivity.

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
| Type errors | Missing types | Add Hex types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/hex/{handlers} src/services/hex src/api/hex
touch src/hex/{client,config,types,errors}.ts
touch src/services/hex/{index,sync,cache}.ts
```

## Resources
- [Hex SDK Documentation](https://docs.hex.com/sdk)
- [Hex Best Practices](https://docs.hex.com/best-practices)

## Flagship Skills
For multi-environment setup, see `hex-multi-env-setup`.
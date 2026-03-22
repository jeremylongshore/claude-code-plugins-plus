---
name: figma-reference-architecture
description: |
  Implement Figma reference architecture with best-practice project layout.
  Use when designing new Figma integrations, reviewing project structure,
  or establishing architecture standards for Figma applications.
  Trigger with phrases like "figma architecture", "figma best practices",
  "figma project structure", "how to organize figma", "figma layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, figma]
---

# Figma Reference Architecture

## Overview
Production-ready architecture patterns for Figma integrations.

## Prerequisites
- Understanding of layered architecture
- Figma SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-figma-project/
├── src/
│   ├── figma/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── figma/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── figma/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── figma/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── figma/
│   └── integration/
│       └── figma/
├── config/
│   ├── figma.development.json
│   ├── figma.staging.json
│   └── figma.production.json
└── docs/
    └── figma/
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
│          Figma Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/figma/client.ts
export class FigmaService {
  private client: FigmaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FigmaConfig) {
    this.client = new FigmaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('figma');
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
// src/figma/errors.ts
export class FigmaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FigmaServiceError';
  }
}

export function wrapFigmaError(error: unknown): FigmaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/figma/health.ts
export async function checkFigmaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await figmaClient.ping();
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
│ Figma    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Figma    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/figma.ts
export interface FigmaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFigmaConfig(): FigmaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./figma.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Figma operations.

### Step 4: Configure Health Checks
Add health check endpoint for Figma connectivity.

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
| Type errors | Missing types | Add Figma types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/figma/{handlers} src/services/figma src/api/figma
touch src/figma/{client,config,types,errors}.ts
touch src/services/figma/{index,sync,cache}.ts
```

## Resources
- [Figma SDK Documentation](https://docs.figma.com/sdk)
- [Figma Best Practices](https://docs.figma.com/best-practices)

## Flagship Skills
For multi-environment setup, see `figma-multi-env-setup`.
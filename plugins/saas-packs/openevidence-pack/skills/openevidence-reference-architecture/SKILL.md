---
name: openevidence-reference-architecture
description: |
  Implement OpenEvidence reference architecture with best-practice project layout.
  Use when designing new OpenEvidence integrations, reviewing project structure,
  or establishing architecture standards for OpenEvidence applications.
  Trigger with phrases like "openevidence architecture", "openevidence best practices",
  "openevidence project structure", "how to organize openevidence", "openevidence layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openevidence]
---

# OpenEvidence Reference Architecture

## Overview
Production-ready architecture patterns for OpenEvidence integrations.

## Prerequisites
- Understanding of layered architecture
- OpenEvidence SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-openevidence-project/
├── src/
│   ├── openevidence/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── openevidence/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── openevidence/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── openevidence/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── openevidence/
│   └── integration/
│       └── openevidence/
├── config/
│   ├── openevidence.development.json
│   ├── openevidence.staging.json
│   └── openevidence.production.json
└── docs/
    └── openevidence/
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
│          OpenEvidence Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/openevidence/client.ts
export class OpenEvidenceService {
  private client: OpenEvidenceClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: OpenEvidenceConfig) {
    this.client = new OpenEvidenceClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('openevidence');
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
// src/openevidence/errors.ts
export class OpenEvidenceServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'OpenEvidenceServiceError';
  }
}

export function wrapOpenEvidenceError(error: unknown): OpenEvidenceServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/openevidence/health.ts
export async function checkOpenEvidenceHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await openevidenceClient.ping();
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
│ OpenEvidence    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ OpenEvidence    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/openevidence.ts
export interface OpenEvidenceConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadOpenEvidenceConfig(): OpenEvidenceConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./openevidence.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for OpenEvidence operations.

### Step 4: Configure Health Checks
Add health check endpoint for OpenEvidence connectivity.

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
| Type errors | Missing types | Add OpenEvidence types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/openevidence/{handlers} src/services/openevidence src/api/openevidence
touch src/openevidence/{client,config,types,errors}.ts
touch src/services/openevidence/{index,sync,cache}.ts
```

## Resources
- [OpenEvidence SDK Documentation](https://docs.openevidence.com/sdk)
- [OpenEvidence Best Practices](https://docs.openevidence.com/best-practices)

## Flagship Skills
For multi-environment setup, see `openevidence-multi-env-setup`.
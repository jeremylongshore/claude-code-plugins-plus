---
name: documenso-reference-architecture
description: |
  Implement Documenso reference architecture with best-practice project layout.
  Use when designing new Documenso integrations, reviewing project structure,
  or establishing architecture standards for Documenso applications.
  Trigger with phrases like "documenso architecture", "documenso best practices",
  "documenso project structure", "how to organize documenso", "documenso layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, documenso]
---

# Documenso Reference Architecture

## Overview
Production-ready architecture patterns for Documenso integrations.

## Prerequisites
- Understanding of layered architecture
- Documenso SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-documenso-project/
├── src/
│   ├── documenso/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── documenso/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── documenso/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── documenso/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── documenso/
│   └── integration/
│       └── documenso/
├── config/
│   ├── documenso.development.json
│   ├── documenso.staging.json
│   └── documenso.production.json
└── docs/
    └── documenso/
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
│          Documenso Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/documenso/client.ts
export class DocumensoService {
  private client: DocumensoClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: DocumensoConfig) {
    this.client = new DocumensoClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('documenso');
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
// src/documenso/errors.ts
export class DocumensoServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'DocumensoServiceError';
  }
}

export function wrapDocumensoError(error: unknown): DocumensoServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/documenso/health.ts
export async function checkDocumensoHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await documensoClient.ping();
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
│ Documenso    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Documenso    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/documenso.ts
export interface DocumensoConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadDocumensoConfig(): DocumensoConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./documenso.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Documenso operations.

### Step 4: Configure Health Checks
Add health check endpoint for Documenso connectivity.

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
| Type errors | Missing types | Add Documenso types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/documenso/{handlers} src/services/documenso src/api/documenso
touch src/documenso/{client,config,types,errors}.ts
touch src/services/documenso/{index,sync,cache}.ts
```

## Resources
- [Documenso SDK Documentation](https://docs.documenso.com/sdk)
- [Documenso Best Practices](https://docs.documenso.com/best-practices)

## Flagship Skills
For multi-environment setup, see `documenso-multi-env-setup`.
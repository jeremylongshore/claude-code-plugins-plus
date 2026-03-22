---
name: cursor-reference-architecture
description: |
  Implement Cursor reference architecture with best-practice project layout.
  Use when designing new Cursor integrations, reviewing project structure,
  or establishing architecture standards for Cursor applications.
  Trigger with phrases like "cursor architecture", "cursor best practices",
  "cursor project structure", "how to organize cursor", "cursor layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Reference Architecture

## Overview
Production-ready architecture patterns for Cursor integrations.

## Prerequisites
- Understanding of layered architecture
- Cursor SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-cursor-project/
├── src/
│   ├── cursor/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── cursor/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── cursor/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── cursor/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── cursor/
│   └── integration/
│       └── cursor/
├── config/
│   ├── cursor.development.json
│   ├── cursor.staging.json
│   └── cursor.production.json
└── docs/
    └── cursor/
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
│          Cursor Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/cursor/client.ts
export class CursorService {
  private client: CursorClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: CursorConfig) {
    this.client = new CursorClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('cursor');
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
// src/cursor/errors.ts
export class CursorServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CursorServiceError';
  }
}

export function wrapCursorError(error: unknown): CursorServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/cursor/health.ts
export async function checkCursorHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await cursorClient.ping();
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
│ Cursor    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cursor    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/cursor.ts
export interface CursorConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCursorConfig(): CursorConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./cursor.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Cursor operations.

### Step 4: Configure Health Checks
Add health check endpoint for Cursor connectivity.

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
| Type errors | Missing types | Add Cursor types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/cursor/{handlers} src/services/cursor src/api/cursor
touch src/cursor/{client,config,types,errors}.ts
touch src/services/cursor/{index,sync,cache}.ts
```

## Resources
- [Cursor SDK Documentation](https://docs.cursor.com/sdk)
- [Cursor Best Practices](https://docs.cursor.com/best-practices)

## Flagship Skills
For multi-environment setup, see `cursor-multi-env-setup`.
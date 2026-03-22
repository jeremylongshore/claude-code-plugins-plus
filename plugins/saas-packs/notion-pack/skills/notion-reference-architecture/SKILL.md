---
name: notion-reference-architecture
description: |
  Implement Notion reference architecture with best-practice project layout.
  Use when designing new Notion integrations, reviewing project structure,
  or establishing architecture standards for Notion applications.
  Trigger with phrases like "notion architecture", "notion best practices",
  "notion project structure", "how to organize notion", "notion layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion Reference Architecture

## Overview
Production-ready architecture patterns for Notion integrations.

## Prerequisites
- Understanding of layered architecture
- Notion SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-notion-project/
├── src/
│   ├── notion/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── notion/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── notion/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── notion/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── notion/
│   └── integration/
│       └── notion/
├── config/
│   ├── notion.development.json
│   ├── notion.staging.json
│   └── notion.production.json
└── docs/
    └── notion/
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
│          Notion Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/notion/client.ts
export class NotionService {
  private client: NotionClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: NotionConfig) {
    this.client = new NotionClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('notion');
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
// src/notion/errors.ts
export class NotionServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'NotionServiceError';
  }
}

export function wrapNotionError(error: unknown): NotionServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/notion/health.ts
export async function checkNotionHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await notionClient.ping();
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
│ Notion    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Notion    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/notion.ts
export interface NotionConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadNotionConfig(): NotionConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./notion.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Notion operations.

### Step 4: Configure Health Checks
Add health check endpoint for Notion connectivity.

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
| Type errors | Missing types | Add Notion types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/notion/{handlers} src/services/notion src/api/notion
touch src/notion/{client,config,types,errors}.ts
touch src/services/notion/{index,sync,cache}.ts
```

## Resources
- [Notion SDK Documentation](https://docs.notion.com/sdk)
- [Notion Best Practices](https://docs.notion.com/best-practices)

## Flagship Skills
For multi-environment setup, see `notion-multi-env-setup`.
---
name: anth-reference-architecture
description: |
  Implement Anthropic reference architecture with best-practice project layout.
  Use when designing new Anthropic integrations, reviewing project structure,
  or establishing architecture standards for Anthropic applications.
  Trigger with phrases like "anthropic architecture", "anthropic best practices",
  "anthropic project structure", "how to organize anthropic", "anthropic layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Reference Architecture

## Overview
Production-ready architecture patterns for Anthropic integrations.

## Prerequisites
- Understanding of layered architecture
- Anthropic SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-anthropic-project/
├── src/
│   ├── anthropic/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── anthropic/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── anthropic/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── anthropic/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── anthropic/
│   └── integration/
│       └── anthropic/
├── config/
│   ├── anthropic.development.json
│   ├── anthropic.staging.json
│   └── anthropic.production.json
└── docs/
    └── anthropic/
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
│          Anthropic Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/anthropic/client.ts
export class AnthropicService {
  private client: AnthropicClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AnthropicConfig) {
    this.client = new AnthropicClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('anthropic');
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
// src/anthropic/errors.ts
export class AnthropicServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AnthropicServiceError';
  }
}

export function wrapAnthropicError(error: unknown): AnthropicServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/anthropic/health.ts
export async function checkAnthropicHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await anthropicClient.ping();
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
│ Anthropic    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Anthropic    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/anthropic.ts
export interface AnthropicConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAnthropicConfig(): AnthropicConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./anthropic.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Anthropic operations.

### Step 4: Configure Health Checks
Add health check endpoint for Anthropic connectivity.

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
| Type errors | Missing types | Add Anthropic types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/anthropic/{handlers} src/services/anthropic src/api/anthropic
touch src/anthropic/{client,config,types,errors}.ts
touch src/services/anthropic/{index,sync,cache}.ts
```

## Resources
- [Anthropic SDK Documentation](https://docs.anthropic.com/sdk)
- [Anthropic Best Practices](https://docs.anthropic.com/best-practices)

## Flagship Skills
For multi-environment setup, see `anthropic-multi-env-setup`.
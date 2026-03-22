---
name: posthog-reference-architecture
description: |
  Implement PostHog reference architecture with best-practice project layout.
  Use when designing new PostHog integrations, reviewing project structure,
  or establishing architecture standards for PostHog applications.
  Trigger with phrases like "posthog architecture", "posthog best practices",
  "posthog project structure", "how to organize posthog", "posthog layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, posthog]
---

# PostHog Reference Architecture

## Overview
Production-ready architecture patterns for PostHog integrations.

## Prerequisites
- Understanding of layered architecture
- PostHog SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-posthog-project/
├── src/
│   ├── posthog/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── posthog/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── posthog/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── posthog/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── posthog/
│   └── integration/
│       └── posthog/
├── config/
│   ├── posthog.development.json
│   ├── posthog.staging.json
│   └── posthog.production.json
└── docs/
    └── posthog/
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
│          PostHog Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/posthog/client.ts
export class PostHogService {
  private client: PostHogClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: PostHogConfig) {
    this.client = new PostHogClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('posthog');
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
// src/posthog/errors.ts
export class PostHogServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'PostHogServiceError';
  }
}

export function wrapPostHogError(error: unknown): PostHogServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/posthog/health.ts
export async function checkPostHogHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await posthogClient.ping();
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
│ PostHog    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostHog    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/posthog.ts
export interface PostHogConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadPostHogConfig(): PostHogConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./posthog.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for PostHog operations.

### Step 4: Configure Health Checks
Add health check endpoint for PostHog connectivity.

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
| Type errors | Missing types | Add PostHog types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/posthog/{handlers} src/services/posthog src/api/posthog
touch src/posthog/{client,config,types,errors}.ts
touch src/services/posthog/{index,sync,cache}.ts
```

## Resources
- [PostHog SDK Documentation](https://docs.posthog.com/sdk)
- [PostHog Best Practices](https://docs.posthog.com/best-practices)

## Flagship Skills
For multi-environment setup, see `posthog-multi-env-setup`.
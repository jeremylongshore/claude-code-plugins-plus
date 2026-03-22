---
name: elevenlabs-reference-architecture
description: |
  Implement ElevenLabs reference architecture with best-practice project layout.
  Use when designing new ElevenLabs integrations, reviewing project structure,
  or establishing architecture standards for ElevenLabs applications.
  Trigger with phrases like "elevenlabs architecture", "elevenlabs best practices",
  "elevenlabs project structure", "how to organize elevenlabs", "elevenlabs layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, elevenlabs]
---

# ElevenLabs Reference Architecture

## Overview
Production-ready architecture patterns for ElevenLabs integrations.

## Prerequisites
- Understanding of layered architecture
- ElevenLabs SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-elevenlabs-project/
├── src/
│   ├── elevenlabs/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── elevenlabs/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── elevenlabs/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── elevenlabs/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── elevenlabs/
│   └── integration/
│       └── elevenlabs/
├── config/
│   ├── elevenlabs.development.json
│   ├── elevenlabs.staging.json
│   └── elevenlabs.production.json
└── docs/
    └── elevenlabs/
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
│          ElevenLabs Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/elevenlabs/client.ts
export class ElevenLabsService {
  private client: ElevenLabsClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ElevenLabsConfig) {
    this.client = new ElevenLabsClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('elevenlabs');
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
// src/elevenlabs/errors.ts
export class ElevenLabsServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ElevenLabsServiceError';
  }
}

export function wrapElevenLabsError(error: unknown): ElevenLabsServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/elevenlabs/health.ts
export async function checkElevenLabsHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await elevenlabsClient.ping();
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
│ ElevenLabs    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ElevenLabs    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/elevenlabs.ts
export interface ElevenLabsConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadElevenLabsConfig(): ElevenLabsConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./elevenlabs.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for ElevenLabs operations.

### Step 4: Configure Health Checks
Add health check endpoint for ElevenLabs connectivity.

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
| Type errors | Missing types | Add ElevenLabs types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/elevenlabs/{handlers} src/services/elevenlabs src/api/elevenlabs
touch src/elevenlabs/{client,config,types,errors}.ts
touch src/services/elevenlabs/{index,sync,cache}.ts
```

## Resources
- [ElevenLabs SDK Documentation](https://docs.elevenlabs.com/sdk)
- [ElevenLabs Best Practices](https://docs.elevenlabs.com/best-practices)

## Flagship Skills
For multi-environment setup, see `elevenlabs-multi-env-setup`.
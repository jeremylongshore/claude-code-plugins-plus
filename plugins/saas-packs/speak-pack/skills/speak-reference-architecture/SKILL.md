---
name: speak-reference-architecture
description: |
  Implement Speak reference architecture with best-practice project layout.
  Use when designing new Speak integrations, reviewing project structure,
  or establishing architecture standards for Speak applications.
  Trigger with phrases like "speak architecture", "speak best practices",
  "speak project structure", "how to organize speak", "speak layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, speak]
---

# Speak Reference Architecture

## Overview
Production-ready architecture patterns for Speak integrations.

## Prerequisites
- Understanding of layered architecture
- Speak SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-speak-project/
├── src/
│   ├── speak/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── speak/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── speak/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── speak/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── speak/
│   └── integration/
│       └── speak/
├── config/
│   ├── speak.development.json
│   ├── speak.staging.json
│   └── speak.production.json
└── docs/
    └── speak/
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
│          Speak Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/speak/client.ts
export class SpeakService {
  private client: SpeakClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SpeakConfig) {
    this.client = new SpeakClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('speak');
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
// src/speak/errors.ts
export class SpeakServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SpeakServiceError';
  }
}

export function wrapSpeakError(error: unknown): SpeakServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/speak/health.ts
export async function checkSpeakHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await speakClient.ping();
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
│ Speak    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Speak    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/speak.ts
export interface SpeakConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSpeakConfig(): SpeakConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./speak.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Speak operations.

### Step 4: Configure Health Checks
Add health check endpoint for Speak connectivity.

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
| Type errors | Missing types | Add Speak types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/speak/{handlers} src/services/speak src/api/speak
touch src/speak/{client,config,types,errors}.ts
touch src/services/speak/{index,sync,cache}.ts
```

## Resources
- [Speak SDK Documentation](https://docs.speak.com/sdk)
- [Speak Best Practices](https://docs.speak.com/best-practices)

## Flagship Skills
For multi-environment setup, see `speak-multi-env-setup`.
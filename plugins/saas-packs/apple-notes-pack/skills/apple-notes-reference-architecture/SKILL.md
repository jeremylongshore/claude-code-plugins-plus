---
name: apple-notes-reference-architecture
description: |
  Implement Apple Notes reference architecture with best-practice project layout.
  Use when designing new Apple Notes integrations, reviewing project structure,
  or establishing architecture standards for Apple Notes applications.
  Trigger with phrases like "apple-notes architecture", "apple-notes best practices",
  "apple-notes project structure", "how to organize apple-notes", "apple-notes layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes Reference Architecture

## Overview
Production-ready architecture patterns for Apple Notes integrations.

## Prerequisites
- Understanding of layered architecture
- Apple Notes SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-apple-notes-project/
├── src/
│   ├── apple-notes/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── apple-notes/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── apple-notes/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── apple-notes/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── apple-notes/
│   └── integration/
│       └── apple-notes/
├── config/
│   ├── apple-notes.development.json
│   ├── apple-notes.staging.json
│   └── apple-notes.production.json
└── docs/
    └── apple-notes/
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
│          Apple Notes Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/apple-notes/client.ts
export class Apple NotesService {
  private client: AppleNotesClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Apple NotesConfig) {
    this.client = new AppleNotesClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('apple-notes');
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
// src/apple-notes/errors.ts
export class Apple NotesServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Apple NotesServiceError';
  }
}

export function wrapApple NotesError(error: unknown): Apple NotesServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/apple-notes/health.ts
export async function checkApple NotesHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await apple-notesClient.ping();
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
│ Apple Notes    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Apple Notes    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/apple-notes.ts
export interface Apple NotesConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadApple NotesConfig(): Apple NotesConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./apple-notes.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Apple Notes operations.

### Step 4: Configure Health Checks
Add health check endpoint for Apple Notes connectivity.

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
| Type errors | Missing types | Add Apple Notes types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/apple-notes/{handlers} src/services/apple-notes src/api/apple-notes
touch src/apple-notes/{client,config,types,errors}.ts
touch src/services/apple-notes/{index,sync,cache}.ts
```

## Resources
- [Apple Notes SDK Documentation](https://docs.apple-notes.com/sdk)
- [Apple Notes Best Practices](https://docs.apple-notes.com/best-practices)

## Flagship Skills
For multi-environment setup, see `apple-notes-multi-env-setup`.
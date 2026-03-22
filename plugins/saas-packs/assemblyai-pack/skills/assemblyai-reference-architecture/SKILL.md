---
name: assemblyai-reference-architecture
description: |
  Implement AssemblyAI reference architecture with best-practice project layout.
  Use when designing new AssemblyAI integrations, reviewing project structure,
  or establishing architecture standards for AssemblyAI applications.
  Trigger with phrases like "assemblyai architecture", "assemblyai best practices",
  "assemblyai project structure", "how to organize assemblyai", "assemblyai layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, assemblyai]
---

# AssemblyAI Reference Architecture

## Overview
Production-ready architecture patterns for AssemblyAI integrations.

## Prerequisites
- Understanding of layered architecture
- AssemblyAI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-assemblyai-project/
├── src/
│   ├── assemblyai/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── assemblyai/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── assemblyai/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── assemblyai/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── assemblyai/
│   └── integration/
│       └── assemblyai/
├── config/
│   ├── assemblyai.development.json
│   ├── assemblyai.staging.json
│   └── assemblyai.production.json
└── docs/
    └── assemblyai/
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
│          AssemblyAI Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/assemblyai/client.ts
export class AssemblyAIService {
  private client: AssemblyAIClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AssemblyAIConfig) {
    this.client = new AssemblyAIClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('assemblyai');
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
// src/assemblyai/errors.ts
export class AssemblyAIServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AssemblyAIServiceError';
  }
}

export function wrapAssemblyAIError(error: unknown): AssemblyAIServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/assemblyai/health.ts
export async function checkAssemblyAIHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await assemblyaiClient.ping();
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
│ AssemblyAI    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AssemblyAI    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/assemblyai.ts
export interface AssemblyAIConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAssemblyAIConfig(): AssemblyAIConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./assemblyai.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for AssemblyAI operations.

### Step 4: Configure Health Checks
Add health check endpoint for AssemblyAI connectivity.

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
| Type errors | Missing types | Add AssemblyAI types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/assemblyai/{handlers} src/services/assemblyai src/api/assemblyai
touch src/assemblyai/{client,config,types,errors}.ts
touch src/services/assemblyai/{index,sync,cache}.ts
```

## Resources
- [AssemblyAI SDK Documentation](https://docs.assemblyai.com/sdk)
- [AssemblyAI Best Practices](https://docs.assemblyai.com/best-practices)

## Flagship Skills
For multi-environment setup, see `assemblyai-multi-env-setup`.
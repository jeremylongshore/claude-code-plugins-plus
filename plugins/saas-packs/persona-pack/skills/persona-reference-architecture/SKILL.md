---
name: persona-reference-architecture
description: |
  Implement Persona reference architecture with best-practice project layout.
  Use when designing new Persona integrations, reviewing project structure,
  or establishing architecture standards for Persona applications.
  Trigger with phrases like "persona architecture", "persona best practices",
  "persona project structure", "how to organize persona", "persona layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, persona]
---

# Persona Reference Architecture

## Overview
Production-ready architecture patterns for Persona integrations.

## Prerequisites
- Understanding of layered architecture
- Persona SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-persona-project/
├── src/
│   ├── persona/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── persona/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── persona/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── persona/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── persona/
│   └── integration/
│       └── persona/
├── config/
│   ├── persona.development.json
│   ├── persona.staging.json
│   └── persona.production.json
└── docs/
    └── persona/
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
│          Persona Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/persona/client.ts
export class PersonaService {
  private client: PersonaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: PersonaConfig) {
    this.client = new PersonaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('persona');
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
// src/persona/errors.ts
export class PersonaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'PersonaServiceError';
  }
}

export function wrapPersonaError(error: unknown): PersonaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/persona/health.ts
export async function checkPersonaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await personaClient.ping();
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
│ Persona    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Persona    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/persona.ts
export interface PersonaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadPersonaConfig(): PersonaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./persona.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Persona operations.

### Step 4: Configure Health Checks
Add health check endpoint for Persona connectivity.

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
| Type errors | Missing types | Add Persona types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/persona/{handlers} src/services/persona src/api/persona
touch src/persona/{client,config,types,errors}.ts
touch src/services/persona/{index,sync,cache}.ts
```

## Resources
- [Persona SDK Documentation](https://docs.persona.com/sdk)
- [Persona Best Practices](https://docs.persona.com/best-practices)

## Flagship Skills
For multi-environment setup, see `persona-multi-env-setup`.
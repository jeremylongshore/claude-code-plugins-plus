---
name: langchain-reference-architecture
description: |
  Implement LangChain reference architecture with best-practice project layout.
  Use when designing new LangChain integrations, reviewing project structure,
  or establishing architecture standards for LangChain applications.
  Trigger with phrases like "langchain architecture", "langchain best practices",
  "langchain project structure", "how to organize langchain", "langchain layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langchain]
---

# LangChain Reference Architecture

## Overview
Production-ready architecture patterns for LangChain integrations.

## Prerequisites
- Understanding of layered architecture
- LangChain SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-langchain-project/
├── src/
│   ├── langchain/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── langchain/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── langchain/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── langchain/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── langchain/
│   └── integration/
│       └── langchain/
├── config/
│   ├── langchain.development.json
│   ├── langchain.staging.json
│   └── langchain.production.json
└── docs/
    └── langchain/
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
│          LangChain Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/langchain/client.ts
export class LangChainService {
  private client: LangChainClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LangChainConfig) {
    this.client = new LangChainClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('langchain');
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
// src/langchain/errors.ts
export class LangChainServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LangChainServiceError';
  }
}

export function wrapLangChainError(error: unknown): LangChainServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/langchain/health.ts
export async function checkLangChainHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await langchainClient.ping();
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
│ LangChain    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ LangChain    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/langchain.ts
export interface LangChainConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLangChainConfig(): LangChainConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./langchain.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for LangChain operations.

### Step 4: Configure Health Checks
Add health check endpoint for LangChain connectivity.

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
| Type errors | Missing types | Add LangChain types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/langchain/{handlers} src/services/langchain src/api/langchain
touch src/langchain/{client,config,types,errors}.ts
touch src/services/langchain/{index,sync,cache}.ts
```

## Resources
- [LangChain SDK Documentation](https://docs.langchain.com/sdk)
- [LangChain Best Practices](https://docs.langchain.com/best-practices)

## Flagship Skills
For multi-environment setup, see `langchain-multi-env-setup`.
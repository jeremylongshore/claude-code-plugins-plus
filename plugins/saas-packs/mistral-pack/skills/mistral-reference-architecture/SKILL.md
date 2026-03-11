---
name: mistral-reference-architecture
description: |
  Implement Mistral AI reference architecture with best-practice project layout.
  Use when designing new Mistral AI integrations, reviewing project structure,
  or establishing architecture standards for Mistral AI applications.
  Trigger with phrases like "mistral architecture", "mistral best practices",
  "mistral project structure", "how to organize mistral", "mistral layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral AI Reference Architecture

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-ready architecture patterns for Mistral AI integrations. Covers layered project structure, client singleton, configuration management, error handling, service layer with caching, health checks, and prompt templates.

## Prerequisites
- Understanding of layered architecture
- Mistral AI SDK knowledge
- TypeScript project setup
- Testing framework configured

## Layer Architecture

```
API Layer (Routes, Controllers, Middleware)
    ↓
Service Layer (Business Logic, Orchestration)
    ↓
Mistral Layer (Client, Prompts, Error Handling)
    ↓
Infrastructure Layer (Cache, Queue, Monitoring)
```

## Instructions

### Step 1: Create Directory Structure
Organize into `src/mistral/` (client, config, types, errors, prompts, handlers), `src/services/ai/` (chat, rag, cache), `src/api/` (routes, streaming), `tests/` (unit, integration), and `config/` (per-environment JSON).

### Step 2: Implement Client Singleton
Create `getMistralClient()` factory that lazily initializes a single `Mistral` instance with config from environment. Include `resetMistralClient()` for testing.

### Step 3: Configure with Zod Validation
Define config schema with `z.object()` for apiKey, model (default `mistral-small-latest`), timeout (30s), maxRetries (3), and cache settings. Parse from environment variables.

### Step 4: Build Error Handling Layer
Create `MistralServiceError` class with code, status, retryable flag. Wrap raw errors: 429 = RATE_LIMIT (retryable), 401 = AUTH_ERROR, 500+ = SERVICE_ERROR (retryable).

### Step 5: Implement Service Layer
Build `ChatService` with `complete()` and `stream()` methods. Add cache check for deterministic requests (temperature=0). Wrap all calls with retry and error handling.

### Step 6: Add Health Check
Implement `checkMistralHealth()` that calls `client.models.list()` and returns status (healthy/degraded/unhealthy) with latency measurement.

### Step 7: Create Prompt Templates
Define reusable `PromptTemplate` interface with system prompt and user template function. Include templates for summarize, classify, and codeReview.

## Output
- Structured project layout with clear layer separation
- Client singleton wrapper with retry logic
- Zod-validated configuration management
- Custom error classes with retryable detection
- Service layer with caching and streaming
- Health check endpoint
- Reusable prompt templates

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Rate limit (429) | Too many requests | Retry with backoff, marked retryable |
| Auth error (401) | Invalid API key | Check credentials, not retryable |
| Server error (5xx) | Mistral service issue | Retry with backoff, marked retryable |
| Config validation | Missing/invalid env vars | Check Zod schema errors |

## Examples

### Client Usage
```typescript
const client = getMistralClient();
const response = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [{ role: 'user', content: 'Hello' }],
});
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Mistral AI API Reference](https://docs.mistral.ai/api/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

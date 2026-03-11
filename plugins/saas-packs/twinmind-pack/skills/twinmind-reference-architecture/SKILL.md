---
name: twinmind-reference-architecture
description: |
  Implement TwinMind reference architecture with best-practice project layout.
  Use when designing new TwinMind integrations, reviewing project structure,
  or establishing architecture standards for meeting AI applications.
  Trigger with phrases like "twinmind architecture", "twinmind best practices",
  "twinmind project structure", "how to organize twinmind", "twinmind layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-ready architecture patterns for TwinMind meeting AI integrations with layered architecture (API -> Service -> TwinMind -> Integration -> Infrastructure), singleton client wrapper, service orchestration, error boundaries, and health checks.

## Prerequisites
- Understanding of layered architecture
- TwinMind API knowledge
- TypeScript project setup
- Testing framework configured

## Instructions

### Step 1: Project Structure
Organize into layers: `src/twinmind/` (client, config, types, errors, handlers), `src/services/meeting/` (transcription, summary, actions, cache), `src/integrations/` (calendar, slack, linear, email), `src/api/` (routes, middleware), `src/jobs/` (sync, cleanup, reports), `src/utils/` (audio, logging, metrics), plus `tests/`, `config/`, and `docs/`.

### Step 2: Client Wrapper
Build a singleton `TwinMindService` with Axios, caching via `TranscriptCache`, metrics via `MetricsCollector`, and request/response interceptors for logging and error tracking.

### Step 3: Service Layer
Create `MeetingService` that orchestrates transcription, summary generation, action item extraction, speaker identification, and Slack notification. Run summary + action items in parallel for performance.

### Step 4: Error Boundary
Implement `TwinMindError` with error codes (AUTH_FAILED, RATE_LIMITED, SERVER_ERROR), retryable flag, and factory method `fromApiError()` for consistent error handling.

### Step 5: Health Checks
Build `checkHealth()` that validates TwinMind API connectivity, cache availability, and database status. Return overall status (healthy/degraded/unhealthy) with per-check latency.

### Step 6: Configuration Management
Create environment-specific JSON config files with `loadConfig()` that merges environment variables with file-based defaults for API URL, timeout, retries, cache TTL, and feature flags.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete client wrapper, service layer, error boundary, health check, and config management code.

## Output
- Structured project layout
- Client wrapper with caching and metrics
- Service layer with business logic
- Error boundary implemented
- Health checks configured
- Configuration management

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns by layer |
| Config not loading | Wrong paths | Verify config file locations |
| Type errors | Missing types | Add TwinMind type definitions |
| Test isolation | Shared state | Use dependency injection |

## Examples


**Basic usage**: Apply twinmind reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind reference architecture for production environments with multiple constraints and team-specific requirements.

## Resources
- [TwinMind API Reference](https://twinmind.com/docs/api)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)

## Next Steps
For multi-environment setup, see `twinmind-multi-env-setup`.
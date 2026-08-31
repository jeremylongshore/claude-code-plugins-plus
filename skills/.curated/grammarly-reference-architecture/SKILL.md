---
name: grammarly-reference-architecture
description: 'Implement Grammarly reference architecture with best-practice project
  layout.

  Use when designing new Grammarly integrations, reviewing project structure,

  or establishing architecture standards for Grammarly applications.

  Trigger with phrases like "grammarly architecture", "grammarly best practices",

  "grammarly project structure", "how to organize grammarly", "grammarly layout".

  '
allowed-tools: Read, Grep
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Reference Architecture

## Architecture

```
┌────────────────────────────────────┐
│         Your Application            │
├────────────────────────────────────┤
│    Content Quality Service          │
│  (Score, AI Detect, Plagiarism)     │
├────────────────────────────────────┤
│    Grammarly API Client             │
│  (Auth, Retry, Cache, Chunking)     │
├────────────────────────────────────┤
│    Grammarly APIs                   │
│  api.grammarly.com                  │
└────────────────────────────────────┘
```

## Project Structure

```
grammarly-integration/
├── src/grammarly/
│   ├── client.ts        # API client with token management
│   ├── scoring.ts       # Writing Score API
│   ├── detection.ts     # AI + Plagiarism detection
│   ├── chunking.ts      # Large document splitting
│   └── types.ts         # TypeScript interfaces
├── src/services/
│   ├── quality-gate.ts  # Threshold enforcement
│   └── content-audit.ts # Full audit pipeline
├── tests/
└── .env.example
```

## API Decision Matrix

| Need | API | Notes |
|------|-----|-------|
| Grammar/style quality | Writing Score v2 | Sync, fast |
| AI content detection | AI Detection v1 | Sync, fast |
| Source matching | Plagiarism v1 | Async, poll |
| All three | Combined pipeline | Parallel where possible |

## Overview

This architecture separates text ingestion, consent/classification, typed client access, bounded asynchronous processing, aggregate observability, and deletion/rollback controls. Source text is never an architecture artifact or telemetry payload.

## Prerequisites

- A data owner for each source, consent/retention policy, destination allowlist, and owner for every integration edge.
- Separate sandbox/staging/production identities and configuration, plus documented rollback for client, queue, and storage controls.

## Instructions

1. Draw every source-to-destination edge with data class, consent basis, owner, retention, access boundary, retry behavior, and rollback.
2. Start with fictional sandbox text and fail closed on unknown consent, destination, or response shape.
3. Make asynchronous work idempotent and bounded; quarantine uncertainty instead of resubmitting or retaining text for debugging.
4. Canary one integration with aggregate metrics and retention probes before promotion, retaining the previous revision.
5. Re-evaluate controls whenever source, credential, client, or retention policy changes.

## Output

Produce an architecture record with component owners, source/destination classes, policy revisions, idempotency/retry behavior, observability signals, test evidence, retention, and rollback revision. Exclude text, suggestions, identities, and credentials.

## Error Handling

Stop the flow for unknown consent/destination, failed redaction, non-idempotent retry, or retention-policy drift. Quarantine the opaque event and escalate rather than adding a broad fallback.

## Examples

`source=synthetic-editor; destination=sandbox-client; consent=test-only; retention=none; client=v4; probe=pass; rollback=arch-r17` is a reviewable architecture receipt.

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)

## Next Steps

Start with `grammarly-install-auth`.

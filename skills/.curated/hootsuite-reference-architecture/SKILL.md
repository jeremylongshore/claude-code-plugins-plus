---
name: hootsuite-reference-architecture
description: 'Implement Hootsuite reference architecture with best-practice project
  layout.

  Use when designing new Hootsuite integrations, reviewing project structure,

  or establishing architecture standards for Hootsuite applications.

  Trigger with phrases like "hootsuite architecture", "hootsuite best practices",

  "hootsuite project structure", "how to organize hootsuite", "hootsuite layout".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite Reference Architecture

## Architecture

```
┌──────────────────────────────────────┐
│         Your Application              │
├──────────────────────────────────────┤
│  Content Manager → Scheduler → Publisher │
├──────────────────────────────────────┤
│      Hootsuite API Client             │
│  (OAuth, Token Refresh, Rate Limit)   │
├──────────────────────────────────────┤
│      Hootsuite REST API v1            │
│  platform.hootsuite.com/v1/           │
└──────────────────────────────────────┘
```

## Project Structure

```
hootsuite-integration/
├── src/
│   ├── hootsuite/
│   │   ├── client.ts        # API client with token management
│   │   ├── auth.ts          # OAuth 2.0 flow
│   │   ├── publishing.ts    # Message scheduling + media
│   │   ├── analytics.ts     # Metrics + URL shortening
│   │   └── types.ts         # TypeScript interfaces
│   ├── services/
│   │   ├── scheduler.ts     # Content calendar logic
│   │   ├── content.ts       # Post formatting per platform
│   │   └── media.ts         # Media processing + upload
│   ├── api/
│   │   └── schedule.ts      # REST endpoint
│   └── store/
│       └── tokens.ts        # Persistent token storage
├── tests/
│   ├── unit/
│   └── fixtures/
└── .env.example
```

## Key Decisions

| Decision | Recommendation | Why |
|----------|---------------|-----|
| Token storage | Database/KV, not env vars | Refresh tokens change each use |
| Scheduling | Queue-based, not direct API | Rate limit compliance |
| Media upload | Pre-process images | Reduce REJECTED media states |
| Multi-profile | Batch schedule per profile | Separate errors per profile |

## Overview

This architecture separates draft creation, approval, audience validation, scoped scheduling, aggregate observability, and cancellation/rollback. Post copy and media stay inside approved publishing boundaries and never become telemetry.

## Prerequisites

- A profile/account owner, audience policy, approval authority, destination allowlist, and owner for every publish edge.
- Separate sandbox/staging/production configuration and documented rollback for client, scheduler, queue, and credential controls.

## Instructions

1. Map every trigger-to-profile path with owner, audience, approval state, allowed operation, idempotency, observability, and rollback.
2. Begin with draft-only sandbox fixtures and fail closed on unknown profile, audience, destination, or approval state.
3. Make scheduling idempotent and bounded; quarantine uncertainty rather than posting, resubmitting, or exporting copy for debugging.
4. Canary one draft-only profile with aggregate signals before promotion and retain the previous revision.
5. Re-evaluate controls after changes to accounts, audiences, credentials, schedules, or approval policy.

## Output

Produce an architecture record with owners, opaque profile IDs, policy revisions, idempotency/retry behavior, observability, test evidence, and rollback revision. Exclude copy, media, handles, tokens, and identities.

## Error Handling

Stop on unknown profile/audience, failed approval assertion, public-post path in a canary, or non-idempotent retry. Quarantine the event and restore the prior controlled path.

## Examples

`source=ci-synthetic; profile=sandbox-brand; audience=r4; approval=required; action=draft-only; probe=pass; rollback=arch-r17` is a reviewable architecture receipt.

## Resources

- [Hootsuite Developer Platform](https://developer.hootsuite.com)
- [API Overview](https://developer.hootsuite.com/docs/api-overview)

## Next Steps

Start with `hootsuite-install-auth` to set up OAuth.

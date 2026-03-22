---
name: grammarly-reference-architecture
description: |
  Implement Grammarly reference architecture with best-practice project layout.
  Use when designing new Grammarly integrations, reviewing project structure,
  or establishing architecture standards for Grammarly applications.
  Trigger with phrases like "grammarly architecture", "grammarly best practices",
  "grammarly project structure", "how to organize grammarly", "grammarly layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
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

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)

## Next Steps

Start with `grammarly-install-auth`.

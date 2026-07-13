# navan-common-errors — One-Pager

Diagnose and resolve the most frequent Navan API errors with targeted fix procedures.

## The Problem

Navan API errors are opaque — a 401 could mean an expired token, a revoked credential, or a malformed Authorization header. A 403 might indicate wrong tier (Business vs Enterprise), insufficient scopes, or a disabled Expense API that requires separate enablement from Navan support. Without a diagnostic guide, developers waste hours on trial-and-error debugging against production endpoints.

## The Solution

This skill provides a complete error reference covering all common HTTP status codes (401, 403, 404, 429, 500, 503) with specific root causes, diagnostic commands, and fix procedures. Each error includes a curl-based verification step so developers can isolate the problem without writing code.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers debugging failed Navan API calls in development or production |
| **What** | Error-to-fix lookup table with diagnostic commands and root cause analysis |
| **When** | When an API call returns an unexpected error, during incident response, or when onboarding to understand failure modes |

## Key Features

1. **Six-error coverage** — 401, 403, 404, 429, 500, 503 with Navan-specific root causes
2. **Diagnostic commands** — curl-based verification steps for each error type
3. **Tier-aware guidance** — Identifies errors caused by Business vs Enterprise feature gates

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

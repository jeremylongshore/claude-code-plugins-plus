# navan-sdk-patterns — One-Pager

Build a typed API wrapper around Navan's raw REST endpoints since no official SDK exists.

## The Problem

Navan provides no public SDK package — no `@navan/sdk` on npm, no `navan` on PyPI. Every team calling the API ends up writing ad-hoc fetch/requests code scattered across their codebase. Without a consistent wrapper, token refresh logic gets duplicated, error handling is inconsistent, and response types are untyped. Teams need SDK-like patterns without an actual SDK.

## The Solution

This skill provides patterns for building a typed NavanAPI wrapper class with automatic token management, request/response typing, retry middleware with exponential backoff, and centralized error handling. It turns raw REST calls into a clean, reusable interface that behaves like an SDK.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers building production Navan integrations that need maintainable API access |
| **What** | Typed API wrapper class, token auto-refresh, retry middleware, response interfaces |
| **When** | After hello-world works and you need production-grade API access patterns |

## Key Features

1. **Typed wrapper class** — NavanAPI class with TypeScript interfaces for all known endpoints
2. **Auto token refresh** — Transparent token lifecycle management with expiry tracking
3. **Retry middleware** — Exponential backoff for 429/503 errors with configurable limits

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

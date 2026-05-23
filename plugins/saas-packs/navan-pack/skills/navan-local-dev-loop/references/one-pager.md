# navan-local-dev-loop — One-Pager

Set up a local development environment for Navan API integrations with token caching and request logging.

## The Problem

Navan has no sandbox or test environment — all API calls hit production. This makes local development risky: accidental bookings, rate limit exhaustion, and credential exposure are all real concerns. Developers need a structured local setup that minimizes production calls, caches tokens to avoid repeated auth requests, and logs every request for debugging.

## The Solution

This skill provides a complete local dev environment setup: .env-based credential management, a token cache that persists across restarts, request/response logging for debugging, mock fixtures for offline development, and a test harness that validates integration logic without hitting production endpoints unnecessarily.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building or maintaining Navan integrations who need a safe local workflow |
| **What** | Project scaffold with .env config, token cache, request logger, mock fixtures, and dev scripts |
| **When** | Starting a new Navan project, setting up CI/CD, or debugging API issues locally |

## Key Features

1. **Token caching** — Persists OAuth tokens to disk with expiry tracking, avoiding redundant auth calls
2. **Request logging** — Logs all API requests/responses for debugging without exposing secrets
3. **Mock fixtures** — Recorded API responses for offline development and testing

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

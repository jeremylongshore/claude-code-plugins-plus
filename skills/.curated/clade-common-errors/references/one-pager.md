# clade-common-errors — One-Pager

Diagnose and fix every Anthropic API error by type and HTTP status code.

## The Problem

The Anthropic API returns structured errors with a `type` field and HTTP status code, but developers waste time guessing what went wrong. A 401 might be a revoked key or a missing header. A 429 might be RPM or TPM. A 529 is not a rate limit at all — it is server overload. Without a clear reference, debugging cycles drag on and production incidents last longer than they should.

## The Solution

This skill provides a complete error reference covering every status code you will encounter: 401 (authentication), 429 (rate limit), 529 (overloaded), 400 (invalid request), 404 (model not found), and context window overflow. Each entry includes the exact JSON error response, root cause analysis, and fix code. A quick diagnostic section provides curl commands to verify API status and key validity in seconds.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Any developer working with the Anthropic Messages API |
| **What** | Error-by-error reference with exact JSON responses, causes, and TypeScript/bash fixes |
| **When** | When you hit an API error and need to identify the cause and fix it fast |

## Key Features

1. **Authentication errors (401)** — Verify key format (`sk-ant-`), test with curl, and rotate credentials
2. **Rate limit handling (429)** — Built-in SDK retries with `maxRetries`, manual `retry-after` header parsing, and a tier table (Tier 1-4 with RPM/TPM limits)
3. **Overloaded fallback (529)** — Distinguish server overload from rate limits, implement model fallback (Sonnet to Haiku)
4. **Input validation (400)** — Role alternation checker, max_tokens validation, image size/format checks, correct model IDs
5. **Context overflow prevention** — `countTokens` API to measure input before sending, conversation trimming to stay under 200K

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

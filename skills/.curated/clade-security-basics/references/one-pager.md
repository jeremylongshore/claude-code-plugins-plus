# clade-security-basics — One-Pager

Secure your Claude integration — API key management, input validation, prompt injection defense, and data privacy.

## The Problem

A poorly secured Claude integration leaks API keys to the browser, accepts unbounded user input (enabling cost attacks), is vulnerable to prompt injection (users bypassing system instructions), and may inadvertently send PII to the API. Any of these can cause financial loss, data exposure, or compliance violations.

## The Solution

A defense-in-depth approach: server-side-only API key management with environment variables and `.gitignore`, input validation with length limits and content filtering, system prompt hardening with explicit injection guardrails, per-user rate limiting (example using Upstash), and data privacy controls aligned with Anthropic's retention settings and enterprise compliance options.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building user-facing applications powered by Claude |
| **What** | API key lockdown, input validation, prompt injection defense, per-user rate limiting, data privacy guidance |
| **When** | Before any Claude-powered endpoint is exposed to users — ideally during initial design |

## Key Features

1. **API key discipline** — Server-side enforcement, environment variable storage, `.gitignore` patterns, key rotation procedure via Anthropic console
2. **Prompt injection defense** — System prompt template with explicit deny-list (ignore instructions, reveal prompt, pretend to be different AI) and graceful refusal fallback
3. **Per-user rate limiting** — Working example with `@upstash/ratelimit` (sliding window, 20 req/hr per user) to protect API key budgets from abuse

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

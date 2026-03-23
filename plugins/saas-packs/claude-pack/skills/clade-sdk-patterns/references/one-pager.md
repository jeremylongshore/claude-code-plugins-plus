# clade-sdk-patterns — One-Pager

Production-ready patterns for the Anthropic TypeScript and Python SDKs.

## The Problem

The Anthropic SDK surface is broad — client configuration, error class hierarchy, three streaming approaches, TypeScript generics, prompt caching headers, and batch processing. Developers end up with fragile integrations because they miss retry configuration, handle errors too broadly, or don't leverage cost-saving features like caching and batches.

## The Solution

A curated pattern library covering both `@claude-ai/sdk` (TypeScript) and `anthropic` (Python): full client configuration with retries/timeouts/custom headers, type-safe error handling using the SDK's exception class hierarchy, three streaming patterns (event-based, async iterator, Python context manager), prompt caching for 90% input token savings, and Message Batches for 50% cost reduction on bulk workloads.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | TypeScript and Python developers integrating the Anthropic SDK |
| **What** | Client setup, error handling, streaming, TypeScript types, prompt caching, batch processing |
| **When** | When starting a new Claude integration or hardening an existing one for production |

## Key Features

1. **Dual-language coverage** — Every pattern shown in both TypeScript and Python with full client configuration (apiKey, maxRetries, timeout, baseURL, defaultHeaders)
2. **Three streaming patterns** — Event-based (`stream.on('text')`), async iterator (`for await...of`), and Python context manager (`with client.messages.stream()`) with error handling
3. **Cost optimization APIs** — Prompt caching setup with `cache_control: { type: 'ephemeral' }` for 90% savings, and Message Batches API for 50% off on up to 10,000 requests

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

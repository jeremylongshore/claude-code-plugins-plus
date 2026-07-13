# clade-known-pitfalls — One-Pager

Ten common mistakes when building with the Anthropic API and how to avoid every one of them.

## The Problem

Developers coming from other LLM APIs (or starting fresh) repeatedly hit the same Anthropic-specific gotchas: forgetting `max_tokens` is required, putting system prompts in the messages array, creating a new client per request, ignoring truncated responses, and sending unnecessary PII. Each mistake costs debugging time or real money.

## The Solution

This skill catalogs ten specific pitfalls with BAD/GOOD code comparisons for each. It covers API contract differences from OpenAI, performance anti-patterns (client-per-request, no streaming), cost traps (expensive output tokens, oversized max_tokens), and security concerns (unnecessary PII). A quick-reference table summarizes all fixes.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building with the Anthropic API, especially those migrating from OpenAI or starting their first integration |
| **What** | Ten numbered pitfalls with BAD/GOOD code examples and a quick-reference summary table |
| **When** | During code review, when debugging unexpected API errors, or as a pre-production audit checklist |

## Key Features

1. **BAD/GOOD Code Comparisons** — Each pitfall shows the wrong way and the right way side by side in TypeScript
2. **Cost and Performance Pitfalls** — Covers output tokens costing 5x input, client-per-request connection overhead, and missing streaming for user-facing apps
3. **Quick-Reference Table** — All ten pitfalls and their one-line fixes in a single scannable table

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

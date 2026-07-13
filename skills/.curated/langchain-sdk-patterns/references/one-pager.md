# langchain-sdk-patterns — One-Pager

Compose LangChain 1.0 runnables with the defaults the docs do not warn you about — parallel batching, narrow fallbacks, and brace-safe prompts.

## The Problem

`chain.batch(inputs)` runs serially on many providers because `max_concurrency` defaults to 1, so "batching 1,000 requests" takes 1,000 round-trips instead of ~50. `.with_fallbacks([backup])` defaults `exceptions_to_handle=(Exception,)` and on Python <3.12 swallows `KeyboardInterrupt`, so `Ctrl+C` during a long run silently falls through to the backup and keeps billing. `ChatPromptTemplate.from_messages` with f-string format raises `KeyError` the moment a user pastes JSON or code containing `{`.

## The Solution

Explicit composition with typed boundaries: `RunnableSequence` with `.with_fallbacks(exceptions_to_handle=(RateLimitError, APITimeoutError))`, `.batch(inputs, config={"max_concurrency": 10})` (or 20+ behind a semaphore), and `ChatPromptTemplate.from_messages([...], template_format="jinja2")` for any template fed user input. Four tight references cover the composition matrix, per-provider fallback whitelist, concurrency tuning, and brace-escaping rules.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers composing LCEL chains, hardening chains for production, or tuning batch throughput with LangChain 1.0 |
| **What** | Runnable composition patterns, fallback exception whitelist, batch concurrency tuning, prompt-template escaping, 4 deep references |
| **When** | After `langchain-model-inference`, before any production chain — concurrency and fallback defaults are the biggest unknown-unknowns in LCEL |

## Key Features

1. **Invoke/batch/abatch/stream comparison matrix** — When to reach for each, concurrency semantics, error propagation, and the `max_concurrency=1` trap with the recommended safe ceilings (10 per provider, 20+ with a semaphore for rate limiting)
2. **Narrow fallback whitelist** — Concrete `exceptions_to_handle=(...)` tuples per provider (`RateLimitError`, `APIError`, `APITimeoutError`) so `Ctrl+C`, `SystemExit`, and schema `ValidationError`s surface instead of being swallowed
3. **Jinja2 prompt templates for untrusted input** — `template_format="jinja2"` pattern that survives literal `{` in JSON payloads, code snippets, and markdown fences, plus `MessagesPlaceholder` for variable message history

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

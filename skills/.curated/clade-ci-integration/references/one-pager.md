# clade-ci-integration — One-Pager

Test and validate Claude integrations in CI/CD without leaking keys or blowing budgets.

## The Problem

Claude API integrations need automated testing, but naively adding API calls to CI creates three problems: API keys get exposed to fork PRs, real API calls slow down pipelines and cost money on every push, and there is no reliable way to assert on nondeterministic LLM outputs. Teams either skip testing entirely or accumulate unexpected API bills.

## The Solution

This skill provides a two-tier testing strategy: mocked unit tests that run on every PR without an API key, and real integration tests that run only on the main branch with secrets. It includes a complete Vitest mock client that returns realistic response shapes, a GitHub Actions workflow with proper secret handling, and a cost control checklist (Haiku-only, tight max_tokens, budget caps).

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and developers adding Claude integrations to CI/CD pipelines |
| **What** | GitHub Actions workflow, Vitest mock client, integration test patterns, and CI cost controls |
| **When** | When setting up automated testing for any project that calls the Anthropic API |

## Key Features

1. **Mock client factory** — `mockAnthropicClient()` returns a Vitest-compatible mock with realistic `messages.create` and `messages.stream` responses, no API key required
2. **GitHub Actions workflow** — Complete YAML with separate unit test (mocked) and integration test (real API) steps, proper `secrets.ANTHROPIC_API_KEY` handling
3. **Cost control strategies** — Use Haiku for CI, limit `max_tokens` to 50, skip integration tests on fork PRs, gate real API calls to main branch only

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

# clade-local-dev-loop — One-Pager

Set up a fast, cheap local development workflow for building with the Claude API.

## The Problem

Developing against the Claude API without a proper local workflow leads to slow iteration cycles and unexpectedly high bills. Developers waste time restarting scripts manually, pay Opus/Sonnet prices for throwaway test calls, and lack a way to unit test without hitting the live API.

## The Solution

This skill scaffolds a complete local dev environment with hot-reload via tsx watch, cost-tracking per request, Haiku as the default dev model (20x cheaper than Opus), and a mock client for unit tests that never touch the API. Supports both TypeScript and Python workflows.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers starting a new Claude-powered project or prototyping features |
| **What** | Scaffolds project with SDK, dotenv, hot reload, mock client, and cost tracking |
| **When** | At the start of any Claude API project, or when dev costs are too high |

## Key Features

1. **Hot Reload with tsx** — File changes automatically re-run your test script, eliminating manual restart cycles
2. **Cost Tracking Per Request** — Every API call prints an estimated cost so you can monitor spend during development
3. **Mock Client for Unit Tests** — Drop-in mock that returns realistic response shapes without any API calls

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

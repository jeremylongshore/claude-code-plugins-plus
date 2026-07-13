# navan-multi-env-setup — One-Pager

Set up dev/staging/prod environment separation for Navan integrations without a sandbox API.

## The Problem

Navan does not provide a sandbox or staging API environment. Every API call hits production data with real corporate travel bookings and expense records. This makes development and testing dangerous — a bug in a sync script could modify live bookings, and CI pipelines cannot safely run integration tests against the real API. Teams need isolation patterns that Navan itself does not offer.

## The Solution

This skill implements environment separation using multiple OAuth apps (one per environment), environment variable management with validation, a request proxy for local development that logs without mutating, and a mock server setup for CI pipelines. The approach gives teams dev/staging/prod isolation even though Navan only provides a single production API.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers and DevOps engineers managing Navan integrations across development lifecycle stages |
| **What** | Per-environment OAuth app configuration, env var management, local dev proxy, CI mock server |
| **When** | Setting up a new Navan integration project, adding CI pipeline testing, or onboarding developers who need safe local testing |

## Key Features

1. **Multi-app OAuth isolation** — Separate client_id/client_secret pairs per environment with scoped permissions
2. **Local dev proxy** — Intercepting proxy that logs requests and optionally replays recorded responses for offline development
3. **CI mock server** — Lightweight Express-based mock that simulates Navan API responses for automated testing

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

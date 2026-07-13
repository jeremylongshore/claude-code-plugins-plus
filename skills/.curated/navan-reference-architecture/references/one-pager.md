# navan-reference-architecture — One-Pager

Production-grade architecture pattern for Navan API integration with token management, data sync pipelines, and monitoring.

## The Problem

Navan provides raw REST APIs with OAuth 2.0 but no SDK, no sandbox environment, and no webhook push mechanism. Teams building integrations must design their own token management, data synchronization, error handling, and monitoring layers from scratch. Without a reference architecture, each team reinvents these patterns — often poorly — leading to brittle integrations that fail silently.

## The Solution

This skill provides a complete reference architecture for Navan integration covering five layers: API gateway with rate limiting, centralized token management service for OAuth lifecycle, data sync pipeline using Fivetran or Airbyte connectors, ERP connector for expense/booking data, and a monitoring stack for observability. The architecture handles Navan's specific constraints including poll-based data refresh (no webhooks), one-time credential visibility, and lack of a sandbox environment.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Solution architects, platform engineers, technical leads designing Navan integrations |
| **What** | Five-layer architecture diagram with component specifications, data flow patterns, and technology recommendations |
| **When** | Greenfield Navan integration planning, existing integration refactoring, architecture review, vendor evaluation |

## Key Features

1. **Token Management Service** — Centralized OAuth lifecycle handling with automatic refresh, secure storage, and multi-tenant support
2. **Data Sync Pipeline** — Fivetran/Airbyte connector patterns for BOOKING (weekly) and TRANSACTION (incremental) tables
3. **Text Architecture Diagram** — Copy-pasteable system diagram showing all five layers and their interactions

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

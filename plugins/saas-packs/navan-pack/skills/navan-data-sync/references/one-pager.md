# navan-data-sync — One-Pager

Implement incremental sync strategies for Navan data, handling weekly BOOKING re-imports, incremental TRANSACTION loads, and real-time webhook callbacks.

## The Problem

Navan exposes two fundamentally different data tables: BOOKING (full re-import weekly, every record refreshed) and TRANSACTION (incremental, append-only). Naive sync implementations either miss updated bookings or create duplicate transactions. Additionally, real-time use cases like approval notifications and policy alerts require webhook-based event handling that sits outside the polling model entirely.

## The Solution

This skill provides three sync tiers: scheduled full-refresh for BOOKING with merge-upsert logic keyed on UUID, incremental append for TRANSACTION with watermark tracking, and webhook-based real-time callbacks for event-driven workflows. It includes Airbyte sync mode configuration, idempotent upsert SQL patterns, and webhook endpoint setup with signature verification.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Data engineers and platform teams maintaining Navan data pipelines in production |
| **What** | Sync strategies for BOOKING (weekly re-import), TRANSACTION (incremental), and webhooks (real-time) |
| **When** | Setting up production data pipelines, debugging sync drift, or adding real-time event processing |

## Key Features

1. **Three-tier sync model** — Full refresh, incremental append, and real-time webhooks for different data needs
2. **Merge-upsert patterns** — SQL and ETL patterns that handle BOOKING re-imports without data loss
3. **Airbyte connector config** — Production-ready sync mode settings for the Navan source connector (v0.0.42)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

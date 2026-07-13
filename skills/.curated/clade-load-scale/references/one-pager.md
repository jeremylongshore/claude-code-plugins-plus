# clade-load-scale — One-Pager

Scale Claude API usage for high-throughput applications with batches, queues, and tier upgrades.

## The Problem

Applications that need to process thousands of Claude API requests hit rate limits quickly. Without a scaling strategy, you either get throttled at 50 RPM (Tier 1) or burn through budget inefficiently by sending requests one at a time at full price.

## The Solution

This skill provides four scaling strategies: Message Batches for bulk processing (up to 10K requests per batch at 50% off with no rate limits), concurrency-controlled request queues using p-limit, tier upgrades via cumulative spending, and model routing to Haiku for throughput-critical paths.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers building high-volume Claude integrations |
| **What** | Configures batch processing, concurrency control, tier upgrades, and throughput monitoring |
| **When** | When your application exceeds basic tier rate limits or processes bulk workloads |

## Key Features

1. **Message Batches** — Process up to 10K requests per batch at 50% cost reduction with no rate limits (24h SLA)
2. **Concurrency Control** — p-limit-based request queue that matches your rate limit tier to avoid 429 errors
3. **Tier Upgrade Path** — Clear qualification table from Tier 1 (50 RPM) through Scale tier (custom limits via sales)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

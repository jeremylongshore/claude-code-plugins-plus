# navan-performance-tuning — One-Pager

Optimizes Navan API call patterns with caching, batching, connection pooling, and pagination strategies for high-volume integrations.

## The Problem

High-volume Navan integrations — syncing thousands of bookings, expenses, or user records — quickly hit performance walls. Naive implementations make redundant API calls, ignore pagination cursors, and serialize requests that could run in parallel. The result is sync jobs that take hours instead of minutes, risk hitting rate limits, and create poor user experiences when dashboards load slowly.

## The Solution

This skill provides concrete optimization patterns for Navan's REST API: response caching with appropriate TTLs for different data types (bookings vs. user profiles vs. policies), parallel request execution with concurrency limits, cursor-based pagination handling, connection pooling for HTTP keep-alive, and batch request strategies. Each pattern includes before/after benchmarks and implementation code.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend engineers, platform teams building or maintaining high-volume Navan integrations |
| **What** | Caching layer with data-type-specific TTLs, parallel fetch orchestration, pagination utilities, connection pool configuration |
| **When** | Sync jobs exceeding SLA, approaching rate limits, scaling integration to more users, optimizing dashboard load times |

## Key Features

1. **Smart Caching** — TTL-based cache with appropriate lifetimes: 5 minutes for bookings, 1 hour for user profiles, 24 hours for policy data
2. **Parallel Fetch with Throttling** — Concurrent API requests bounded by configurable concurrency limits to maximize throughput without triggering rate limits
3. **Cursor Pagination Optimization** — Efficient page-through of large result sets with prefetch and early termination for filtered queries

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

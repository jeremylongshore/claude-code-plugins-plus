# navan-rate-limits — One-Pager

Implement defensive rate-limiting patterns for the Navan REST API, which has no publicly documented limits.

## The Problem

Navan does not publish official rate limit documentation. Developers discover limits the hard way — bulk data pulls suddenly return HTTP 429, batch user imports stall mid-run, and report generation scripts fail unpredictably. Without knowing the exact thresholds, teams need defensive patterns that adapt to server responses rather than relying on fixed quotas.

## The Solution

This skill provides adaptive rate-limiting strategies built around response header inspection, exponential backoff with jitter, and request queuing. Since Navan's limits are undocumented, the approach treats every 429 response as a learning signal — extracting Retry-After headers when present and falling back to exponential delays when they are not.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers running bulk operations, data syncs, or scheduled reports against the Navan API |
| **What** | Adaptive retry logic, request queue with concurrency control, bulk operation throttling patterns |
| **When** | Building batch data exports, syncing large traveler lists, running scheduled expense pulls, or after encountering 429 errors |

## Key Features

1. **Adaptive backoff** — Exponential retry with jitter that respects Retry-After headers when Navan provides them
2. **Request queue** — Concurrency-limited queue that prevents flooding the API during bulk operations
3. **Header inspection** — Automatic detection and logging of X-RateLimit-* and Retry-After response headers

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

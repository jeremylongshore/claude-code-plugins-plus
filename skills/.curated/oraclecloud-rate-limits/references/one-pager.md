# oraclecloud-rate-limits — One-Pager

Handle OCI API rate limits with defensive retry patterns and known limits by service.

## The Problem

OCI API rate limits vary by service and aren't well-documented. A 429 TooManyRequests kills your automation with no Retry-After header. Unlike AWS or Azure, you're flying blind on exactly when you'll be throttled, and the SDK's default behavior is no retry at all. Bulk operations (tag all instances, list all compartments) are especially vulnerable. This skill maps known limits by service and implements defensive retry patterns.

## The Solution

This skill provides an observed rate limits table by service (Compute, Object Storage, Identity, Database, Networking), exponential backoff with jitter for 429 handling, SDK-native RetryStrategyBuilder configuration, a circuit breaker pattern for bulk operations, and proactive batch throttling. All patterns use the OCI Python SDK with real class names.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and automation developers running bulk OCI operations or scheduled scripts |
| **What** | Resilient retry wrappers, SDK retry configuration, circuit breakers, and batch throttling for OCI API calls |
| **When** | Building automation that processes many resources, hitting 429 errors, or designing production-grade OCI integrations |

## Key Features

1. **Known limits table** — Observed rate limits by service (Compute, Object Storage, Identity, Database) with notes on shared vs per-user limits
2. **Exponential backoff with jitter** — Handles the missing Retry-After header with randomized delays to prevent thundering herd
3. **Circuit breaker pattern** — Stops cascading failures during bulk operations by pausing after consecutive throttle errors

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

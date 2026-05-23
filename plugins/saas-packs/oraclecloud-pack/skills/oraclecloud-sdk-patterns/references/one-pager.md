# oraclecloud-sdk-patterns — One-Pager

Production-grade OCI SDK patterns for client lifecycle, retry logic, and memory leak avoidance.

## The Problem

OCI has SDKs in 6 languages, each with different exception types, timeout behavior, and a known memory leak in Instance Principal authentication (~10 MiB/hour if clients are recreated per request). The Python SDK has no connection timeout by default — a hung connection blocks forever. The built-in retry strategy is opt-in, and 429 rate limit errors do not include a Retry-After header, so you must implement your own backoff. Pagination is manual unless you know about the underdocumented `oci.pagination` helpers.

## The Solution

This skill provides correct client lifecycle patterns that avoid the Instance Principal memory leak: a thread-safe singleton that creates clients once and reuses them. It covers explicit timeout configuration per service (Compute: 60s, Object Storage: 300s), exponential backoff with decorrelated jitter for rate limits, automatic and lazy pagination helpers, and composite operations that wait for resource state transitions.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers building long-running services or automation on OCI |
| **What** | Thread-safe singleton client, retry strategies, timeout config, pagination, and composite operations |
| **When** | Moving from prototype to production, debugging memory leaks, or handling intermittent 429/500 errors |

## Key Features

1. **Singleton pattern** — Thread-safe client reuse that prevents the Instance Principal memory leak
2. **Timeout configuration** — Explicit connect + read timeouts per service client
3. **Retry strategies** — Built-in DEFAULT_RETRY_STRATEGY and custom exponential backoff with jitter
4. **Pagination helpers** — `list_call_get_all_results` and lazy generator for memory-efficient iteration

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

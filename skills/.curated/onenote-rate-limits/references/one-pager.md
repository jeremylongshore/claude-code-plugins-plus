# OneNote Rate Limits — One-Pager

## The Problem

Microsoft Graph rate limits OneNote at 600 requests per 60 seconds per user and 10,000 requests per 10 minutes per app/tenant. When exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header in seconds (not milliseconds). Most implementations either ignore this header entirely — retrying immediately and compounding the problem — or use a fixed backoff that wastes capacity. After a 429, all OneNote endpoints for that user are throttled, not just the one that triggered it.

## The Solution

A token bucket rate limiter with queue-based request throttling that preemptively stays below the limit. Includes proper `Retry-After` header parsing, per-user and per-tenant tracking for multi-user apps, exponential backoff with jitter as a fallback, and batch request consolidation (20 operations per HTTP call). Also provides a monitoring system that dynamically adjusts throughput based on observed throttle rates.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building high-throughput OneNote integrations, bulk migration tools, or multi-user apps |
| **What** | Preemptive rate limiting, queue-based throttling, batch consolidation, and monitoring |
| **When** | Any integration making more than 100 OneNote API calls per minute, or serving multiple users |
| **Where** | Client-side middleware wrapping Microsoft Graph API calls to OneNote endpoints |
| **Why** | Aggressive 600/min per-user limit plus cross-endpoint throttling makes naive retry loops fatal |

## Key Differentiators

- Token bucket implementation prevents 429s preemptively rather than reacting to them
- Per-user AND per-tenant tracking for multi-user SaaS applications
- Budget allocation model that reserves capacity for polling alongside user-initiated operations
- Batch request pattern that reduces 100 API calls to 5 while staying within rate limits

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — app-only deprecated March 2025) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Queue (optional) | p-queue (Node) / asyncio (Python) |

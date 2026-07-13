# OneNote Cost Tuning — One-Pager

## The Problem

Microsoft Graph API calls for OneNote are included in M365 licenses with no per-request charge — but rate limits at 600 requests/user/minute and 10,000 requests/tenant/10 minutes create an effective cost ceiling. A naive integration that polls notebook metadata on every user interaction burns through the tenant limit with just 200 concurrent users. Every 429 response adds retry latency, and sustained throttling degrades user experience identically to a service outage. Developers often do not discover the tenant-level limit until production load testing because development environments never hit it.

## The Solution

This skill provides five concrete optimization strategies that reduce API call volume by 80-95%: metadata caching with 15-minute TTL (100 calls to 4), JSON batch requests via `$batch` (20 calls to 1), delta sync for incremental page updates (full list replaced by changes-only), payload minimization with `$select`/`$expand`, and content deduplication via hashing. Includes a cost modeling spreadsheet template to estimate calls-per-user-per-day and a monitoring framework with alert thresholds for throttle rate, latency, and per-user call volume.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Backend developers and platform engineers managing M365 integrations at scale |
| **What** | Caching, batching, delta sync, payload minimization, and API usage monitoring for OneNote |
| **When** | When approaching rate limits (429 errors), onboarding new user cohorts, or capacity planning |
| **Where** | Application service layer, HTTP client middleware, monitoring dashboards |
| **Why** | Rate limits act as a cost ceiling — exceeding them degrades UX identically to a service outage |

## Key Differentiators

- Quantifies savings for each strategy (e.g., metadata caching: 100 calls to 4; batching: 20 calls to 1)
- Includes a per-user-per-day cost modeling template with tenant capacity planning
- Monitoring framework with specific alert thresholds (throttle rate > 1%, latency > 2s, user > 300 calls/hr)
- Covers the tenant-level limit (10K/10min) that per-user testing never hits

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Batch Endpoint | `https://graph.microsoft.com/v1.0/$batch` |
| Monitoring | Custom ApiMetrics class with throttle/latency tracking |

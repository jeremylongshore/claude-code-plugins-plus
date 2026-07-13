# OneNote Webhooks & Events — One-Pager

## The Problem

OneNote webhooks were decommissioned June 16, 2023. The Graph subscription API (`POST /subscriptions` on OneNote resources) returns `400 Bad Request`. Unlike Outlook, calendar, and OneDrive — which all still support push notifications — OneNote has no webhook replacement. Every tutorial and StackOverflow answer referencing OneNote webhooks is outdated. You must poll, and polling must respect the 600 requests/minute per-user rate limit.

## The Solution

A polling-based change detection system using `lastModifiedDateTime` watermarks and tiered poll intervals. Includes a TypeScript `OneNotePoller` class, Python async equivalent, rate budget planning tables, and an event processing pipeline for decoupling detection from handling. The tiered approach polls recently-active sections every 15 seconds while checking stale sections only every 10 minutes.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building sync engines, change monitors, or event-driven integrations with OneNote |
| **What** | Polling-based change detection with tiered intervals, watermark tracking, and event processing |
| **When** | Any time you need near-real-time awareness of OneNote content changes |
| **Where** | Microsoft Graph API v1.0 page listing endpoints with `$filter` on `lastModifiedDateTime` |
| **Why** | Webhooks decommissioned June 2023 — polling is the only option, and naive polling burns rate budget |

## Key Differentiators

- Explicit warning that OneNote webhooks are dead — with the exact decommission date and error behavior
- Rate budget planning table showing requests/minute for different section counts and intervals
- Tiered polling (hot/warm/cold) that adapts frequency based on section activity
- Event processing pipeline pattern for decoupling change detection from business logic

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — app-only deprecated March 2025) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| State Store | Redis, SQLite, or file system (for watermark persistence) |

# navan-core-workflow-a — One-Pager

Manage the complete travel booking lifecycle through the Navan REST API, from trip search to itinerary retrieval and cancellation handling.

## The Problem

Corporate travel teams rely on the Navan web UI to search, book, and manage employee trips. When building internal tools, dashboards, or approval automations, developers need to replicate these workflows programmatically. But Navan has no SDK — only a set of REST endpoints behind OAuth 2.0. The help center docs are fragmented, and the relationship between booking UUIDs, trip objects, and itinerary PDFs is not obvious.

## The Solution

This skill provides the complete travel booking workflow via raw REST calls: authenticating with OAuth 2.0, retrieving trips with GET /get_user_trips and GET /get_admin_trips, downloading itinerary PDFs with GET /get_itineraries_pdf, and pulling invoices with GET /get_invoices_poc. Each step uses real endpoints with proper error handling and policy-compliance awareness.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers building travel dashboards, approval bots, or ERP integrations |
| **What** | Working REST API calls for trip retrieval, itinerary downloads, and invoice access |
| **When** | Building a travel management integration, automating trip reporting, or syncing booking data to internal systems |

## Key Features

1. **Full trip lifecycle** — Retrieve, filter, and manage trips across user and admin scopes
2. **Itinerary PDF export** — Download formatted itinerary documents via the API
3. **Invoice retrieval** — Pull invoices for reconciliation with finance systems

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

# OneNote Core Workflow B — One-Pager

## The Problem

OneNote's dedicated search endpoint was deprecated in April 2024. The replacement uses OData `$filter` queries that can only search metadata fields (title, dates) — not page body content. There is no single endpoint to search across all notebooks. Deleted pages continue appearing in list results for up to 30 minutes, and the `@odata.nextLink` pagination token is sometimes omitted by the Graph API even when more results exist.

## The Solution

Production-tested patterns for content discovery in OneNote: OData filter queries for metadata search, cross-notebook iteration with caching, client-side full-text search using Fuse.js, safe pagination with guard rails for missing `@odata.nextLink`, and deleted page filtering. Includes both TypeScript and Python implementations.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building search, content indexing, or reporting features on OneNote data |
| **What** | Cross-notebook search, OData filtering, paginated queries, and deleted page detection |
| **When** | Any time you need to find, list, or iterate OneNote pages — especially across multiple notebooks |
| **Where** | Microsoft Graph API v1.0 `/me/onenote/pages` and `/me/onenote/sections/{id}/pages` endpoints |
| **Why** | Deprecated search endpoint, missing pagination links, and ghost deleted pages break production integrations |

## Key Differentiators

- Explicitly warns about the April 2024 search deprecation that most tutorials still reference
- Provides a cross-notebook search pattern since no single-query solution exists
- Implements pagination safety limits for the missing `@odata.nextLink` Graph bug
- Includes client-side Fuse.js search for body content that OData cannot filter

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — app-only deprecated March 2025) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Client Search | Fuse.js (TypeScript) / thefuzz (Python) |

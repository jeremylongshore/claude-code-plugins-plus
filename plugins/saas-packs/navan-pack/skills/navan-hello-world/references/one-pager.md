# navan-hello-world — One-Pager

Make your first successful Navan API call to retrieve trip data using OAuth 2.0 bearer tokens.

## The Problem

After setting up Navan OAuth credentials, developers have no quickstart example showing how to actually call the API. The Navan docs are scattered across help center articles, and the available endpoints (get_user_trips, get_admin_trips, get_users) are not well-documented with request/response shapes. Developers need a working "hello world" to confirm their integration works end-to-end.

## The Solution

This skill provides a complete first-call workflow: acquire an OAuth token, call GET /get_user_trips, and parse the response including the uuid primary key. Both TypeScript and Python examples are included, with real response field handling and error checking.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers who have completed navan-install-auth and want to verify their integration |
| **What** | Working API calls to retrieve trip data with typed response parsing |
| **When** | After initial credential setup, when validating API connectivity, or when exploring available endpoints |

## Key Features

1. **Token-to-data pipeline** — Complete flow from OAuth token acquisition to parsed trip data
2. **Dual-language examples** — TypeScript (fetch) and Python (requests) with real endpoint URLs
3. **Response field mapping** — Documents actual response structure including uuid primary keys

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

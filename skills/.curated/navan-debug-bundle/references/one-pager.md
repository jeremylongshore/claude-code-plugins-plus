# navan-debug-bundle — One-Pager

Collects diagnostic data from Navan API integrations into a structured debug bundle for rapid troubleshooting.

## The Problem

When Navan API integrations fail, engineers waste hours manually testing endpoints, inspecting OAuth tokens, and correlating request/response logs across scattered systems. Without a systematic diagnostic collection process, root cause analysis is slow and inconsistent, especially when credentials are only viewable once during initial setup.

## The Solution

This skill automates diagnostic data collection from Navan REST API integrations. It captures OAuth token state, API response codes, request/response pairs, connectivity test results, and environment configuration into a single timestamped bundle that can be shared with support or used for offline analysis.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Integration engineers, DevOps, on-call responders debugging Navan API issues |
| **What** | Timestamped debug bundle with OAuth status, API responses, connectivity tests, and environment config |
| **When** | API calls returning unexpected errors, OAuth token refresh failures, intermittent connectivity issues, pre-escalation to Navan support |

## Key Features

1. **OAuth Token Inspection** — Validates token expiry, refresh state, and grant type without exposing credentials
2. **API Endpoint Probing** — Tests /authenticate, /get_users, /get_user_trips with curl and captures full response headers and bodies
3. **Bundle Packaging** — Compresses all diagnostic artifacts into a single tarball with sanitized secrets for safe sharing

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.

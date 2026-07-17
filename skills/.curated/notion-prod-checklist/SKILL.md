---
name: notion-prod-checklist
description: |
  Execute a Notion API production deployment checklist and readiness verification.
  Use when deploying Notion integrations to production, preparing for launch,
  verifying go-live readiness, or auditing an existing Notion integration.
  Trigger with "notion production checklist", "deploy notion integration",
  "notion go-live", "notion launch readiness", "notion prod audit".
allowed-tools: Read, Write, Bash(grep:*), Bash(curl:*), Bash(jq:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- deployment
- checklist
compatibility: Designed for Claude Code
---
# Notion API Production Deployment Checklist

## Overview

A structured 12-section checklist for deploying Notion API integrations to production, covering authentication security, capability scoping, page sharing, rate limits, pagination, error handling, versioning, retries, monitoring, graceful degradation, data validation, and OAuth token lifecycle. Each section maps to a specific failure mode seen in production Notion integrations, and every item is testable — the skill produces a verified pass/fail report, not aspirational guidance.

## Prerequisites

- **Node.js 18+** with `@notionhq/client` v2.x installed
- Working Notion integration tested in a development workspace
- Production Notion API token (internal) or OAuth credentials (public integration)
- Target databases and pages identified by ID
- Deployment platform configured (Vercel, Railway, AWS, etc.)

Verify SDK is installed:

```bash
node -e "const { Client } = require('@notionhq/client'); console.log('SDK loaded')" 2>/dev/null \
  || echo "MISSING: npm install @notionhq/client"
```

## Instructions

Work through the checklist in order, marking each item pass or fail. **A single fail in sections 1-6 is a deployment blocker.**

1. **Run the pre-deploy smoke test** (see [Examples](#examples)) to confirm the token is set, auth works, and target databases are reachable. This catches the most common failure — a page that is not shared with the integration — before you go deeper.
2. **Grade each of the 12 sections** against its checkbox items. The summary table below is the map; the full item-by-item detail, fail criteria, and code snippets live in [references/checklist-sections.md](references/checklist-sections.md).
3. **Pull implementation patterns** (rate-limited queue, paginator, typed error handler, retry, cache fallback, property validator, OAuth exchange) from [references/code-examples.md](references/code-examples.md) as each section requires them.
4. **Record a pass/fail per section** and total the blocking (1-6) vs non-blocking (7-12) failures.
5. **Emit the readiness report** (see [Output](#output)) with the final verdict: ready to deploy, or blocked with the count of items to fix.

### The 12 sections at a glance

| # | Section | Blocking? | Fails if |
| --- | --- | --- | --- |
| 1 | Token in env vars (never hardcoded) | Yes | Token found in source, git history, or client bundle |
| 2 | Minimum required capabilities | Yes | Integration has scopes it does not use |
| 3 | Target pages/DBs shared with integration | Yes | Any target returns 404 `object_not_found` |
| 4 | Rate limit handling (3 req/sec, backoff) | Yes | Any path issues >3 concurrent requests unqueued |
| 5 | Pagination for all list endpoints | Yes | Any list endpoint skips the `has_more` loop |
| 6 | Error handling with `isNotionClientError` | Yes | Bare `catch` that loses error context |
| 7 | `Notion-Version` header pinned (2022-06-28) | No | Client created without explicit `notionVersion` |
| 8 | Retry logic for 429/500/503 | No | Retries 400/401/404, or no retry on 429/5xx |
| 9 | Monitoring for API failures | No | No alerting on auth failures or sustained errors |
| 10 | Graceful degradation when Notion is down | No | Returns 500 to users when the API is unreachable |
| 11 | Data validation for property types | No | 400 validation errors from unvalidated property data |
| 12 | OAuth token refresh (public integrations) | No | Tokens stored plaintext, or no 401 revocation handling |

Full detail for every section — all checkbox items, capability/alert tables, and inline snippets — is in [references/checklist-sections.md](references/checklist-sections.md).

## Output

After completing all 12 sections, produce a deployment readiness report:

```
NOTION PRODUCTION READINESS REPORT
===================================
Date: YYYY-MM-DD
Integration: [integration name]
Environment: [production|staging]

Section 1:  Token Security          [PASS/FAIL]
Section 2:  Capability Scoping      [PASS/FAIL]
Section 3:  Page/DB Sharing         [PASS/FAIL]
Section 4:  Rate Limit Handling     [PASS/FAIL]
Section 5:  Pagination              [PASS/FAIL]
Section 6:  Error Handling          [PASS/FAIL]
Section 7:  API Version Pinned     [PASS/FAIL]
Section 8:  Retry Logic             [PASS/FAIL]
Section 9:  Monitoring              [PASS/FAIL]
Section 10: Graceful Degradation    [PASS/FAIL]
Section 11: Data Validation         [PASS/FAIL]
Section 12: OAuth (if applicable)   [PASS/FAIL/N/A]

BLOCKING FAILURES (Sections 1-6): [count]
NON-BLOCKING ISSUES (Sections 7-12): [count]

VERDICT: [READY TO DEPLOY / BLOCKED — fix N items]
```

## Error Handling

| Scenario | Detection | Response |
| --- | --- | --- |
| Token not in env vars | `process.env.NOTION_TOKEN` is undefined | Abort deploy, log setup instructions |
| Page not shared | 404 `object_not_found` on retrieve | List unshared targets, block deploy |
| Rate limit exceeded | 429 response despite queueing | Reduce concurrency, check for competing integrations |
| Validation error (400) | `isNotionClientError` with `validation_error` | Log full error body, fix property data |
| Auth failure (401) | `isNotionClientError` with `unauthorized` | Alert ops, rotate token, re-deploy |
| Notion outage (5xx) | Multiple 500/502/503 in sequence | Activate cache/fallback mode |
| Property type mismatch | 400 on `pages.create` or `pages.update` | Run property validator, fix schema mapping |
| Pagination missed | Query returns exactly 100 results | Audit code for missing `has_more` loops |

## Examples

### Pre-Deploy Smoke Test Script

Run this first — it validates the token, auth, and target-database access in seconds.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Notion Production Smoke Test ==="

# 1. Token is set
if [ -z "${NOTION_TOKEN:-}" ]; then
  echo "FAIL: NOTION_TOKEN not set"
  exit 1
fi
echo "PASS: NOTION_TOKEN is set (${#NOTION_TOKEN} chars)"

# 2. Token works (auth check)
AUTH_RESULT=$(curl -s -w "\n%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28")

HTTP_CODE=$(echo "$AUTH_RESULT" | tail -1)
BODY=$(echo "$AUTH_RESULT" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  BOT_NAME=$(echo "$BODY" | jq -r '.name // "unknown"')
  echo "PASS: Auth OK — bot name: $BOT_NAME"
else
  echo "FAIL: Auth returned HTTP $HTTP_CODE"
  echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
  exit 1
fi

# 3. Target database accessible (set NOTION_TARGET_DB to test)
DB_ID="${NOTION_TARGET_DB:-}"
if [ -n "$DB_ID" ]; then
  DB_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.notion.com/v1/databases/${DB_ID}" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28")

  if [ "$DB_RESULT" = "200" ]; then
    echo "PASS: Target database accessible"
  else
    echo "FAIL: Target database returned HTTP $DB_RESULT — is it shared with the integration?"
    exit 1
  fi
fi

echo "=== Smoke Test Complete ==="
```

### Production Client Initialization

See [full production initialization](references/code-examples.md) for complete setup with rate limiting, version pinning, and log levels. For the per-section snippets (paginator, typed error handler, retry, cache fallback, property validator, OAuth exchange), see [references/code-examples.md](references/code-examples.md).

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro) — Complete endpoint documentation
- [Notion API Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys) — Official key management guide
- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per integration
- Notion API Changelog — Version differences and migration guides
- [Notion Status Page](https://status.notion.com) — Real-time API availability
- [`@notionhq/client` on npm](https://www.npmjs.com/package/@notionhq/client) — Official SDK documentation
- [Notion OAuth Documentation](https://developers.notion.com/docs/authorization) — Public integration auth flow

## Next Steps

After passing the production checklist, continue with related skills for ongoing operations. For initial setup and authentication, see `notion-install-auth`. For rate limit deep-dive, see `notion-rate-limits`. For error troubleshooting, see `notion-common-errors`. For incident response, see `notion-incident-runbook`. For API version migration, see `notion-upgrade-migration`. For monitoring setup, see `notion-observability`.

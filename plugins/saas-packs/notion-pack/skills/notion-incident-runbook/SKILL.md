---
name: notion-incident-runbook
description: |
  Execute Notion incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Notion API outages, investigating errors, or running
  post-incident reviews for Notion integration failures. Trigger with phrases like
  "notion incident", "notion outage", "notion down", "notion on-call",
  "notion emergency", "notion broken".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Incident Runbook

## Overview

Rapid incident response for Notion API failures. This runbook drives a sub-5-minute
triage that classifies the failure as Notion-side vs. integration-side, then routes to
per-error-type mitigation, cached fallback, and a structured postmortem.

Deep material — full triage scripts, remediation code, and templates — lives in
`references/`; this file is the high-level flow you follow live.

## Prerequisites

- Access to application monitoring dashboards and log aggregator
- `NOTION_TOKEN` environment variable set for diagnostic API calls
- `curl` and `jq` installed for quick CLI triage
- Python alternative: `notion-client` (`pip install notion-client`)
- Communication channels configured (Slack webhook, PagerDuty, etc.)

## Instructions

### Step 1: Quick Triage (Under 5 Minutes)

At first alert, decide whether the fault is Notion's or yours. Check the platform
status page, then test your own auth. This one call is enough to start:

```bash
curl -sf -o /dev/null -w "%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28"   # 2022-06-28 = pinned Notion API version
```

Map the result: `200` → integration-side, `401` → token expired/revoked, `429` →
rate limited, `000` → network/DNS. If `status.notion.so` shows an active incident, it
is Notion-side regardless of your auth code.

Read [references/triage.md](references/triage.md) for the full `notion-triage.sh`
diagnostic (status page + auth + DB-query latency + auto-classification) and a
TypeScript `triageNotionHealth()` equivalent for in-app health checks.

### Step 2: Decision Tree and Mitigation

Route the classification to a remediation path:

- **Notion-side outage** — enable cached/fallback mode, notify users, monitor the
  status page. Do NOT restart or rotate tokens.
- **401 token expired/revoked** — regenerate at `notion.so/my-integrations`, update the
  secret manager, restart the app.
- **429 rate limited** — you are exceeding the 3 req/s average; find runaway loops or
  webhook storms, drop concurrency to 1, add exponential backoff.
- **404 on known resources** — pages unshared or trashed; re-share via the Connections menu.
- **400 validation errors** — the database schema changed in the UI; re-fetch with
  `databases.retrieve` and update property mappings.

Read [references/mitigation.md](references/mitigation.md) for the full decision tree,
token-rotation commands (AWS/GCP Secret Manager + `kubectl` restart), the
`queryWithFallback()` cached-fallback pattern, and `detectSchemaChanges()`.

### Step 3: Communication and Postmortem

Post an internal Slack update on every state change (INVESTIGATING → MITIGATING →
RESOLVED), an external status-page notice if users are impacted, and file a structured
postmortem once resolved. Copy-paste templates for all three are in
[references/communication-and-postmortem.md](references/communication-and-postmortem.md).

## Output

- Automated triage script classifying incidents in under 5 minutes
- Decision tree mapping HTTP status codes to root causes
- Per-error-type mitigation procedures with real code
- Cached fallback mode for Notion outages
- Schema change detection for 400 validation errors
- Communication templates for internal and external stakeholders
- Postmortem template with timeline and action items

## Error Handling

| Scenario | Triage Signal | Immediate Action |
| ---------- | -------------- | ------------------ |
| Notion platform outage | status.notion.so incident | Enable fallback mode, notify users |
| Token expired/revoked | All requests return 401 | Rotate token in secret manager, restart |
| Rate limited | 429 errors spiking | Reduce concurrency to 1, check for loops |
| Schema changed | 400 on specific operations | Run `databases.retrieve`, update mappings |
| Network/DNS issue | Timeouts, no HTTP response | Check firewall, DNS resolution, proxy config |
| Pages unshared | 404 on previously working pages | Re-share via Connections menu in Notion |

## Examples

### One-Line Health Check

```bash
curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq '{name: .name, type: .type}' \
  || echo "UNHEALTHY: Notion API unreachable or auth failed"
```

### Python Quick Triage

```python
from notion_client import Client, APIResponseError
import os

def quick_triage():
    try:
        client = Client(auth=os.environ["NOTION_TOKEN"], timeout_ms=10_000)
        me = client.users.me()
        print(f"OK: Connected as {me['name']}")
    except APIResponseError as e:
        print(f"ERROR: {e.code} (HTTP {e.status}): {e.message}")
    except Exception as e:
        print(f"NETWORK ERROR: {e}")

quick_triage()
```

For the full `notion-triage.sh` diagnostic and the TypeScript in-app variant, see
[references/triage.md](references/triage.md).

## Resources

- [Notion Status Page](https://status.notion.so) — real-time platform status
- [Notion API Error Codes](https://developers.notion.com/reference/errors) — full error reference
- [Notion Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/s average
- [Statuspage API](https://www.atlassianstatuspage.io/api) — programmatic status checks
- For data handling and privacy compliance, see the `notion-data-handling` skill.

---
name: klaviyo-incident-runbook
description: |
  Execute Klaviyo incident response procedures with triage, mitigation, and postmortem.

  Use when responding to Klaviyo-related outages, investigating API errors (401/403/429/5xx),
  or running post-incident reviews for Klaviyo integration failures on an on-call rotation.

  Trigger with phrases like "klaviyo incident", "klaviyo outage", "klaviyo down",
  "klaviyo on-call", "klaviyo emergency", "klaviyo broken".
allowed-tools: Read, Bash(curl:*), Bash(kubectl:*), Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Incident Runbook

## Overview

Rapid incident response for Klaviyo API outages and integration failures: quick
triage, decision trees, mitigation steps, and postmortem templates. Use this
skill to move from "Klaviyo is broken" to a classified severity, an applied
mitigation, and a written postmortem — without improvising under pressure.

The heavy content (full triage script, per-error remediation blocks, and the
communication + postmortem templates) lives in `references/` so this file stays
a fast high-level runbook you can follow end-to-end, then drill into for depth.

## Prerequisites

- `KLAVIYO_PRIVATE_KEY` exported in the shell (a private API key, `pk_...`).
- `curl` and `python3` available for the triage and monitoring commands.
- Read access to your app's health endpoint and, ideally, its Prometheus metrics.
- Access to the [Klaviyo dashboard](https://www.klaviyo.com) to rotate a key if needed.
- Klaviyo's `revision` header value your app ships (this runbook pins `2024-10-15`,
  a dated stable API version — Klaviyo requires the header on every request).

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | Complete outage | <15 min | All Klaviyo API calls returning 5xx |
| P2 | Degraded service | <1 hour | 429 rate limiting, high latency |
| P3 | Minor impact | <4 hours | Webhook delays, single endpoint errors |
| P4 | No user impact | Next business day | Monitoring gaps, deprecation warnings |

## Instructions

Work the incident in five steps. Each step points at the reference file that
carries the full, copy-paste-ready detail.

1. **Triage immediately.** Run the quick-triage script to answer the four
   questions that classify every Klaviyo incident: Is Klaviyo itself down? Can
   we authenticate? Are we rate limited? Is our app healthy? See the full script
   in [references/triage.md](references/triage.md).
2. **Classify the failure.** Walk the decision tree in
   [references/triage.md](references/triage.md) to split a Klaviyo-side outage
   (status page shows an incident → enable fallback, monitor, communicate) from
   an integration issue (route by status code: 401/403, 429, 400, 5xx).
3. **Assign a severity** from the table above and set the response-time clock.
4. **Apply the remediation** for the observed error type — auth failure (401),
   rate limit (429), or Klaviyo server error (5xx). The exact commands are in
   [references/remediation.md](references/remediation.md).
5. **Communicate and write the postmortem.** Post the internal + external
   updates and, once resolved, collect evidence and fill the postmortem template
   from [references/communication-and-postmortem.md](references/communication-and-postmortem.md).

## Output

Following this runbook produces:

- A **triage report** printed to the terminal: Klaviyo status-page state, your
  API auth HTTP code, current rate-limit headers, and app health.
- A **severity classification** (P1–P4) with the matching response-time target.
- An **applied mitigation** (key rotation, concurrency reduction, or graceful
  degradation) with confirmation the error rate is recovering.
- **Stakeholder updates** — one internal Slack message and, for P1/P2, one
  external status-page note.
- A **completed postmortem** document (summary, timeline, root cause, impact,
  action items, lessons learned) plus an evidence bundle of logs and metrics.

## Examples

**Triage first (always run this before anything else):**

```bash
# Is Klaviyo itself down, or is it us?
curl -s "https://status.klaviyo.com/api/v2/status.json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['description'])"
```

**Then classify by the auth HTTP code:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"
# 401 → key problem  ·  429 → rate limited  ·  5xx → Klaviyo server error
```

For the complete triage script and decision tree see
[references/triage.md](references/triage.md); for the full per-error remediation
commands see [references/remediation.md](references/remediation.md); for the
Slack/status-page templates and the postmortem template see
[references/communication-and-postmortem.md](references/communication-and-postmortem.md).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or check Twitter @klaviyo |
| Metrics unavailable | Prometheus down | Check direct API with cURL |
| Key rotation panic | No backup key | Always have a rotation procedure documented |
| Alert fatigue | Too many false alarms | Tune thresholds based on baseline |

## Resources

- [Triage script and decision tree](references/triage.md)
- [Per-error remediation (401 / 429 / 5xx)](references/remediation.md)
- [Communication templates and postmortem](references/communication-and-postmortem.md)
- [Klaviyo Status Page](https://status.klaviyo.com)
- [Klaviyo API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)
- For data handling, see the `klaviyo-data-handling` skill.

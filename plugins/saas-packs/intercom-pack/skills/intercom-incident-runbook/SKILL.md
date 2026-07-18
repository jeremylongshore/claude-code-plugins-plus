---
name: intercom-incident-runbook
description: |
  Execute Intercom incident response procedures with triage, mitigation, and postmortem.

  Use when responding to Intercom API outages, investigating integration errors,
  or running post-incident reviews for Intercom failures.

  Trigger with phrases like "intercom incident", "intercom outage",
  "intercom down", "intercom on-call", "intercom emergency", "intercom broken".
allowed-tools: Bash(curl:*), Bash(kubectl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Incident Runbook

## Overview

Rapid incident response procedures for Intercom integration failures. The runbook
takes you from alert to resolution in four phases — triage, decision, mitigation,
and postmortem — with HTTP-status-code-driven branching so you always know whether
the fault is yours or Intercom's. High-level workflow lives here; the full
copy-paste scripts and templates live in `references/`.

## Prerequisites

- `INTERCOM_ACCESS_TOKEN` exported in your shell (a workspace admin token).
- `curl` and `jq` installed for API + status-page probing.
- `kubectl` access to the deployment running your Intercom integration (for restarts).
- Access to your secret manager (e.g. AWS Secrets Manager) to rotate a compromised token.
- Developer Hub access for the Intercom app, or a path to escalate to a workspace admin.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | All Intercom API calls failing | < 15 min | 401 auth failures, API unreachable |
| P2 | Degraded service | < 1 hour | High latency, rate limited (429) |
| P3 | Partial impact | < 4 hours | Webhook delays, search timeouts |
| P4 | No user impact | Next business day | Monitoring gaps, stale cache |

## Instructions

Work the phases in order. Each phase links to the full reference when you need depth.

1. **Assign severity.** Match the symptom to the table above; this sets your clock
   and who you page.

2. **Triage — is it you or Intercom?** Run the first probe to confirm reachability:

   ```bash
   curl -s -o /dev/null -w "%{http_code}" \
     -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
     https://api.intercom.io/me
   ```

   Then check `status.intercom.com` for a platform incident and read the rate-limit
   headers. The full 5-step diagnostic script and the branch-by-branch decision tree
   are in [references/triage.md](references/triage.md).

3. **Decide.** If Intercom reports an incident, it is their problem — enable graceful
   degradation and monitor. If not, it is your integration; branch on the status code:
   401 → rotate token, 403 → add OAuth scope, 429 → queue/backoff, 5xx → retry with backoff.

4. **Mitigate by error type.** Apply the matching remediation — token rotation for 401,
   volume reduction for 429, cached-data fallback for 5xx. Full commands (including the
   `aws secretsmanager` rotation and the `kubectl rollout restart`) plus the TypeScript
   graceful-degradation pattern are in [references/mitigation.md](references/mitigation.md).

5. **Communicate.** Post the internal Slack status update on a fixed cadence using the
   template in [references/templates.md](references/templates.md).

6. **Write the postmortem.** After resolution, fill in the postmortem template
   (timeline, root cause, impact counts, action items) from
   [references/templates.md](references/templates.md). Always record Intercom
   `request_id`s captured during the incident — Intercom support needs them.

## Output

Working through the runbook produces:

- A **severity classification** (P1–P4) with a bounded response clock.
- A **fault verdict** — Intercom-side platform incident vs. your integration — backed by
  the triage script's HTTP codes, status-page state, and rate-limit headers.
- A **mitigation applied** for the specific error class (rotated token, paused sync jobs,
  enabled cache fallback, or retry/backoff).
- A **communication trail** — timestamped Slack updates on cadence.
- A **completed postmortem** with timeline, root cause, impact counts, captured Intercom
  `request_id`s, and owned action items.

## Examples

**Fast triage during a suspected outage** — confirm reachability, then check the platform:

```bash
curl -s -o /dev/null -w "API=%{http_code}\n" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" https://api.intercom.io/me
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.description'
```

A `401` with a green status page means your token, not Intercom — jump to the 401
mitigation. The full 5-step diagnostic, the decision tree, per-status mitigation
commands, and the Slack/postmortem templates are all in `references/`:

- [references/triage.md](references/triage.md) — full triage script + decision tree
- [references/mitigation.md](references/mitigation.md) — 401 / 429 / 5xx remediation + graceful degradation
- [references/templates.md](references/templates.md) — Slack update + postmortem templates

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Triage script fails | Token not set | Export INTERCOM_ACCESS_TOKEN |
| Status page unreachable | DNS/network | Try mobile network or VPN |
| Can't rotate token | No Developer Hub access | Escalate to workspace admin |
| Cache empty during outage | No pre-warming | Implement cache warming job |

## Resources

- [Intercom Status Page](https://status.intercom.com)
- [Intercom Status API](https://status.intercom.com/api)
- [Error Codes](https://developers.intercom.com/docs/references/rest-api/errors/error-codes)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)

For data handling compliance, see `intercom-data-handling`.

---
name: guidewire-observability-and-incident-response
description: Operate a Guidewire Cloud API integration in production — define SLIs/SLOs for token availability, bind success rate, FNOL p99 latency; route alerts so the on-call gets paged for real outages and never for transient noise; triage 401 spikes, 409 storms, 429 saturation, scope drift, and Gosu OOM cascades from signal to recovery in 15 minutes or less. Use when designing a dashboard for a new integration, writing the on-call runbook, or running a post-incident review. Trigger with "guidewire observability", "guidewire slo", "guidewire on-call", "guidewire 401 spike", "guidewire 409 storm", "guidewire incident".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep, Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - observability
  - sli-slo
  - incident-response
  - on-call
  - runbook
---

# Guidewire Observability and Incident Response

## Overview

Run a production Guidewire Cloud API integration with the dashboards, alerts, and runbooks an on-call engineer can act on at 3am. This skill consolidates the operational layer: what to measure, what to alert on, how to triage the top five incident classes, and how to close the loop with a post-incident review that prevents recurrence rather than performing root-cause theater.

Five operational failures this skill prevents:

1. **Vanity dashboards** — graphs of total request count, no per-endpoint p99, no SLI burn rate; on-call sees green during a real outage because the right thing was never measured.
2. **Alert fatigue** — every transient `5xx` pages someone; in three weeks the team mutes the channel; a real incident two weeks later goes unnoticed for an hour.
3. **No triage tree** — on-call wakes up to "401 spike", does not know whether to rotate a secret, restart the integration, or call GCC; loses 20 minutes Googling.
4. **Skipped post-incident review** — the same root cause produces three incidents in a quarter because no one wrote down the action items from the first one.
5. **Common-errors table living in nine Slack threads** — operators cannot find the recovery for an error they have seen before, ask the same question in #ops, the answer takes 45 minutes.

## Prerequisites

- A working integration emitting structured logs and metrics to a backend (Datadog, Grafana+Prometheus, New Relic, Splunk, or equivalent)
- Access to a paging system (PagerDuty, Opsgenie, VictorOps) with on-call rotations defined
- The `integration_audit` table from `guidewire-security-and-rbac` populated — incident triage depends on knowing what the integration tried to do
- `correlation_id` propagated end-to-end through every Cloud API call

## Instructions

Build the operational layer in this order. Each step targets one of the five operational failures listed in Overview.

### 1. Define SLIs that measure user-visible behavior

Track what users care about, not what is easy to measure. For a Guidewire integration, the SLIs that matter:

| SLI | Measurement | Target |
|---|---|---|
| Token-endpoint availability | success rate of `/oauth/token` over a rolling 5min window | ≥99.9% |
| Cloud API write success | `2xx` rate on POST/PATCH calls, excluding 4xx caller errors | ≥99.5% |
| Bind success rate | `bound` / `quoted` ratio over rolling 1h, excluding referrals | ≥98% |
| FNOL intake p99 latency | end-to-end time from inbound event to `claim.created` log | ≤2s |
| Quote-to-bind median latency | median time from quote-call to bind-success | ≤30s |

`5xx` from upstream Cloud API counts against availability; `4xx` from caller bugs (validation failures, scope mismatches) does not — those are caller errors, not integration outages. Distinguishing the two is the single biggest cause of either alert fatigue or missed incidents, depending on which way the bias goes.

### 2. Burn-rate-based alerting, not threshold alerting

Alerting on "error rate > 1%" pages the on-call every time a transient `502` happens. Alert on **SLO burn rate** instead — the rate at which the error budget is being consumed.

```
Fast burn:   2% error budget consumed in 1 hour       → page immediately
Slow burn:   5% error budget consumed in 6 hours      → page during business hours
Trickle:     10% error budget consumed in 3 days      → ticket, not page
```

A 5-minute outage that consumes 1% of the monthly budget should not page; a 20-minute outage that consumes 4% should. Burn-rate alerts encode this naturally.

### 3. Top-five triage trees

Each tree is the ~5-step decision sequence on-call follows from signal to recovery. Memorize the entry signal; the body is in the runbook.

**T1: 401 spike on Cloud API calls**

```
401s > 1% for 5min
├─ Check token age in cache: is the integration refreshing? → if no, restart token-cache process
├─ Decode a recent token, verify exp > now + 60s         → if no, clock skew or aggressive proxy caching
├─ Check GCC: is the Service Application enabled?         → if no, talk to tenant admin
└─ Check secret-rotation history: was a secret rotated in the last 24h? → if yes, run dual-secret swap or restart
```

**T2: 409 storm on PATCH calls**

```
409s > 5% for 5min
├─ Are concurrent writers expected? → if yes, scale checksum round-trip retry budget
├─ Is one resource-id producing all 409s? → if yes, it's a hot key; coordinate writes via queue
└─ Is the client retrying the bare PATCH instead of the GET-PATCH cycle? → fix the retry layer
```

**T3: 429 saturation on Cloud API or Hub**

```
429s > 1% for 10min
├─ Is the Hub /oauth/token endpoint 429ing? → token cache missing single-flight gate; deploy fix immediately
├─ Is the data-plane API 429ing? → check tenant quota in GCC, request increase if legitimate growth
└─ Is one customer driving the saturation? → tenant-side rate limit on the integration's intake
```

**T4: Scope drift detected**

```
Scope-drift alert from auth refresh
├─ What scope is missing? → check GCC > Identity & Access > Applications > [app] > Permissions
├─ Was a permission removed by a tenant admin? → coordinate; restore or accept loss of capability
└─ Was a scope renamed in a tenant config push? → update GW_SCOPES env, redeploy
```

**T5: GUnit / runServer OOM (dev or staging)**

```
OOMKilled or heap dump generated
├─ Is sample data set abnormally large? → reset dev DB, reload fixtures
├─ Is a recent change loading too many entities (no pagination, no filter)? → revert; add limit
└─ Is the JVM under-provisioned? → bump -Xmx in gradle.properties; restart
```

### 4. Recovery playbooks (top 5 incident classes)

Each playbook is one page in the on-call runbook. Concrete commands, not prose.

```markdown
## Playbook: 401 spike — secret rotation suspected
1. Rotate in GCC > Identity & Access > Applications > [app] > Generate Secret
2. sops secrets.prod.<tenant>.sops.yaml  # set new GW_CLIENT_SECRET (and SECONDARY = old)
3. git commit -m "rotate(secrets): incident-driven rotation $(date -Iseconds)"
4. Trigger deploy of token service
5. Confirm token claims show iat > rotation timestamp: kubectl exec ... -- /token-debug
6. After 24h zero failures from primary: remove SECONDARY
7. Open audit row with reason="incident-401-spike"
```

Each playbook ends with an audit-row insert so the next post-incident review has the full timeline.

### 5. Post-incident review template (PIR)

```markdown
# PIR: <date> — <one-line summary>

## Timeline
- HH:MM — first signal (alert link, dashboard screenshot)
- HH:MM — on-call paged
- HH:MM — root cause identified
- HH:MM — mitigation applied
- HH:MM — confirmation of recovery

## SLO impact
- Error budget consumed: X%
- Customer-impacting requests: N
- Compliance impact: <yes / no — if yes, NAIC notification window>

## Root cause
<the actual root cause, not a symptom; use 5-whys but don't perform; one paragraph max>

## What worked
<what the team did right; preserve these>

## What didn't
<what slowed the response; this drives action items>

## Action items (each with owner + target date)
- [ ] OWNER, BY: <date> — <concrete change>
- [ ] OWNER, BY: <date> — <concrete change>

## Recurrence prevention
<the one change that makes this exact incident impossible next time, not "be more careful">
```

The discipline is the action items having owners and dates. PIRs without those are theater.

## Output

A production-grade observability layer ships with all of the following:

- A dashboard showing the five SLIs with their targets and current burn rate; one panel per SLI, each linked to the underlying logs/metrics query.
- Burn-rate-based alerts wired to the paging system; fast-burn pages immediately, slow-burn opens a ticket, trickle goes to a weekly review.
- Five triage trees memorized by every on-call rotation member; the entry signal is the alert title, the body is the runbook.
- Five recovery playbooks one-page each, kept in the integration repo (so they version with the code), linked from each alert.
- A PIR template applied to every incident with SLO impact > 0; action items tracked in the work-management system with owners and dates.

## Examples

### Example 1 — Datadog burn-rate monitor (SLO target 99.5%)

```python
# error_budget = 0.5%/month = ~3.6h/month
# fast-burn: 2% budget in 1h → page
sum:trace.http_request.errors{service:guidewire-integration}.as_count() / 
sum:trace.http_request.hits{service:guidewire-integration}.as_count() > 0.144   # 14.4x normal
```

### Example 2 — Audit-table query for triage

```sql
-- "What was the integration trying to do during the 401 spike?"
SELECT correlation_id, actor, api_method, api_path, status_code, reason, at
FROM integration_audit
WHERE at BETWEEN '2026-04-15T03:00:00Z' AND '2026-04-15T03:30:00Z'
  AND status_code = 401
ORDER BY at;
```

### Example 3 — Runbook link in alert

```yaml
# Alert config
title: "GW Cloud API 401 spike"
runbook: https://github.com/acme/guidewire-integration/blob/main/runbooks/401-spike.md
priority: P1
escalation: "platform-oncall"
```

The on-call clicks the runbook link from the page; the runbook is in the repo so it versions with the code; updates land in PRs reviewed like any other change.

## Error Handling

| Symptom | First check | Likely cause |
|---|---|---|
| 401 spike on Cloud API | token cache age | reactive refresh, clock skew, secret rotation in flight |
| 409 storm on PATCH | concurrent writers + retry pattern | client retrying bare PATCH instead of GET-then-PATCH |
| 429 on `/oauth/token` | single-flight gate active? | thundering herd refresh from a stampede on token expiry |
| 429 on data-plane API | per-tenant quota | another integration sharing the tenant quota; growth past quota |
| `403 Forbidden` despite valid token | scope-drift gate | tenant admin removed a permission |
| `PKIX path building failed` | cert chain in JVM trust store | private-CA cert renewal not propagated |
| Gosu OOM in production | recent deploy + heap dump | unbounded entity load (missing filter or pagination) |
| FNOL p99 latency spike | upstream lookup latency | external policy-resolution service degraded |
| Bind success rate drops below SLO | UW-issue volume + product mix | new product or new broker producing high-referral volume; not an outage |
| Audit table empty for an outage window | audit insert path failing | check the audit-write retry budget; never let audit failures block the request |

For deeper coverage (RED method vs USE method tradeoffs, multi-tenant dashboard partitioning, synthetic FNOL probes, chaos-engineering tests for token-cache resilience), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — produces the auth-side signals this skill alerts on (token cache, scope drift)
- `guidewire-sdk-patterns` — the structured `GwError` and 409 retry semantics this skill's triage trees assume
- `guidewire-security-and-rbac` — the `integration_audit` table this skill queries during incidents
- `guidewire-ci-cd-pipeline` — the deployment surface incident response interacts with (rollback, canary)

## Resources

- [Google SRE Workbook — SLO engineering](https://sre.google/workbook/implementing-slos/)
- [Datadog SLO documentation](https://docs.datadoghq.com/service_management/service_level_objectives/)
- [PagerDuty incident response guide](https://response.pagerduty.com/)
- [Guidewire Cloud Console — tenant quotas and audit](https://gcc.guidewire.com)
- [USE method (Brendan Gregg)](https://www.brendangregg.com/usemethod.html)

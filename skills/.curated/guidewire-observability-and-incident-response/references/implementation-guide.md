# Observability & Incident Response — Implementation Guide

Extended walkthrough and supplementary patterns for the SKILL.md.

## RED method vs USE method

Two complementary instrumentation philosophies; use both, applied to different layers.

**RED (Rate, Errors, Duration)** — applied at the request layer (HTTP, message-queue consumer, business-event handler). For every request type, track:

- **Rate**: requests per second
- **Errors**: error rate (separated by class — caller error vs server error vs external)
- **Duration**: latency distribution (p50, p95, p99)

**USE (Utilization, Saturation, Errors)** — applied at the resource layer (CPU, memory, threads, DB connections, JVM heap). For every resource, track:

- **Utilization**: percentage of resource consumed
- **Saturation**: queue depth or backlog
- **Errors**: resource-level failures

A Guidewire integration's full instrumentation:

| Layer | Method | Examples |
|---|---|---|
| Inbound HTTP / event consumer | RED | FNOL intake rate, error rate by class, p99 latency |
| Outbound Cloud API | RED | per-endpoint rate, status-class breakdown, duration |
| Token cache | USE | utilization (cache age), errors (refresh failures) |
| Database connection pool | USE | active vs total, queue depth, acquisition timeout count |
| JVM | USE | heap %, GC pause time, thread count |

## Multi-tenant SLO budgets

When tenants have different SLO targets, the alert thresholds must partition. A naive global alert pages when the tier-3 tenant misbehaves and the tier-1 tenant is fine.

```yaml
- alert: GwAuthFastBurnTier1
  expr: |
    {tenant=~"acme|globex"} (1 - sli_token_availability) > (1 - 0.9995) * 14.4
- alert: GwAuthFastBurnTier3
  expr: |
    {tenant=~"smallco|microco"} (1 - sli_token_availability) > (1 - 0.99) * 14.4
```

Per-tenant on-call rotations can also apply: a tier-1 tenant's incidents page the platform team and the customer's TAM; a tier-3 incident pages only the platform team.

## Chaos engineering for token-cache resilience

Once a quarter, kill the token cache mid-traffic and verify the integration recovers without manual intervention. The single-flight gate, the proactive refresh window, and the rate-of-Hub-calls metric should all behave correctly.

```bash
# Datadog: drop a synthetic token expiry
kubectl exec deployment/integration -- /control kill-token-cache
# Watch: no 429 from Hub, no 401 spike on Cloud API, p99 latency stable
```

If any of those fail, the auth layer has a bug; the chaos test caught what production traffic eventually would.

## Distributed tracing across the workflow

Every Cloud API call should carry the originating `correlation_id` as a header (e.g., `X-Correlation-Id` or W3C `traceparent`). The integration's tracing backend then shows the full span from inbound user action through every Cloud API call to final response.

```typescript
const traceparent = ctx.traceparent ?? generateTraceparent();
const res = await fetch(`${BASE}${path}`, {
  headers: { 
    Authorization: `Bearer ${await getToken()}`,
    "X-Correlation-Id": ctx.correlationId,
    traceparent,
  },
});
```

Without distributed tracing, debugging "why did this submission take 45 seconds" requires correlating timestamps by hand across three log streams. With tracing, it's one screen.

## On-call rotation hygiene

| Practice | Why |
|---|---|
| Rotation length: 1 week | shorter is too disruptive, longer accumulates fatigue |
| Hand-off doc: 5 minutes Friday | what's outstanding, what's noisy, what's quiet |
| Quarterly tabletop incident | practice the runbook before the real incident |
| Blameless PIR culture | action items, not finger-pointing |
| On-call gets to drive their own action items | the person paged twice has the most incentive to fix it |

## Cost-of-incident calculation

For prioritizing PIR action items, compute the rough cost of each incident class:

```
cost = (incidents/quarter) × (avg duration) × (impacted requests/min) × (cost per impacted request)
```

`cost per impacted request` includes customer-experience cost (broker abandons quote), regulatory cost (NAIC disclosure), and operational cost (engineer hours during incident). Action items below ~$10K/quarter cost rarely justify the engineering hours; above that, fix it now.

## Incident communication template

```markdown
**Incident**: [SEV-1] Guidewire integration auth failures
**Status**: Investigating | Identified | Mitigating | Monitoring | Resolved
**Impact**: <user-visible description>
**Affected tenants**: <list or "all">
**Started**: HH:MM UTC
**Last update**: HH:MM UTC
**Next update**: HH:MM UTC

<summary of what we know and what we're doing>
```

Update every 15 minutes during active incident; final post-resolution summary within 1 hour. Public-facing communication for customer-impacting incidents needs legal/comms review per the carrier's external-comms policy.

## SLO review cadence

| Cadence | Activity |
|---|---|
| Weekly | review burn rate of every SLI; investigate any SLI burning >50% of monthly budget |
| Monthly | review action-item closure from PIRs; aged items get surfaced |
| Quarterly | review SLI definitions — are we still measuring what users care about |
| Annually | review SLO targets — are they too lax (we always meet) or too aggressive (constantly missing) |

## Related

- `SKILL.md` — production patterns
- `references/API_REFERENCE.md` — SLI queries, alert templates, runbook format, common-errors table
- Sibling `guidewire-install-auth` — auth signals this skill consumes
- Sibling `guidewire-security-and-rbac` — `integration_audit` table this skill queries

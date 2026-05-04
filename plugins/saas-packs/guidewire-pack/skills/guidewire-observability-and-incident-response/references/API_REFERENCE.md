# Observability & Incident Response — Reference

Metric definitions, alert configuration templates, and runbook formats supporting the patterns in `SKILL.md`.

## SLI definitions (precise queries)

### Token-endpoint availability

```
sli_token_availability = 1 - (
  sum(rate(http_requests_total{service="auth", status=~"5..|429"}[5m]))
  / sum(rate(http_requests_total{service="auth"}[5m]))
)
target: ≥ 0.999
```

Excludes `4xx` other than `429` — the integration's own auth bug returning `400` is not an outage.

### Cloud API write success

```
sli_write_success = 
  sum(rate(http_requests_total{service="gw-client", method=~"POST|PATCH|PUT", status=~"2.."}[5m]))
  / sum(rate(http_requests_total{service="gw-client", method=~"POST|PATCH|PUT", status!~"4.."}[5m]))
target: ≥ 0.995
```

`4xx` excluded from denominator entirely — caller validation errors are not an integration availability problem.

### Bind success rate (workflow SLI)

```
sli_bind_success = 
  count_over_time(workflow_event{event="submission.bound"}[1h])
  / count_over_time(workflow_event{event="submission.quoted", referred=false}[1h])
target: ≥ 0.98
```

Excludes referred submissions — those are a product outcome, not an integration outcome.

### FNOL intake p99 latency

```
sli_fnol_p99 = histogram_quantile(0.99, 
  rate(fnol_intake_duration_seconds_bucket[5m])
)
target: ≤ 2.0
```

Measured end-to-end from inbound HTTP request to `claim.created` log emission.

## Alert configuration template (Prometheus / Datadog)

### Fast-burn (page immediately)

```yaml
- alert: GwAuthFastBurn
  expr: |
    (1 - sli_token_availability) > (1 - 0.999) * 14.4   # 2% of monthly budget in 1h
  for: 5m
  labels:
    severity: page
    runbook: https://github.com/acme/guidewire-integration/blob/main/runbooks/auth-fast-burn.md
  annotations:
    summary: "Auth availability burning fast"
```

### Slow-burn (page during business hours)

```yaml
- alert: GwAuthSlowBurn
  expr: |
    (1 - sli_token_availability) > (1 - 0.999) * 6.0    # 5% of monthly budget in 6h
  for: 30m
  labels:
    severity: ticket
    runbook: <link>
```

### Trickle (weekly review)

```yaml
- alert: GwAuthTrickle
  expr: |
    (1 - sli_token_availability) > (1 - 0.999) * 1.0    # 10% of monthly budget in 3 days
  for: 6h
  labels:
    severity: review
```

## Runbook standard format

Every runbook follows this template; one runbook per alert.

```markdown
# Runbook: <alert-title>

## Signal
- Alert: <link>
- Trigger: <metric query that fired>
- Typical duration of impact: <minutes/hours>

## Diagnose (~3 min)
1. <First check, with the exact query/command>
2. <Second check>
3. <Third check>

## Decision tree
<the triage tree from SKILL.md, expanded with concrete kubectl/sql/curl commands>

## Mitigate (~5 min)
- Option A: <action> — when to choose this
- Option B: <action> — when to choose this

## Verify recovery
- <metric/query that should return to normal>
- <expected time-to-green from mitigation>

## Escalate when
- <conditions that require involving a different team or vendor>

## Audit
- Insert audit row: `reason="<incident-class>", correlation_id=<page-id>`
```

Runbooks live in the integration repo at `runbooks/<alert-slug>.md`. They version with the code, are reviewed in PRs, and are linked directly from alert payloads.

## Common-errors triage reference

This is the merged content from the original `guidewire-common-errors` skill; kept here as the reference one-stop for on-call triage.

| Error | First diagnostic | Likely cause | Quickest mitigation |
|---|---|---|---|
| `invalid_client` | check secret-rotation log | mid-rotation | fall back to secondary or rotate fully |
| `invalid_scope` | check GCC permissions | tenant admin removed it | restore permission or accept loss |
| `401 Unauthorized` | decode token, check exp | reactive refresh / clock skew | tighten early-refresh window |
| `403 Forbidden` | check scope claim | least-privilege drift | re-issue from GCC with correct role |
| `409 Conflict` | check checksum round-trip | retry-without-re-GET | fix retry layer |
| `422 rule-violation` (UW issue) | check `underwritingIssues[]` | unaddressed blocking issue | route to manual review, do not retry |
| `422 quote-expired` | check `quoteExpirationDate` | stale quote | re-quote |
| `422 reserve-required` | check reserve list for cost category | payment before reserve | set reserve first |
| `422 close-blocked` | run isReadyToSettle() | open reserves or activities | resolve blockers |
| `429 Too Many Requests` | check `Retry-After` header | quota exceeded or thundering herd | honour header; check single-flight gate |
| `PKIX path building failed` | check JVM trust store | cert chain missing | import to cacerts via keytool |
| `ENOTFOUND .guidewire.net` | check DNS | egress firewall | open `*.guidewire.net` |
| `entity-conflict` | check checksum | optimistic-lock failure | retry GET-then-PATCH |
| `submission-state-invalid` | check submission status | wrong state for operation | call the prerequisite transition |
| `renewal-window-closed` | check policy expirationDate | renewal too early | back off until window opens |

Operators should bookmark this table; treat it as the merged successor to the legacy `guidewire-common-errors` skill which was a subset of this content.

## Multi-tenant dashboard partitioning

For integrations serving multiple carriers, every dashboard panel partitions by tenant tag. Datadog example:

```
tenant:* avg:sli_token_availability{service:guidewire-integration} by {tenant}
```

Per-tenant SLOs may differ — a tier-1 carrier paying for premium service may have a 99.95% target while a tier-3 carrier has 99.5%. Encode in alert thresholds; do not run one global SLO.

## Synthetic FNOL probes

A synthetic check runs a known-good FNOL through the intake pipeline every 5 minutes against a sandbox tenant; fail = page. Catches integration breakage independent of customer traffic — a quiet weekend with broken intake gets caught.

```bash
# Cron, every 5 minutes
curl -sf -X POST $INTEGRATION_URL/fnol \
  -H "X-Synthetic: true" \
  -d @synthetic-fnol-payload.json \
  | jq -e '.claimNumber | startswith("CLM-")' \
  || trigger-page "Synthetic FNOL failed"
```

Tag the synthetic with `X-Synthetic: true` so business analytics excludes it from real-claim metrics.

## Related references

- `references/implementation-guide.md` — extended walkthrough
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth signals
- Sibling `guidewire-security-and-rbac/references/API_REFERENCE.md` — `integration_audit` schema this references

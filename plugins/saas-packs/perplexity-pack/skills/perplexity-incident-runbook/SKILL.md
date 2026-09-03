---
name: perplexity-incident-runbook
description: 'Execute Perplexity incident response procedures with triage, mitigation,
  and postmortem.

  Use when responding to Perplexity API outages, investigating search failures,

  or running post-incident reviews for Perplexity integration issues.

  Trigger with phrases like "perplexity incident", "perplexity outage",

  "perplexity down", "perplexity on-call", "perplexity emergency".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(jq:*), Bash(mktemp:*), Bash(tar:*), Bash(rm:*)
version: 1.12.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- perplexity
- incident-response
compatibility: Designed for Claude Code
---
# Perplexity Incident Runbook

## Overview

Rapid incident response for Perplexity Sonar API issues. Perplexity-specific: the API depends on live web search, so outages can be partial (search degraded but API responding), model-specific (sonar-pro down but sonar working), or citation-related (answers returned but no sources).

## Prerequisites

- Incident commander, severity, affected tenant or route, and next update time assigned
- `PERPLEXITY_API_KEY` supplied by the approved secret manager
- `curl`, `jq`, `mktemp`, and `tar` installed for the metadata-only evidence collector
- A synthetic prompt that contains no customer, employee, credential, or regulated data
- Approved fallback and cache policy; never expose stale or cross-tenant content implicitly

## Instructions

1. Declare the incident and freeze unrelated changes. Use `Read` and `Grep` only on approved telemetry to record aggregate symptoms and provider request IDs, never prompts, answers, API keys, or raw logs.
2. Run the bounded triage against the fixed Perplexity API origin with a synthetic prompt. Treat non-200 and malformed 200 responses as failures.
3. Classify the fault as credential/billing, throttling, provider 5xx, network, model-specific, or citation-quality degradation before choosing mitigation.
4. Apply only a pre-approved mitigation: bounded retry, concurrency reduction, model fallback for compatible requests, or tenant-scoped cache fallback.
5. Verify recovery with the same probe, monitor one complete traffic window, then create the allowlisted evidence bundle and postmortem.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|--------------|---------|
| P1 | Complete API failure | < 15 min | All requests returning 500/503 |
| P2 | Degraded service | < 1 hour | High latency, 429 rate limits, no citations |
| P3 | Minor impact | < 4 hours | Single model unavailable, sporadic errors |
| P4 | No user impact | Next business day | Monitoring gap, stale cache |

## Quick Triage (Run Immediately)

```bash
set -euo pipefail
test -n "${PERPLEXITY_API_KEY:-}" || {
  echo "PERPLEXITY_API_KEY is not set" >&2
  exit 1
}
echo "=== Perplexity Triage ==="

# 1. Test sonar model
echo -n "sonar: "
curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out "HTTP %{http_code} in %{time_total}s" --output /dev/null \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
echo ""

# 2. Test sonar-pro model
echo -n "sonar-pro: "
curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out "HTTP %{http_code} in %{time_total}s" --output /dev/null \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar-pro","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
echo ""

# A 200 status proves authenticated reachability. Do not send a deliberately
# invalid credential: it creates avoidable authentication noise and no stronger proof.
```

## Decision Tree

```
API returning errors?
├─ 401/402: Auth issue
│   └─ Verify API key → Regenerate at perplexity.ai/settings/api
├─ 429: Rate limited
│   └─ Enable request queue → Reduce concurrency → Wait
├─ 500/503: Server error
│   ├─ All models affected?
│   │   ├─ YES → Perplexity outage. Enable fallback/cache.
│   │   └─ NO → Model-specific issue. Route to working model.
│   └─ Check the official Perplexity system-status page
├─ Timeout: No response
│   ├─ DNS resolves? → Check network/firewall
│   └─ DNS fails? → DNS issue. Use alternative resolver.
└─ 200 but no citations: Search degraded
    └─ Switch to sonar-pro for more citations
```

## Immediate Actions

### Auth Failure (401/402)

```bash
set -euo pipefail
test -n "${PERPLEXITY_API_KEY:-}" || {
  echo "credential is absent from this process" >&2
  exit 1
}
printf '%s\n' "credential is configured; do not print its prefix, length, or value"
```

If rotation is required, use the organization secret manager's audited rotation procedure, update the workload reference without placing the value on a command line, and verify rollout health before revoking the previous version.

### Rate Limited (429)

```bash
set -euo pipefail
printf '%s\n' "pause admission or reduce concurrency through the approved deployment control"
printf '%s\n' "honor bounded Retry-After and queue overflow; do not guess a universal RPM limit"
```

### Model-Specific Fallback

```typescript
// If sonar-pro is failing, fall back to sonar
async function resilientSearch(query: string) {
  try {
    return await perplexity.chat.completions.create({
      model: "sonar-pro",
      messages: [{ role: "user", content: query }],
    });
  } catch (err: unknown) {
    const status = typeof err === "object" && err !== null && "status" in err
      ? Number((err as { status: unknown }).status)
      : 0;
    if (status === 408 || status >= 500) {
      console.warn("sonar-pro unavailable, falling back to sonar");
      return await perplexity.chat.completions.create({
        model: "sonar",
        messages: [{ role: "user", content: query }],
      });
    }
    throw err instanceof Error ? err : new Error("Perplexity request failed");
  }
}
```

## Communication Templates

### Internal (Slack)

```
P[1-4] INCIDENT: Perplexity Search Integration
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [What users see — degraded search, no citations, etc.]
Cause: [API error / rate limit / auth / Perplexity outage]
Action: [What we're doing]
ETA: [Next update time]
IC: @[name]
```

## Post-Incident

### Evidence Collection

```bash
set -euo pipefail
umask 077
test -n "${PERPLEXITY_API_KEY:-}" || {
  echo "PERPLEXITY_API_KEY is not set" >&2
  exit 1
}
case "${PERPLEXITY_INCIDENT_ID:-}" in
  ""|*[!A-Za-z0-9._-]*)
    echo "PERPLEXITY_INCIDENT_ID must use only letters, digits, dot, underscore, or hyphen" >&2
    exit 1
    ;;
esac

evidence_dir="$(mktemp -d)"
trap 'rm -rf -- "${evidence_dir}"' EXIT

response="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}\n%{time_total}' \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"model":"sonar","messages":[{"role":"user","content":"Reply with the single word ready."}],"max_tokens":8}' \
  https://api.perplexity.ai/chat/completions)"

latency_seconds="${response##*$'\n'}"
without_latency="${response%$'\n'*}"
http_status="${without_latency##*$'\n'}"
body="${without_latency%$'\n'*}"
test "${http_status}" = "200" || {
  echo "evidence probe failed with HTTP ${http_status}; body suppressed" >&2
  exit 1
}

printf '%s\n' "${body}" | jq -e \
  --arg incident_id "${PERPLEXITY_INCIDENT_ID}" \
  --arg status "${http_status}" \
  --arg latency "${latency_seconds}" '
    {
      schema_version: "perplexity-incident-summary/v1",
      incident_id: $incident_id,
      provider: "perplexity",
      http_status: ($status | tonumber),
      latency_seconds: ($latency | tonumber),
      model: (.model | select(type == "string" and length > 0)),
      finish_reason: (.choices[0].finish_reason | select(type == "string")),
      citation_count: ((.citations // []) | length),
      usage: {
        prompt_tokens: (.usage.prompt_tokens | select(type == "number")),
        completion_tokens: (.usage.completion_tokens | select(type == "number")),
        total_tokens: (.usage.total_tokens | select(type == "number"))
      }
    }
  ' >"${evidence_dir}/summary.json"

# Archive one explicit allowlisted file. Raw API bodies, prompts, answers,
# citations, request headers, environment, and application logs are never collected.
tar -czf "perplexity-incident-${PERPLEXITY_INCIDENT_ID}.tar.gz" \
  -C "${evidence_dir}" summary.json
```

### Postmortem Template

```markdown
## Incident: Perplexity [Error Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Summary
[1-2 sentences]

### Timeline
- HH:MM — Alert fired: [description]
- HH:MM — Triage: [findings]
- HH:MM — Mitigation: [action taken]
- HH:MM — Resolved

### Root Cause
[Technical explanation — API outage / rate limit / auth / our bug]

### Action Items
- [ ] [Fix] — Owner — Due
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| All models failing | Perplexity outage | Serve cached results, notify users |
| Intermittent 500s | Transient API issue | Retry with backoff |
| Latency spike | Complex searches | Timeout + fallback to sonar |
| No citations | Search degradation | Log and monitor, usually resolves |

## Examples

### Provider degradation with a healthy fallback

If `sonar-pro` produces repeated 5xx responses while `sonar` passes the same synthetic probe, route only compatible requests to `sonar`, mark responses as degraded where product behavior differs, and keep the circuit open for a bounded interval. Do not retry authentication, billing, or invalid-request failures through another model.

### Safe post-incident evidence

Set a non-sensitive incident identifier such as `INC-2026-0042`, run the evidence collector, and inspect the archive manifest. It must contain exactly `summary.json`; the JSON must contain only the documented schema fields. Store provider request IDs separately in the incident system, whose access and retention controls are already approved.

## Output

- Issue triaged and categorized
- Remediation applied (fallback/queue/key rotation)
- Stakeholders notified
- Evidence collected for postmortem

## Resources

- [Perplexity Community Forum](https://community.perplexity.ai)
- [Perplexity System Status](https://docs.perplexity.ai/docs/resources/status)
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Evidence bundle contract](references/evidence-contract.md)

## Next Steps

For data handling, see `perplexity-data-handling`.

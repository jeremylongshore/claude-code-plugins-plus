---
name: replit-incident-runbook
description: 'Triage a Replit published-app incident, separate platform from application failures, contain safely, and preserve redacted evidence. Use when handling outages, crash loops, failed releases, database errors, or production authentication failures. Trigger with phrases like "replit incident", "replit outage", "replit down", or "replit crash".'
allowed-tools: Read, Grep, Bash(curl:*), Bash(jq:*)
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- replit
- incident-response
- debugging
compatibility: Designed for Claude Code
---
# Replit Incident Runbook

## Overview

Restore a Replit published app without turning an outage into a data, credential, or billing incident. Separate a Replit platform event from an application regression, keep evidence allowlisted, and use only a recovery action that the owner approved before the incident.

## Prerequisites

- The published `replit.app` hostname, incident identifier, impact statement, and owner-defined severity policy.
- Read-only access to Publishing status, logs, monitoring, and the source revision.
- A named incident commander, communications owner, and production-data owner.
- The last verified release, migration state, and a tested rollback or fix-forward path.
- Approval requirements for republishing, changing deployment type/capacity, rotating Secrets, or modifying production data.

## Instructions

### Step 1 — Establish impact and freeze unrelated changes

Record the failing user journey, first-seen time, affected population, and current deployment version. Pause unrelated releases. Do not change capacity, DNS, access, Secrets, or data while the failure domain is unknown.

### Step 2 — Run metadata-only triage

This probe accepts only a single-label Replit-owned production hostname. It emits the public platform indicator, HTTP status, and duration; it never prints the response body.

Use `Read` for the source revision and configuration, and `Grep` only for incident-relevant call sites or request identifiers; do not export whole files or logs.

```bash
set -euo pipefail
: "${REPLIT_DEPLOY_URL:?Set the exact https://<app>.replit.app origin}"

if [[ ! "$REPLIT_DEPLOY_URL" =~ ^https://[a-z0-9]([a-z0-9-]*[a-z0-9])?\.replit\.app$ ]]; then
  printf 'Refusing unapproved deployment origin\n' >&2
  exit 64
fi

# Bound the third-party status payload to 64 KiB before parsing it.
status_json="$(curl --silent --show-error --fail --location --max-redirs 2 \
  --connect-timeout 5 --max-time 10 --max-filesize 65536 --proto '=https' \
  'https://status.replit.com/api/v2/summary.json')" || {
  printf 'Unable to retrieve Replit status safely\n' >&2
  exit 1
}
platform_indicator="$(printf '%s' "$status_json" | jq -er \
  '.status.indicator | select(type == "string" and length <= 32)')" || {
  printf 'Invalid Replit status response\n' >&2
  exit 1
}

app_probe="$(curl --silent --show-error --output /dev/null \
  --write-out '%{http_code} %{time_total}' --connect-timeout 5 --max-time 10 \
  --proto '=https' "$REPLIT_DEPLOY_URL/healthz")" || {
  printf 'Published app probe failed\n' >&2
  exit 1
}
read -r app_status duration_seconds <<<"$app_probe"
[[ "$app_status" =~ ^[0-9]{3}$ && "$duration_seconds" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
  printf 'Invalid probe metadata\n' >&2
  exit 1
}

jq -cn --arg platform "$platform_indicator" --arg status "$app_status" \
  --arg duration "$duration_seconds" \
  '{platform_indicator:$platform,http_status:$status,duration_seconds:$duration}'
```

Do not add authorization headers, cookies, query tokens, or arbitrary custom origins to this probe. Review custom domains separately.

### Step 3 — Classify the failure domain

| Evidence | Likely domain | Next safe check |
|---|---|---|
| Replit status indicates an incident | Platform | communicate impact; avoid speculative app changes |
| Preview fails before publishing | Application/build | run command, dependency, port, application error |
| Preview passes; publishing fails | Release configuration | Publishing logs, build/run commands, production Secrets |
| Release succeeds; public URL fails | Runtime/environment | callback URLs, database, access policy, storage |
| Only some users fail | Auth/authorization/data | two-user isolation and tenant-scoped queries |
| Error rate/latency rises with load | Capacity/dependency | Monitoring, pool limits, downstream latency |

### Step 4 — Contain with the smallest reversible action

- Platform incident: communicate, preserve evidence, and monitor. Do not churn configuration.
- Bad release with a verified prior version: use the preapproved recovery procedure exposed by the current Publishing/version-control flow, then verify the public URL.
- Missing production configuration: add only the approved Secret name/value through Publishing; never paste it into chat, logs, or source.
- Capacity exhaustion: shed optional work or apply an approved capacity change with cost owner acknowledgment.
- Bad database migration: follow the database-specific recovery plan. An application release change does not reverse data mutations.

### Step 5 — Inspect logs without exporting them wholesale

Search Publishing logs for the relevant time window, request identifier, and error class. Record only timestamp, deployment version, coarse error class, request identifier, and redacted finding. Never archive or paste unrestricted logs, prompts, request bodies, headers, URLs containing tokens, environment output, or customer records.

### Step 6 — Verify recovery

Repeat the failed user journey at the published URL, confirm coarse health and monitoring recovery, test authentication/tenant isolation when implicated, and observe for the owner-defined stabilization window. Resume releases only after the incident commander records the outcome.

## Examples

Platform degradation:

```text
Evidence: public Replit status is degraded; multiple unrelated apps affected
Action: communicate impact, pause releases, monitor provider recovery
Avoid: changing app configuration without app-specific evidence
```

Application regression:

```text
Evidence: Replit status normal; Preview passes; new published release returns 5xx
Action: compare release revision and production configuration, then use the pretested recovery
Verify: original user journey, public health, error rate, and tenant isolation
```

## Output

Produce a redacted incident record containing incident ID, severity, impact, first/last timestamps, published revision, Replit status indicator, HTTP status, failure domain, containment, recovery action, verification, owners, and follow-ups. Link restricted evidence rather than embedding raw logs or customer data.

## Error Handling

- If the probe rejects the hostname, verify the Replit-owned origin manually; do not weaken the allowlist during an incident.
- If Replit status cannot be parsed, mark provider state unknown and continue with application evidence.
- If logs contain possible credentials or customer data, stop copying and use the approved security review channel.
- If no verified recovery exists, fix forward with a bounded change instead of improvising a destructive rollback.
- If production data may be inconsistent, freeze writes when the owner-approved plan permits and involve the data owner.

## Resources

- [Replit Status](https://status.replit.com)
- [Troubleshoot publishing](https://docs.replit.com/build/troubleshooting)
- [Publishing overview](https://docs.replit.com/features/publishing/overview)
- [Deployment types](https://docs.replit.com/features/publishing/deployment-types)
- [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets)
- [Storage and Databases](https://docs.replit.com/learn/projects-and-artifacts/storage-and-databases)

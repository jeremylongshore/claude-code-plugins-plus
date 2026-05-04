---
name: guidewire-security-and-rbac
description: Lock down a Guidewire Cloud API integration so it survives a SOC 2 audit, an NAIC Model Audit Rule review, and a real-world incident — least-privilege role design, encrypted committed secrets via SOPS+age, PII redaction in logs (SSN/DOB/claim narrative), audit-trail capture, cross-tenant isolation for multi-carrier integrations, and detect-and-rotate response to token leaks. Use when designing the security posture for a new integration, hardening an existing one before audit, or responding to a leaked credential. Trigger with "guidewire security", "guidewire rbac", "guidewire pii redaction", "guidewire audit trail", "guidewire secret leak".
allowed-tools: Read, Write, Edit, Bash(sops:*), Bash(age:*), Bash(curl:*), Grep, Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - security
  - rbac
  - pii
  - sops
  - audit
---

# Guidewire Security and RBAC

## Overview

Build the security posture an integration needs in production: secrets that cannot leak from the repo, roles that cannot escalate beyond their job, logs that cannot exfiltrate PII, and an audit trail that satisfies SOC 2 and NAIC Model Audit Rule reviewers. This skill is the application of generic security practice to the specific shape of Guidewire Cloud API — claim and policy data carry regulated PII; a leaked client_secret can read or write a carrier's entire book of business; carriers operate under state-level insurance regulator scrutiny.

Five real-world failures this skill prevents:

1. **Plaintext `.env` in the repo** — a `git push` to a public mirror leaks live credentials; the only defense is to never have plaintext in the tree, full stop.
2. **Over-scoped Service Application** — every integration starts with `pc.account.write` "to make development easier" and is never narrowed; the audit finding cites OWASP A01 broken access control.
3. **PII in observability** — `console.log(claim)` dumps SSN, DOB, claim narrative, and phone numbers into the logging pipeline, where they replicate to every downstream tool the company uses.
4. **No audit trail of what the integration did** — security review asks "what did this service touch in the last 90 days" and the answer is "everything in the access log, but we cannot tell which actor"; the audit fails.
5. **Cross-tenant data bleed** — a multi-tenant integration uses one set of credentials per environment instead of per tenant; a bug in tenant routing leaks Carrier A's data into Carrier B's response.

## Prerequisites

- A working auth + SDK layer per `guidewire-install-auth` and `guidewire-sdk-patterns`
- `sops` and `age` installed locally (`brew install sops age` / `apt install sops` / `mise install age`)
- Access to GCC for the integration's Service Application configuration
- A logging/observability stack the integration writes to (Datadog, Splunk, ELK, or similar) — required for the redaction patterns to apply

## Instructions

Build the posture in this order. Each layer addresses one of the five failures listed in Overview.

### 1. Encrypted committed secrets via SOPS + age

Plaintext `.env` files committed to a repo are the single largest source of credential leaks in the SaaS world. SOPS + age allows secrets to live in the repo as ciphertext that only holders of the age private key can read. The audit trail of "who rotated what when" comes free with `git log`.

```bash
sops-init                                    # writes .sops.yaml + .env.sops + scripts/sops-env (idempotent)
sops secrets.prod.sops.yaml                  # interactive edit; saves re-encrypted
git add secrets.prod.sops.yaml && git commit -m "chore(secrets): rotate gw client secret"
```

In the runtime, decrypt via the anchored regex pattern (do not use the naive `sed 's/^/export /'` — see `guidewire-install-auth` for the bare-export-leak failure mode):

```bash
eval "$(sops -d secrets.prod.sops.yaml | sed -nE 's/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/export \1=\2/p')"
```

Per-environment recipient lists in `.sops.yaml` mean dev keys cannot decrypt prod secrets — limit blast radius of a compromised dev workstation.

### 2. Least-privilege roles per Service Application

In **GCC > Identity & Access > Applications > [your-app] > Permissions**, assign only the roles the integration actually needs. A read-only reporting integration should hold `pc.account.read` and `pc.policy.read` only; a webhook event consumer needs zero write roles.

```
Reporting integration:        pc.account.read, pc.policy.read, cc.claim.read
Broker portal (read+quote):   pc.account.read, pc.account.write, pc.submission.write
Renewal job:                  pc.policy.read, pc.policy.write
Claims FNOL intake:           cc.claim.write, cc.contact.write
Webhook event consumer:       (no Cloud API roles — just receives App Events)
```

Validate the issued token carries only the expected scopes on every refresh (`guidewire-install-auth`'s scope-drift gate). A token with extra scopes is a configuration error; alert and treat as an incident.

### 3. PII redaction in logs

Guidewire claim and contact resources carry regulated PII: SSN, date of birth, driver's license number, claim narrative, phone, email, address. Redact at the logging boundary, not in the calling code (which always misses cases). Apply the redactor to every structured log entry the integration emits.

```typescript
const PII_PATHS = [
  "ssn", "taxId", "dateOfBirth", "driversLicenseNumber",
  "primaryPhone.phoneNumber", "workPhone.phoneNumber", "primaryEmail",
  "addressLine1", "addressLine2", "description", // claim narrative
];

export function redactPii<T extends object>(record: T): T {
  const clone = JSON.parse(JSON.stringify(record));
  for (const path of PII_PATHS) {
    setByPath(clone, path, redactValue(getByPath(clone, path)));
  }
  return clone;
}

function redactValue(v: unknown): string | unknown {
  if (typeof v !== "string" || !v) return v;
  if (/^\d{3}-?\d{2}-?\d{4}$/.test(v)) return "***-**-****";       // SSN
  if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 4) + "-**-**"; // DOB → year only
  if (v.length <= 4) return "***";
  return v.slice(0, 2) + "***" + v.slice(-2);
}
```

Wire the redactor into the logger transport (Pino redact, Winston format, OpenTelemetry log processor) so every log entry passes through it before serialization. Per-call `console.log(redactPii(claim))` works in theory and fails in practice — engineers forget.

### 4. Audit trail of integration actions

Every state-mutating Cloud API call should leave a row in an internal audit table the integration owns. Cloud API has its own audit, but it cannot tell investigators which logical operation drove a request, only that the Service Application made the call.

```sql
CREATE TABLE integration_audit (
  id UUID PRIMARY KEY,
  correlation_id UUID NOT NULL,
  actor TEXT NOT NULL,                 -- the upstream user, broker, or job triggering the call
  service_app TEXT NOT NULL,           -- the GCC Service Application id
  api_method TEXT NOT NULL,            -- POST / PATCH / DELETE
  api_path TEXT NOT NULL,              -- /pc/rest/v1/policies/pc:8001
  resource_id TEXT,                    -- post-response id
  idempotency_key UUID NOT NULL,
  status_code INT NOT NULL,
  reason TEXT,                         -- "renewal-window-open", "broker-quote-flow", etc.
  at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Each row pairs to one Cloud API call. SOC 2 reviewers ask "show me every write this integration made on behalf of broker `acme-insurance` in March"; this table makes the answer a SQL query, not a forensic exercise.

### 5. Cross-tenant isolation for multi-carrier integrations

If the integration serves more than one carrier, every carrier gets:

- A separate Service Application registration in GCC (separate `client_id`/`client_secret`)
- A separate entry in `secrets.[carrier-slug].sops.yaml` encrypted to a tenant-specific recipient
- A separate row in tenant-routing config that maps inbound requests to outbound credentials
- A separate scope assignment audited per the role table above

Sharing one Service Application across tenants creates legal and contractual exposure beyond the technical risk; a single compromised credential reveals every tenant's data, and an audit finding will cite SOC 2 CC6.1 (logical access controls).

### 6. Detect-and-rotate response to suspected secret leak

When a secret is suspected leaked (a developer pasted it into a Slack message, a CI log captured it, a public commit briefly contained it):

```bash
# 1. Rotate immediately in GCC — generates a new client_secret
# 2. Update the encrypted secret file
sops secrets.prod.sops.yaml             # set GW_CLIENT_SECRET to the new value
git commit -m "rotate(secrets): GW client secret — leak suspected $(date -Iseconds)"
# 3. Deploy to all environments
# 4. Use dual-secret window (per guidewire-install-auth) so in-flight requests do not fail
# 5. Audit Cloud API access logs for unauthorized calls during the leak window
# 6. Document the incident in the audit table per step 4
```

Do not "wait until business hours" — credential leaks compound by the minute. The rotation is reversible; the data exfiltration is not.

## Output

A production-grade security posture ships with all of the following:

- All secrets stored as `secrets.*.sops.yaml` files committed to git, encrypted to per-environment age recipients; no plaintext `.env` files anywhere in the tree.
- Service Application roles assigned per least privilege, validated on every token refresh by the scope-drift gate.
- A logger configured to apply `redactPii()` to every structured log entry before serialization.
- An `integration_audit` table populated synchronously with every state-mutating Cloud API call.
- Per-tenant Service Applications and secret files for any multi-carrier integration.
- A documented detect-and-rotate runbook with a target rotation time of <30 minutes from suspicion to deploy.

## Examples

### Example 1 — `.sops.yaml` recipient layering

```yaml
creation_rules:
  - path_regex: secrets\.dev\.sops\.yaml$
    age: age1devkey...,age1leadkey...
  - path_regex: secrets\.uat\.sops\.yaml$
    age: age1uatkey...,age1leadkey...
  - path_regex: secrets\.prod\.sops\.yaml$
    age: age1prodkey...,age1leadkey...
```

A developer's age key decrypts dev only; the lead's key decrypts every environment for incident response. Rotation of an environment's age recipient is `sops updatekeys secrets.<env>.sops.yaml`.

### Example 2 — Pino redactor wiring

```typescript
import pino from "pino";
const log = pino({
  redact: {
    paths: [
      "*.ssn", "*.taxId", "*.dateOfBirth",
      "*.primaryPhone.phoneNumber", "*.primaryEmail",
      "*.description",
    ],
    censor: "[REDACTED]",
  },
});
log.info({ claim: claimResource }, "claim received");
```

### Example 3 — Audit row on a write

```typescript
await db.insert("integration_audit", {
  id: crypto.randomUUID(),
  correlation_id: ctx.correlationId,
  actor: ctx.user.id,
  service_app: process.env.GW_CLIENT_ID,
  api_method: "POST",
  api_path: "/pc/rest/v1/policies/pc:8001/endorse",
  resource_id: response.data.id,
  idempotency_key: idempotencyKey,
  status_code: 200,
  reason: "broker-portal-mid-term-coverage-add",
});
```

## Error Handling

| Symptom | Cause | Solution |
|---|---|---|
| `403 Forbidden` despite valid token | scope drift — GCC admin removed a role | scope-drift gate alerts on every refresh; not a transport failure, surface as incident |
| Plaintext `.env` discovered in git history | committed before SOPS adoption | rotate every credential in the leaked file immediately; rewrite history with `git filter-repo` if the leak is recent |
| Logger emits SSN to Splunk | `redactPii` not wired into the transport | add at the logger config, not at call sites; remove the per-call `redactPii()` in favor of transport-level |
| SOPS commit accidentally encrypted to wrong recipient | `.sops.yaml` regex did not match | run `sops updatekeys` on the affected file; recipients are visible in the YAML metadata |
| Bare `export` in cron mail leaks every env var | naive `sed 's/^/export /'` instead of anchored regex | switch to `sed -nE 's/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/export \1=\2/p'` |
| Audit query "what did integration do for broker X last month" returns nothing | audit table not populated | wire `integration_audit` insert into every write helper; backfill is impossible |
| One client_secret used across two carriers | shared Service Application | split immediately; rotate both halves to scope the blast radius |
| Token in a CI log | secret printed accidentally during deployment | rotate via the detect-and-rotate runbook; audit access during the leak window |

For deeper coverage (Vault Agent integration, dynamic secrets, token-binding, federated identity, FIPS-140 trust stores), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — the auth layer this hardens; scope-drift gate, dual-secret rotation
- `guidewire-sdk-patterns` — error mapping that surfaces `403` as a structured exception this skill alerts on
- `guidewire-observability-and-incident-response` — emits the alerts this skill's audit table powers
- `guidewire-ci-cd-pipeline` — promotes encrypted secrets through environments without plaintext exposure

## Resources

- [SOPS — Secrets OPerationS](https://github.com/getsops/sops)
- [age encryption tool](https://github.com/FiloSottile/age)
- [OWASP A01:2021 — Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [OWASP A02:2021 — Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [SOC 2 CC6.1 — Logical Access Controls](https://www.aicpa-cima.com/topic/audit-assurance/soc-for-service-organizations)
- [NAIC Model Audit Rule (MAR)](https://content.naic.org/cipr-topics/insurance-data-security-model-law)

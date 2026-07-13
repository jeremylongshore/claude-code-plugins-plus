---
name: hubspot-agency-multi-portal
description: |
  Manage 10-100 HubSpot portals for agency clients with credential isolation that prevents
  cross-portal data contamination, per-portal audit trails for billing and GDPR/CCPA
  attribution, and a scriptable bulk-onboarding workflow that eliminates one-at-a-time
  credential setup. Use when onboarding new client portals, building a compliant per-client
  API call log, rotating tokens across a full agency fleet, or generating per-client
  compliance reports. Trigger with "hubspot agency", "multi-portal management",
  "hubspot credential isolation", "per-portal audit log", "hubspot compliance report",
  "bulk portal onboarding", "token rotation cascade", "hubspot client portals".
allowed-tools: Read, Write, Bash(curl:*), Bash(jq:*), Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - multi-portal
  - agency
  - compliance
  - audit
---

# HubSpot Agency Multi-Portal

## Overview

Operate a fleet of HubSpot portals for agency clients without cross-portal contamination, attribution loss, or onboarding bottlenecks. This is not a getting-started guide — it is the infrastructure your agency runs on day one with client one and scales to client one hundred without revisiting.

The six production failures this skill prevents:

1. **Cross-portal credential contamination** — a shared `HUBSPOT_ACCESS_TOKEN` env var causes API writes intended for Client A to silently land in Client B's CRM. The HubSpot API does not reject the call; it accepts it. Data corruption is silent and may not be discovered for days. Per-portal credential isolation — enforced in code, not convention — is the only fix.
2. **Audit trail gaps** — agency billing, SLA compliance, and GDPR/CCPA data-processing agreements all require proof of which API calls were made on behalf of which client. A shared token makes post-hoc attribution impossible. A per-portal structured audit log with portalId, clientSlug, operation, and timestamp makes attribution irrefutable.
3. **Bulk onboarding bottleneck** — onboarding 50 new clients one-at-a-time requires 50 manual credential setups, 50 manual verifications, and 50 opportunities for human error. A scriptable bulk onboarding workflow reads a CSV of client names and tokens, validates each against the account-info endpoint, and seeds the credential store in one pass.
4. **Token rotation cascade** — rotating one client's private-app token in HubSpot does not update any downstream system. With 50 portals, a partial rotation — some systems updated, some not — leaves stale tokens in production for undetermined periods. A per-portal rotation runbook with a cross-system checklist closes the gap.
5. **Rate-limit aggregation confusion** — each portal has its own independent 500K/day quota. An agency analytics system reading all 50 portals is NOT limited to 500K calls total — it has 500K per portal per day, but only if the token used for each portal belongs to that portal. A shared token collapses all quota attribution to one portal, causing artificial exhaustion and incorrect monitoring.
6. **Compliance reporting ambiguity** — under GDPR Article 30 and CCPA, a data processor (the agency) must demonstrate which operations were performed on which controller's (client's) data and when. A shared token makes this demonstration impossible after the fact. Per-portal audit logs with structured fields make it a simple query.

## Prerequisites

- Node.js 18+ or Python 3.10+
- One HubSpot private-app token per client portal (Settings → Integrations → Private Apps → Create private app → Auth tab)
- A secret store the credential router can read at startup: AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, or `pass` for local development
- `jq` installed for CLI validation steps
- `python3` with standard library only for bulk onboarding script (no external deps required)
- CSV file of client slugs and tokens for bulk onboarding (format: `clientSlug,portalToken,portalId`)

## Instructions

Build in this order. Each section closes one production failure mode.

### 1. Credential store design (closes cross-portal contamination)

The credential store is a JSON map of `clientSlug → token`. It lives in your secret manager, never in source code or environment variables. The key insight is that `clientSlug` is the primary key — every operation starts by selecting a slug, which deterministically selects the token. There is no ambient credential and no fallback to a global env var.

```typescript
// Shape of the credential store (stored in secret manager, NOT in git or env vars)
interface PortalCredentialStore {
  version: number; // increment on every write; used for drift detection
  portals: Record<string, PortalCredential>;
}

interface PortalCredential {
  token: string;            // HubSpot private-app token: pat-na1-...
  portalId: number;         // HubSpot portal ID — verified via account-info on onboard
  clientSlug: string;       // kebab-case client identifier: "acme-corp"
  addedAt: string;          // ISO 8601 — when this credential was seeded
  lastRotatedAt: string;    // ISO 8601 — updated on every token rotation
  datacenter: string;       // "na1" | "eu1" | "au1" — extracted from token prefix
}

// Load from secret manager at process startup — never re-read per-request
async function loadCredentialStore(): Promise<PortalCredentialStore> {
  const raw = await readSecret("hubspot/agency-portals");
  const store: PortalCredentialStore = JSON.parse(raw);
  if (!store.portals || typeof store.portals !== "object") {
    throw new Error("Credential store is malformed — missing portals map");
  }
  return store;
}
```

The `datacenter` field matters: a `pat-na1-*` token sent to `api.hubapi.com` (which routes to `na1`) will work, but if HubSpot migrates the portal to `eu1`, the token prefix changes and calls to the wrong datacenter return 404. Storing the datacenter alongside the token surfaces this mismatch immediately.

### 2. Portal identity verification (confirm token points to expected portal)

Every token must be verified against the `GET /account-info/v3/details` endpoint before being admitted to the credential store. This endpoint returns the portalId for the token's portal — which is the ground truth for "which portal does this token belong to."

```typescript
interface PortalDetails {
  portalId: number;
  timeZone: string;
  currency: string;
  portalType: string; // "STANDARD" | "DEVELOPER" | "SANDBOX" | "TRIAL"
}

async function verifyPortalIdentity(
  token: string,
  expectedPortalId?: number
): Promise<PortalDetails> {
  const res = await fetch("https://api.hubapi.com/account-info/v3/details", {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (res.status === 401) {
    throw new Error("Token rejected (401) — revoked, malformed, or wrong datacenter");
  }
  if (res.status === 403) {
    throw new Error("Token lacks account-info scope — re-create private app with account-info scope");
  }
  if (!res.ok) {
    throw new Error(`account-info returned ${res.status}: ${await res.text()}`);
  }

  const details: PortalDetails = await res.json();

  if (expectedPortalId !== undefined && details.portalId !== expectedPortalId) {
    throw new Error(
      `Portal ID mismatch — token belongs to portal ${details.portalId}, ` +
      `expected ${expectedPortalId}. Token is for the wrong client.`
    );
  }

  return details;
}
```

Run `verifyPortalIdentity` during onboarding (to populate `portalId` in the credential store) and during rotation (to confirm the new token belongs to the same portal before committing it).

### 3. Per-portal HTTP client factory with audit-log middleware (closes audit trail gaps)

The client factory produces an HTTP client bound to a single portal's token. Every request made through this client is logged to the audit trail with a structured record. There is no way to make an unlogged HubSpot API call through this factory — the audit middleware is non-optional.

```typescript
interface AuditRecord {
  ts: string;           // ISO 8601 timestamp
  portalId: number;
  clientSlug: string;
  method: string;       // GET | POST | PATCH | DELETE
  path: string;         // /crm/v3/objects/contacts
  statusCode: number;
  durationMs: number;
  objectType?: string;  // "contacts" | "deals" | "companies" — extracted from path
  objectId?: string;    // from path or response body
  actor: string;        // "hubspot-agency-router/2.0.0"
  rateLimitRemaining?: number; // from X-HubSpot-RateLimit-Daily-Remaining header
}

type AuditWriter = (record: AuditRecord) => void | Promise<void>;

function createPortalClient(
  credential: PortalCredential,
  auditWriter: AuditWriter
) {
  const baseUrl = "https://api.hubapi.com";

  return async function portalFetch(
    path: string,
    init: RequestInit = {}
  ): Promise<Response> {
    const start = Date.now();
    const method = (init.method ?? "GET").toUpperCase();

    const res = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${credential.token}`,
        "Content-Type": "application/json",
        ...init.headers,
      },
    });

    const durationMs = Date.now() - start;
    const objectType = extractObjectType(path);
    const objectId = extractObjectId(path);

    const record: AuditRecord = {
      ts: new Date().toISOString(),
      portalId: credential.portalId,
      clientSlug: credential.clientSlug,
      method,
      path,
      statusCode: res.status,
      durationMs,
      objectType,
      objectId,
      actor: "hubspot-agency-router/2.0.0",
      rateLimitRemaining: parseInt(
        res.headers.get("X-HubSpot-RateLimit-Daily-Remaining") ?? "0",
        10
      ),
    };

    // Fire-and-forget — do not block the response on audit write
    Promise.resolve(auditWriter(record)).catch((err) => {
      console.error("Audit write failed — call was NOT prevented:", err);
    });

    return res;
  };
}

function extractObjectType(path: string): string | undefined {
  const match = path.match(/\/crm\/v\d+\/objects\/([^/?]+)/);
  return match?.[1];
}

function extractObjectId(path: string): string | undefined {
  const match = path.match(/\/crm\/v\d+\/objects\/[^/?]+\/(\d+)/);
  return match?.[1];
}
```

The audit writer can be any function that accepts an `AuditRecord` — write to stdout (structured JSON), append to a file, push to a database, or forward to a logging pipeline. The factory does not care.

### 4. Router class (ties credentials + audit + identity together)

```typescript
class HubSpotAgencyRouter {
  private store: PortalCredentialStore;
  private clientCache = new Map<string, ReturnType<typeof createPortalClient>>();
  private auditWriter: AuditWriter;

  constructor(store: PortalCredentialStore, auditWriter: AuditWriter) {
    this.store = store;
    this.auditWriter = auditWriter;
  }

  getClient(clientSlug: string): ReturnType<typeof createPortalClient> {
    if (!this.store.portals[clientSlug]) {
      throw new Error(
        `No credential found for client slug "${clientSlug}". ` +
        `Available slugs: ${Object.keys(this.store.portals).join(", ")}`
      );
    }
    if (!this.clientCache.has(clientSlug)) {
      this.clientCache.set(
        clientSlug,
        createPortalClient(this.store.portals[clientSlug], this.auditWriter)
      );
    }
    return this.clientCache.get(clientSlug)!;
  }

  listClients(): string[] {
    return Object.keys(this.store.portals).sort();
  }

  getPortalId(clientSlug: string): number {
    const cred = this.store.portals[clientSlug];
    if (!cred) throw new Error(`Unknown client slug: ${clientSlug}`);
    return cred.portalId;
  }
}

// Startup
const store = await loadCredentialStore();
const router = new HubSpotAgencyRouter(store, (record) => {
  process.stdout.write(JSON.stringify(record) + "\n");
});

// Usage — every call is slug-scoped; no ambient credential
const client = router.getClient("acme-corp");
const contacts = await client("/crm/v3/objects/contacts?limit=10");
```

### 5. Rate-limit attribution (closes quota confusion)

Each portal's 500K daily quota is tracked independently by HubSpot — but only if the token used for each portal belongs exclusively to that portal. A shared token collapses all quota into the token's home portal, making the remaining-quota header meaningless for any client except the token's owner.

Read the `X-HubSpot-RateLimit-Daily-Remaining` header from every response and log it with the `clientSlug`. When any portal's remaining quota drops below a threshold, throttle that portal's calls — not the agency's calls globally.

```typescript
const RATE_LIMIT_WARN_THRESHOLD = 50_000; // warn at 50K remaining of 500K daily

// Inside the audit writer
function checkRateLimit(record: AuditRecord): void {
  if (
    record.rateLimitRemaining !== undefined &&
    record.rateLimitRemaining < RATE_LIMIT_WARN_THRESHOLD
  ) {
    console.warn(JSON.stringify({
      event: "rate_limit_warning",
      clientSlug: record.clientSlug,
      portalId: record.portalId,
      dailyRemaining: record.rateLimitRemaining,
      threshold: RATE_LIMIT_WARN_THRESHOLD,
    }));
  }
}
```

### 6. Bulk onboarding script (closes the bottleneck)

The bulk onboarding script reads a CSV of client slugs, HubSpot tokens, and expected portal IDs. It validates each token against `account-info/v3/details`, confirms portal identity, and seeds the credential store. See `references/implementation-guide.md` for the full Python implementation.

Quick-verify a single portal from the CLI before seeding:

```bash
# Verify a token returns the expected portal ID
TOKEN="pat-na1-your-token-here"
EXPECTED_PORTAL_ID="12345678"

curl -s "https://api.hubapi.com/account-info/v3/details" \
  -H "Authorization: Bearer $TOKEN" | \
  jq --argjson expected "$EXPECTED_PORTAL_ID" '
    if .portalId == $expected
    then "OK — portal \(.portalId) (\(.portalType))"
    else "MISMATCH — token belongs to portal \(.portalId), expected \($expected)"
    end
  '
```

### 7. Token rotation runbook (closes the cascade problem)

HubSpot does not offer an API for rotating private-app tokens. Rotation happens in the HubSpot Settings UI, which immediately revokes the old token and generates a new one. The cascade problem is that with 50 portals, any system that stored the old token (secret manager, CI secrets, staging environment, webhook receiver) must be updated before the old token is revoked — or it will fail immediately.

**Rotation order matters: update all consuming systems BEFORE revoking the old token in HubSpot.**

See `references/implementation-guide.md` for the per-portal rotation runbook with a cross-system checklist.

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `200 OK` with wrong `portalId` | Identity mismatch on `account-info` | Token belongs to a different portal than expected | Reject the token; do not admit to credential store; flag for human review |
| `401 UNAUTHORIZED` | `INVALID_AUTHENTICATION` | Token revoked, malformed, or sent to wrong datacenter endpoint | Verify token format matches datacenter; check if a rotation left stale token in store |
| `403 FORBIDDEN` | `MISSING_SCOPES` | Private app does not have the required scope | Re-create private app with correct scopes; update token in credential store |
| `403 FORBIDDEN` | `PORTAL_SUSPENDED` | Client portal is suspended or deactivated | Contact client; stop all calls for this slug |
| `404 NOT_FOUND` | Resource does not exist | Object ID does not exist in this portal | Normal — handle in application logic; log objectType and objectId for audit |
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | Portal's 500K daily quota exhausted | Back off with `Retry-After`; alert on daily-remaining; do NOT retry blind |
| `429 TOO_MANY_REQUESTS` | `TEN_SECONDLY_ROLLING` | 100–150 calls/10s burst limit hit | Exponential backoff with jitter; this is per-portal, not per-agency |
| `503 SERVICE_UNAVAILABLE` | HubSpot outage | HubSpot API unavailable | Back off with jitter; check status.hubspot.com; do not rotate credentials |

### Cross-portal contamination detection

If a write operation (POST/PATCH/DELETE) succeeds but the response body's `portalId` (available on some endpoints) does not match the expected portal, you have a contamination event. Stop immediately:

```typescript
async function assertPortalSafety(
  response: Response,
  expectedPortalId: number,
  clientSlug: string
): Promise<void> {
  const body = await response.clone().json().catch(() => null);
  if (body?.portalId && body.portalId !== expectedPortalId) {
    throw new Error(
      `CRITICAL: Cross-portal contamination detected. ` +
      `Write intended for portal ${expectedPortalId} (${clientSlug}) ` +
      `landed in portal ${body.portalId}. ` +
      `Halt all operations and audit credential store immediately.`
    );
  }
}
```

## Examples

### Onboard a single client portal

```bash
# 1. Verify the token belongs to the expected portal
TOKEN="pat-na1-abc123..."
EXPECTED="12345678"
curl -s "https://api.hubapi.com/account-info/v3/details" \
  -H "Authorization: Bearer $TOKEN" | jq '{portalId, portalType, currency}'

# 2. Add to credential store (read existing, append, write back)
STORE=$(pass show hubspot/agency-portals | python3 -c "import sys,json; d=json.load(sys.stdin); \
  d['portals']['new-client']={'token':'$TOKEN','portalId':$EXPECTED,'clientSlug':'new-client',\
  'addedAt':'$(date -u +%Y-%m-%dT%H:%M:%SZ)','lastRotatedAt':'$(date -u +%Y-%m-%dT%H:%M:%SZ)',\
  'datacenter':'na1'}; d['version']+=1; print(json.dumps(d))" )
echo "$STORE" | pass insert -e hubspot/agency-portals
```

### Bulk onboard from CSV

```bash
# clients.csv format: clientSlug,portalToken,expectedPortalId
# acme-corp,pat-na1-abc...,12345678
# beta-inc,pat-eu1-def...,87654321

python3 references/bulk-onboard.py \
  --csv clients.csv \
  --secret-backend pass \
  --secret-path hubspot/agency-portals \
  --dry-run  # remove --dry-run to commit
```

### Generate a per-client compliance report

```bash
# Summarize API calls for acme-corp in May 2026
python3 references/compliance-report.py \
  --audit-log /var/log/hubspot-agency/audit.jsonl \
  --client-slug acme-corp \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --output acme-corp-jan-2026-compliance.csv
```

### Rate limit check across all portals

```bash
# Poll account-info for each portal and report daily remaining
for slug in $(pass show hubspot/agency-portals | jq -r '.portals | keys[]'); do
  TOKEN=$(pass show hubspot/agency-portals | jq -r ".portals[\"$slug\"].token")
  REMAINING=$(curl -si "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
    -H "Authorization: Bearer $TOKEN" | grep -i x-hubspot-ratelimit-daily-remaining | awk '{print $2}' | tr -d '\r')
  echo "$slug: $REMAINING remaining"
done
```

## Output

- Credential store seeded with per-portal records, each verified against `account-info/v3/details`
- Per-portal HTTP client factory with audit-log middleware on every call
- Structured audit log emitting JSON records with portalId, clientSlug, method, path, statusCode, durationMs, rateLimitRemaining
- Rate-limit warnings per portal when daily remaining drops below configurable threshold
- Bulk onboarding script that validates and seeds 10-100 portals from a CSV in a single pass
- Token rotation runbook with cross-system checklist preventing partial rotation
- Compliance report generator producing per-client call counts by date range from audit logs

## Resources

- [HubSpot Account Info API](https://developers.hubspot.com/docs/reference/api/account-management/account-information)
- [HubSpot Private Apps Guide](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [Rate Limits Reference](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [GDPR and HubSpot Data Processing](https://legal.hubspot.com/dpa)
- [API_REFERENCE.md](references/API_REFERENCE.md) — account-info endpoint shape, per-portal rate limit headers, audit log schema
- [implementation-guide.md](references/implementation-guide.md) — credential store design, bulk onboarding script, rotation runbook, compliance report generator

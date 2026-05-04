---
name: guidewire-install-auth
description: Authenticate production Guidewire Cloud API integrations and survive the auth-side failures — token expiry storms, scope drift, private-CA PKIX errors, secret rotation. Use when hardening OAuth2 token caching, configuring JVM trust stores, or rotating client secrets without downtime. Trigger with "guidewire auth", "guidewire OAuth2", "guidewire token cache", "guidewire PKIX", "guidewire secret rotation".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(java:*), Bash(keytool:*), Bash(openssl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - oauth2
  - authentication
  - token-management
  - secret-rotation
  - pkix
---

# Guidewire Install & Auth

## Overview

Authenticate a backend service to a Guidewire Cloud tenant using OAuth2 client credentials and operate the auth layer in production. This is not a hello-world walkthrough; it is the auth code your service runs at 3am when a token expires mid-batch, when a tenant admin rotates a scope, when a private CA renews a cert, and when on-call needs to swap a leaked secret without dropping in-flight requests.

The four production failures this skill prevents:

1. **Token expiry storms** — every request races to refresh, the Hub rate-limits the auth endpoint, the integration cascades to red.
2. **Scope drift** — a GCC admin removes a scope, every cached token starts returning `403`, retrying does not help.
3. **PKIX path building failed** — JVM cannot validate the tenant's TLS chain because the private CA is not in the trust store; common when carriers front Cloud API with their own DLP appliance.
4. **Secret rotation downtime** — the active client secret is rotated and the old secret stops working before the new one is loaded; in-flight token refreshes fail until restart.

## Prerequisites

- JDK 17 (Guidewire Cloud release `202503` and later)
- A registered **Service Application** in Guidewire Cloud Console (GCC) with Cloud API roles assigned per least privilege
- Network egress from your runtime to `*.guidewire.net` (runtime APIs) and `gcc.guidewire.com` (console only)
- A secret store the runtime can read at startup and on rotation signal (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, or Kubernetes Secret with CSI driver)
- For private-CA tenants: the carrier's CA chain in PEM form

## Instructions

Build the auth layer in this order. Each section solves one production failure mode; do not skip steps because the failure shows up in production, not in dev.

1. Implement the **token-cache pattern** below — proactive refresh, single-flight gate, JWT-based expiry.
2. Wire **secret rotation** to your secret store; do not commit secrets or bake them into images.
3. For private-CA tenants, install the **trust store** at the JVM/init-container layer.
4. Validate **scope hardening** on every refresh so drift fails fast, not on the next business call.

### Token-cache pattern (production)

Tokens are short-lived, typically one hour. Reactive refresh on `401` is wrong: it doubles latency on the failing request and creates a thundering herd when many requests notice expiry simultaneously. Cache the token in-process and refresh **proactively** at 80% of TTL, behind a single-flight gate so concurrent refreshers serialize.

```typescript
import jwt from "jsonwebtoken";

type Cached = { value: string; expiresAt: number };
let cached: Cached | null = null;
let inflight: Promise<string> | null = null;

export async function getToken(): Promise<string> {
  if (cached && Date.now() < cached.expiresAt - 60_000) return cached.value;
  if (inflight) return inflight;

  inflight = (async () => {
    const res = await fetch(process.env.GW_AUTH_URL!, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "client_credentials",
        client_id: process.env.GW_CLIENT_ID!,
        client_secret: process.env.GW_CLIENT_SECRET!,
        scope: process.env.GW_SCOPES!,
      }),
    });
    if (!res.ok) throw new Error(`auth ${res.status}: ${await res.text()}`);
    const { access_token } = await res.json();
    const { exp } = jwt.decode(access_token) as { exp: number };
    // exp is seconds since epoch; multiply by 1000 for JS ms. Refresh at 80% of remaining TTL.
    const expMs = exp * 1000;
    cached = { value: access_token, expiresAt: expMs - 0.2 * (expMs - Date.now()) };
    return access_token;
  })().finally(() => { inflight = null; });

  return inflight;
}
```

The `exp - 20%` early-refresh window absorbs clock skew and prevents the cliff at TTL boundary. The `inflight` single-flight gate makes a high-rps service issue one refresh per cache-miss, not one per concurrent request — without it, a 1000-rps service produces 1000 simultaneous Hub calls and trips `429` rate-limiting on the auth endpoint.

### Secret rotation without downtime

Rotation breaks if the runtime reads the secret only at startup, or if the plaintext lives somewhere reviewable (committed `.env`, container image layer, unencrypted Kubernetes `Secret`). Three patterns work, in order of operational simplicity:

**SOPS + age (recommended for VM/container deployments).** Encrypt `secrets.prod.sops.yaml` with one or more age public keys, commit the encrypted file to git, decrypt in-process at startup and on `SIGHUP`. The repo holds an auditable history of who rotated what and when; only holders of the age private key can read plaintext. Bootstrap a repo with the same conventions used across this organization:

```bash
sops-init                                    # idempotent; writes .sops.yaml + .env.sops + scripts/sops-env
sops [secrets.prod.sops.yaml](secrets.prod.sops.yaml)   # interactive edit; ciphertext re-written on save
eval "$(sops -d secrets.prod.sops.yaml | sed -nE 's/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/export \1=\2/p')"
```

The anchored `sed` regex is non-negotiable: a naive `sed 's/^/export /'` turns blank lines and comments into bare `export` calls, and bare `export` dumps every exported variable to stdout — every secret leaks if anything captures that stdout (cron mail, an SSH session running this).

**Cloud-native projection (managed Kubernetes / cloud VMs).** Mount the secret as a file from the secret store via Vault Agent, the Secrets Store CSI driver, or AWS Secrets and Configuration Provider. The orchestrator handles restart-on-rotation and the runtime re-reads the file on each token refresh.

**Dual-secret env-var window (manual rotation, last resort).** Configure the runtime with both `GW_CLIENT_SECRET_PRIMARY` and `GW_CLIENT_SECRET_SECONDARY`. On `invalid_client` from the primary, fall back to the secondary; on success, schedule the swap. Close the window when monitoring confirms 24h of zero primary failures.

### Private-CA trust store setup (PKIX)

When a carrier fronts Cloud API with a DLP appliance or proxy that re-signs TLS with a private CA, the JVM rejects the chain. Symptom: `PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException`.

Fix at the JVM level, not the application level:

```bash
keytool -importcert \
  -alias guidewire-tenant-ca \
  -file ./tenant-ca.pem \
  -keystore "$JAVA_HOME/lib/security/cacerts" \
  -storepass changeit -noprompt
```

For Kubernetes deployments, bake the CA into a sidecar that runs `keytool` against a shared `cacerts` volume, or use `JAVA_OPTS=-Djavax.net.ssl.trustStore=/etc/ssl/cacerts.jks`. Do not disable validation with `-Dcom.sun.net.ssl.checkRevocation=false` or trust-all SSL contexts; the OWASP A02 audit will find that too.

### Scope hardening

Assign roles per least privilege under **GCC > Identity & Access > Applications > [your-app] > Permissions**. A read-only reporting integration should not hold `pc.account.write`; a webhook consumer should not hold `pc.policy.bind`. Scope strings are tenant-configured and vary across environments, so do not hard-code them — read from `GW_SCOPES` and validate at startup that the issued token contains the expected scopes:

```typescript
const decoded = jwt.decode(token) as { scope: string };
const required = (process.env.GW_REQUIRED_SCOPES || "").split(" ");
const granted = decoded.scope.split(" ");
const missing = required.filter(s => !granted.includes(s));
if (missing.length) throw new Error(`scope drift: missing ${missing.join(", ")}`);
```

Run this check on every token refresh. It catches scope drift the moment a tenant admin removes a permission, instead of letting it surface as `403` on the next business call.

## Output

A production-grade auth layer ships with all of the following:

- A token cache with proactive refresh (80% TTL), single-flight gate, and JWT-based expiry calculation rather than fixed 3600s assumption.
- Secret loading from a runtime-readable secret store (CSI / Vault Agent / dual-secret env), not a `.env` file or container image.
- JVM trust store containing the tenant's CA chain when applicable, configured at the JVM or sidecar layer rather than at application startup.
- Scope-drift detection on every refresh, failing fast on missing required scopes.
- Structured logs distinguishing `invalid_client`, `invalid_scope`, expired token, and PKIX failures — recognizable in the observability dashboard before they cascade.

## Examples

### Example 1 — Production token-cache module (TypeScript)

The `getToken()` snippet above is the canonical implementation. Drop it into the integration's auth module and call it from every Cloud API request wrapper. Validates against scope drift on each refresh; absorbs Hub-side 5xx with retry-once.

### Example 2 — SOPS + age rotation (Bash)

```bash
# Edit the encrypted file in-place; sops handles re-encryption transparently
sops secrets.prod.sops.yaml         # change GW_CLIENT_SECRET_SECONDARY to the newly issued value
git add secrets.prod.sops.yaml && git commit -m "rotate(gw): issue secondary client secret"

# In the runtime startup or SIGHUP handler — anchored regex prevents bare-export leak
eval "$(sops -d secrets.prod.sops.yaml | sed -nE 's/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/export \1=\2/p')"
# Monitor: zero invalid_client failures from primary for 24h, then promote secondary → primary
```

### Example 3 — PKIX recovery for private-CA tenant

```bash
# Pull the tenant's chain straight from the endpoint
echo | openssl s_client -connect "[TENANT].guidewire.net:443" -servername "[TENANT].guidewire.net" -showcerts 2>/dev/null \
  | sed -ne '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' > tenant-chain.pem

# Import into JVM trust store (do this in the Dockerfile or init container, not at runtime)
keytool -importcert -alias gw-tenant-ca -file tenant-chain.pem \
  -keystore "$JAVA_HOME/lib/security/cacerts" -storepass changeit -noprompt
```

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `invalid_client` (400 from `/oauth/token`) | wrong `client_id`/`client_secret`, or app disabled in GCC | verify in **GCC > Identity & Access > Applications**; if mid-rotation, fall back to secondary secret per dual-secret pattern |
| `invalid_scope` (400 from `/oauth/token`) | requested scope not granted to this app, or tenant admin removed it | scope-drift check on every refresh catches this immediately; alert and re-issue from GCC |
| `401 Unauthorized` (from Cloud API) | token expired before next refresh window | indicates clock skew or aggressive proxy caching; tighten the early-refresh window from 20% to 30% |
| `403 Forbidden` (from Cloud API) | token valid but app lacks the role for that resource | least-privilege violation surfaced — assign the role in GCC, do not retry |
| `409 Conflict` (from PATCH/POST) | stale `checksum` on the resource | not an auth error — covered in `guidewire-sdk-patterns` |
| `PKIX path building failed` | private-CA cert chain missing from JVM trust store | import per the trust-store section above; fix at JVM/init-container layer, not in code |
| `ENOTFOUND [TENANT].guidewire.net` | DNS or firewall blocking egress to runtime API domain | confirm `*.guidewire.net` egress; runtime APIs are NOT on `*.guidewire.com` (that is the console) |
| `429 Too Many Requests` from Hub `/oauth/token` | thundering herd refresh from token cache without single-flight | the `inflight` gate in the token-cache pattern prevents this; verify it's active |

For deeper coverage (M2M vs delegated flows, mTLS-fronted tenants, multi-region failover, GCC scope auditing), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-sdk-patterns` — wraps this auth into a retrying, rate-limit-aware Cloud API client; handles checksum-based optimistic locking
- `guidewire-security-and-rbac` — secret storage architecture, least-privilege role design, audit capture, PII redaction in logs
- `guidewire-observability-and-incident-response` — triage trees and recovery playbooks for 401 spikes, scope drift, and PKIX cascades in production
- `guidewire-ci-cd-pipeline` — credential rotation across promoted environments without breaking running deployments

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Authentication overview](https://docs.guidewire.com/education/cloud-integration-basics/latest/docs/integration_cloud_basics/rest_api_client_overview/)
- [PolicyCenter Cloud API reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [ClaimCenter Cloud API reference](https://docs.guidewire.com/cloud/cc/202407/apiref/)
- [OWASP A02:2021 — Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)

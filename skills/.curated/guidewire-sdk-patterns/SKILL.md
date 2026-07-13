---
name: guidewire-sdk-patterns
description: Build a production-grade Guidewire Cloud API client that survives the request-side failures — 409 checksum conflicts on PATCH/PUT, 429 quota throttling, offsetToken pagination drift, retry-unsafe POSTs, and unstructured error responses. Use when designing an HTTP client wrapper around PolicyCenter, ClaimCenter, or BillingCenter REST endpoints. Trigger with "guidewire client", "guidewire sdk", "checksum 409", "guidewire pagination", "guidewire rate limit", "Retry-After".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - rest-client
  - retry
  - idempotency
  - rate-limiting
  - pagination
---

# Guidewire SDK Patterns

## Overview

Build the Cloud API request layer that runs in production. This skill assumes the auth layer from `guidewire-install-auth` is in place — bearer tokens come from the cached token provider, not a static `API_KEY`. What this layer adds: safe mutations under optimistic locking, retry-aware writes, quota-friendly request pacing, complete pagination, and a typed error surface that business logic can pattern-match.

Five production failures this skill prevents:

1. **409 Conflict storms** — client GETs a record, lets the user (or workflow) edit it, then PATCHes back without the latest `checksum`; the next concurrent edit causes both PATCHes to lose.
2. **429 cascades** — every retry on `429` happens at the same backoff, all clients hammer the endpoint together, the tenant rate quota stays pinned.
3. **Silent data loss in pagination** — client treats `pageSize=100` as "all results"; misses page 2 onward; reports inflated coverage to downstream.
4. **Duplicate writes on retry** — POST to create-claim times out at the load balancer, client retries, two claims land with the same FNOL.
5. **Generic error handling** — every non-2xx response collapses into "request failed", losing the `userMessage`, `errors[].type`, and `attributes` structure the API actually returns.

## Prerequisites

- A working auth layer per `guidewire-install-auth` — `getToken()` returning a cached, scope-validated bearer
- Cloud API endpoints reachable on `[TENANT].guidewire.net` (PC/CC/BC base URLs in env)
- Node 20+ or equivalent runtime supporting `fetch`, `AbortController`, and `crypto.randomUUID`
- Familiarity with the Cloud API response envelope (`data[]`, `attributes`, `checksum`, `links`) — see `guidewire-install-auth/references/API_REFERENCE.md`

## Instructions

Implement the patterns below as composable layers on top of `fetch`. Each pattern targets one of the five production failures listed in Overview; do not skip any layer in production code.

### 1. Checksum round-trip for safe mutations

Every Cloud API resource carries a `checksum`. PATCH and PUT must echo the latest checksum in the request body, or the API returns `409 Conflict` to protect concurrent writers. Wrap mutations in a fetch-then-mutate helper that does the round-trip automatically.

```typescript
export async function patchResource<T>(path: string, mutate: (current: T) => Partial<T>): Promise<T> {
  const token = await getToken();
  const getRes = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!getRes.ok) throw await mapError(getRes, "GET", path);
  const { data: current } = await getRes.json();

  const patchRes = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      data: { attributes: mutate(current.attributes), checksum: current.checksum },
    }),
  });
  if (!patchRes.ok) throw await mapError(patchRes, "PATCH", path);
  return (await patchRes.json()).data;
}
```

When 409 still occurs (rare race), the caller should retry the helper itself, not the inner PATCH — the inner PATCH would just hit 409 again with the same stale checksum.

### 2. Retry-After-aware rate limiting

On `429 Too Many Requests`, Cloud API returns a `Retry-After` header that is either an integer (seconds) or an HTTP date. Honour both forms; never use a fixed backoff. Combine with exponential-with-jitter for transient `5xx` so concurrent clients do not synchronize their retries.

```typescript
async function backoffFor(res: Response, attempt: number): Promise<number> {
  if (res.status === 429) {
    const ra = res.headers.get("Retry-After");
    if (ra) return /^\d+$/.test(ra) ? Number(ra) * 1000 : Math.max(0, Date.parse(ra) - Date.now());
  }
  // Decorrelated jitter: caps the herd, keeps p99 sane
  return Math.min(30_000, Math.random() * (200 * 2 ** attempt));
}
```

### 3. Pagination via offsetToken

Cloud API does not page by number. The response carries `links.next.href` until the data is exhausted; absence of `links.next` is the terminator. Iterate as a generator so callers do not buffer the whole dataset.

```typescript
export async function* paginate<T>(path: string): AsyncGenerator<T> {
  let next: string | null = path;
  while (next) {
    const token = await getToken();
    const res = await fetch(`${BASE}${next}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw await mapError(res, "GET", next);
    const body = await res.json();
    for (const item of body.data) yield item.attributes as T;
    next = body.links?.next?.href ?? null;
  }
}
```

### 4. Idempotency-Key for retry-safe writes

POST is not naturally idempotent. A timeout at the load balancer can cause the client to retry a request the API already processed — duplicate claim, duplicate payment, duplicate activity. Cloud API accepts an `Idempotency-Key` header; supplied keys deduplicate within a 24-hour window. Generate a v4 UUID per logical operation (not per HTTP attempt).

```typescript
export async function createClaim(payload: NewClaim): Promise<Claim> {
  const idempotencyKey = crypto.randomUUID(); // generated once, reused across retries
  return retryable(async () => {
    const token = await getToken();
    const res = await fetch(`${BASE}/cc/rest/v1/claims`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ data: { attributes: payload } }),
    });
    if (!res.ok) throw await mapError(res, "POST", "/cc/rest/v1/claims");
    return (await res.json()).data;
  });
}
```

### 5. Structured error mapping

Cloud API error bodies are structured: `{ userMessage, errors: [{ message, type, attributes }] }`. Lift the structure into a typed exception so business logic can pattern-match (`if (e instanceof GwBusinessRuleError)` rather than `if (msg.includes("policy"))`).

```typescript
export class GwError extends Error {
  constructor(public status: number, public op: string, public path: string,
              public body: { userMessage?: string; errors?: { type?: string; message: string; attributes?: unknown }[] }) {
    super(body.userMessage ?? `${op} ${path} failed: ${status}`);
  }
  is(type: string): boolean { return !!this.body.errors?.some(e => e.type === type); }
}

async function mapError(res: Response, op: string, path: string): Promise<GwError> {
  const body = await res.json().catch(() => ({}));
  return new GwError(res.status, op, path, body);
}
```

## Output

A production-grade Cloud API client ships with all five layers wired:

- `patchResource(path, mutate)` and `putResource(path, replace)` helpers performing checksum round-trip — callers never touch raw `checksum` fields.
- A `retryable(fn)` wrapper using `backoffFor()` to honour `Retry-After` and apply jitter on transient `5xx`.
- `paginate(path)` async generator yielding all records without buffering; callers iterate naturally.
- `Idempotency-Key` set on every POST, with the key generated once per logical operation and persisted across retries.
- `GwError` exceptions exposing `.status`, `.op`, `.path`, structured `.body`, and `.is(type)` for pattern matching.

## Examples

### Example 1 — Safe policy update under concurrent writers

```typescript
const updated = await patchResource<Policy>("/pc/rest/v1/policies/pc:8001", current => ({
  expirationDate: addYears(current.expirationDate, 1),
}));
```

The helper performs GET, applies the mutation, PATCHes back with the latest `checksum`. If two services update the same policy simultaneously, one wins, the other gets 409 and can retry the helper for a clean re-merge.

### Example 2 — Bulk import with quota-friendly pacing

```typescript
const claims: NewClaim[] = await loadFnolBatch();
for (const claim of claims) {
  await retryable(() => createClaim(claim)); // honours Retry-After on 429, jitter on 5xx
}
```

A 10,000-record batch import that respects the tenant quota without manual rate calculations. The single-flight token cache from `guidewire-install-auth` keeps Hub calls bounded as well.

### Example 3 — Pagination without surprises

```typescript
let total = 0;
for await (const acct of paginate<Account>("/pc/rest/v1/accounts?pageSize=100")) {
  await indexAccount(acct);
  total++;
}
console.log(`indexed ${total} accounts`);
```

`paginate()` follows `links.next.href` until exhausted; the caller cannot accidentally truncate at page 1.

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `409 Conflict` on PATCH/PUT | stale `checksum` — another writer mutated the resource between your GET and PATCH | retry the **outer** helper (re-GET + re-mutate); retrying the PATCH alone re-uses the stale checksum and will 409 again |
| `429 Too Many Requests` | tenant quota exceeded | honour `Retry-After`; if it recurs, the client is missing a token-bucket layer or another integration shares the tenant quota |
| `400 Bad Request` with `errors[].type === "invalid-attribute"` | validation failure on a field | inspect `errors[].attributes` for the offending path; do not blanket-retry |
| `422 Unprocessable Entity` with `errors[].type === "rule-violation"` | Gosu business rule rejected the payload | not a transport failure — surface `userMessage` to the caller, do not retry |
| `502/503/504` | transient gateway or upstream blip | retry with `backoffFor()` jitter, max 3 attempts |
| Duplicate POST when `Idempotency-Key` is omitted or per-attempt | client treated each retry as a new logical operation | generate the key once per logical operation, reuse across retries |
| Truncated dataset from a paginating endpoint | caller treated first page as complete | replace ad-hoc pagination with the `paginate()` generator |
| `userMessage` lost in logs | error wrapper stringified the body and discarded structure | use `GwError` and log `.body.errors` separately |

For a deeper reference on Cloud API request shapes, the batch endpoint, the `included` parameter for N+1 elimination, and HTTP/2 connection pooling, see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — token provider, scope hardening, secret rotation; this skill consumes `getToken()` from there
- `guidewire-core-workflow-a` — applies these patterns to the PolicyCenter account → submission → quote → bind pipeline
- `guidewire-core-workflow-b` — applies these patterns to the ClaimCenter FNOL → reserve → settle pipeline
- `guidewire-observability-and-incident-response` — interpretation of 409/429/5xx signals in production dashboards

## Resources

- [Guidewire Cloud API reference (PolicyCenter)](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud API reference (ClaimCenter)](https://docs.guidewire.com/cloud/cc/202407/apiref/)
- [Guidewire Cloud Integration developer guide](https://docs.guidewire.com/education/cloud-integration-basics/latest/)
- [RFC 7231 — HTTP Retry-After header semantics](https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3)
- [AWS — exponential backoff and jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

# Notion Production Deployment Checklist — Full Section Detail

The 12 sections below are the authoritative checklist. Work through each sequentially,
marking items pass or fail. A single fail in sections 1-6 is a deployment blocker.

---

## Section 1: Token Stored in Environment Variables (Never Hardcoded)

Production tokens must never appear in source code, config files committed to git, or client-side bundles.

- [ ] `NOTION_TOKEN` loaded from environment variable or secret manager (AWS Secrets Manager, GCP Secret Manager, Vault, Vercel env vars)
- [ ] No tokens in source code — verify: `grep -rn "ntn_\|secret_\|NOTION.*=.*ntn" --include="*.ts" --include="*.js" --include="*.env" .`
- [ ] No tokens in git history: `git log -p --all -S "ntn_" -- "*.ts" "*.js" "*.env"`
- [ ] `.env` and `.env.*` files are in `.gitignore`
- [ ] Token rotation procedure documented — who rotates, how to deploy new token without downtime

```typescript
// CORRECT: Token from environment
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// WRONG: Hardcoded token — immediate security incident
const notion = new Client({ auth: 'ntn_R8dkf92jfKLsd9f2...' });
```

**Fail criteria:** Any token found in source, git history, or client bundle.

---

## Section 2: Integration Has Minimum Required Capabilities

Notion integrations request capability scopes at creation time. Production integrations must follow least-privilege.

- [ ] Integration capabilities reviewed at <https://www.notion.so/my-integrations>
- [ ] Only required capabilities enabled (no "Read user information" unless explicitly needed)
- [ ] "Insert content" vs "Update content" scoped appropriately
- [ ] No "Internal Integration Token" used for public-facing apps (use OAuth instead)

| Capability | Enable if |
| --- | --- |
| Read content | Reading pages or databases |
| Update content | Modifying existing pages/blocks |
| Insert content | Creating new pages or appending blocks |
| Read comments | Reading page comments |
| Create comments | Adding comments to pages |
| Read user info | Resolving user names/emails (rarely needed) |

**Fail criteria:** Integration has capabilities it does not use in production code paths.

---

## Section 3: All Target Pages/Databases Shared with Integration

The most common production issue: the integration works in dev but fails in prod because pages are not shared.

- [ ] Every database queried via `databases.query()` is shared with the integration
- [ ] Every page retrieved via `pages.retrieve()` is shared with the integration
- [ ] Parent pages for `pages.create()` are shared with the integration
- [ ] Sharing verified programmatically at deploy time (see [access verification script](code-examples.md))
- [ ] Sharing verification runs as part of deployment health check (not just once manually)
- [ ] Documented procedure for sharing new pages/databases post-deploy

**Fail criteria:** Any target page or database returns 404 (object_not_found) when accessed by the integration.

---

## Section 4: Rate Limit Handling (3 req/sec, Exponential Backoff)

Notion enforces a hard limit of 3 requests per second per integration. Exceeding this returns HTTP 429.

- [ ] Request rate limited to 3 req/sec maximum using a queue or semaphore
- [ ] Bulk operations use a concurrency limiter (e.g., `p-queue` with `intervalCap: 3, interval: 1000`)
- [ ] No unbounded `Promise.all()` over arrays of API calls
- [ ] Exponential backoff implemented for 429 responses (SDK handles this by default)
- [ ] Backoff caps at a reasonable maximum (e.g., 30 seconds) to avoid infinite waits
- [ ] SDK `@notionhq/client` built-in retry is enabled (default behavior, not explicitly disabled)
- [ ] Monitoring tracks 429 frequency to detect capacity issues

See [rate-limited queue setup](code-examples.md) for `p-queue` implementation pattern.

**Fail criteria:** Any code path that can issue more than 3 concurrent requests without queuing.

---

## Section 5: Pagination for All List Endpoints

All Notion list endpoints return paginated results (max 100 items per page). Failing to paginate silently drops data.

- [ ] Every `databases.query()` call handles pagination
- [ ] Every `blocks.children.list()` call handles pagination
- [ ] Every `search()` call handles pagination
- [ ] Every `users.list()` call handles pagination
- [ ] `page_size` explicitly set (default is 100, max is 100)
- [ ] No assumption that results fit in a single page
- [ ] Pagination tested with a database containing >100 items
- [ ] `start_cursor` passed correctly from `next_cursor` (not from offset arithmetic)

See [generic paginator](code-examples.md) for a reusable pagination helper.

**Fail criteria:** Any list endpoint that does not loop on `has_more === true`.

---

## Section 6: Error Handling with `isNotionClientError`

The Notion SDK provides `isNotionClientError` for typed error discrimination. Using generic catch blocks loses error context.

- [ ] All Notion API calls use try/catch with `isNotionClientError` for typed handling
- [ ] Error codes handled specifically: `object_not_found`, `validation_error`, `rate_limited`, `unauthorized`, `restricted_resource`, `conflict_error`
- [ ] Errors logged with: error code, request ID (for Notion support), and timestamp
- [ ] User-facing errors do not leak internal IDs or tokens
- [ ] 401 errors trigger immediate alerts (token revoked or expired)
- [ ] 400 validation errors include the full error body in logs
- [ ] Network errors (ECONNREFUSED, ETIMEDOUT) handled separately from API errors

See [typed error handler](code-examples.md) for discriminated error handling with `APIErrorCode`.

**Fail criteria:** Any API call with a bare `catch (e) { console.log(e) }` that loses error context.

---

## Section 7: Notion-Version Header Set (2022-06-28)

Notion API responses change between versions. Pinning the version prevents unexpected breaking changes.

- [ ] `notionVersion` explicitly set in Client constructor
- [ ] Version matches the one used during development and testing
- [ ] Current stable version: `2022-06-28`
- [ ] Team aware of Notion API changelog:

```typescript
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28',  // Pin to tested version — do not omit
});
```

- [ ] If using raw HTTP calls, `Notion-Version` header is set explicitly
- [ ] API version upgrade plan documented (test in staging first, then update)

**Fail criteria:** Client created without explicit `notionVersion`, relying on SDK default that may change.

---

## Section 8: Retry Logic for 429/500/503 Responses

The `@notionhq/client` SDK retries automatically, but custom HTTP clients and edge cases need explicit retry logic.

- [ ] SDK default retry behavior verified (not disabled via constructor options)
- [ ] Custom HTTP calls (if any) implement retry for: 429, 500, 502, 503
- [ ] Retry uses exponential backoff: 1s, 2s, 4s, 8s (max 3-5 attempts)
- [ ] `Retry-After` header respected when present on 429 responses
- [ ] Non-retryable errors (400, 401, 403, 404) are NOT retried
- [ ] Circuit breaker considered for sustained 500/503 errors
- [ ] Total retry duration bounded (e.g., max 30s total wait)

See [retry with exponential backoff](code-examples.md) for implementation pattern.

**Fail criteria:** Retrying 400/401/404 errors, or no retry on 429/5xx.

---

## Section 9: Monitoring for API Failures

Production Notion integrations must have observability. Silent failures erode data integrity.

- [ ] Structured logging for every Notion API call: method, endpoint, latency, status code, request ID
- [ ] Error rate tracked (target: <1% of requests)
- [ ] Latency percentiles tracked (P50, P95, P99)
- [ ] Alerts configured per severity table below
- [ ] Health check endpoint exposed (e.g., `GET /health/notion`)
- [ ] Monitoring dashboard shows Notion API metrics separately from app metrics
- [ ] On-call runbook references `notion-incident-runbook` skill for triage steps

| Alert | Condition | Severity |
| --- | --- | --- |
| Auth failure | Any 401/403 response | P1 — token may be revoked |
| High error rate | >5% of requests failing in 5min window | P2 |
| Sustained rate limiting | >10 429s in 5min | P2 — review request patterns |
| High latency | P95 > 3000ms over 5min | P3 |
| Notion outage | `status.notion.com` incident or >50% 5xx | P2 — activate fallback |

**Fail criteria:** No alerting on auth failures or sustained errors.

---

## Section 10: Graceful Degradation When Notion Is Down

Notion experiences outages (check <https://status.notion.com>). The application must not crash when the API is unavailable.

- [ ] Read-heavy endpoints have a cache layer (Redis, in-memory, file-based)
- [ ] Cache TTL set appropriately (e.g., 5-15 minutes for dashboard data)
- [ ] Write operations queue for later retry when Notion is down (dead letter queue or local buffer)
- [ ] Users receive clear feedback: "Data may be stale — Notion is currently unavailable"
- [ ] Application remains functional in degraded mode (serves cached data, disables Notion-dependent features)
- [ ] Cache invalidation strategy documented (how stale can data get?)
- [ ] Feature flags available to disable Notion-dependent features during extended outages

See [cache with fallback](code-examples.md) for LRU cache implementation with source tracking.

**Fail criteria:** Application returns 500 to end users when Notion API is unreachable.

---

## Section 11: Data Validation for Property Types

Notion rejects malformed property values with 400 validation errors. Validate before sending.

- [ ] Page title property always provided for `pages.create()` (required by Notion)
- [ ] Select values match existing options in the database schema (Notion rejects unknown options for select, auto-creates for multi-select)
- [ ] Date properties use ISO 8601 format: `2026-04-01` or `2026-04-01T09:00:00.000-05:00`
- [ ] Rich text arrays are never empty — Notion rejects `rich_text: []`
- [ ] Number properties are actual numbers, not strings
- [ ] URL properties contain valid URLs; email properties contain valid email addresses
- [ ] Relation properties reference valid page IDs
- [ ] Property names match the production database schema exactly (case-sensitive)
- [ ] Block content respects Notion limits: 2000 chars per rich text block, 100 blocks per `blocks.children.append()`
- [ ] Input data sanitized before sending (strip control characters, validate UTF-8)

See [property validator](code-examples.md) for a validation function that catches common issues.

**Fail criteria:** 400 validation errors occurring in production due to unvalidated property data.

---

## Section 12: OAuth Token Refresh (For Public Integrations)

Public integrations using OAuth must handle token lifecycle. Internal integrations can skip this section.

- [ ] Access tokens stored securely per-workspace (encrypted at rest)
- [ ] Token exchange implemented: authorization code to access token via `POST /v1/oauth/token`
- [ ] `bot_id` and `workspace_id` stored alongside the access token for multi-tenant routing
- [ ] Token revocation handled: if Notion returns 401, prompt user to re-authorize
- [ ] User-initiated disconnect flow removes stored tokens
- [ ] Notion OAuth does NOT use refresh tokens — access tokens are long-lived but can be revoked
- [ ] Re-authorization flow tested: user clicks disconnect, then reconnects
- [ ] OAuth client secret stored in secret manager (not in code or env files)
- [ ] Redirect URI matches exactly what is registered in the Notion integration settings

See [OAuth token exchange](code-examples.md) for the authorization code exchange implementation.

**Fail criteria:** OAuth tokens stored in plaintext, or no handling for token revocation (401 responses).

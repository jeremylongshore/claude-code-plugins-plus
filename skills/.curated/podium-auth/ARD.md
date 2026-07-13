# ARD: Podium Auth

## Architecture Pattern

**Library + scripts.** The core of this skill is a small in-process token-cache library (`PodiumAuth`) plus a multi-tenant router (`PodiumOrgRouter`) plus a set of operator CLI scripts (`token_refresh.py`, `rotate_secret.py`, `verify_creds.py`, `scope_audit.py`). The library is async-first because every realistic Podium integration is webhook-driven and benefits from coroutine concurrency; the scripts are synchronous CLIs that wrap the library for operator workflows.

Pattern: **Cache-aside with single-flight, atomic side-effect persistence, and three-tier liveness monitoring.**

## Workflow

```
                     ┌──────────────────────────────┐
                     │  Application code            │
                     │  await auth.get_token()      │
                     └───────────┬──────────────────┘
                                 │
                                 ▼
                     ┌──────────────────────────────┐
        cache hit    │  PodiumAuth.get_token()      │
       (fast path) ──┤  - check _cached TTL > 80%   │
                     │  - return cached if valid    │
                     └───────────┬──────────────────┘
                                 │ cache miss
                                 ▼
                     ┌──────────────────────────────┐
                     │  asyncio.Lock acquire        │
                     │  re-check cache inside lock  │
                     └───────────┬──────────────────┘
                                 │
                                 ▼
                     ┌──────────────────────────────┐
                     │  _refresh()                  │
                     │  ├ POST /oauth/token         │
                     │  ├ validate_scopes(body)     │
                     │  ├ persist new refresh_token │
                     │  │  (atomic temp+rename)     │
                     │  └ update _cached            │
                     └───────────┬──────────────────┘
                                 │
                                 ▼
                          return access_token

           ┌──────────────────────────────────────────┐
           │  background: decay_monitor (every 1h)    │
           │  ├ read last_used_at from secret store   │
           │  ├ if age >= 60d  → log warn             │
           │  ├ if age >= 75d  → page on-call         │
           │  └ if age >= 85d  → raise on next call   │
           └──────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their problem before reading a line of code, then walks through one mitigation per failure mode in a fixed order.
- **PRD.md** is the product framing for stakeholders who need to justify the work (acceptance criteria, success metrics, risk register).
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together.
- **references/errors.md** is a flat lookup table — `ERR_AUTH_001` → cause + solution — that on-call references under stress.
- **references/examples.md** is a cookbook of full worked snippets (no truncated `...` placeholders).
- **references/implementation.md** is the language-portability layer: Node.js equivalents, secret-store-specific wiring (AWS / GCP / SOPS), and the rotation runbook.
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON-on-stdout, human-on-stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read           # read config, secret-store files, source for grep audits
  - Write          # write rotation runbook, audit reports, new config files
  - Edit           # edit .gitignore to add credential patterns
  - Bash(curl:*)   # call Podium OAuth endpoints in shell examples
  - Bash(jq:*)     # parse OAuth responses in shell examples
  - Bash(python3:*) # invoke the operator scripts
  - Bash(openssl:*) # verify TLS connectivity to Podium accounts.podium.com
  - Grep           # audit the repo for leaked secrets
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files and never makes git commits. Rotation drafts a runbook for the operator; the operator commits.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-auth/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # TTL thresholds, decay alert routing, scope list
├── references/
│   ├── errors.md              # ERR_AUTH_001..014 with cause + solution
│   ├── examples.md            # 10 worked examples
│   └── implementation.md      # Node equivalents, secret-store wiring, runbook
└── scripts/
    ├── token_refresh.py       # CLI: manual refresh + persistence
    ├── rotate_secret.py       # CLI: dual-credential rotation orchestrator
    ├── verify_creds.py        # CLI: health-check a credential pair
    └── scope_audit.py         # CLI: compare required vs granted scopes
```

## API Integration Architecture

The Podium auth surface is three endpoints. Each is wrapped by exactly one method:

| Endpoint | Method | Wrapping |
|---|---|---|
| `POST /oauth/token` | `PodiumAuth._refresh()` | Single call site; all refreshes flow through here |
| `GET /v4/me` | `verify_credential()` | Stateless function; reused by `verify_creds.py` and the rotation runbook |
| `POST /oauth/revoke` | `revoke_refresh_token()` | Called only by `rotate_secret.py` after health check passes |

All three calls share a single `httpx.AsyncClient` factory (`_client()`) with `timeout=10`, `http2=True`, and connection pooling sized to `max(2, num_orgs)` for the multi-tenant case.

## Data Flow Architecture

```
[Secret Store]                          [Podium]                  [Application]
      │                                    │                            │
      │ load refresh_token + last_used_at  │                            │
      ├───────────────────────────────────►│                            │
      │                                    │                            │
      │ POST /oauth/token (refresh_grant)  │                            │
      ├───────────────────────────────────►│                            │
      │  ◄ access_token, new refresh_token │                            │
      │                                    │                            │
      │ atomic write new refresh_token     │                            │
      │ + last_used_at = now()             │                            │
      ├──┐                                 │                            │
      │  │                                 │                            │
      │◄─┘                                 │                            │
      │                                    │                            │
      │                                    │ access_token (in memory)   │
      │                                    ├───────────────────────────►│
      │                                    │                            │
```

Persistence is the critical write — the new refresh token must hit disk before the application sees the new access token, or a crash here leaves the system unrecoverable.

## Error Handling Strategy

Three error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PodiumAuthError` (transient) | 5xx from `/oauth/token`, connection timeout | Retry with exponential backoff + jitter, max 4 attempts |
| `PodiumAuthError` (permanent) | 401 `invalid_grant`, 400 `invalid_client` | Surface to ops; refresh token is dead, user re-auth required |
| `PodiumScopeError` | Missing required scope in refresh response | Page on-call; admin re-grant required |

Retry policy is in `withRetry()` in the library. Permanent errors short-circuit retry — there is no value in retrying `invalid_grant`.

## Composability & Stacking

`podium-auth` is the **foundation layer**. Every other skill in the podium-pack depends on it for HTTP authentication. Stacking pattern:

```
podium-rag-context-bridge
        │
        ▼
podium-conversation-history-export
        │
        ▼
podium-call-transcript-pipeline ◄────── podium-webhook-reliability
        │                                       │
        ▼                                       │
podium-webchat-handler                          │
        │                                       │
        ▼                                       │
podium-review-request-automation                │
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                podium-rate-limit-survival
                        │
                        ▼
                  podium-auth   ◄── this skill
```

A consumer skill that holds a `PodiumAuth` instance gets free token refresh, scope validation, decay monitoring, and rotation support without re-implementing any of it.

## Performance & Scalability

- **Single-org throughput**: bounded by Podium's per-org rate limits, not by this skill. The cache eliminates auth-call overhead from the hot path.
- **Multi-org throughput**: linear in number of orgs (one cache + one lock per org); memory cost is O(orgs) — trivial for 50+ orgs.
- **Cold start**: one POST `/oauth/token` per org on first request. With 50 orgs and a warm-up loop, ~5 seconds to fully primed.
- **Decay monitor cost**: 1 stat-style read per org per hour. Negligible.

## Security & Compliance

- **Credentials at rest**: SOPS + age (Intent Solutions standard). Plaintext never lands on disk in prod.
- **Credentials in transit**: TLS 1.2+ enforced by Podium endpoints; library does not relax cert verification.
- **Credentials in logs**: `PodiumAuthError.body` is the raw response — error path must redact `client_secret` and `refresh_token` substrings before logging. The library does this at `__str__()` time.
- **Audit trail**: every refresh logs `{org, expires_at, scopes_granted, rotated_refresh=true|false}` as structured JSON. No tokens themselves logged.
- **Rotation**: dual-credential window required by runbook; old secret revoked only after health-check passes.

## Testing Strategy

- **Unit tests**: mock `httpx` responses for the four happy paths (refresh success, scope drift, 401, 429) and the rotation-persistence atomic-write contract.
- **Integration tests**: against a Podium sandbox OAuth app with a known fixture credential; verify a full refresh cycle and persistence.
- **Soak test**: 7-day continuous run with hourly forced refreshes against the sandbox; verify zero refresh-token loss and stable cache state.
- **Chaos test**: SIGKILL the process mid-refresh and verify the next start picks up the new refresh token (proves atomic write).
- **Decay test**: stub `time.time()` forward 60/75/85 days and verify warn/page/raise behavior.

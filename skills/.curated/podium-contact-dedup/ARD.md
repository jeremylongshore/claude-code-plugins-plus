# ARD: Podium Contact Dedup

## Architecture Pattern

**Index-then-cluster-then-merge pipeline with idempotent state.** The skill is a four-stage batch pipeline plus a set of operator CLIs. Stage 1 ingests contacts from Podium and writes a SQLite-backed natural-key index. Stage 2 scans the index for duplicate clusters and emits proposals with confidence scores. Stage 3 is the merge orchestrator — deterministic primary selection, opt-out union, conflict detection, and the merge + PATCH sequence. Stage 4 is the cross-location scanner that runs after per-location dedup completes.

Pattern: **Indexed cluster detection + deterministic primary selection + union-preserving opt-out merge + idempotent state-machine execution.**

## Workflow

```
                  ┌──────────────────────────────────┐
                  │  Operator: dedup run             │
                  │  for each location_uid:          │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │  STAGE 1: scan                   │
                  │  - GET /v4/contacts (paginated)  │
                  │  - phonenumbers.parse() each row │
                  │  - drop invalid; UPSERT valid    │
                  │  - field_count precomputed       │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │  STAGE 2: cluster                │
                  │  - GROUP BY natural_key          │
                  │  - HAVING COUNT(*) >= 2          │
                  │  - cluster_confidence(a, b)      │
                  │  - emit auto-merge vs review     │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │  STAGE 3: merge orchestrator     │
                  │  for each auto-merge cluster:    │
                  │  ├ select_primary()              │
                  │  ├ union_opt_outs()              │
                  │  ├ INSERT merge_state(pending)   │
                  │  ├ re-fetch each duplicate       │
                  │  ├   if updated_at drift → abort │
                  │  ├ POST /contacts/{p}/merge      │
                  │  ├   status = merged             │
                  │  ├ PATCH /contacts/{p} opt-outs  │
                  │  └   status = patched (terminal) │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │  STAGE 4: cross-location scan    │
                  │  (runs after all locations done) │
                  │  - GROUP BY natural_key          │
                  │  - HAVING COUNT(DISTINCT loc)>1  │
                  │  - emit human-review queue       │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                          audit-log.jsonl
                          review-queue.json
                          dedup-summary.txt

      ┌────────────────────────────────────────────────────────┐
      │  resume path (called on every run start):              │
      │  ├ SELECT * FROM merge_state WHERE status != 'patched' │
      │  ├ for each row: GET /v4/contacts/{primary_uid}        │
      │  ├   if merged in Podium → status = patched (done)     │
      │  └   else retry from current state                     │
      └────────────────────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their problem before reading a line of code, then walks through one mitigation per failure mode in a fixed order.
- **PRD.md** is the product framing for stakeholders who need to justify the work (acceptance criteria, success metrics, risk register, compliance posture).
- **ARD.md** (this document) is the engineer's reference for how the four stages fit together.
- **references/errors.md** is a flat lookup table — `ERR_DEDUP_001` → cause + solution — that on-call references under stress.
- **references/examples.md** is a cookbook of full worked snippets (no truncated `...` placeholders).
- **references/implementation.md** is the language-portability layer: Node.js port using `awesome-phonenumber`, audit log schema, and the cluster-review queue shape.
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON-on-stdout, human-on-stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read              # read config, SQLite database, audit logs
  - Write             # write merge plans, review queues, audit logs
  - Edit              # edit config thresholds, default-region settings
  - Bash(curl:*)      # call Podium API endpoints in shell examples
  - Bash(jq:*)        # parse API responses in shell examples
  - Bash(python3:*)   # invoke the operator scripts
  - Bash(sqlite3:*)   # inspect the natural-key index and merge_state from the shell
  - Grep              # audit the codebase for hardcoded numbers, secret leakage
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files (the SQLite is a long-lived asset) and never makes git commits. Dedup runs produce artifacts for human review; the operator commits.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-contact-dedup/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # region defaults, confidence thresholds, opt-out policy, cross-location policy
├── references/
│   ├── errors.md              # ERR_DEDUP_001..014 with cause + solution
│   ├── examples.md            # 10 worked examples (normalize, cluster, merge, cross-location, resume)
│   └── implementation.md      # Node port (awesome-phonenumber), audit log schema, review queue shape
└── scripts/
    ├── phone_normalize.py     # CLI: normalize a single phone to E.164 + natural_key
    ├── find_duplicates.py     # CLI: scan + cluster proposal with confidence scores
    ├── merge_contacts.py      # CLI: merge a cluster with --dry-run; opt-out union + PATCH
    └── cross_location_dedup.py # CLI: cross-location scan emitting human-review queue
```

## API Integration Architecture

The Podium surface is four endpoints. Each maps to exactly one orchestrator method:

| Endpoint | Method | Wrapping |
|---|---|---|
| `GET /v4/contacts` (paginated) | `Indexer.scan(location_uid)` | One call per page; cursor in the indexer state |
| `GET /v4/contacts/{uid}` | `Orchestrator._refetch(uid)` | Called before every merge for conflict detection |
| `POST /v4/contacts/{primary_uid}/merge` | `Orchestrator._merge(cluster)` | Body: `{duplicate_uids: [...]}` |
| `PATCH /v4/contacts/{primary_uid}` | `Orchestrator._apply_opt_outs(primary_uid, union)` | Always called immediately after `_merge()` |

All four calls share a single `httpx.Client` factory (`_client()`) with `timeout=10`, `http2=True`, and connection pooling sized to the orchestrator's concurrency (default 4). The token is loaded from `podium-auth` via `PodiumAuth.get_token()`.

## Data Flow Architecture

```
[Podium]                       [SQLite local]                  [Filesystem]
   │                                 │                              │
   │ GET /v4/contacts (page 1..N)    │                              │
   │◄────────────────────────────────┤                              │
   │                                 │                              │
   │                                 │ UPSERT contact_index rows    │
   │                                 ├──┐                           │
   │                                 │  │                           │
   │                                 │◄─┘                           │
   │                                 │                              │
   │                                 │ SELECT clusters              │
   │                                 ├──┐                           │
   │                                 │◄─┘                           │
   │                                 │                              │
   │ GET /v4/contacts/{dup_uid}      │                              │
   │ (conflict check per duplicate)  │                              │
   │◄────────────────────────────────┤                              │
   │                                 │                              │
   │                                 │ INSERT merge_state(pending)  │
   │                                 ├──┐                           │
   │                                 │◄─┘                           │
   │                                 │                              │
   │ POST /contacts/{p}/merge        │                              │
   │◄────────────────────────────────┤                              │
   │  ◄ 200 OK, soft-deleted dupes   │                              │
   │                                 │                              │
   │                                 │ UPDATE merge_state(merged)   │
   │                                 │                              │
   │ PATCH /contacts/{p} opt_outs    │                              │
   │◄────────────────────────────────┤                              │
   │  ◄ 200 OK                       │                              │
   │                                 │                              │
   │                                 │ UPDATE merge_state(patched)  │
   │                                 │                              │
   │                                 │                              │ append audit-log.jsonl
   │                                 │                              ├──┐
   │                                 │                              │◄─┘
```

The critical write is the merge_state row transitioning to `patched` AFTER the opt-out PATCH succeeds. Until that final UPDATE lands, the cluster is non-terminal and the resume path will re-evaluate it on the next run.

## Error Handling Strategy

Three error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PodiumDedupError` (transient) | 5xx, 429, network timeout | Retry with exponential backoff + jitter, max 4 attempts; cluster stays in current pending state |
| `PodiumDedupError` (permanent) | 400 invalid_duplicate_uid, 422 cross_location_merge_blocked | Mark cluster `failed_permanent`; surface to human review; do not retry |
| `PodiumDedupConflict` | `updated_at_podium` mismatch on pre-merge re-fetch | Mark cluster `re_index_required`; abort merge; next run rebuilds index for this natural_key |

Retry policy is in `withRetry()` in the orchestrator. Compliance failures (post-merge PATCH fails) have a dedicated path: `compliance_failed` cluster state, immediate page to the compliance officer's channel, and the merge stays half-complete until the PATCH is reconciled.

## Composability & Stacking

`podium-contact-dedup` stacks on three foundation skills and is consumed by two consumer skills:

```
                  podium-rag-context-bridge
                          │
                          ▼
              podium-conversation-history-export
                          │
                          ▼
                  podium-webchat-handler ◄──┐
                          │                 │ uses normalize_phone()
                          ▼                 │ for phone-as-natural-key
              podium-review-request-automation ◄─┐
                          │                      │ uses natural_key
                          ▼                      │ for "did we already
                  podium-contact-dedup ◄─────────┘ ask this person"
                          │
                          ▼
                  podium-multi-location-router  (location_uid resolution)
                          │
                          ▼
                  podium-rate-limit-survival    (per-tenant rate limits)
                          │
                          ▼
                       podium-auth             (token + scope validation)
```

A consumer skill (`podium-webchat-handler`, `podium-review-request-automation`) imports `normalize_phone` from this skill's scripts module to compute the natural key for an incoming webchat or review-request candidate, then checks the local SQLite index for an existing contact before creating a new one. This prevents new duplicates from entering the corpus at write time, not just cleaning them up after.

## Performance & Scalability

- **Index throughput**: bounded by Podium's contact listing endpoint (typically 100 contacts/page, ~5 pages/sec sustained). For a 50k corpus, full index ~2 minutes.
- **Cluster detection**: O(N) over the index with the SQL `GROUP BY natural_key HAVING COUNT(*) >= 2`. Sub-second on 50k rows.
- **Merge throughput**: bounded by Podium's per-tenant merge rate limit (~2-5 merges/sec sustained with `podium-rate-limit-survival` backoff). 1000 clusters → ~5 minutes.
- **SQLite size**: ~500 bytes/contact in the index. 50k contacts ≈ 25 MB. Trivial.
- **Memory**: cluster proposal is streamed to disk; orchestrator processes one cluster at a time. Memory cost is O(largest_cluster), typically < 100 contacts per cluster.

## Security & Compliance

- **PII at rest**: phone numbers and names land in the local SQLite. Treat the database as a PII asset — file mode 0600, owner-only, never committed to git, encrypted at rest if the host disk is unencrypted.
- **PII in logs**: the audit log records `contact_uid` (Podium-opaque) and natural keys (the customer's phone). Restrict log access to the compliance team; rotate weekly.
- **Opt-out compliance**: union-preservation is the load-bearing rule. Every audit log entry records pre-merge per-record opt-outs AND post-merge unioned opt-outs — this is the evidence trail for a compliance audit.
- **TCPA / GDPR / ACMA**: this skill is a control surface for opt-out preservation but does not implement consent capture. Consent capture lives upstream in `podium-webchat-handler` and the webhook ingest path.
- **Soft-delete only**: no path in this skill calls hard-delete. Hard-delete (GDPR erasure) is delegated to a separate compliance workflow that signs off on each erasure individually.

## Testing Strategy

- **Unit tests**: `normalize_phone` against a fixture of 100 phone strings spanning AU/US/UK formats including invalid inputs; `cluster_confidence` against pairs spanning every score combination; `select_primary` against ties on every field; `union_opt_outs` against every flag combination.
- **Integration tests**: against a Podium sandbox tenant with a synthetic 1000-contact corpus pre-populated with known duplicates; verify post-run duplicate rate is zero and every opt-out flag is preserved.
- **Soak test**: 7-day continuous run with a webhook ingestor generating ~100 new contacts/hour (some duplicates by design); verify duplicate rate stays under 1% with the dedup running every 4 hours.
- **Chaos test**: SIGKILL the orchestrator mid-merge (between merge API call and PATCH); verify the next run sees `merging` state, queries Podium, and either completes the PATCH or rolls back to retry.
- **Conflict test**: two orchestrator processes running simultaneously on overlapping clusters; verify the second process detects the `updated_at` drift and aborts with `re_index_required` rather than corrupting state.
- **Compliance test**: synthetic cluster with one opted-out duplicate and one opted-in primary; verify post-merge state has `marketing_opt_out=true`. If this test ever fails, treat as a P0 release-blocker.

# PRD: Podium Contact Dedup

## Summary

**One-liner**: Production-grade contact deduplication pipeline for Podium — E.164 phone normalization, SQLite-backed natural-key index, confidence-scored cluster detection, deterministic merge orchestration with opt-out preservation, cross-location dedup, and idempotent resumable execution.

**Domain**: SaaS integration / data quality / SMB customer-engagement platforms / compliance (TCPA, GDPR, ACMA)

**Users**: Data engineers, operations managers, compliance officers, agency operators running Podium for multi-location businesses

## Problem Statement

Podium dedups contacts on exact string match. In production, operators paste phone numbers from four different surfaces — a CRM export, a phone-screen display, a written walk-in form, a stored fragment from a webhook — and Podium happily creates four contacts for the same human. Within months a 5,000-contact corpus has 20% duplicates, the marketing team sends the same review-request SMS to the same person four times, an opted-out contact receives marketing again because a duplicate did not carry the flag, and operations cannot answer "how many unique customers do we actually have."

The six failure modes are: phone-format inconsistency producing N contacts per phone, merge-API ordering silently discarding the richer record, opt-out flags lost on merge re-enabling marketing on opted-out contacts (a compliance incident), soft-delete vs hard-delete confusion producing "contact reappeared" support tickets, cross-location blind spots where the same phone exists as two contacts in two locations, and simultaneous-merge race conditions where one operator's intent is dropped without surfacing the conflict.

The off-the-shelf Podium UI offers manual merge only — no policy, no opt-out union, no cross-location view, no audit log. This skill installs the production data-quality layer that prevents each failure mode by construction.

## Target Users

### Persona 1: Data Engineer (Dana)

- **Role**: Owns the data pipeline that ingests Podium contacts into the warehouse and pushes enrichments back. Responsible for the contact corpus being internally consistent.
- **Goals**: One canonical contact per real human; phone is always E.164; duplicate rate trends down month-over-month; dedup runs are idempotent and resumable.
- **Pain Points**: Last quarter's dedup script ran for 4 hours, crashed at 80%, and left the corpus in an unknown half-merged state with no resume capability; spent two days reconciling manually.
- **Technical Level**: High (SQL fluent, Python fluent, comfortable with API orchestration and state machines).

### Persona 2: Operations Manager (Mark)

- **Role**: Runs the location-floor for an SMB or multi-location franchise. Reads the daily "duplicate complaints" queue — customers asking why they got the same review request twice.
- **Goals**: Duplicate complaints drop to zero; staff stop having to ask "are you the same person who called last week?"; the marketing team's outbound list reflects unique humans, not duplicate rows.
- **Pain Points**: Has heard "I already gave you my number" from customers four times this week; cannot explain why Sydney and Burleigh Heads each show a separate contact for the same caller.
- **Technical Level**: Low-Medium (operates dashboards; does not write code; reads CSV exports).

### Persona 3: Compliance Officer (Casey)

- **Role**: Owns TCPA, GDPR Article 21, and ACMA Spam Act compliance for marketing communications. Signs the attestation that opt-outs are honored.
- **Goals**: Zero re-enables — once a contact opts out, that flag survives every operation (merge, restore, manual edit) for the lifetime of the data.
- **Pain Points**: A contact opted out in March, was merged in April, and received marketing in May because the merge dropped the flag. Filed an incident, paid a fine, never wants to repeat.
- **Technical Level**: Medium (reads code patterns; reviews audit logs; does not deploy).

## User Stories

### US-1: E.164 normalization (P0)

**As** a data engineer,
**I want** every phone number in the corpus normalized to E.164 with a natural key,
**So that** `+61 412 345 678`, `0412 345 678`, `(04) 1234-5678`, and `+61412345678` all index to the same row in the duplicate detector.

**Acceptance Criteria:**

- Normalization uses Google's `libphonenumber` (Python: `phonenumbers`) — no hand-rolled regex
- Invalid numbers (too short, wrong region code, parse failure) return `{valid: false, reason: ...}` and do not enter the index
- The E.164 string IS the natural key — no additional hashing required
- A default region (`AU`, `US`, etc.) is configurable per-tenant for parsing numbers in national format

### US-2: Duplicate cluster detection (P0)

**As** a data engineer,
**I want** clusters of contacts sharing a natural key surfaced with a confidence score,
**So that** auto-merge happens only above the 0.80 threshold and lower-confidence clusters route to human review.

**Acceptance Criteria:**

- Confidence formula: 0.60 (same E.164) + 0.20 (same name) + 0.15 (same email) + 0.05 (overlapping tags)
- Clusters with all pairwise scores ≥ 0.80 are auto-mergeable
- Clusters between 0.60 and 0.80 surface to a human-review queue
- The 0.60 floor is non-configurable — same phone is the required minimum signal

### US-3: Deterministic primary selection (P0)

**As** a data engineer,
**I want** the merge orchestrator to pick `primary` by a deterministic, reproducible rule,
**So that** re-running the same dedup against the same corpus produces the same merge outcome and no field is silently discarded.

**Acceptance Criteria:**

- Primary selection: `max(field_count, updated_at_podium, lowest_uid_lexical)`
- Caller cannot override the primary choice for auto-merges (override only for human-review queue)
- The "richer record wins" rule is documented in the audit log alongside every merge

### US-4: Opt-out preservation by union (P0)

**As** a compliance officer,
**I want** the strongest opt-out flag in any cluster member to win,
**So that** no merge ever re-enables marketing, SMS, or email on a person who explicitly opted out.

**Acceptance Criteria:**

- `marketing_opt_out`, `sms_opt_out`, `email_opt_out` are unioned across the cluster BEFORE the merge API call
- After Podium's merge completes, a `PATCH /contacts/{primary_uid}` immediately overwrites the opt-out fields with the unioned values
- The audit log records the pre-merge per-record opt-out state AND the post-merge unioned state
- If the post-merge PATCH fails, the merge is marked `compliance_failed` and surfaces immediately to the compliance officer's queue

### US-5: Cross-location dedup (P1)

**As** an operations manager,
**I want** the same phone across two locations to surface as a single dedup candidate,
**So that** "Sydney has a record AND Burleigh Heads has a record" stops producing two contacts for the same caller.

**Acceptance Criteria:**

- Cross-location scan runs AFTER per-location scans complete
- Output is a human-review queue by default — does NOT auto-merge across locations
- Each cross-location candidate carries both location names and the operator's last-touch evidence
- Tenants can opt into cross-location auto-merge via a per-deployment policy flag

### US-6: Soft-delete handling (P1)

**As** a data engineer,
**I want** the pipeline to treat Podium's DELETE as soft-delete and never call hard-delete,
**So that** customer-restored contacts simply re-enter the next dedup cycle rather than producing a "contact reappeared" support ticket.

**Acceptance Criteria:**

- The skill never calls hard-delete endpoints — hard delete is delegated to a separate compliance-erasure workflow
- The audit log records every merge as `soft_delete: true, restorable: true`
- A restored duplicate is detected and re-merged on the next run with a log entry noting the restore-then-remerge loop

### US-7: Idempotent resumable execution (P1)

**As** a data engineer,
**I want** a crash mid-run to leave clusters in a `pending` state that the next run picks up,
**So that** a 4-hour dedup that fails at 80% does not require manual reconciliation.

**Acceptance Criteria:**

- Every cluster operation writes a row to `merge_state` BEFORE the API call (status=pending)
- State transitions: `pending → merging → merged → patched`
- Only `patched` is terminal-success
- A resumed run queries Podium for the live state of the primary before deciding to retry vs confirm-done

### US-8: Simultaneous-merge conflict detection (P1)

**As** a data engineer,
**I want** the orchestrator to abort a merge if any duplicate has been updated since the index was built,
**So that** a race between two operators or a manual edit during an automated run surfaces as a conflict in the audit log, not as silent data loss.

**Acceptance Criteria:**

- Before each merge API call, re-fetch each duplicate and compare `updated_at_podium` to the indexed value
- A mismatch aborts the merge for this cluster, logs `conflict_detected`, and marks the cluster `re_index_required`
- The next run rebuilds the index for the affected natural keys and re-evaluates

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | E.164 normalization uses `phonenumbers` library; no hand-rolled regex parsing |
| REQ-2 | Natural-key index is SQLite-backed with indexes on `natural_key` and `(natural_key, location_uid)` |
| REQ-3 | Confidence score floor is 0.60 (non-configurable); auto-merge threshold is 0.80 (configurable per tenant) |
| REQ-4 | Primary selection is deterministic by `(field_count, updated_at_podium, lowest_uid)` |
| REQ-5 | Opt-out preservation is a union across the cluster, applied via post-merge PATCH |
| REQ-6 | Cross-location merges do not auto-execute; they surface to a human-review queue by default |
| REQ-7 | The skill never calls hard-delete; soft-delete is the only deletion semantic |
| REQ-8 | Merge state file is durable across crashes; every cluster transitions through `pending → merging → merged → patched` |
| REQ-9 | Pre-merge conflict check re-fetches each duplicate and verifies `updated_at_podium` matches the index |
| REQ-10 | All Podium API calls have a timeout (default 10s) and exponential backoff on 5xx + 429 |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/contacts?location_uid={uid}` | GET (paginated) | Populate the natural-key index |
| `https://api.podium.com/v4/contacts/{uid}` | GET | Re-fetch a duplicate for conflict detection |
| `https://api.podium.com/v4/contacts/{primary_uid}/merge` | POST | Execute the merge with `{duplicate_uids: [...]}` body |
| `https://api.podium.com/v4/contacts/{primary_uid}` | PATCH | Apply the unioned opt-out state immediately after merge |

## Non-Goals

- This skill does not implement hard-delete or GDPR erasure — that is a separate compliance workflow.
- This skill does not deduplicate on email alone; phone is the natural key. Email-only contacts (no phone) are out of scope for v2.0.
- This skill does not provide a UI for cluster review — it emits a JSON queue file consumed by an external tool (operator's CSV, a notebook, a dashboard).
- This skill does not authenticate to Podium directly — it consumes a token from `podium-auth`.
- This skill does not handle rate-limit recovery — that is `podium-rate-limit-survival`.

## Success Metrics

| Metric | Target |
|---|---|
| Duplicate rate in the contact corpus after first full run | < 1% within 30 days |
| Opt-out re-enable incidents per quarter | 0 |
| Mid-run crashes requiring manual reconciliation | 0 (every run is resumable) |
| Cross-location duplicates auto-resolved without operator review | 0 by default (policy-gated) |
| Median dedup throughput | ≥ 1000 contacts/min indexed; ≥ 100 clusters/min merged |
| Simultaneous-merge conflicts that reach silent data loss | 0 (all surface in audit log) |

## Constraints & Assumptions

- The `phonenumbers` library is current with E.164 country code allocations as of skill author date. Library updates may change parse outcomes for fringe number formats — re-validate the corpus after major library upgrades.
- Podium's merge API takes one primary and a list of duplicate_uids in a single call; the implementation assumes this contract. If Podium changes to one-duplicate-per-call, the orchestrator loops.
- The default-region setting is per-tenant; mixed-country corpora require pre-classification (e.g., by `phone_country` heuristics) before normalization. v2.0 supports a single default region per run.
- `updated_at_podium` is assumed to monotonically increase on any contact mutation. If Podium ever updates a contact without bumping this field, conflict detection becomes unreliable for that mutation type.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Opt-out PATCH fails after merge succeeds | Low | Critical (compliance) | Mark cluster `compliance_failed`; page compliance officer; retry PATCH with exponential backoff |
| `phonenumbers` library mis-parses a number, producing wrong natural key | Low | Medium | Confidence scoring catches it (different names won't auto-merge); library is the industry standard |
| Cross-location auto-merge enabled by mistake on a true multi-tenant corpus | Medium | High | Default-off policy flag; explicit per-deployment opt-in; audit log surfaces all cross-location merges |
| Merge state file corrupted | Low | Medium | SQLite is robust; backup before every run; resume queries Podium for live state |
| Podium silently changes merge semantics (e.g., starts dropping opt-outs in a different field) | Low | Critical | Post-merge PATCH overwrites opt-outs regardless — defensive against upstream changes |
| Operator runs dedup while another automated job is merging | Medium | High | Conflict detection via `updated_at_podium` re-check before each merge |

## Educational Disclaimer

This skill ships production-grade data-quality patterns for the Podium contact corpus as of the date the skill was authored. Podium's API and merge semantics evolve. Validate the specific endpoint paths, field names, and merge response shapes against the Podium developer documentation before deploying. Compliance regimes (TCPA, GDPR, ACMA, CCPA) evolve faster — consult counsel for jurisdictional specifics. The skill author is not responsible for breaking changes in upstream Podium behavior or for compliance attestation outcomes.

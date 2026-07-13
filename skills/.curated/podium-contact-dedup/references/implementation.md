# Implementation Reference — podium-contact-dedup

Language-portability layer plus audit-log schema plus the cluster-review queue contract.

## Node.js / TypeScript port

The Python normalization layer translates to TypeScript using `awesome-phonenumber` (a maintained Google libphonenumber port). The orchestrator translates with `better-sqlite3` for synchronous SQLite access (simplest state machine) and `undici` for HTTP.

```typescript
import { parsePhoneNumber } from "awesome-phonenumber";
import Database from "better-sqlite3";
import { fetch } from "undici";

interface Normalized {
  valid: boolean;
  e164?: string;
  national?: string;
  country?: string;
  natural_key?: string;
  reason?: string;
}

export function normalizePhone(raw: string, defaultRegion: string = "AU"): Normalized {
  const pn = parsePhoneNumber(raw, { regionCode: defaultRegion });
  if (!pn.valid) return { valid: false, reason: pn.possible ? "not_a_valid_number" : "parse_failed" };
  return {
    valid: true,
    e164: pn.number.e164,
    national: pn.number.national,
    country: pn.regionCode,
    natural_key: pn.number.e164,
  };
}

interface ClusterMember {
  contact_uid: string;
  field_count: number;
  updated_at_podium: string;   // ISO8601
  marketing_opt_out: boolean;
  sms_opt_out: boolean;
  email_opt_out: boolean;
  name?: string;
  email?: string;
  tags?: string[];
}

export function unionOptOuts(cluster: ClusterMember[]) {
  return {
    marketing_opt_out: cluster.some(c => c.marketing_opt_out),
    sms_opt_out:       cluster.some(c => c.sms_opt_out),
    email_opt_out:     cluster.some(c => c.email_opt_out),
  };
}

export function selectPrimary(cluster: ClusterMember[]): ClusterMember {
  return [...cluster].sort((a, b) => {
    if (a.field_count !== b.field_count) return b.field_count - a.field_count;
    const at = Date.parse(a.updated_at_podium);
    const bt = Date.parse(b.updated_at_podium);
    if (at !== bt) return bt - at;
    return a.contact_uid.localeCompare(b.contact_uid);
  })[0];
}
```

## SQLite schema (full)

```sql
-- The natural-key index. Source of truth for "which contact_uids share a phone".
CREATE TABLE IF NOT EXISTS contact_index (
    contact_uid        TEXT PRIMARY KEY,
    location_uid       TEXT NOT NULL,
    natural_key        TEXT NOT NULL,
    raw_phone          TEXT,
    name               TEXT,
    email              TEXT,
    tags_json          TEXT,            -- JSON array stored as TEXT for SQLite portability
    field_count        INTEGER NOT NULL DEFAULT 0,
    marketing_opt_out  INTEGER NOT NULL DEFAULT 0,
    sms_opt_out        INTEGER NOT NULL DEFAULT 0,
    email_opt_out      INTEGER NOT NULL DEFAULT 0,
    deleted_at_podium  TEXT,
    updated_at_podium  TEXT NOT NULL,
    indexed_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_natural_key             ON contact_index(natural_key);
CREATE INDEX IF NOT EXISTS idx_natural_key_per_location ON contact_index(natural_key, location_uid);
CREATE INDEX IF NOT EXISTS idx_location                ON contact_index(location_uid);

-- The merge state machine. One row per cluster operation.
CREATE TABLE IF NOT EXISTS merge_state (
    cluster_id        TEXT PRIMARY KEY,
    natural_key       TEXT NOT NULL,
    primary_uid       TEXT NOT NULL,
    duplicate_uids    TEXT NOT NULL,       -- JSON array
    opt_out_pre_json  TEXT NOT NULL,       -- JSON {uid: {flag: bool}}
    opt_out_post_json TEXT,                -- JSON {flag: bool}; NULL until union computed
    status            TEXT NOT NULL CHECK (status IN (
                          'pending', 'merging', 'merged', 'patched',
                          'failed_permanent', 'compliance_failed',
                          're_index_required', 'conflict_pending'
                      )),
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    started_at        TEXT NOT NULL,
    completed_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_merge_status ON merge_state(status);
```

## Audit log schema (JSON Lines)

Every operation produces one line in `audit-log.jsonl`. The schema below is stable across the v2.x line — additive changes only.

```json
{
  "ts": "ISO8601 timestamp",
  "event": "merge_complete | merge_failed | conflict_detected | compliance_failed | cluster_skipped",
  "cluster_id": "cl_...",
  "natural_key": "+61...",
  "primary_uid": "ct_...",
  "duplicate_uids": ["ct_...", "ct_..."],
  "opt_out_pre_merge": {
    "ct_<uid>": {"marketing_opt_out": bool, "sms_opt_out": bool, "email_opt_out": bool}
  },
  "opt_out_post_merge": {"marketing_opt_out": bool, "sms_opt_out": bool, "email_opt_out": bool},
  "soft_delete": true,
  "restorable": true,
  "attempts": int,
  "duration_ms": int,
  "error": "optional, only on failure events"
}
```

Compliance evidence is the union of `opt_out_pre_merge` and `opt_out_post_merge` per cluster — the audit log is the only artifact needed to prove every merge preserved the strongest opt-out flag.

## Cluster-review queue contract

When a cluster's confidence is below the auto-merge threshold OR the cluster is cross-location with policy=review, the cluster is emitted to `review-queue.json` (NDJSON, one cluster per line).

The contract:

```json
{
  "cluster_id": "cl_...",
  "natural_key": "+61...",
  "confidence": 0.72,
  "auto_merge": false,
  "review_reason": "cross_location | low_confidence | large_cluster | manual_required",
  "members": [
    {
      "contact_uid": "ct_...",
      "location_uid": "loc_...",
      "location_name": "Sydney CBD",
      "name": "Casey Default",
      "email": "casey@example.invalid",
      "field_count": 12,
      "updated_at_podium": "2026-05-10T08:00:00Z",
      "marketing_opt_out": false,
      "sms_opt_out": false,
      "email_opt_out": false,
      "last_touch_event": "webchat_inbound",
      "last_touch_ts": "2026-05-09T14:00:00Z"
    }
  ],
  "suggested_primary_uid": "ct_...",
  "opt_out_union_if_merged": {
    "marketing_opt_out": true,
    "sms_opt_out": false,
    "email_opt_out": false
  }
}
```

Consumers of this queue (a dashboard, a notebook, a CSV export) should display:

1. The phone (natural_key) prominently — it is the only reason these are clustered.
2. Each member's name and last-touch event so the operator can judge whether they are the same person.
3. The opt-out union prominently — the operator should know what the merged state would be before confirming.
4. The cross-location flag if applicable, with both location names.

## Library packaging notes

This skill ships the normalization + clustering logic inline in `scripts/*.py` rather than as a separate pip package. The rationale: each Podium integration tunes the default region and the confidence weights per-tenant; an extracted package would add a configuration surface that mostly just re-exports the script's arguments. If three independent consumer skills end up depending on identical normalization behavior with no per-call configuration drift, promote `phone_normalize.py` to `intent-podium-dedup` on PyPI.

The `phonenumbers` library is a hard dependency for all paths. The skill assumes operators have already installed it (`pip install phonenumbers`) — there is no fallback regex parser by design (hand-rolled phone parsers are a known anti-pattern).

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_normalize_au_formats`          | unit        | 4+ AU phone formats all produce the same natural_key |
| `test_normalize_us_formats`          | unit        | 4+ US phone formats all produce the same natural_key |
| `test_normalize_invalid_returns_false` | unit      | Garbage strings return `{valid: false}` not raised exceptions |
| `test_cluster_confidence_floor`      | unit        | Same phone, different name, different email → 0.60 floor |
| `test_cluster_confidence_max`        | unit        | Same phone, name, email, tags → 1.00 |
| `test_select_primary_deterministic`  | unit        | Same input always produces same primary across 100 runs |
| `test_union_opt_outs_strongest_wins` | unit        | Any true → true in result; all false → false |
| `test_merge_state_transitions`       | unit        | pending → merging → merged → patched only |
| `test_resume_from_merging`           | integration | SIGKILL between merge and PATCH; resume completes PATCH |
| `test_conflict_detection_aborts`     | integration | Mutate a duplicate between index and merge; merge aborts cleanly |
| `test_compliance_failure_pages`      | integration | Simulated 500 on PATCH; cluster enters `compliance_failed` and alert fires |
| `test_cross_location_does_not_auto`  | integration | Two locations, same phone, default policy → review queue, no API calls |
| `test_soft_delete_loop_detection`    | integration | Same cluster merged 3 runs in a row → ERR_DEDUP_013 surfaces |
| `test_concurrent_dedup_run_blocked`  | integration | Second process exits with ERR_DEDUP_014 rather than corrupting state |

# Current-state and settled-history contract

Pipeline Guardian accepts a canonical JSON object whose `collector_receipts`
array contains the six reviewed schema-2 surface types. The bundle is fail-closed:
receipt validity is necessary but not sufficient for trust or completeness.

## Required coverage

Supply exactly one receipt for each of:

- `pipeline`
- `pipeline-task-current`
- `pipeline-stream-current`
- `pipeline-dynamic-table-current`
- `pipeline-pipe-current`

Supply one `pipeline-pipe-status` receipt for every object hash in the
`pipeline-pipe-current` inventory. This surface is repeatable because its
validated three-part pipe selector is bound to one projected object hash. No
status receipt is required when the current pipe inventory is empty.

Each receipt must contain exactly its reviewed datasets, including explicit empty
arrays, plus exactly one same-statement `execution_context`. Missing, duplicate,
unexpected, capped, stale, error, or offline-normalized surfaces make the bundle
insufficient.

## Context and time

Every context contains:

- `observed_at` in UTC;
- scoped hashes for organization, account, collector user, primary role, and
  secondary roles;
- `primary_role_type` equal to the documented `ROLE` or
  `APPLICATION_INSTANCE` value; and
- `timezone: UTC`.

All context identity fields must match across receipts. Every observation must
fall inside its receipt's bounded collection interval, be no more than 15 minutes
old at the caller-supplied explicit evaluation timestamp, and fall within a
bundle observation span no longer than 15 minutes. Binding evaluation time makes
replay deterministic; it remains an operator assertion. These checks prove
context equivalence, not one Snowflake session or an atomic snapshot.

The `pipeline` receipt additionally binds explicit canonical UTC
`window_start_utc` and exclusive `window_end_utc`, `HALF_OPEN_UTC` semantics, and
a requested interval no longer than seven days. The receipt retains these
non-sensitive window values so the analyzer can recompute both the selector
fingerprint and rendered-query digest. Raw identity selectors remain forbidden.

## Settlement and caps

The history query only admits rows before the conservative settlement point for
each source:

| Dataset | Settled through | Row cap |
| --- | --- | --- |
| `task_history` | `min(window_end, observed_at - 45 minutes)` | 5,000 |
| `dynamic_table_refresh_history` | `min(window_end, observed_at - 3 hours)` | 5,000 |
| `copy_history` | `min(window_end, observed_at - 48 hours)` | 5,000 |

The interval applies to `COMPLETED_TIME` for tasks, non-null
`REFRESH_END_TIME` for non-executing dynamic-table refreshes, and
`LAST_LOAD_TIME` for completed copy loads. A schedule/start time never makes a
recently completed or still-executing event settled.

The current task, stream, dynamic-table, and pipe datasets each have a 10,000-row
cap. A count equal to a cap is potentially truncated and cannot support coverage
or absence claims. `pipeline-pipe-status` has one projected status row per
selector.

Do not silently shorten the declared history window to the settlement cutoff.
Report the requested window and every `*_settled_through_utc`; the remaining
tail is explicitly unknown. Narrow or partition capped history, but never combine
partitions collected under mismatched authorization contexts.

## Integrity and trust

The analyzer validates exact receipt, context, and per-dataset field schemas;
finite documented domains for every admitted text value; exact fixed
`non_claims`; live collection mode; source/template binding; unselected
current-query bytes; history selector and rendered-query digests; pipe
selector-to-object binding; result and receipt digests; datasets/counts;
SQL-reported and receipt caps; event-time coverage; privacy fields; and context.
For successfully selected pipe status, the collector replaces the raw local
selector in a receipt-only rendering with its Snowflake-produced scoped object
hash. The analyzer recomputes that privacy-bound rendering and its digest without
retaining the identifier. If collection fails before that scoped hash exists,
the error receipt records only the reviewed template digest and a null selector
fingerprint; it never hashes the raw pipe name. These are self-consistency checks.
Because anyone holding a receipt can recompute its self-hash, it is not an
independent trust anchor.

After assembling the exact bundle, calculate its canonical digest with
`--print-input-sha256` and record that value through a separate trusted local
step. Pass the recorded value with `--trusted-input-sha256`. The digest covers the
entire analyzer input and must be recomputed after any change. A match means only
that the analyzed bytes equal the operator-recorded bytes; it does not prove
collector identity, authenticity, or Snowflake origin.

## Privacy

Object relationships use organization/account-scoped SHA-256 pseudonyms. Raw
names, query IDs, file/stage paths, roles, users, definitions, query text,
notification endpoints, integration names, and free-text errors are forbidden in
the evidence bundle. After successful collection, the local pipe selector is
replaced by a fingerprint of its scoped object hash. Failed collection retains
neither a raw-selector fingerprint nor a rendered-query digest containing the
selector. Raw `SYSTEM$PIPE_STATUS` JSON is never admissible.
Unknown state/status values, extra fields, duplicate current object keys, and
modified envelope statements make a receipt invalid. Invalid receipts are never
classified into findings, so rejected provider text cannot be reflected into a
report.

Hashes remain linkable within their scope. Store and share them as operational
data, and do not attempt to reverse them with a name dictionary.

## Nonclaims

Even a trusted, validated, uncapped bundle proves only what its authorization
context could observe during the bounded intervals. It does not prove:

- account-wide inventory or absence of hidden objects;
- an atomic snapshot across the six surface types;
- that current state existed throughout the history window;
- absence of activity after a history settlement cutoff;
- causal dependency, complete graph topology, delivery correctness, or replay
  idempotence;
- that raw Snowflake, cloud-event, or target-table state matches a projected
  status; or
- that a recovery action occurred or succeeded.

Current/history disagreement is a bounded observation requiring more read-only
evidence. Offline or manually mapped snapshots can support hypotheses but never
positive completeness, health, absence, or root-cause claims.

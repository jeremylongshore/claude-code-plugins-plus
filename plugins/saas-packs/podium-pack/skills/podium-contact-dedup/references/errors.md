# Errors — podium-contact-dedup

Lookup table for `ERR_DEDUP_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_DEDUP_001 — phone_parse_failed

- **HTTP**: N/A (raised by `normalize_phone`)
- **Cause**: The input string could not be parsed by `phonenumbers.parse` — typically a non-numeric string, an empty value, or a free-form note in the phone field.
- **Detection**: `normalize_phone(raw)` returns `{valid: false, reason: "parse_failed: ..."}`.
- **Action**: The contact is excluded from the natural-key index. Surface in the `uncategorized` queue for manual review. Do NOT attempt to fuzzy-match — wrong matches produce compliance incidents.

## ERR_DEDUP_002 — phone_not_valid

- **HTTP**: N/A (raised by `normalize_phone`)
- **Cause**: The string parsed but `phonenumbers.is_valid_number()` returned false — the number has the right shape but does not match any allocatable range (e.g., `+1 555 555 5555` is reserved-for-fiction in the NANP).
- **Detection**: `normalize_phone(raw)` returns `{valid: false, reason: "not_a_valid_number"}`.
- **Action**: Excluded from the index. If the operator believes the number is real, escalate to verify the country code or default-region setting — a misconfigured default region produces this error in volume.

## ERR_DEDUP_003 — index_build_failed

- **HTTP**: N/A (local SQLite or upstream API error)
- **Cause**: SQLite write error, schema mismatch on a partially-migrated DB, or Podium contact-list endpoint returning 5xx during the scan.
- **Detection**: `find_duplicates.py` exits with code 3 and the failure point logged.
- **Action**: Inspect the SQLite error or retry against Podium. Index build is idempotent — re-run the same command and it resumes from where it failed.

## ERR_DEDUP_004 — cluster_confidence_below_threshold

- **HTTP**: N/A (raised by cluster orchestrator)
- **Cause**: A candidate cluster has pairwise confidence below `auto_merge_threshold` (default 0.80). Examples: same phone but conflicting names ("Maria Garcia" vs "John Smith"); same phone but conflicting emails.
- **Detection**: Cluster is emitted to the human-review queue rather than the auto-merge queue.
- **Action**: Human review. Common resolution: the lower-confidence record is a legitimately different person (number reassignment) or a typo that needs operator judgment. The skill does NOT auto-merge below threshold by design.

## ERR_DEDUP_005 — primary_selection_tie

- **HTTP**: N/A (raised by `select_primary`)
- **Cause**: Two or more cluster members tie on `(field_count, updated_at_podium)` after the deterministic tiebreak. Theoretically impossible because `lowest_uid_lexical` is final.
- **Detection**: An assertion in `select_primary` would catch this; the code path is defensive.
- **Action**: File a bug report — this indicates a logic defect. The cluster is held in the review queue until resolved.

## ERR_DEDUP_006 — invalid_duplicate_uid

- **HTTP**: 400 from `POST /contacts/{p}/merge`
- **Cause**: One of the `duplicate_uids` no longer exists or was already soft-deleted (likely merged into a different record between index build and merge call).
- **Detection**: Podium returns 400 with `{"error": "invalid_duplicate_uid", "uid": "..."}`.
- **Action**: Re-fetch the cluster — the conflicting duplicate may already be in the desired merged state. Remove it from `duplicate_uids` and retry the merge with the remaining duplicates.

## ERR_DEDUP_007 — contact_not_found

- **HTTP**: 404 from `POST /contacts/{p}/merge` or `PATCH /contacts/{p}`
- **Cause**: The primary contact was hard-deleted between index build and merge — typically by an admin running a GDPR erasure or a manual purge.
- **Detection**: Podium returns 404.
- **Action**: Skip the cluster. The data is gone; there is nothing to merge into. Re-evaluate on the next run; if all duplicates are also gone, the cluster resolves itself.

## ERR_DEDUP_008 — merge_in_progress

- **HTTP**: 409 from `POST /contacts/{p}/merge`
- **Cause**: Another merge is operating on one of these contacts simultaneously — typically a second orchestrator instance, a manual merge from the Podium UI, or a webhook-triggered automation.
- **Detection**: Podium returns 409 with `{"error": "merge_in_progress"}`.
- **Action**: Wait with exponential backoff. After `max_attempts`, mark the cluster `conflict_pending` and surface it on the next run. Investigate whether two automation jobs are stepping on each other.

## ERR_DEDUP_009 — cross_location_merge_blocked

- **HTTP**: 422 from `POST /contacts/{p}/merge`
- **Cause**: Primary and one or more duplicates are in different `location_uid` values and the tenant's Podium policy forbids cross-location merges via the API.
- **Detection**: Podium returns 422.
- **Action**: Move the cluster to the cross-location review queue. Do NOT retry. The operator must either confirm the locations are the same business entity (and enable cross-location auto-merge in config) or merge manually via the Podium UI with admin override.

## ERR_DEDUP_010 — opt_out_patch_failed

- **HTTP**: 4xx/5xx from `PATCH /contacts/{primary_uid}`
- **Cause**: The post-merge PATCH that applies the unioned opt-out flags failed. The merge itself succeeded; the opt-outs may now be in Podium's default state for the merged record.
- **Detection**: `_apply_opt_outs()` returns non-2xx.
- **Action**: **CRITICAL — COMPLIANCE INCIDENT.** Cluster enters `compliance_failed` state. Page the compliance channel immediately. Retry the PATCH with exponential backoff; if it fails persistently, manually set the opt-out flags via the Podium UI and document the incident in the audit log.

## ERR_DEDUP_011 — updated_at_drift_conflict

- **HTTP**: N/A (raised by pre-merge conflict check)
- **Cause**: A duplicate's `updated_at_podium` on re-fetch does not match the value indexed at scan time. Something modified the contact between index build and merge execution — a manual edit, a webhook ingest, or a competing merge.
- **Detection**: Orchestrator's `_refetch_and_verify()` returns mismatch.
- **Action**: Abort this cluster's merge. Mark `re_index_required`. The next run rebuilds the index for this natural_key and re-evaluates the cluster fresh.

## ERR_DEDUP_012 — merge_state_corruption

- **HTTP**: N/A (local SQLite)
- **Cause**: `merge_state` row exists in a non-terminal status but the corresponding Podium contacts do not match any consistent state — e.g., status=`merged` but primary's `deleted_at` is set, or status=`pending` but Podium has no record of any of the cluster members.
- **Detection**: `resume()` cannot reconcile the row against Podium state.
- **Action**: Manual reconciliation. Inspect the cluster, decide whether to mark the row `manually_resolved` or to delete it and re-run dedup for the affected natural_key. Log the reconciliation decision.

## ERR_DEDUP_013 — soft_delete_loop_detected

- **HTTP**: N/A (raised by audit-log analyzer)
- **Cause**: The same cluster has been auto-merged on 3+ consecutive runs because an admin keeps restoring the soft-deleted duplicates via the Podium UI.
- **Detection**: Audit log shows `cluster_id` appearing in `patched` status repeatedly with the same `duplicate_uids`.
- **Action**: Surface to the operations team. Either the restores are intentional (legitimate separate contacts share a phone — e.g., shared business line) and the cluster needs to be allow-listed, or the restores are an admin reflex and need a training conversation.

## ERR_DEDUP_014 — concurrent_dedup_run

- **HTTP**: N/A (raised by lock check)
- **Cause**: Two dedup processes started against the same database simultaneously. The SQLite file lock prevents corruption but the second process detects the running first and exits.
- **Detection**: `find_duplicates.py` or `merge_contacts.py` detects an active orchestrator lock file (`.dedup.lock`) less than `pending_stale_seconds` old.
- **Action**: Wait for the running process to complete, or kill it if hung. Do NOT force-acquire the lock — corrupted merge_state requires manual reconciliation. Stale locks (>30 min, originating PID dead) can be deleted; live locks must not.

#!/usr/bin/env python3
"""recover-streaming-source.py — a deterministic 4-way recovery decision tree for a
broken Structured Streaming source (bead 4kau / pains D03/D04/D12).

When a stream dies because its checkpoint no longer lines up with its Delta source,
there are four ways out, and the RIGHT one depends on facts an engineer knows but
tends not to reason through under pressure: what failed, whether the source can be
replayed, whether the sink is idempotent, and whether time travel still reaches
before the damage. This script encodes that decision so the recommendation is
reproducible and the data-loss tradeoff of each path is stated up front — the LLM
never free-hands "just reset the checkpoint".

The four recoveries (least to most destructive):
  SAFE_RESTART            restart the query as-is (the checkpoint is intact; this
                          was a transient failure).
  REPROCESS_FROM_OFFSET   reset the reader to a newer/known offset (startingOffsets)
                          and let an idempotent sink de-dup the overlap.
  RESTORE_FROM_TIME_TRAVEL restore the SOURCE table to a version before the damage
                          (e.g. before VACUUM deleted the pinned files), then restart.
  FULL_RESET_BACKFILL     new checkpoint + full re-read of the source. The last
                          resort — safe only if the source is replayable; otherwise
                          it silently drops the un-replayable data.

Failure classes it reasons over:
  file-not-found   DELTA_FILE_NOT_FOUND_DETAILED — VACUUM deleted files the
                   checkpoint pins to (D03).
  uuid-changed     DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE — CREATE OR
                   REPLACE minted a new source UUID (D12); the old checkpoint is dead.
  checkpoint-reset silent reset to batch 0 / batchId regression — corruption (D04).
  transient        a restartable blip (network, node loss) with an intact checkpoint.

Usage:
  recover-streaming-source.py --failure file-not-found \
      [--source-replayable yes|no] [--sink-idempotent yes|no] \
      [--time-travel yes|no] [--json]
Unknown facts default to the SAFE (pessimistic) assumption and are surfaced.
Exit codes: 0 ok · 2 bad usage.
"""

import argparse
import json
import sys

FAILURES = ("file-not-found", "uuid-changed", "checkpoint-reset", "transient")

# The canonical Databricks error string each failure class corresponds to — always
# surface this exact, searchable code, never only the short class name.
FAILURE_CODES = {
    "file-not-found": "DELTA_FILE_NOT_FOUND_DETAILED",
    "uuid-changed": "DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE",
    "checkpoint-reset": "(silent batchId regression / checkpoint corruption — no single code)",
    "transient": "(no specific code — a restartable blip)",
}
SAFE_RESTART = "SAFE_RESTART"
REPROCESS = "REPROCESS_FROM_OFFSET"
TIME_TRAVEL = "RESTORE_FROM_TIME_TRAVEL"
FULL_RESET = "FULL_RESET_BACKFILL"


def recovery_decision(failure, source_replayable, sink_idempotent, time_travel):
    """Return {tier, rationale, data_loss_risk, steps}. Pure — the decision tree
    is testable with no workspace. Unknown (None) inputs are treated pessimistically."""
    replay = source_replayable is True
    idem = sink_idempotent is True
    tt = time_travel is True

    if failure == "transient":
        return _mk(
            SAFE_RESTART,
            "low",
            "The checkpoint is intact; the failure was transient (node loss / network). "
            "Restart the query — Structured Streaming resumes from the committed offset.",
            ["Restart the streaming query as-is.", "Confirm the batchId advances past the last committed batch."],
        )

    if failure == "file-not-found":
        # D03: VACUUM deleted files the checkpoint pins to.
        if tt:
            return _mk(
                TIME_TRAVEL,
                "none",
                "VACUUM deleted files the checkpoint references, but the source's history "
                "still reaches before the deletion — restore the source, then restart the "
                "existing checkpoint (no reprocessing, no data loss).",
                [
                    "RESTORE TABLE <source> TO VERSION AS OF <pre-VACUUM version> (or TIMESTAMP).",
                    "Restart the query on the existing checkpoint.",
                    "Fix the root cause: align VACUUM retention with the consumers' checkpoint lag.",
                ],
            )
        if replay and idem:
            return _mk(
                REPROCESS,
                "low (duplicates de-duped by the idempotent sink)",
                "History no longer reaches the deleted files, but the source is replayable and "
                "the sink is idempotent — reset the reader to a newer available offset and let "
                "the sink de-dup the overlap.",
                [
                    "Find the earliest still-available offset/version of the source.",
                    "Restart with startingVersion/startingOffsets at that point.",
                    "Rely on the idempotent sink (MERGE / foreachBatch upsert) to absorb overlap.",
                ],
            )
        return _mk(
            FULL_RESET,
            "HIGH — data between the deleted files and the new start is lost",
            "The pinned files are gone, history cannot restore them, and the source is not "
            "replayable (or the sink is not idempotent) — a full reset will lose the gap. "
            "Do this only after accepting the loss; back up the sink first.",
            [
                "Snapshot the sink for audit.",
                "Delete the checkpoint and start a new one from the current source state.",
                "Document the lost window; add VACUUM-retention guards so it cannot recur.",
            ],
        )

    if failure == "uuid-changed":
        # D12: CREATE OR REPLACE minted a new UUID; the old checkpoint is dead.
        if replay:
            return _mk(
                FULL_RESET,
                "low if fully replayable; otherwise the un-replayable tail is lost",
                "CREATE OR REPLACE changed the source table's UUID, so the old checkpoint can "
                "never resume. The source is replayable — start a fresh checkpoint against the "
                "new table and backfill from the beginning.",
                [
                    "Point the stream at the new table; start a NEW checkpoint location.",
                    "Backfill from the source's earliest available offset.",
                    "Prevent recurrence: never CREATE OR REPLACE a streamed-from source — use "
                    "ALTER / in-place changes (this is what the skill's PreToolUse hook blocks).",
                ],
            )
        return _mk(
            FULL_RESET,
            "HIGH — the pre-migration data is unrecoverable",
            "The source UUID changed (CREATE OR REPLACE) AND the source is not replayable — the "
            "old data is gone with the old UUID. A new checkpoint is the only path; the gap is lost.",
            [
                "Accept the loss; snapshot the sink first.",
                "Start a fresh checkpoint on the new table.",
                "Prevent recurrence: block CREATE OR REPLACE on streamed-from sources.",
            ],
        )

    if failure == "checkpoint-reset":
        # D04: corruption / silent reset to batch 0.
        if replay and idem:
            return _mk(
                REPROCESS,
                "low (idempotent sink de-dups the replay)",
                "The checkpoint corrupted / reset (a platform-bug class). A plain restart risks "
                "reprocessing from batch 0 — instead pin startingOffsets to the last known-good "
                "point and rely on the idempotent sink to absorb any replay.",
                [
                    "Identify the last known-good offset from system.streaming.query_progress.",
                    "Restart with explicit startingOffsets/startingVersion at that point.",
                    "Confirm the sink is idempotent so the replay does not double-write.",
                ],
            )
        return _mk(
            FULL_RESET,
            "review — a naive restart may double-write or reprocess everything",
            "The checkpoint is corrupt and the sink is not confirmed idempotent — do not blindly "
            "restart. Rebuild the checkpoint deliberately and make the sink idempotent first.",
            [
                "Make the sink idempotent (MERGE/upsert keyed on a business key).",
                "Start a fresh checkpoint; backfill from a safe offset.",
                "File the corruption with Databricks support (D04 has no documented root cause).",
            ],
        )

    return _mk(
        SAFE_RESTART,
        "unknown",
        "Unrecognized failure class — restart and observe, then re-run "
        "this tool with the specific failure once identified.",
        ["Restart and capture the exact error."],
    )


def _mk(tier, data_loss_risk, rationale, steps):
    return {"tier": tier, "data_loss_risk": data_loss_risk, "rationale": rationale, "steps": steps}


def _yn(v):
    if v is None:
        return None
    return v.strip().lower() in ("yes", "y", "true", "1")


def main():
    ap = argparse.ArgumentParser(description="Recommend a Structured Streaming source recovery")
    ap.add_argument("--failure", required=True, choices=FAILURES)
    ap.add_argument("--source-replayable", choices=["yes", "no"], default=None)
    ap.add_argument("--sink-idempotent", choices=["yes", "no"], default=None)
    ap.add_argument(
        "--time-travel",
        choices=["yes", "no"],
        default=None,
        help="is the source's history still within VACUUM retention before the damage?",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    unknowns = [
        n
        for n, v in (
            ("source-replayable", args.source_replayable),
            ("sink-idempotent", args.sink_idempotent),
            ("time-travel", args.time_travel),
        )
        if v is None
    ]
    result = recovery_decision(
        args.failure, _yn(args.source_replayable), _yn(args.sink_idempotent), _yn(args.time_travel)
    )
    result["failure"] = args.failure
    result["error_code"] = FAILURE_CODES.get(args.failure, "")
    result["assumed_pessimistic"] = unknowns

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Failure: {args.failure}  (Databricks error: {result['error_code']})")
        print(f"Recommended recovery: {result['tier']}")
        print(f"Data-loss risk: {result['data_loss_risk']}")
        print(f"\n{result['rationale']}\n\nSteps:")
        for i, s in enumerate(result["steps"], 1):
            print(f"  {i}. {s}")
        if unknowns:
            print(
                f"\n(assumed the safe/pessimistic answer for unknown facts: {', '.join(unknowns)} — "
                "re-run with those flags for a sharper call.)"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

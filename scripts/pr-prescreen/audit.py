"""PR pre-screen audit log writer.

Appends one row per pre-screen run to freshie/inventory.sqlite's
pr_prescreen_log table. The table is created on first write — no separate
migration step. Concurrent runs are safe because sqlite3 handles row-level
insert serialization via the default journal mode.

Invocation (from the workflow, with the augmented verdict.json):

    python3 scripts/pr-prescreen/audit.py \
        --db freshie/inventory.sqlite \
        --pr-number 712 \
        --verdict-file /tmp/verdict.json \
        --latency-ms 1820

If the DB path doesn't exist (e.g. the workflow runs against a fresh
clone), the file is created with the single table.

Columns:
    pr_number INTEGER NOT NULL
    verdict TEXT NOT NULL           PASS | CHANGES_REQUESTED | HARD_BLOCK
    validator_avg_score REAL        average across matched skills (NULL ok)
    matched_skill_count INTEGER
    blockers_count INTEGER
    warnings_count INTEGER
    groq_used INTEGER (0/1)
    llm_status TEXT
    latency_ms INTEGER NOT NULL     end-to-end pre-screen wall time
    created_at TEXT NOT NULL        ISO-8601 UTC
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sqlite3
import sys
from typing import Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS pr_prescreen_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pr_number INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    validator_avg_score REAL,
    matched_skill_count INTEGER NOT NULL DEFAULT 0,
    blockers_count INTEGER NOT NULL DEFAULT 0,
    warnings_count INTEGER NOT NULL DEFAULT 0,
    groq_used INTEGER NOT NULL DEFAULT 0,
    llm_status TEXT,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS pr_prescreen_log_pr_idx
    ON pr_prescreen_log(pr_number);
CREATE INDEX IF NOT EXISTS pr_prescreen_log_verdict_idx
    ON pr_prescreen_log(verdict);
"""


def _avg_score(results: list[dict]) -> Optional[float]:
    # Column is REAL; preserve precision and handle JSON null + numeric
    # strings ("4.5") cleanly. `r.get("score") is not None` guards both
    # the missing-key case and an explicit null.
    scores = [float(r["score"]) for r in results if r.get("score") is not None]
    return (sum(scores) / len(scores)) if scores else None


def write_log(
    db_path: str,
    *,
    pr_number: int,
    verdict_payload: dict,
    latency_ms: int,
) -> int:
    """Append one row and return the inserted rowid."""
    path = pathlib.Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    verdict = verdict_payload.get("verdict", "UNKNOWN")
    results = verdict_payload.get("results", []) or []
    blockers = verdict_payload.get("blockers", []) or []
    warnings = verdict_payload.get("warnings", []) or []
    llm_status = verdict_payload.get("llm_status")
    groq_used = 1 if llm_status == "ok" else 0
    avg = _avg_score(results)

    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA)
        cur = conn.execute(
            """
            INSERT INTO pr_prescreen_log
                (pr_number, verdict, validator_avg_score, matched_skill_count,
                 blockers_count, warnings_count, groq_used, llm_status,
                 latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(pr_number),
                verdict,
                avg,
                len(results),
                len(blockers),
                len(warnings),
                groq_used,
                llm_status,
                int(latency_ms),
                _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid or 0)
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="PR pre-screen audit log writer")
    parser.add_argument("--db", required=True, help="Path to freshie/inventory.sqlite")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--verdict-file", required=True, help="Path to verdict.json (augmented)")
    parser.add_argument("--latency-ms", type=int, default=0)
    args = parser.parse_args(argv[1:])

    raw = pathlib.Path(args.verdict_file).read_text(encoding="utf-8")
    verdict_payload = json.loads(raw)
    if not isinstance(verdict_payload, dict):
        print("audit.py: --verdict-file must contain a JSON object", file=sys.stderr)
        return 2

    rowid = write_log(
        args.db,
        pr_number=args.pr_number,
        verdict_payload=verdict_payload,
        latency_ms=args.latency_ms,
    )
    print(json.dumps({"db": args.db, "rowid": rowid, "verdict": verdict_payload.get("verdict")}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))

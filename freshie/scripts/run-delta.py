#!/usr/bin/env python3
"""run-delta.py — structured run-over-run delta report for the freshie Dolt repo.

Applies the DoltHub VCS-plugin patterns to the inventory sync: after a sync
commits run N, this module compares the `run-(N-1)` and `run-N` tags and
writes freshie/reports/run-delta-<N>.json containing:

  1. Schema-vs-data change classification per table, via
     DOLT_DIFF_SUMMARY(from, to) (schema_change / data_change flags) merged
     with DOLT_DIFF_STAT(from, to) (rows added / deleted / modified). The
     append-only run_id model means a git diff of grades.csv shows grade
     movement, but only Dolt's diff functions can say "table X changed
     SHAPE, not just content" — that distinction is this report's point.
  2. A grade-regression list: skills whose grade dropped run-over-run
     (e.g. A→B), computed from a temporal `AS OF '<tag>'` compare of
     skill_compliance at the two tags — a data-quality probe emitted as
     structured output, not a human eyeballing a diff.
  3. The Dolt commit hash the delta was computed against, so the artifact
     traces to an immutable revision, not only the mutable-in-principle
     tag name.

Called two ways:
  - by dolt-sync.py post-commit and before push (fail-closed — a receipt
    failure blocks remote publication while leaving the local commit
    recoverable);
  - standalone, to (re)generate a report for any run:
        python3 freshie/scripts/run-delta.py [--dolt-dir PATH] [--run-id N]
            [--out-dir PATH] [--alert-on-regression]

Exit codes (standalone): 0 ok · 1 failure · 4 ok but grade regressions
found (only with --alert-on-regression — the GH-Actions-consumable signal).

Pure functions (tag parsing, previous-tag selection, diff-row merging,
grade-regression detection, report assembly) are unit-tested in
tests/test_run_delta.py with fixture rows — no dolt binary, no network.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOLT_DIR = REPO_ROOT / "freshie" / "dolt" / "freshie"
DEFAULT_REPORTS_DIR = REPO_ROOT / "freshie" / "reports"

# Grade ranking for regression detection — higher is better. A grade absent
# from this map (e.g. NULL/"ungraded") cannot be ranked and never produces a
# regression row; a skill entering or leaving the graded set is a membership
# change, not a grade movement.
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}

RUN_TAG_RE = re.compile(r"^run-(\d+)(?:\.(\d+))?$")


class DeltaError(Exception):
    """Fatal delta failure (bad repo state, missing tag, query failure)."""


def log(msg: str) -> None:
    print(f"[run-delta] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Pure functions — unit-tested
# ---------------------------------------------------------------------------


def parse_run_tag(tag: str) -> tuple[int, int] | None:
    """`run-9` → (9, 0); `run-9.1` → (9, 1); anything else → None.

    The suffix form comes from dolt-sync's tag-collision handling (run N
    re-tagged on a newer commit when compliance was re-populated without a
    new discovery run) — it sorts AFTER the base tag of the same run.
    """
    m = RUN_TAG_RE.match(tag)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2) or 0)


def pick_previous_tag(tags: list[str], current_tag: str) -> str | None:
    """The run tag immediately preceding current_tag in (run, suffix) order.

    Non-run tags are ignored. Returns None when current_tag is the earliest
    run tag (or unparseable) — i.e. there is nothing to diff against.
    """
    cur = parse_run_tag(current_tag)
    if cur is None:
        return None
    best: tuple[tuple[int, int], str] | None = None
    for t in tags:
        key = parse_run_tag(t)
        if key is None or key >= cur:
            continue
        if best is None or key > best[0]:
            best = (key, t)
    return best[1] if best else None


def _truthy(val: str) -> bool:
    return str(val).strip().lower() in ("true", "1")


def _int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _table_name(row: dict) -> str:
    """Table name from a diff row, robust to Dolt column-name variants.

    DOLT_DIFF_SUMMARY emits from_table_name/to_table_name (older builds:
    table_name); a dropped table has an empty to_table_name, so prefer the
    populated one.
    """
    return row.get("to_table_name") or row.get("from_table_name") or row.get("table_name") or ""


def merge_diff_rows(summary_rows: list[dict], stat_rows: list[dict]) -> list[dict]:
    """Merge DOLT_DIFF_SUMMARY rows (diff_type + schema/data flags) with
    DOLT_DIFF_STAT rows (row counts) into one per-table record list.

    A table can appear in the summary but not the stat output (pure schema
    change, no row movement) — its counts stay 0.
    """
    stats: dict[str, dict] = {}
    for row in stat_rows:
        name = _table_name(row)
        if name:
            stats[name] = row
    merged = []
    for row in summary_rows:
        name = _table_name(row)
        if not name:
            continue
        st = stats.get(name, {})
        merged.append(
            {
                "table": name,
                "diff_type": row.get("diff_type", ""),
                "schema_change": _truthy(row.get("schema_change", "")),
                "data_change": _truthy(row.get("data_change", "")),
                "rows_added": _int(st.get("rows_added")),
                "rows_deleted": _int(st.get("rows_deleted")),
                "rows_modified": _int(st.get("rows_modified")),
            }
        )
    merged.sort(key=lambda r: r["table"])
    return merged


def detect_grade_regressions(prev: dict[str, str], curr: dict[str, str]) -> list[dict]:
    """Skills whose grade DROPPED between two {skill_path: grade} maps.

    Only skills present in both maps with rankable grades are compared —
    additions, removals, improvements, and unrankable grades are not
    regressions. Sorted by skill_path for a deterministic report.
    """
    out = []
    for path in sorted(set(prev) & set(curr)):
        p, c = prev[path], curr[path]
        if p in GRADE_RANK and c in GRADE_RANK and GRADE_RANK[c] < GRADE_RANK[p]:
            out.append({"skill_path": path, "from_grade": p, "to_grade": c})
    return out


def build_report(
    run_id: int,
    from_tag: str | None,
    to_tag: str,
    dolt_commit: str,
    tables: list[dict],
    regressions: list[dict],
    run_coherence: dict | None = None,
    grade_export: dict | None = None,
    forge_proofs: dict | None = None,
) -> dict:
    """Assemble the report payload (pure — the file writer stays dumb)."""
    return {
        "schema_version": "freshie-run-delta/v3",
        "run_id": run_id,
        "from_tag": from_tag,
        "to_tag": to_tag,
        "dolt_commit": dolt_commit,
        "run_coherence": run_coherence,
        "grade_export": grade_export,
        "forge_proofs": forge_proofs,
        "tables_changed": len(tables),
        "schema_changes": sorted(t["table"] for t in tables if t["schema_change"]),
        "rows_added": sum(t["rows_added"] for t in tables),
        "rows_deleted": sum(t["rows_deleted"] for t in tables),
        "rows_modified": sum(t["rows_modified"] for t in tables),
        "tables": tables,
        "grade_regressions": regressions,
    }


def _n(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def summary_line(report: dict, out_path: Path) -> str:
    """One line a GitHub-Actions step (or an operator) can consume."""
    if report["from_tag"] is None:
        return f"run-delta: {report['to_tag']} is the earliest run tag — no previous run to diff against → {out_path}"
    return (
        f"run-delta: {report['from_tag']} → {report['to_tag']} · "
        f"{_n(report['tables_changed'], 'table', 'tables')} changed "
        f"({len(report['schema_changes'])} schema) · "
        f"+{report['rows_added']}/-{report['rows_deleted']}"
        f"/~{report['rows_modified']} rows · "
        f"{_n(len(report['grade_regressions']), 'grade regression', 'grade regressions')}"
        f" → {out_path}"
    )


# ---------------------------------------------------------------------------
# Thin Dolt-query wrapper
# ---------------------------------------------------------------------------


def dolt_query_dicts(repo: Path, sql: str) -> list[dict]:
    """Run a query in the Dolt repo, return rows as header-keyed dicts.

    Keyed by header (not position) so the parsing survives Dolt renaming or
    reordering the diff-function output columns across versions.
    """
    proc = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", sql],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise DeltaError(f"dolt query failed: {sql!r}\n{proc.stderr or proc.stdout}")
    return list(csv.DictReader(io.StringIO(proc.stdout)))


def local_tags(repo: Path) -> list[str]:
    return [r["tag_name"] for r in dolt_query_dicts(repo, "SELECT tag_name FROM dolt_tags")]


def commit_of_tag(repo: Path, tag: str) -> str:
    rows = dolt_query_dicts(repo, f"SELECT tag_hash FROM dolt_tags WHERE tag_name = '{tag}'")
    if not rows:
        raise DeltaError(f"tag {tag!r} not found in dolt_tags")
    return rows[0]["tag_hash"]


def grades_at_tag(repo: Path, tag: str, run_id: int) -> dict[str, str]:
    """{skill_path: grade} for one run, read AS OF a tag — a temporal read
    against the immutable tagged revision, not the working set."""
    rows = dolt_query_dicts(
        repo,
        f"SELECT skill_path, grade FROM `skill_compliance` AS OF '{tag}' WHERE run_id = {int(run_id)}",
    )
    return {r["skill_path"]: r["grade"] for r in rows}


def _required_count(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise DeltaError(f"{label} is not an integer: {value!r}") from exc
    if parsed < 0:
        raise DeltaError(f"{label} is negative: {parsed}")
    return parsed


def run_coherence_at_tag(repo: Path, tag: str, run_id: int) -> dict:
    """Read one run's declared and actual denominators at its immutable tag."""
    headers = dolt_query_dicts(
        repo,
        f"SELECT total_skills FROM `discovery_runs` AS OF '{tag}' WHERE id = {int(run_id)}",
    )
    if len(headers) != 1:
        raise DeltaError(f"run {run_id} has {len(headers)} discovery_runs headers at tag {tag!r}")
    skill_rows = dolt_query_dicts(
        repo,
        f"SELECT COUNT(*) AS row_count FROM `skills` AS OF '{tag}' WHERE run_id = {int(run_id)}",
    )
    compliance_rows = dolt_query_dicts(
        repo,
        f"SELECT COUNT(*) AS row_count FROM `skill_compliance` AS OF '{tag}' WHERE run_id = {int(run_id)}",
    )
    if len(skill_rows) != 1 or len(compliance_rows) != 1:
        raise DeltaError(f"run {run_id} count queries did not return one row at tag {tag!r}")

    declared = _required_count(headers[0].get("total_skills"), "total_skills")
    actual = _required_count(skill_rows[0].get("row_count"), "skills row count")
    compliance = _required_count(compliance_rows[0].get("row_count"), "skill_compliance row count")
    return {
        "discovery_run_id": run_id,
        "header_total_skills": declared,
        "skill_rows": actual,
        "skill_row_delta": actual - declared,
        "skill_compliance_rows": compliance,
    }


def grade_export_at_tag(repo: Path, tag: str, run_id: int) -> dict:
    """Hash the exact canonical grade CSV derivable from an immutable tag."""
    rows = dolt_query_dicts(
        repo,
        f"SELECT skill_path, grade, score FROM `skill_compliance` AS OF '{tag}' "
        f"WHERE run_id = {int(run_id)} ORDER BY skill_path",
    )
    paths = [row.get("skill_path") for row in rows]
    if any(not isinstance(path, str) or not path for path in paths):
        raise DeltaError(f"run {run_id} has an empty skill_path at tag {tag!r}")
    if len(set(paths)) != len(paths):
        raise DeltaError(f"run {run_id} has duplicate skill_path rows at tag {tag!r}")

    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["skill_path", "grade", "score"])
    grade_counts: dict[str, int] = {}
    for row in rows:
        grade = row.get("grade") or ""
        if grade not in GRADE_RANK:
            raise DeltaError(f"run {run_id} has unrankable grade {grade!r} for {row.get('skill_path')!r}")
        writer.writerow([row["skill_path"], grade, row.get("score") or ""])
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    payload = output.getvalue().encode("utf-8")
    return {
        "row_count": len(rows),
        "csv_sha256": hashlib.sha256(payload).hexdigest(),
        "grade_counts": {key: grade_counts[key] for key in sorted(grade_counts)},
    }


def forge_proofs_at_tag(repo: Path, tag: str) -> dict:
    """Snapshot and validate the evidence ledger at an immutable Dolt tag.

    Querying every governed column is deliberate: a legacy schema cannot
    masquerade as a classed, hash-bearing ledger. E2/E3 rows are re-opened and
    hash-checked here, after the Dolt commit and before publication.
    """
    rows = dolt_query_dicts(
        repo,
        "SELECT plugin_name, jrig_run_id, discovery_run_id, evidence_class, "
        "artifact_uri, artifact_sha256, baseline_delta "
        f"FROM `forge_proofs` AS OF '{tag}' ORDER BY plugin_name, jrig_run_id",
    )
    records = []
    identities: set[tuple[str, int]] = set()
    class_counts = {key: 0 for key in ("E0", "E1", "E2", "E3")}
    retained_e2_e3 = 0
    for row in rows:
        plugin_name = row.get("plugin_name") or ""
        if not plugin_name:
            raise DeltaError(f"forge_proofs has an empty plugin_name at tag {tag!r}")
        jrig_run_id = _required_count(row.get("jrig_run_id"), "forge_proofs.jrig_run_id")
        identity = (plugin_name, jrig_run_id)
        if identity in identities:
            raise DeltaError(f"forge_proofs has duplicate identity {identity!r} at tag {tag!r}")
        identities.add(identity)
        evidence_class = row.get("evidence_class") or ""
        if evidence_class not in class_counts:
            raise DeltaError(f"forge_proofs has invalid evidence_class {evidence_class!r} at tag {tag!r}")
        class_counts[evidence_class] += 1
        artifact_uri = row.get("artifact_uri") or None
        artifact_sha256 = row.get("artifact_sha256") or None
        discovery_raw = row.get("discovery_run_id")
        discovery_run_id = (
            None if discovery_raw in (None, "") else _required_count(discovery_raw, "forge_proofs.discovery_run_id")
        )
        baseline_raw = row.get("baseline_delta")
        try:
            baseline_delta = None if baseline_raw in (None, "") else float(baseline_raw)
        except (TypeError, ValueError) as exc:
            raise DeltaError(f"forge_proofs.baseline_delta is not numeric: {baseline_raw!r}") from exc

        if evidence_class in {"E2", "E3"}:
            if (
                not artifact_uri
                or not isinstance(artifact_sha256, str)
                or not re.fullmatch(r"[a-f0-9]{64}", artifact_sha256, re.IGNORECASE)
            ):
                raise DeltaError(f"{plugin_name}:{jrig_run_id} claims {evidence_class} without a retained artifact")
            try:
                actual_hash = hashlib.sha256(Path(artifact_uri).read_bytes()).hexdigest()
            except OSError as exc:
                raise DeltaError(f"{plugin_name}:{jrig_run_id} artifact is not retrievable: {artifact_uri}") from exc
            if actual_hash != artifact_sha256.lower():
                raise DeltaError(f"{plugin_name}:{jrig_run_id} artifact hash mismatch at {artifact_uri}")
            if evidence_class == "E3" and baseline_delta is None:
                raise DeltaError(f"{plugin_name}:{jrig_run_id} claims E3 without baseline_delta")
            retained_e2_e3 += 1

        records.append(
            {
                "plugin_name": plugin_name,
                "jrig_run_id": jrig_run_id,
                "discovery_run_id": discovery_run_id,
                "evidence_class": evidence_class,
                "artifact_uri": artifact_uri,
                "artifact_sha256": artifact_sha256.lower() if artifact_sha256 else None,
                "baseline_delta": baseline_delta,
            }
        )

    canonical = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    total_e2_e3 = class_counts["E2"] + class_counts["E3"]
    return {
        "row_count": len(records),
        "records_sha256": hashlib.sha256(canonical).hexdigest(),
        "class_counts": class_counts,
        "retained_e2_e3": retained_e2_e3,
        "total_e2_e3": total_e2_e3,
        "records": records,
    }


def build_forge_proof_receipt(report: dict) -> dict:
    """Project the immutable ledger snapshot into its public demotion receipt."""
    snapshot = report["forge_proofs"]
    return {
        "schema_version": "forge-proof-demotion/v2",
        "status": "immutable-ledger-snapshot",
        "source": "freshie/reports/run-delta-<N>.json forge_proofs snapshot",
        "source_run_id": report["run_id"],
        "source_tag": report["to_tag"],
        "source_dolt_commit": report["dolt_commit"],
        "records_sha256": snapshot["records_sha256"],
        "records": snapshot["records"],
        "rendering": {
            "badge": "disabled" if snapshot["total_e2_e3"] == 0 else "class-derived",
            "claim_ceiling": "E0" if snapshot["total_e2_e3"] == 0 else "ledger-minimum",
        },
    }


# ---------------------------------------------------------------------------
# Emit — the entry point dolt-sync calls post-commit
# ---------------------------------------------------------------------------


def emit(
    repo: Path, run_id: int, dolt_commit: str, to_tag: str, reports_dir: Path = DEFAULT_REPORTS_DIR
) -> tuple[Path, dict]:
    """Compute and write the run-delta report. Returns (path, report).

    Raises DeltaError on failure — dolt-sync treats this as a publication
    blocker before push; the standalone CLI exits 1.
    """
    tags = local_tags(repo)
    from_tag = pick_previous_tag(tags, to_tag)

    if from_tag is None:
        tables: list[dict] = []
        regressions: list[dict] = []
    else:
        summary_rows = dolt_query_dicts(repo, f"SELECT * FROM DOLT_DIFF_SUMMARY('{from_tag}', '{to_tag}')")
        stat_rows = dolt_query_dicts(repo, f"SELECT * FROM DOLT_DIFF_STAT('{from_tag}', '{to_tag}')")
        tables = merge_diff_rows(summary_rows, stat_rows)
        prev_key = parse_run_tag(from_tag)
        prev_grades = grades_at_tag(repo, from_tag, prev_key[0]) if prev_key else {}
        curr_grades = grades_at_tag(repo, to_tag, run_id)
        regressions = detect_grade_regressions(prev_grades, curr_grades)

    coherence = run_coherence_at_tag(repo, to_tag, run_id)
    grade_export = grade_export_at_tag(repo, to_tag, run_id)
    forge_proofs = forge_proofs_at_tag(repo, to_tag)
    report = build_report(
        run_id,
        from_tag,
        to_tag,
        dolt_commit,
        tables,
        regressions,
        coherence,
        grade_export,
        forge_proofs,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / f"run-delta-{run_id}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    demotion_path = reports_dir / "legacy-forge-proofs-demotion.json"
    demotion_path.write_text(json.dumps(build_forge_proof_receipt(report), indent=2) + "\n")
    return out_path, report


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------


def newest_run_tag(tags: list[str]) -> str | None:
    keyed = [(parse_run_tag(t), t) for t in tags]
    keyed = [(k, t) for k, t in keyed if k is not None]
    return max(keyed)[1] if keyed else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dolt-dir", type=Path, default=DEFAULT_DOLT_DIR)
    parser.add_argument("--run-id", type=int, default=None, help="run to report on (default: newest run tag)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument(
        "--alert-on-regression",
        action="store_true",
        help="exit 4 when grade regressions are found (a downstream-consumable signal; default inert)",
    )
    args = parser.parse_args()

    if not (args.dolt_dir / ".dolt").is_dir():
        log(f"not a Dolt repo: {args.dolt_dir}")
        return 1
    try:
        tags = local_tags(args.dolt_dir)
        if args.run_id is not None:
            # Prefer the highest suffix of the requested run (the tag that
            # actually carries the latest data for run N).
            candidates = [t for t in tags if (k := parse_run_tag(t)) and k[0] == args.run_id]
            if not candidates:
                log(f"no run-{args.run_id} tag in {args.dolt_dir}")
                return 1
            to_tag = max(candidates, key=parse_run_tag)
            run_id = args.run_id
        else:
            to_tag = newest_run_tag(tags)
            if to_tag is None:
                log("no run tags found — nothing to report on")
                return 1
            run_id = parse_run_tag(to_tag)[0]
        out_path, report = emit(
            args.dolt_dir,
            run_id,
            commit_of_tag(args.dolt_dir, to_tag),
            to_tag,
            args.out_dir,
        )
        log(summary_line(report, out_path))
        if args.alert_on_regression and report["grade_regressions"]:
            log(f"ALERT: {len(report['grade_regressions'])} grade regressions detected — exiting 4 as requested")
            return 4
        return 0
    except DeltaError as exc:
        log(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

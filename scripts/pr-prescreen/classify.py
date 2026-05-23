"""PR pre-screen classifier.

Pure function: validator JSON output -> verdict for a contributor PR.

Input is the list emitted by `validate-skills-schema.py --marketplace --json`,
optionally filtered to only paths the PR touches. Each entry is one of:
    {"path": str, "score": int, "grade": str, "errors": int, "warnings": int}
    {"path": str, "fatal": str}

Output:
    {
      "verdict": "PASS" | "CHANGES_REQUESTED" | "HARD_BLOCK",
      "blockers": [str, ...],       # human-readable blocker reasons
      "warnings": [str, ...],       # non-blocking advisories
      "summary":  str,              # short one-line summary
      "results":  [ ... ],          # the (filtered) input list, echoed back
    }

Verdicts:
    HARD_BLOCK         - any fatal entry, or any caller-supplied
                         hard-block signal (no catalog entry, no
                         implementation files, license mismatch, secret
                         in diff, etc.).
    CHANGES_REQUESTED  - validator errors OR any skill graded D/F.
    PASS               - zero errors AND every skill graded C or better.

No I/O, no network, no dependencies beyond stdlib. Designed for unit-testing.
"""

from __future__ import annotations

import json
import sys
from typing import Iterable


GRADE_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def classify(
    validator_results: list[dict],
    *,
    hard_block_signals: Iterable[str] = (),
) -> dict:
    """Classify a set of validator results into a single PR verdict.

    Args:
        validator_results: list of dicts from `validate-skills-schema.py --json`.
        hard_block_signals: optional caller-supplied reasons that elevate the
            verdict to HARD_BLOCK regardless of validator output (e.g. the
            workflow detected no implementation files, no catalog entry, a
            license mismatch, or a secret in the diff).

    Returns:
        dict with keys verdict, blockers, warnings, summary, results.
    """
    # Materialize once — a generator gets exhausted by the loop below and
    # the later truthiness check would silently see an empty iterator.
    signals = [s for s in hard_block_signals if s]
    blockers: list[str] = list(signals)
    warnings: list[str] = []

    fatal_count = 0
    failing_skills: list[tuple[str, str]] = []  # (path, grade) for errors or D/F
    weak_skills: list[tuple[str, str]] = []  # (path, grade) for C

    for entry in validator_results:
        path = entry.get("path", "<unknown>")
        if "fatal" in entry:
            fatal_count += 1
            blockers.append(f"{path}: fatal — {entry['fatal']}")
            continue
        # `or 0` handles JSON null explicitly; .get default only fires on missing key.
        errors = int(entry.get("errors") or 0)
        grade = entry.get("grade", "F")
        if errors or grade in ("D", "F"):
            if (path, grade) not in failing_skills:
                failing_skills.append((path, grade))
        elif grade == "C":
            if (path, grade) not in weak_skills:
                weak_skills.append((path, grade))

    if fatal_count or signals:
        verdict = "HARD_BLOCK"
    elif failing_skills:
        verdict = "CHANGES_REQUESTED"
    else:
        verdict = "PASS"

    # Always surface failing-skill detail as blockers — both HARD_BLOCK and
    # CHANGES_REQUESTED need to tell the contributor *what* broke.
    for path, grade in failing_skills:
        blockers.append(f"{path}: validator errors / grade {grade}")

    for path, grade in weak_skills:
        warnings.append(f"{path}: grade {grade} — borderline, consider polish")

    summary = _summarize(verdict, validator_results, blockers, warnings)

    return {
        "verdict": verdict,
        "blockers": blockers,
        "warnings": warnings,
        "summary": summary,
        "results": validator_results,
    }


def _summarize(verdict: str, results: list[dict], blockers: list[str], warnings: list[str]) -> str:
    n = len(results)
    if n == 0:
        return f"{verdict}: no plugin paths matched the PR diff."
    # Null-safe: validator can emit "score": null on partial results.
    scores = [int(r["score"]) for r in results if r.get("score") is not None]
    avg = (sum(scores) / len(scores)) if scores else 0
    parts = [f"{verdict}: {n} skill(s) inspected"]
    if scores:
        parts.append(f"avg score {avg:.0f}/100")
    if blockers:
        parts.append(f"{len(blockers)} blocker(s)")
    if warnings:
        parts.append(f"{len(warnings)} warning(s)")
    return " · ".join(parts)


def main(argv: list[str]) -> int:
    """Read validator JSON from stdin (or argv[1]) and emit classifier JSON.

    Hard-block signals come from the env var PR_PRESCREEN_HARD_BLOCKS, a
    newline-separated list (set by the workflow when it detects e.g. no
    catalog entry).
    """
    import os

    raw: str
    if len(argv) > 1 and argv[1] != "-":
        with open(argv[1], "r", encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = sys.stdin.read()

    raw = raw.strip()
    if not raw:
        results = []
    else:
        results = json.loads(raw)
        if not isinstance(results, list):
            print("classify.py: expected a JSON list on stdin", file=sys.stderr)
            return 2

    signals = [s for s in os.environ.get("PR_PRESCREEN_HARD_BLOCKS", "").split("\n") if s.strip()]
    out = classify(results, hard_block_signals=signals)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))

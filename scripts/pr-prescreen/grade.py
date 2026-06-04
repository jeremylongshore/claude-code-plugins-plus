"""PR-level grade composer.

Given per-skill validator results plus per-component evaluator outputs (agents,
MCP, hooks, catalog adds), compute a SINGLE overall PR grade (A/B/C/D/F) and
generate actionable "how to reach A" deltas.

Grade semantics:
    The PR grade is the WEAKEST per-component grade. A PR with three A-grade
    skills and one C-grade skill grades C. The rationale: the marketplace
    surfaces every artifact; one weak skill drags the whole submission's
    reputation. Contributors get specific deltas for the weakest items.

Score → grade mapping (matches the IS marketplace validator):
    A:  90–100
    B:  80–89
    C:  70–79
    D:  60–69
    F:   0–59

No I/O, no network, no dependencies beyond stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GRADE_ORDER = ("A", "B", "C", "D", "F")
GRADE_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
PASS_GRADE = "A"


# --- Score → grade ----------------------------------------------------------


def score_to_grade(score: int | float | None) -> str:
    if score is None:
        return "F"
    s = float(score)
    if s >= 90:
        return "A"
    if s >= 80:
        return "B"
    if s >= 70:
        return "C"
    if s >= 60:
        return "D"
    return "F"


def grade_to_band(grade: str) -> tuple[int, int]:
    """Return (low, high) inclusive band for a grade letter."""
    bands = {"A": (90, 100), "B": (80, 89), "C": (70, 79), "D": (60, 69), "F": (0, 59)}
    return bands.get(grade.upper(), (0, 0))


def points_to_next_grade(score: int | float, current_grade: str) -> int:
    """How many points are needed to escape the current grade band upward."""
    next_grade_index = max(GRADE_ORDER.index(current_grade) - 1, 0)
    if next_grade_index == GRADE_ORDER.index(current_grade):
        return 0  # already at A
    next_grade = GRADE_ORDER[next_grade_index]
    next_low, _ = grade_to_band(next_grade)
    return max(int(next_low - float(score)), 1)


# --- Per-skill delta extraction --------------------------------------------


@dataclass
class SkillFinding:
    """One actionable delta for a specific skill on the path to A."""

    path: str
    current_score: int
    current_grade: str
    points_to_a: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def headline(self) -> str:
        return (
            f"{self.path}: {self.current_grade} ({self.current_score}/100), "
            f"+{self.points_to_a} pts to A"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "current_score": self.current_score,
            "current_grade": self.current_grade,
            "points_to_a": self.points_to_a,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def extract_skill_findings(
    validator_results: list[dict[str, Any]]
) -> list[SkillFinding]:
    """Pull SkillFinding objects out of validator JSON output.

    Each input record is expected to follow the shape emitted by
    scripts/validate-skills-schema.py --json:
        {"path": str, "score": int, "grade": str,
         "errors": int, "warnings": int,
         "error_messages": [str, ...], "warning_messages": [str, ...]}
    Older shapes use "errors"/"warnings" as plain counts; if a list is
    present under "error_messages" we surface it.
    """
    out: list[SkillFinding] = []
    for entry in validator_results:
        if "fatal" in entry:
            out.append(
                SkillFinding(
                    path=entry.get("path", "<unknown>"),
                    current_score=0,
                    current_grade="F",
                    points_to_a=90,
                    errors=[entry["fatal"]],
                )
            )
            continue
        score = int(entry.get("score") or 0)
        grade = (entry.get("grade") or score_to_grade(score)).upper()
        errors = entry.get("error_messages") or []
        warnings = entry.get("warning_messages") or []
        if grade == "A":
            continue  # nothing to surface
        out.append(
            SkillFinding(
                path=entry.get("path", "<unknown>"),
                current_score=score,
                current_grade=grade,
                points_to_a=points_to_next_grade(score, grade)
                if grade != "A"
                else 0,
                errors=list(errors) if isinstance(errors, list) else [str(errors)],
                warnings=list(warnings) if isinstance(warnings, list) else [str(warnings)],
            )
        )
    # Sort by lowest grade first (most urgent), then by points-to-A (closest first)
    out.sort(key=lambda f: (GRADE_RANK[f.current_grade], -f.points_to_a))
    return out


# --- Overall grade composition ---------------------------------------------


def compose_grade(
    validator_results: list[dict[str, Any]],
    *,
    hard_block_signals: list[str] | None = None,
) -> dict[str, Any]:
    """Compose the PR-level grade + deltas + verdict.

    Args:
        validator_results: per-skill validator records.
        hard_block_signals: caller-supplied conditions that force F regardless
            of validator output (e.g. no catalog entry, secret in diff).

    Returns:
        {
            "grade":           "A" | "B" | "C" | "D" | "F",
            "score":           min per-component score (or 0 if hard-blocked),
            "verdict":         "PASS" | "CHANGES_REQUESTED" | "HARD_BLOCK",
            "hard_block_signals": [...],
            "deltas":          [SkillFinding.to_dict(), ...],
            "summary_line":    short one-line description,
            "rubric_url":      pointer to the public grading rubric,
        }
    """
    signals = [s for s in (hard_block_signals or []) if s]
    if signals:
        return {
            "grade": "F",
            "score": 0,
            "verdict": "HARD_BLOCK",
            "hard_block_signals": signals,
            "deltas": [],
            "summary_line": f"HARD_BLOCK: {signals[0]}"
            + (f" (+{len(signals) - 1} more)" if len(signals) > 1 else ""),
            "rubric_url": _RUBRIC_URL,
        }

    if not validator_results:
        return {
            "grade": "F",
            "score": 0,
            "verdict": "HARD_BLOCK",
            "hard_block_signals": ["no validator results"],
            "deltas": [],
            "summary_line": "HARD_BLOCK: no skill/agent/MCP/hook artifacts evaluated",
            "rubric_url": _RUBRIC_URL,
        }

    scores: list[int] = []
    grades: list[str] = []
    fatal_paths: list[str] = []
    for r in validator_results:
        if "fatal" in r:
            fatal_paths.append(r.get("path", "<unknown>"))
            continue
        if r.get("score") is not None:
            scores.append(int(r["score"]))
        if r.get("grade"):
            grades.append(str(r["grade"]).upper())

    if fatal_paths:
        return {
            "grade": "F",
            "score": 0,
            "verdict": "HARD_BLOCK",
            "hard_block_signals": [f"fatal: {p}" for p in fatal_paths],
            "deltas": [d.to_dict() for d in extract_skill_findings(validator_results)],
            "summary_line": f"HARD_BLOCK: {len(fatal_paths)} fatal validator error(s)",
            "rubric_url": _RUBRIC_URL,
        }

    min_score = min(scores) if scores else 0
    lowest_grade = (
        max(grades, key=lambda g: GRADE_RANK.get(g, 0)) if False else None
    )
    # Take the WORST grade (lowest in rank), not the highest
    lowest_grade = min(grades, key=lambda g: GRADE_RANK.get(g, 0)) if grades else "F"
    if not lowest_grade:
        lowest_grade = score_to_grade(min_score)

    deltas = [d.to_dict() for d in extract_skill_findings(validator_results)]

    if lowest_grade == "A":
        verdict = "PASS"
        summary = f"PASS: {len(validator_results)} component(s), all A-grade (min {min_score}/100)"
    elif lowest_grade == "B":
        verdict = "CHANGES_REQUESTED"
        summary = (
            f"CHANGES_REQUESTED: {len(validator_results)} component(s), "
            f"weakest grade B (min {min_score}/100). Close — see deltas."
        )
    elif lowest_grade == "C":
        verdict = "CHANGES_REQUESTED"
        summary = (
            f"CHANGES_REQUESTED: {len(validator_results)} component(s), "
            f"weakest grade C (min {min_score}/100)"
        )
    else:
        verdict = "CHANGES_REQUESTED"
        summary = (
            f"CHANGES_REQUESTED: {len(validator_results)} component(s), "
            f"weakest grade {lowest_grade} (min {min_score}/100)"
        )

    return {
        "grade": lowest_grade,
        "score": min_score,
        "verdict": verdict,
        "hard_block_signals": [],
        "deltas": deltas,
        "summary_line": summary,
        "rubric_url": _RUBRIC_URL,
    }


# --- Comment composition ---------------------------------------------------


_RUBRIC_URL = "https://tonsofskills.com/grading"


def render_comment(grade_result: dict[str, Any]) -> str:
    """Render the prescreen comment markdown for posting to a PR."""
    grade = grade_result["grade"]
    score = grade_result["score"]
    verdict = grade_result["verdict"]
    summary = grade_result["summary_line"]
    deltas = grade_result.get("deltas", [])
    hard_signals = grade_result.get("hard_block_signals", [])

    lines: list[str] = []
    if verdict == "PASS":
        lines.append(f"## ✅ Prescreen: Grade **A** ({score}/100)")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("All components meet the marketplace bar. Ready to merge once required checks pass.")
    elif verdict == "HARD_BLOCK":
        lines.append(f"## 🛑 Prescreen: HARD BLOCK")
        lines.append("")
        lines.append(summary)
        lines.append("")
        if hard_signals:
            lines.append("**Blockers:**")
            lines.append("")
            for s in hard_signals:
                lines.append(f"- {s}")
            lines.append("")
    else:
        lines.append(f"## 🟡 Prescreen: Grade **{grade}** ({score}/100)")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append(
            f"Marketplace bar is **A** (≥90). See the public rubric at "
            f"<{_RUBRIC_URL}> for the full 100-point breakdown."
        )
        lines.append("")

    if deltas:
        lines.append("### How to reach A")
        lines.append("")
        for d in deltas[:5]:
            lines.append(
                f"- **{d['path']}** — {d['current_grade']} "
                f"({d['current_score']}/100, +{d['points_to_a']} pts needed)"
            )
            for err in (d.get("errors") or [])[:3]:
                lines.append(f"    - error: {err}")
            for warn in (d.get("warnings") or [])[:2]:
                lines.append(f"    - warning: {warn}")
        if len(deltas) > 5:
            lines.append(f"- … and {len(deltas) - 5} more component(s)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"_Public rubric:_ <{_RUBRIC_URL}> _·_ "
        "_How submissions are graded across 200+ marketplace plugins._"
    )

    return "\n".join(lines)

#!/usr/bin/env python3
"""PR pre-screen coordinator.

Consumes the output of `scripts/pr-classifier/detect_components.py`,
dispatches per-contribution-type evaluators (validate-skills-schema.py for
skills, validate-agent.py for agents, etc.), composes the per-skill validator
results via grade.py, and emits a single structured output that drives:

  1. ONE composed PR comment (markdown), and
  2. A `prescreen-grade` status check verdict (PASS / CHANGES_REQUESTED /
     HARD_BLOCK) → drives merge gating.

This script ABSORBS the existing scripts/pr-prescreen/classify.py +
summarize.py outputs into a single coordinator. The old scripts remain
importable and are still wired into the current pr-prescreen.yml workflow;
this script will become the new workflow's single entry point in PR 3c.

The coordinator is read-only — it does not modify files. Validator invocations
are subprocess calls; no network unless an evaluator script makes one. Designed
for `pull_request_target` execution per the existing prescreen safety model
(persist-credentials: false, pinned SHAs).

Usage:
    # End-to-end: read classifier output, run evaluators, emit comment
    python3 scripts/pr-prescreen/coordinator.py \\
        --classifier-output /tmp/classifier.json \\
        --comment-output /tmp/prescreen-comment.md \\
        --verdict-output /tmp/prescreen-verdict.json

    # Skip subprocess evaluator calls (useful for testing the composition logic):
    python3 scripts/pr-prescreen/coordinator.py \\
        --classifier-output /tmp/classifier.json \\
        --validator-results-file /tmp/validator-results.json \\
        --comment-output /tmp/prescreen-comment.md \\
        --verdict-output /tmp/prescreen-verdict.json

Exit codes:
    0 — coordinator ran successfully (verdict captured in --verdict-output)
    2 — input error (missing classifier output, malformed JSON, etc.)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_SELF = Path(__file__).resolve()
_REPO_ROOT = _SELF.parents[2]


# Load grade.py via importlib so this works whether imported as a package
# member or executed as a standalone script.
def _load_grade_module() -> Any:
    spec = importlib.util.spec_from_file_location("_pr_prescreen_grade", _SELF.parent / "grade.py")
    mod = importlib.util.module_from_spec(spec)
    # dataclass uses sys.modules lookup during decoration — register the
    # module under its spec name before exec so the decorator can resolve it.
    sys.modules["_pr_prescreen_grade"] = mod
    spec.loader.exec_module(mod)
    return mod


_grade = _load_grade_module()


# --- Classifier output → evaluator dispatch ---------------------------------


def _is_within_repo(candidate: Path) -> bool:
    """Defense-in-depth bounds check — reject resolved paths outside the repo.

    Reviewer (PR #840) flagged: `affected_skills` and `plugin_paths` come
    from classifier output, which is derived from the PR's file diff. A
    malicious or accidental ../-traversal entry like `affected_skills:
    ['../../etc/passwd']` would otherwise let _resolve_skill_paths construct
    a path outside the repo root. We resolve + check is_relative_to before
    accepting the path.
    """
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        return False
    try:
        return resolved.is_relative_to(_REPO_ROOT)
    except AttributeError:  # pragma: no cover — pre-Python 3.9 fallback
        return str(resolved).startswith(str(_REPO_ROOT))


def _resolve_skill_paths(affected_skills: list[str], plugin_paths: list[str]) -> list[Path]:
    """For each affected skill name, locate its SKILL.md within the affected
    plugin paths. Returns absolute paths CONFINED to the repo root."""
    out: list[Path] = []
    for skill_name in affected_skills:
        for plugin_path in plugin_paths:
            candidate = _REPO_ROOT / plugin_path / "skills" / skill_name / "SKILL.md"
            if not _is_within_repo(candidate):
                # Reject path-traversal attempts silently. Logging here would
                # be useful in CI but log-noise everywhere else.
                continue
            if candidate.exists():
                out.append(candidate)
                break
        else:
            continue
    return out


def run_skill_validator(skill_paths: list[Path], *, validator_script: Path | None = None) -> list[dict[str, Any]]:
    """Invoke validate-skills-schema.py --marketplace --json against the given
    SKILL.md paths. Returns the parsed JSON list."""
    if not skill_paths:
        return []
    script = validator_script or (_REPO_ROOT / "scripts" / "validate-skills-schema.py")
    if not script.exists():
        return [{"path": str(p), "fatal": f"validator script missing at {script}"} for p in skill_paths]
    # `--` separates flags from positional args so a path like `--foo` cannot
    # be parsed as a CLI flag by the validator (reviewer fix PR #840).
    cmd: list[str] = [
        "python3",
        str(script),
        "--marketplace",
        "--json",
        "--",
        *(str(p) for p in skill_paths),
    ]
    try:
        proc = subprocess.run(  # noqa: S603 — script paths controlled by repo
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return [{"path": str(p), "fatal": f"validator invocation failed: {e}"} for p in skill_paths]
    if proc.returncode != 0 and not proc.stdout.strip():
        return [
            {"path": str(p), "fatal": f"validator exit {proc.returncode}: {proc.stderr.strip()[:200]}"}
            for p in skill_paths
        ]
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return [{"path": str(p), "fatal": f"validator JSON parse: {e}"} for p in skill_paths]
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    if not isinstance(data, list):
        return [{"path": str(p), "fatal": "validator returned non-list JSON"} for p in skill_paths]
    # Drop the trailing kernel_shadow advisory element (DR-049 shadow block) —
    # it is not a per-skill result and must not become a SkillFinding.
    return [entry for entry in data if not (isinstance(entry, dict) and "kernel_shadow" in entry)]


# --- Top-level coordination -------------------------------------------------


def coordinate(
    classifier_output: dict[str, Any],
    *,
    validator_results: list[dict[str, Any]] | None = None,
    validator_invoker: Any = run_skill_validator,
    hard_block_signals: list[str] | None = None,
) -> dict[str, Any]:
    """Run the end-to-end coordinator.

    Args:
        classifier_output: parsed JSON from pr-classifier.
        validator_results: optional pre-computed validator results. When
            supplied, skips subprocess invocations — useful for tests.
        validator_invoker: callable accepting (skill_paths) → validator
            results list. Override for tests.
        hard_block_signals: additional caller-supplied blockers.

    Returns:
        {
          "classifier":    <classifier_output>,
          "validator_results": [...],
          "grade":         "A" | "B" | "C" | "D" | "F",
          "score":         int,
          "verdict":       "PASS" | "CHANGES_REQUESTED" | "HARD_BLOCK",
          "comment":       markdown comment string,
          "status_check":  "success" | "failure",
        }
    """
    affected_skills = classifier_output.get("affected_skills") or []
    affected_agents = classifier_output.get("affected_agents") or []
    affected_mcp = classifier_output.get("affected_mcp") or []
    affected_hooks = classifier_output.get("affected_hooks") or []
    catalog_adds = classifier_output.get("catalog_additions") or []
    plugin_paths = classifier_output.get("plugin_paths") or []

    no_evaluable_artifacts = (
        not affected_skills and not affected_agents and not affected_mcp and not affected_hooks and not catalog_adds
    )

    # Doc-only / scripts-only / ci-only PRs have no evaluable skill artifacts.
    # Reviewer (PR #840) correctly flagged that the prior HARD_BLOCK policy
    # here blocked every doc fix and typo correction. Explicit PASS instead,
    # so the prescreen never blocks a PR that has nothing the marketplace
    # validator can grade.
    if no_evaluable_artifacts and not hard_block_signals:
        verdict_payload = {
            "grade": "A",
            "score": 100,
            "verdict": "PASS",
            "hard_block_signals": [],
            "summary_line": ("PASS: no skill / agent / MCP / hook / catalog-add artifacts in scope for this PR"),
            "deltas": [],
            "rubric_url": "https://tonsofskills.com/grading",
        }
        return {
            "classifier": classifier_output,
            "validator_results": [],
            "grade": "A",
            "score": 100,
            "verdict": "PASS",
            "hard_block_signals": [],
            "summary_line": verdict_payload["summary_line"],
            "deltas": [],
            "comment": _grade.render_comment(verdict_payload),
            "status_check": "success",
        }

    if validator_results is None:
        if affected_skills:
            skill_paths = _resolve_skill_paths(affected_skills, plugin_paths)
            validator_results = validator_invoker(skill_paths)
        else:
            validator_results = []

    grade_result = _grade.compose_grade(validator_results, hard_block_signals=hard_block_signals)

    comment = _grade.render_comment(grade_result)

    status_check = "success" if grade_result["grade"] == _grade.PASS_GRADE else "failure"
    # Hard blocks always fail
    if grade_result["verdict"] == "HARD_BLOCK":
        status_check = "failure"

    return {
        "classifier": classifier_output,
        "validator_results": validator_results,
        "grade": grade_result["grade"],
        "score": grade_result["score"],
        "verdict": grade_result["verdict"],
        "hard_block_signals": grade_result.get("hard_block_signals", []),
        "summary_line": grade_result.get("summary_line", ""),
        "deltas": grade_result.get("deltas", []),
        "comment": comment,
        "status_check": status_check,
    }


# --- CLI -------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--classifier-output",
        required=True,
        help="Path to JSON produced by scripts/pr-classifier/detect_components.py",
    )
    p.add_argument(
        "--validator-results-file",
        default=None,
        help="Optional pre-computed validator JSON to skip subprocess calls",
    )
    p.add_argument(
        "--comment-output",
        default=None,
        help="Write the composed comment markdown to FILE (default: stdout)",
    )
    p.add_argument(
        "--verdict-output",
        default=None,
        help="Write the coordinator verdict JSON to FILE",
    )
    p.add_argument(
        "--hard-block-signal",
        action="append",
        default=[],
        help="Caller-supplied hard-block reason (repeatable)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    classifier_path = Path(args.classifier_output)
    if not classifier_path.exists():
        print(f"error: --classifier-output {classifier_path} not found", file=sys.stderr)
        return 2
    try:
        classifier_output = json.loads(classifier_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: malformed classifier JSON: {e}", file=sys.stderr)
        return 2

    validator_results: list[dict[str, Any]] | None = None
    if args.validator_results_file:
        try:
            validator_results = json.loads(Path(args.validator_results_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: --validator-results-file: {e}", file=sys.stderr)
            return 2

    coord = coordinate(
        classifier_output,
        validator_results=validator_results,
        hard_block_signals=list(args.hard_block_signal),
    )

    comment_md = coord["comment"]
    if args.comment_output:
        Path(args.comment_output).write_text(comment_md, encoding="utf-8")
    else:
        print(comment_md)

    if args.verdict_output:
        # Trim noisy embedded comment from the verdict json so the file is small
        verdict = {k: v for k, v in coord.items() if k != "comment"}
        Path(args.verdict_output).write_text(json.dumps(verdict, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())

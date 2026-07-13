#!/usr/bin/env python3
"""promote-to-curated.py — generate `skills/.curated/` as a rebuilt-every-run MIRROR of
the repo's best plugin skills, so skills.sh (which only crawls root `skills/`, `.curated/`,
`.experimental/` and agent dirs — NOT `plugins/**/skills/`) can surface them.

Why this exists
---------------
skills.sh indexes skills at the repository root; it does not descend into
`plugins/**/skills/`, where ~3,100 of our real skills live. Symlinks are skipped by the
skills CLI (tested); only real files under `skills/.curated/` are discovered. So the only
way to put our best plugin skills on skills.sh is a generated mirror of copies — with the
plugin skill under `plugins/**` staying the SOURCE OF TRUTH (graded in Dolt/Freshie), and
the copies rebuilt from it, never hand-edited.

Selection (decided): grade **A + B**, plugin skills only, EXCLUDING external mirrors (a
plugin root carrying a `.source.json`) so we never republish someone else's work under our
name. That is ~1,881 of our own skills.

Selection source = `freshie/grades.csv` — the TRACKED, compact export of the latest Freshie
run (`skill_path,grade,score`). We deliberately read the CSV, not `freshie/inventory.sqlite`:
the sqlite blob is git-ignored and absent in CI, but the `--check` drift gate has to run in
CI. The CSV is the same latest-run grade surface, is committed, and makes the whole pipeline
byte-reproducible between a dev box and CI's clean checkout (the same reason
`generate-readme-toc.mjs` computes its counts from `git ls-files`, not the working tree).

Defense (build mode only): the recorded grade can go stale if a source SKILL.md was edited
after the last inventory run. So each candidate is RE-GRADED in-process by the canonical
validator (`scripts/validate-skills-schema.py::validate_skill`, marketplace tier); it is
promoted only if its FRESH grade is still A or B and it parses. We gate on the grade (the
validator's holistic verdict), NOT on the marketplace ERROR list: ~52% of even A/B skills
carry non-blocking marketplace warnings/errors (missing body sections, tool-permission
nits) — the same posture their sources already have on `main`, where the full `--marketplace`
sweep runs `|| true`. Gating on zero errors would silently halve the corpus and defeat the
"maximum reach" goal. (Grade-stability drops 0 skills today and still catches a source that
regressed below B since grading.)

Copy fidelity: we copy only the GIT-TRACKED files of each source skill dir (`git ls-files`),
never the working-tree junk or a git-ignored `data/` blob. That makes a local build identical
to a CI build (a fresh checkout only has tracked files anyway) and sidesteps the
`**/skills/*/data/` .gitignore depth mismatch.

Modes
-----
  (default / build)  Wipe `skills/.curated/` and rebuild it from the current selection.
                     Writes `skills/.curated/MANIFEST.json` (the audit trail of what was
                     promoted and why). Needs the validator importable (local dev / the
                     weekly workflow after `pnpm install`); degrades to the recorded grade
                     with a loud warning if it is not.
  --check            CI drift gate. Reads the committed MANIFEST and verifies every promoted
                     copy is byte-identical to the current git-tracked source, with no orphan
                     or missing dirs. Deterministic, git-only — no validator, no sqlite, no
                     node_modules — so it runs in a minimal CI job without false drift. Exits
                     1 on any drift (same contract as `generate-readme-toc.mjs --check`).

Usage
-----
  python3 freshie/scripts/promote-to-curated.py            # rebuild skills/.curated/
  python3 freshie/scripts/promote-to-curated.py --check    # CI: exit 1 if stale vs source
  python3 freshie/scripts/promote-to-curated.py --no-validate   # skip the in-process regrade
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
GRADES_CSV = ROOT / "freshie" / "grades.csv"
CURATED_DIR = ROOT / "skills" / ".curated"
MANIFEST = CURATED_DIR / "MANIFEST.json"
VALIDATOR = ROOT / "scripts" / "validate-skills-schema.py"

PROMOTE_GRADES = {"A", "B"}


# ── selection ────────────────────────────────────────────────────────────────
def _plugin_root(skill_path: str) -> str:
    """The plugin dir that owns a skill: everything before `/skills/`."""
    return skill_path.split("/skills/")[0] if "/skills/" in skill_path else skill_path


def load_candidates(grades_csv: Path) -> List[Dict[str, str]]:
    """A+B plugin skills, our own (no `.source.json`), whose source dir still exists.

    Sorted by skill_path for deterministic output.
    """
    if not grades_csv.exists():
        sys.exit(
            f"error: {grades_csv} not found — run the Freshie cycle first "
            f"(rebuild-inventory.py → validate --populate-db → dolt-sync.py)."
        )
    out: List[Dict[str, str]] = []
    with grades_csv.open(newline="") as fh:
        for row in csv.DictReader(fh):
            sp, grade = row.get("skill_path", ""), row.get("grade", "")
            if not sp.startswith("plugins/") or grade not in PROMOTE_GRADES:
                continue
            root = _plugin_root(sp)
            if (ROOT / root / ".source.json").exists():
                continue  # external mirror — never republish under our name
            if not (ROOT / sp).is_dir():
                continue  # source removed / downgraded since the graded run
            parts = sp.split("/")  # plugins/<category>/<plugin>/skills/<name>  (or shorter)
            out.append(
                {
                    "skill_path": sp,
                    "grade": grade,
                    "score": row.get("score", ""),
                    "category": parts[1] if len(parts) > 1 else "uncategorized",
                    "plugin": root.split("/")[-1],
                    "name": parts[-1],
                }
            )
    out.sort(key=lambda c: c["skill_path"])
    return out


# ── in-process re-grade (defense) ────────────────────────────────────────────
def load_validator():
    """Import scripts/validate-skills-schema.py as a module (hyphenated filename ⇒ importlib).

    Returns the module, or None if it cannot be loaded — the caller degrades gracefully.
    """
    try:
        spec = importlib.util.spec_from_file_location("vss_promote", VALIDATOR)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:  # noqa: BLE001 — any failure ⇒ fall back to recorded grade
        print(f"⚠️  could not import validator ({e}); falling back to recorded grades.", file=sys.stderr)
        return None


def fresh_grade(vss, skill_dir: Path) -> Optional[str]:
    """Re-grade a skill's SKILL.md at marketplace tier; return the letter grade, or None
    if it cannot be graded (missing/unparseable — a hard defense against a broken source)."""
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return None
    try:
        res = vss.validate_skill(md, tier=vss.TIER_MARKETPLACE)
    except Exception:  # noqa: BLE001 — a validator crash on one file must not sink the run
        return None
    if res.get("fatal"):
        return None
    return (res.get("grade") or {}).get("grade")


# ── curated names (collision-safe, deterministic) ────────────────────────────
def assign_curated_names(candidates: List[Dict[str, str]]) -> None:
    """Set c['curated_name'] on each candidate. Default is the skill dir name; on a name
    collision, prefix ALL colliding members with `<plugin>__`; a residual collision gets a
    deterministic numeric suffix. Mutates candidates in place."""
    counts: Dict[str, int] = {}
    for c in candidates:
        counts[c["name"]] = counts.get(c["name"], 0) + 1
    used: Dict[str, int] = {}
    for c in candidates:  # candidates are already sorted by skill_path ⇒ deterministic
        base = c["name"] if counts[c["name"]] == 1 else f"{c['plugin']}__{c['name']}"
        name = base
        while name in used:  # residual collision (rare): append -2, -3, …
            used[base] += 1
            name = f"{base}-{used[base]}"
        used.setdefault(base, 1)
        used[name] = used.get(name, 1)
        c["curated_name"] = name


# ── git-tracked file enumeration ─────────────────────────────────────────────
def tracked_files(skill_dir: Path) -> List[str]:
    """Relative paths of the git-tracked files under a skill dir, sorted. Uses the committed
    tree so local == CI. Empty list means nothing tracked (skip)."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", str(skill_dir.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return []
    rel_to_root = [p for p in out.split("\0") if p]
    base = skill_dir.relative_to(ROOT).as_posix()
    files = [p[len(base) + 1 :] for p in rel_to_root if p.startswith(base + "/")]
    return sorted(files)


# ── build ────────────────────────────────────────────────────────────────────
def build(validate: bool = True, quiet: bool = False) -> int:
    candidates = load_candidates(GRADES_CSV)
    if not quiet:
        print(f"selection: {len(candidates)} A/B plugin skills (own, source present)")

    vss = load_validator() if validate else None
    if validate and vss is None:
        validate = False  # degrade: recorded grade only

    run_id = _run_id()
    assign_curated_names(candidates)

    # Wipe and rebuild — deletions/downgrades propagate, like build-cowork-zips.mjs.
    if CURATED_DIR.exists():
        shutil.rmtree(CURATED_DIR)
    CURATED_DIR.mkdir(parents=True)

    promoted: List[Dict] = []
    dropped_grade = 0
    dropped_empty = 0
    for c in candidates:
        src_dir = ROOT / c["skill_path"]

        fg: Optional[str] = None
        if validate:
            fg = fresh_grade(vss, src_dir)
            if fg not in PROMOTE_GRADES:
                dropped_grade += 1
                continue  # regressed below B (or unparseable) since the graded run

        files = tracked_files(src_dir)
        if not files or "SKILL.md" not in files:
            dropped_empty += 1
            continue  # nothing tracked to mirror

        dest_dir = CURATED_DIR / c["curated_name"]
        for rel in files:
            dst = dest_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src_dir / rel, dst)

        promoted.append(
            {
                "curated_name": c["curated_name"],
                "source_path": c["skill_path"],
                "category": c["category"],
                "plugin": c["plugin"],
                "recorded_grade": c["grade"],
                "fresh_grade": fg,  # None when --no-validate
                "run_id": run_id,
                "files": files,
            }
        )

    promoted.sort(key=lambda p: p["curated_name"])
    manifest = {
        "generator": "freshie/scripts/promote-to-curated.py",
        "generated_from": "freshie/grades.csv",
        "run_id": run_id,
        "threshold": "".join(sorted(PROMOTE_GRADES)),
        "validated": validate,
        "count": len(promoted),
        "skills": promoted,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    if not quiet:
        print(f"promoted: {len(promoted)} → skills/.curated/")
        if validate:
            print(f"dropped (fresh grade < B / unparseable): {dropped_grade}")
        if dropped_empty:
            print(f"dropped (no tracked files): {dropped_empty}")
        print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    return 0


def _run_id() -> Optional[int]:
    """Latest run id from grade-histogram.json (tracked), for the audit trail."""
    hist = ROOT / "freshie" / "grade-histogram.json"
    if hist.exists():
        try:
            return json.loads(hist.read_text()).get("run_id")
        except Exception:  # noqa: BLE001
            return None
    return None


# ── check (CI drift gate) ────────────────────────────────────────────────────
def _files_equal(a: Path, b: Path) -> bool:
    try:
        return a.read_bytes() == b.read_bytes()
    except OSError:
        return False


def check(quiet: bool = False) -> int:
    """Verify skills/.curated/ is a faithful, complete mirror of its recorded sources.

    Deterministic and git-only: for each MANIFEST entry, the copy must be byte-identical to
    the current git-tracked source; no orphan dirs, no missing dirs, no stale sources. This
    catches the primary failure mode — a promoted source edited without regenerating the
    mirror — without re-running the validator (whose grade depends on installed kernel
    schemas + validator version, which would risk false drift in a minimal CI job). Full
    selection refresh (newly-A skills, sources that dropped below B) is the weekly workflow's
    job, not this per-PR gate.
    """
    curated_present = (
        CURATED_DIR.exists() and any(p.is_dir() for p in CURATED_DIR.iterdir()) if CURATED_DIR.exists() else False
    )

    if not MANIFEST.exists():
        if not curated_present:
            if not quiet:
                print("skills/.curated/ not built — nothing to check.")
            return 0
        print(
            "::error::skills/.curated/ has skill dirs but no MANIFEST.json. "
            "Run: python3 freshie/scripts/promote-to-curated.py"
        )
        return 1

    manifest = json.loads(MANIFEST.read_text())
    entries = manifest.get("skills", [])
    expected_dirs = {e["curated_name"] for e in entries}
    drift: List[str] = []

    for e in entries:
        cname = e["curated_name"]
        src_dir = ROOT / e["source_path"]
        dst_dir = CURATED_DIR / cname
        if not src_dir.is_dir():
            drift.append(f"source removed: {e['source_path']} (promoted as {cname})")
            continue
        if not dst_dir.is_dir():
            drift.append(f"missing mirror dir: skills/.curated/{cname}")
            continue
        # Compare against the CURRENT git-tracked source (not the recorded file list) so a
        # newly-added or deleted source file surfaces as drift too.
        src_files = tracked_files(src_dir)
        for rel in src_files:
            if not _files_equal(src_dir / rel, dst_dir / rel):
                drift.append(f"stale copy: skills/.curated/{cname}/{rel} != {e['source_path']}/{rel}")
        # No extra files in the mirror beyond the tracked source set.
        src_set = set(src_files)
        for f in dst_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(dst_dir).as_posix()
                if rel not in src_set:
                    drift.append(f"orphan file: skills/.curated/{cname}/{rel}")

    # Orphan dirs: a `.curated/<dir>/` not named in the manifest.
    for p in CURATED_DIR.iterdir():
        if p.is_dir() and p.name not in expected_dirs:
            drift.append(f"orphan dir: skills/.curated/{p.name} (not in MANIFEST.json)")

    if drift:
        print("::error::skills/.curated/ is out of sync with its plugin sources.")
        for d in drift[:50]:
            print(f"  - {d}")
        if len(drift) > 50:
            print(f"  … and {len(drift) - 50} more")
        print("\nRun: python3 freshie/scripts/promote-to-curated.py")
        return 1

    if not quiet:
        print(f"skills/.curated/ in sync ({len(entries)} promoted skills).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Promote A/B plugin skills into skills/.curated/ for skills.sh.")
    ap.add_argument("--check", action="store_true", help="CI drift gate: exit 1 if the mirror is stale vs source.")
    ap.add_argument("--no-validate", action="store_true", help="Skip the in-process re-grade defense (build mode).")
    ap.add_argument("--quiet", action="store_true", help="Only print on error.")
    args = ap.parse_args()
    if args.check:
        return check(quiet=args.quiet)
    return build(validate=not args.no_validate, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())

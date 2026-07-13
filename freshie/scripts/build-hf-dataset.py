#!/usr/bin/env python3
"""build-hf-dataset.py — regenerate the HuggingFace skills dataset from the SAME source
of truth as the Dolt/Freshie CMDB: the marketplace catalog (skill content) JOINED with
`skill_compliance` (grades, JRig verdicts) from `freshie/inventory.sqlite`.

This is a published, browsable VIEW — not a hand-curated copy. Dolt/DoltHub stays the
versioned system-of-record for grades; this dataset is a rebuilt export (exactly like
`freshie/grades.csv`), so it can never diverge: re-run it and it reflects the current
inventory run. One JSONL row per skill = its content + frontmatter + its Freshie grade
and JRig-verified flag.

Join: catalog `filePath` (or slug/name fallback) ↔ `skill_compliance.skill_path`.

Inputs (read-only):
  marketplace/public/data/skills-catalog.json   full skill bodies + metadata
  marketplace/src/data/skills-index.json         category enrichment
  freshie/inventory.sqlite                        skill_compliance (latest run_id)

Outputs (build artifacts, git-ignored — regenerate any time):
  freshie/hf-dataset/skills.jsonl                 the dataset
  freshie/hf-dataset/README.md                    the HF dataset card
  freshie/hf-dataset/STATS.json                   run stats (counts, grade histogram)

Usage: python3 freshie/scripts/build-hf-dataset.py
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "marketplace" / "public" / "data" / "skills-catalog.json"
INDEX = ROOT / "marketplace" / "src" / "data" / "skills-index.json"
DB = ROOT / "freshie" / "inventory.sqlite"
OUT_DIR = ROOT / "freshie" / "hf-dataset"


def _norm_path(p):
    """Normalize a skill path for join: strip trailing /SKILL.md and slashes, lowercase."""
    if not p:
        return ""
    p = p.strip().replace("\\", "/").rstrip("/")
    low = p.lower()
    if low.endswith("/skill.md"):
        p = p[: -len("/skill.md")]
    return p.lower()


def _dir_key(p):
    """The skill's own directory name — the fallback join key (slug/name equivalent)."""
    p = _norm_path(p)
    return p.split("/")[-1] if p else ""


def load_grades():
    """Return (by_path, by_dir, run_id): grade/JRig maps keyed by normalized path and by
    dir name, for the latest inventory run."""
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    run_id = cur.execute("SELECT MAX(run_id) FROM skill_compliance").fetchone()[0]
    rows = cur.execute(
        "SELECT skill_path, grade, score, jrig_passed, jrig_tier_blocked, is_stub "
        "FROM skill_compliance WHERE run_id = ?",
        (run_id,),
    ).fetchall()
    con.close()
    by_path, by_dir = {}, {}
    for skill_path, grade, score, jrig_passed, jrig_blocked, is_stub in rows:
        rec = {
            "grade": grade,
            "score": score,
            "jrig_passed": bool(jrig_passed) if jrig_passed is not None else None,
            "jrig_tier_blocked": bool(jrig_blocked) if jrig_blocked is not None else None,
            "is_stub": bool(is_stub) if is_stub is not None else None,
        }
        by_path[_norm_path(skill_path)] = rec
        by_dir.setdefault(_dir_key(skill_path), rec)
    return by_path, by_dir, run_id


def load_categories():
    """slug -> category from the L0 index."""
    d = json.loads(INDEX.read_text())
    skills = d["skills"] if isinstance(d, dict) and "skills" in d else d
    return {s.get("slug"): s.get("category") for s in skills}


def main():
    for f in (CATALOG, INDEX, DB):
        if not f.exists():
            print(f"missing input: {f}", file=sys.stderr)
            return 2

    by_path, by_dir, run_id = load_grades()
    categories = load_categories()
    catalog = json.loads(CATALOG.read_text())
    skills = catalog["skills"] if isinstance(catalog, dict) and "skills" in catalog else catalog

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matched = 0
    grade_hist = {}
    with (OUT_DIR / "skills.jsonl").open("w") as fh:
        for s in skills:
            fp = _norm_path(s.get("filePath"))
            grade_rec = by_path.get(fp) or by_dir.get(_dir_key(s.get("filePath") or s.get("slug") or ""))
            if grade_rec is None:
                grade_rec = by_dir.get(s.get("slug") or "") or by_dir.get(s.get("name") or "")
            if grade_rec:
                matched += 1
                grade_hist[grade_rec["grade"]] = grade_hist.get(grade_rec["grade"], 0) + 1
            row = {
                "name": s.get("name"),
                "slug": s.get("slug"),
                "category": categories.get(s.get("slug")),
                "parent_plugin": s.get("parentPlugin"),
                "description": s.get("description"),
                "author": s.get("author"),
                "license": s.get("license"),
                "allowed_tools": s.get("allowedTools"),
                "version": s.get("version"),
                "visibility": s.get("visibility"),
                "file_path": s.get("filePath"),
                "content_html": s.get("content"),
                # Freshie CMDB quality signal (same source of truth as DoltHub):
                "grade": (grade_rec or {}).get("grade"),
                "score": (grade_rec or {}).get("score"),
                "jrig_passed": (grade_rec or {}).get("jrig_passed"),
                "jrig_tier_blocked": (grade_rec or {}).get("jrig_tier_blocked"),
                "is_stub": (grade_rec or {}).get("is_stub"),
                "inventory_run_id": run_id,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    total = len(skills)
    stats = {
        "skills": total,
        "graded": matched,
        "ungraded": total - matched,
        "inventory_run_id": run_id,
        "grade_histogram": dict(sorted(grade_hist.items())),
    }
    (OUT_DIR / "STATS.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

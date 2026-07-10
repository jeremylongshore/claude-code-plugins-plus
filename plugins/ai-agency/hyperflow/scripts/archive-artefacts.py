#!/usr/bin/env python3
"""Auto-archive stale .hyperflow/ artefacts and promote learnings to memory.

Runs at session start (and on demand). Idempotent. Daily-gated so repeat
session-starts don't churn. Never raises — best-effort cleanup.

Flow
----
For each *.md in .hyperflow/{tasks,audits,specs}/ whose mtime is older than
``staleDays`` (default 7):

  1. Parse its ``## Learnings`` / ``## Decisions`` / ``## Anti-patterns`` /
     ``## Pitfalls`` sections.
  2. Append (whole-line de-duplicated) to .hyperflow/memory/{learnings,
     decisions,anti-patterns}.md so the durable insight survives.
  3. Move the source file to .hyperflow/archive/<type>/YYYY-MM/<name>.

Completed (``feature.md`` Status = completed), stale ``.hyperflow/features/<slug>/``
folders are promoted (every phase's learnings) and the whole folder moved to
``.hyperflow/archive/features/YYYY-MM/<slug>/``. In-progress features are never
archived, however old.

Then prune .hyperflow/archive/** entries older than ``pruneDays`` (default 30).

Config (~/.hyperflow/config.json)
---------------------------------
  "cleanup": { "auto": true, "staleDays": 7, "pruneDays": 30 }

Set ``auto: false`` to disable. Defaults apply if any field is missing.

Usage
-----
  archive-artefacts.py <path-to-.hyperflow>
"""
from __future__ import annotations
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = {"auto": True, "staleDays": 7, "pruneDays": 30}

# Section title (lowercased) → target memory file
SECTION_TO_MEMORY = {
    "learnings": "learnings.md",
    "learning": "learnings.md",
    "decisions": "decisions.md",
    "decision": "decisions.md",
    "anti-patterns": "anti-patterns.md",
    "anti-pattern": "anti-patterns.md",
    "pitfalls": "anti-patterns.md",
    "pitfall": "anti-patterns.md",
}

TYPES = ("tasks", "audits", "specs")
DAY = 86400


def load_cfg() -> dict:
    cfg = dict(DEFAULTS)
    path = Path(os.environ.get("HOME", "")) / ".hyperflow" / "config.json"
    try:
        user = json.loads(path.read_text())
        cleanup = user.get("cleanup", {}) if isinstance(user, dict) else {}
        for k in cfg:
            v = cleanup.get(k)
            if isinstance(v, (bool, int)):
                cfg[k] = v
    except Exception:
        pass
    return cfg


def extract_sections(text: str) -> dict[str, list[str]]:
    """Return {memory_file: [body_lines]} for promotion-worthy sections."""
    out: dict[str, list[str]] = {}
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(#+)\s+(.*?)\s*$", lines[i])
        if not m:
            i += 1
            continue
        level = len(m.group(1))
        title = m.group(2).strip().lower()
        key = SECTION_TO_MEMORY.get(title)
        if not key:
            i += 1
            continue
        body: list[str] = []
        i += 1
        while i < n:
            nxt = re.match(r"^(#+)\s+", lines[i])
            if nxt and len(nxt.group(1)) <= level:
                break
            body.append(lines[i])
            i += 1
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        if body:
            out.setdefault(key, []).extend(body)
    return out


def append_deduped(target: Path, lines: list[str], source: str) -> int:
    existing: set[str] = set()
    if target.exists():
        try:
            existing = {ln.rstrip("\n") for ln in target.read_text().splitlines()}
        except Exception:
            existing = set()
    new = [ln for ln in lines if ln.strip() and ln.rstrip("\n") not in existing]
    if not new:
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        with target.open("a", encoding="utf-8") as f:
            f.write(f"\n<!-- promoted from {source} on {today} -->\n")
            for ln in new:
                f.write(ln.rstrip("\n") + "\n")
    except Exception:
        return 0
    return len(new)


def archive_file(hf: Path, type_: str, fpath: Path) -> tuple[bool, int]:
    """Promote sections then move file to archive. Returns (moved, lines_promoted)."""
    try:
        text = fpath.read_text(errors="replace")
    except Exception:
        return (False, 0)
    sections = extract_sections(text)
    promoted = 0
    for memfile, body in sections.items():
        promoted += append_deduped(hf / "memory" / memfile, body, fpath.name)
    try:
        bucket = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m")
    except Exception:
        bucket = "unknown"
    dest_dir = hf / "archive" / type_ / bucket
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fpath.name
    if dest.exists():
        dest = dest.with_name(f"{fpath.stem}-{int(time.time())}{fpath.suffix}")
    try:
        shutil.move(str(fpath), str(dest))
        return (True, promoted)
    except Exception:
        return (False, promoted)


def feature_is_completed(fdir: Path) -> bool:
    """True when the feature's feature.md Status block reads completed."""
    fm = fdir / "feature.md"
    try:
        text = fm.read_text(errors="replace")
    except Exception:
        return False
    # Match a Status table row: | Status | completed |
    return bool(re.search(r"^\|\s*Status\s*\|\s*completed\b", text, re.MULTILINE | re.IGNORECASE))


def archive_feature(hf: Path, fdir: Path) -> tuple[bool, int]:
    """Promote learnings from every .md in a completed feature folder, then move
    the whole folder to archive/features/YYYY-MM/<slug>/. Returns (moved, lines)."""
    promoted = 0
    for md in sorted(fdir.rglob("*.md")):
        try:
            sections = extract_sections(md.read_text(errors="replace"))
        except Exception:
            continue
        for memfile, body in sections.items():
            promoted += append_deduped(hf / "memory" / memfile, body, f"{fdir.name}/{md.name}")
    try:
        bucket = datetime.fromtimestamp(fdir.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m")
    except Exception:
        bucket = "unknown"
    dest_dir = hf / "archive" / "features" / bucket
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fdir.name
    if dest.exists():
        dest = dest.with_name(f"{fdir.name}-{int(time.time())}")
    try:
        shutil.move(str(fdir), str(dest))
        return (True, promoted)
    except Exception:
        return (False, promoted)


def prune_archive(hf: Path, prune_days: int) -> int:
    archive = hf / "archive"
    if not archive.exists():
        return 0
    cutoff = time.time() - prune_days * DAY
    pruned = 0
    for root, _dirs, files in os.walk(archive):
        for name in files:
            fp = Path(root) / name
            try:
                if fp.stat().st_mtime < cutoff:
                    fp.unlink()
                    pruned += 1
            except Exception:
                pass
    for root, _dirs, _files in os.walk(archive, topdown=False):
        try:
            p = Path(root)
            if p != archive and not any(p.iterdir()):
                p.rmdir()
        except Exception:
            pass
    return pruned


def main() -> None:
    if len(sys.argv) < 2:
        return
    hf = Path(sys.argv[1])
    if not hf.is_dir() or hf.name != ".hyperflow":
        return

    cfg = load_cfg()
    if not cfg.get("auto", True):
        return
    stale = max(1, int(cfg.get("staleDays", 7)))
    prune = max(stale, int(cfg.get("pruneDays", 30)))

    # ─── On-completion mode: --file <path> archives one file immediately ──────
    # Skills call this when a chain finishes successfully so the task/audit/spec
    # is promoted + archived right away rather than waiting for it to go stale.
    file_arg = None
    args = sys.argv[2:]
    for i, a in enumerate(args):
        if a == "--file" and i + 1 < len(args):
            file_arg = args[i + 1]
            break
        if a.startswith("--file="):
            file_arg = a.split("=", 1)[1]
            break
    if file_arg:
        fpath = Path(file_arg)
        if not fpath.is_absolute():
            fpath = hf.parent / fpath
        if not fpath.is_file():
            return
        # Determine artefact type from the path (tasks/audits/specs).
        type_ = "tasks"
        for t in TYPES:
            try:
                if (hf / t).resolve() in fpath.resolve().parents:
                    type_ = t
                    break
            except Exception:
                pass
        moved, promoted = archive_file(hf, type_, fpath)
        if moved or promoted:
            print(
                f"hyperflow cleanup: archived {fpath.name} on completion · "
                f"promoted {promoted} line(s) to memory",
                file=sys.stderr,
            )
        return

    # Daily gate — don't re-walk the tree on every session this day.
    marker = hf / ".last-cleanup"
    force = "--force" in sys.argv
    if not force and marker.exists():
        try:
            if time.time() - marker.stat().st_mtime < DAY:
                return
        except Exception:
            pass

    cutoff = time.time() - stale * DAY
    archived = 0
    promoted = 0
    for t in TYPES:
        d = hf / t
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if not p.is_file() or not p.name.endswith(".md"):
                continue
            try:
                if p.stat().st_mtime >= cutoff:
                    continue
            except Exception:
                continue
            moved, lines = archive_file(hf, t, p)
            if moved:
                archived += 1
            promoted += lines

    # Completed, stale feature folders → archive the whole folder.
    fdir_root = hf / "features"
    if fdir_root.is_dir():
        for fdir in sorted(fdir_root.iterdir()):
            if not fdir.is_dir() or not (fdir / "feature.md").is_file():
                continue
            try:
                if fdir.stat().st_mtime >= cutoff:
                    continue
            except Exception:
                continue
            if not feature_is_completed(fdir):
                continue  # never archive an in-progress feature, however old
            moved, lines = archive_feature(hf, fdir)
            if moved:
                archived += 1
            promoted += lines

    pruned = prune_archive(hf, prune)

    try:
        marker.write_text(datetime.now(timezone.utc).isoformat() + "\n")
    except Exception:
        pass

    if archived or promoted or pruned:
        print(
            f"hyperflow cleanup: archived {archived} stale file(s) · "
            f"promoted {promoted} line(s) to memory · pruned {pruned} old archive(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

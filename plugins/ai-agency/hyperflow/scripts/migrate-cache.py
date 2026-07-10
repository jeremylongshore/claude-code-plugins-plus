#!/usr/bin/env python3
"""Migrate a project's .hyperflow/ cache forward when the plugin version moves.

Runs at session start (and is safe to run on demand). Idempotent, non-destructive,
never raises — best-effort. A project set up by an older Hyperflow gets brought up
to the current cache structure the first time a newer plugin starts a session.

Mechanism
---------
- The cache version is stamped in ``.hyperflow/.version`` (the plugin version that
  last set up or migrated the cache). Missing marker ⇒ treat as a legacy cache.
- Each entry in ``MIGRATIONS`` declares ``since`` (the plugin version that introduced
  the change) and a function. A step runs when ``cache_version < since`` — so a cache
  several versions behind catches up through every intermediate step, in order.
- After applying, ``.hyperflow/.version`` is stamped to the current plugin version.
- When cache version already equals the plugin version, this is a fast no-op.

Migrations must be additive and data-preserving — never delete or rewrite user
content. Creating missing skeleton files and refreshing the read-only doctrine copy
is allowed; touching learnings/decisions/task content is not.

Usage
-----
  migrate-cache.py <path-to-.hyperflow> <plugin-version> [--plugin-root <dir>]
"""
from __future__ import annotations
import sys
from pathlib import Path


def parse_version(v: str) -> tuple:
    parts = []
    for chunk in str(v).strip().lstrip("v").split("."):
        num = "".join(c for c in chunk if c.isdigit())
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def read_marker(hf: Path) -> str | None:
    m = hf / ".version"
    try:
        return m.read_text().strip() or None
    except Exception:
        return None


def write_marker(hf: Path, version: str) -> None:
    try:
        (hf / ".version").write_text(version.strip() + "\n", encoding="utf-8")
    except Exception:
        pass


def _ensure_memory_stub(hf: Path, name: str) -> bool:
    """Create an empty memory stub if absent. Returns True if created."""
    mem = hf / "memory"
    if not mem.is_dir():
        return False
    f = mem / name
    if f.exists():
        return False
    title = name[:-3].replace("-", " ").title() if name.endswith(".md") else name
    try:
        f.write_text(f"# {title}\n\n<!-- to be populated by future runs -->\n", encoding="utf-8")
        return True
    except Exception:
        return False


# ── Migration steps ──────────────────────────────────────────────────────────
# Each: (since_version, human_label, fn(hf, plugin_root) -> bool changed)

def _m_memory_files(hf: Path, plugin_root: Path | None) -> bool:
    """Add memory files introduced after the original skeleton."""
    changed = False
    for name in ("anti-patterns.md", "project-decisions.md"):
        changed |= _ensure_memory_stub(hf, name)
    return changed


def _m_refresh_doctrine(hf: Path, plugin_root: Path | None) -> bool:
    """Refresh the read-only doctrine copy so an old project picks up new rules
    (specialist registry, feature/phase structure, …). Only the doctrine *copy*
    is touched — never user learnings."""
    if not plugin_root:
        return False
    src = plugin_root / "skills" / "hyperflow" / "DOCTRINE.md"
    dst = hf / "memory" / "doctrine.md"
    try:
        if not src.is_file() or not (hf / "memory").is_dir():
            return False
        new = src.read_text(errors="replace")
        if dst.exists() and dst.read_text(errors="replace") == new:
            return False
        dst.write_text(new, encoding="utf-8")
        return True
    except Exception:
        return False


MIGRATIONS = [
    ("4.29.0", "add anti-patterns + project-decisions memory files", _m_memory_files),
    ("4.29.0", "refresh portable doctrine copy", _m_refresh_doctrine),
]


def main() -> None:
    if len(sys.argv) < 3:
        return
    hf = Path(sys.argv[1])
    plugin_version = sys.argv[2]
    plugin_root = None
    args = sys.argv[3:]
    for i, a in enumerate(args):
        if a == "--plugin-root" and i + 1 < len(args):
            plugin_root = Path(args[i + 1])
        elif a.startswith("--plugin-root="):
            plugin_root = Path(a.split("=", 1)[1])
    if not hf.is_dir() or hf.name != ".hyperflow":
        return

    cache_version = read_marker(hf)
    cur = parse_version(plugin_version)

    # Already current → fast no-op (but stamp if the marker was simply missing on
    # an otherwise up-to-date cache so we don't re-scan every session).
    if cache_version is not None and parse_version(cache_version) >= cur:
        return

    # Legacy cache (no marker) is treated as version 0.0.0 so every step applies.
    from_v = parse_version(cache_version) if cache_version else (0, 0, 0)

    applied = []
    for since, label, fn in MIGRATIONS:
        if from_v < parse_version(since):
            try:
                if fn(hf, plugin_root):
                    applied.append(label)
            except Exception:
                pass  # never fail the session over a migration step

    write_marker(hf, plugin_version)

    if applied:
        frm = cache_version or "legacy"
        # User-facing notice on stdout (session-start hook surfaces it); the
        # marker write above means this fires once per version bump, not per session.
        print(
            f"Migrated `.hyperflow/` cache **{frm} → v{plugin_version}** "
            f"({len(applied)} change(s): {', '.join(applied)}). No action needed."
        )


if __name__ == "__main__":
    main()

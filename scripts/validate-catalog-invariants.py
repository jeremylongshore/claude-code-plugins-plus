#!/usr/bin/env python3
"""
Catalog invariant validator.

Enforces structural invariants on .claude-plugin/marketplace.extended.json that
cannot drift if the website, CLI, and ccpi are to stay coherent.

Invariants:
1. Every plugin's `source` path exists on disk.
2. Every plugin's `category` equals the second segment of its `source` path.
   (i.e., ./plugins/<category>/<slug> — FS path is the source of truth.)
3. No plugin with a source under ./plugins/jeremy-*/ appears in the catalog.
   (personal-prefix directories are FS-only by policy.)
4. marketplace.extended.json and marketplace.json report the same plugin count.

Exits non-zero on any violation. Used by CI and by `pnpm run sync-marketplace`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENDED = ROOT / ".claude-plugin" / "marketplace.extended.json"
SYNCED = ROOT / ".claude-plugin" / "marketplace.json"


def get_source(plugin: dict) -> str:
    src = plugin.get("source", "")
    if isinstance(src, dict):
        return src.get("source", "") or src.get("path", "")
    return str(src)


def fs_category(source: str) -> str | None:
    s = source.strip()
    if s.startswith("./"):
        s = s[2:]
    parts = s.split("/")
    if len(parts) >= 2 and parts[0] == "plugins":
        return parts[1]
    return None


def main() -> int:
    with EXTENDED.open() as f:
        data = json.load(f)
    plugins = data.get("plugins", [])

    errors: list[str] = []

    for p in plugins:
        name = p.get("name", "<unnamed>")
        src = get_source(p)

        if not src:
            errors.append(f"{name}: missing `source` field")
            continue

        fs_path = src[2:] if src.startswith("./") else src
        if not (ROOT / fs_path).is_dir():
            errors.append(f"{name}: source `{src}` does not exist on filesystem")
            continue

        fs_cat = fs_category(src)
        if fs_cat is None:
            errors.append(f"{name}: source `{src}` is not under ./plugins/<category>/")
            continue

        catalog_cat = p.get("category")
        if catalog_cat != fs_cat:
            errors.append(
                f"{name}: category=`{catalog_cat}` but FS path implies `{fs_cat}` (source=`{src}`)"
            )

        if fs_cat.startswith("jeremy-"):
            errors.append(
                f"{name}: personal-prefix category `{fs_cat}` is FS-only; remove from catalog"
            )

    # Invariant 4: extended <-> synced count match
    if SYNCED.exists():
        with SYNCED.open() as f:
            synced = json.load(f)
        synced_count = len(synced.get("plugins", []))
        if synced_count != len(plugins):
            errors.append(
                f"marketplace.json has {synced_count} plugins but extended has {len(plugins)}. "
                "Run `pnpm run sync-marketplace`."
            )

    if errors:
        print(f"Catalog invariant check FAILED ({len(errors)} violations):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Catalog invariant check passed ({len(plugins)} plugins).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

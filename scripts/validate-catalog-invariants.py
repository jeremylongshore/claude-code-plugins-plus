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
4. Every plugin name is a non-empty string and appears exactly once.
5. marketplace.json contains exactly the publishable extended rows; provenance-only
   rows marked `publication: quarantined` remain only in the extended catalog.
6. Every plugin directory in the catalog has a sibling `package.json`. Lets
   the npm tracking/publish workflow enumerate a complete set of packages.
7. The two catalogs named by STANDARDS.md are the only tracked
   `.claude-plugin/marketplace*.json*` files; every additional variant is a
   forbidden shadow, regardless of backup/staging suffix.

Exits non-zero on any violation. Used by CI and by `pnpm run sync-marketplace`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENDED = ROOT / ".claude-plugin" / "marketplace.extended.json"
SYNCED = ROOT / ".claude-plugin" / "marketplace.json"
# Reuse the validator's pre-existing operational paths instead of copying the
# STANDARDS.md canonical pair into a second literal list.
CANONICAL_CATALOGS = {path.relative_to(ROOT).as_posix() for path in (EXTENDED, SYNCED)}


class CatalogInventoryError(RuntimeError):
    """Raised when Git cannot prove the canonical tracked catalog inventory."""


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


def catalog_name_errors(plugins: list[object]) -> list[str]:
    """Return fail-closed errors for invalid or duplicate catalog names."""
    counts: Counter[str] = Counter()
    errors: list[str] = []

    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            errors.append(f"catalog row {index}: expected an object")
            continue
        name = plugin.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"catalog row {index}: `name` must be a non-empty string")
            continue
        counts[name.strip().casefold()] += 1

    for name, count in sorted(counts.items()):
        if count > 1:
            errors.append(
                f"duplicate plugin identity `{name}` appears {count} times after trimming and case-folding; "
                "names must be unique"
            )
    return errors


def publishable_plugins(plugins: list[object]) -> tuple[list[dict], list[str]]:
    """Return public rows and fail-closed errors for unknown publication states."""
    published: list[dict] = []
    errors: list[str] = []
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            continue
        state = plugin.get("publication")
        if state is None:
            published.append(plugin)
        elif state != "quarantined":
            errors.append(f"catalog row {index}: unknown publication state `{state}`")
    return published, errors


def tracked_catalog_shadows(root: Path | None = None) -> list[str]:
    """Return tracked catalog-shaped files under `.claude-plugin/` except the canonical pair.

    Git failure is deliberately fatal: without the tracked-file set this invariant
    cannot prove that a shadow is absent.
    """
    root = ROOT if root is None else root
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", ".claude-plugin"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise CatalogInventoryError("cannot enumerate tracked root catalogs with git ls-files") from error

    tracked = {path for path in result.stdout.decode().split("\0") if path}
    missing = sorted(CANONICAL_CATALOGS - tracked)
    if missing:
        raise CatalogInventoryError(f"canonical root catalogs are not tracked: {missing}")

    shadows = []
    for path in tracked:
        if path in CANONICAL_CATALOGS:
            continue
        name = Path(path).name
        if name.startswith("marketplace") and ".json" in name:
            shadows.append(path)
    return sorted(shadows)


def main() -> int:
    with EXTENDED.open() as f:
        data = json.load(f)
    plugins = data.get("plugins", [])

    errors: list[str] = catalog_name_errors(plugins)
    published, publication_errors = publishable_plugins(plugins)
    errors.extend(publication_errors)

    try:
        for shadow in tracked_catalog_shadows():
            errors.append(
                f"tracked catalog shadow `{shadow}`; keep only the canonical root catalogs {sorted(CANONICAL_CATALOGS)}"
            )
    except CatalogInventoryError as error:
        errors.append(str(error))

    for p in plugins:
        if not isinstance(p, dict):
            continue
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
            errors.append(f"{name}: category=`{catalog_cat}` but FS path implies `{fs_cat}` (source=`{src}`)")

        if fs_cat.startswith("jeremy-"):
            errors.append(f"{name}: personal-prefix category `{fs_cat}` is FS-only; remove from catalog")

        # Invariant 6: plugin directory has a sibling package.json (npm tracking).
        pkg_json = ROOT / fs_path / "package.json"
        if not pkg_json.is_file():
            errors.append(
                f"{name}: missing package.json at `{fs_path}/package.json` "
                "(run `node scripts/generate-plugin-package-jsons.mjs`)"
            )

    # Invariant 5: extended <-> synced count match
    if SYNCED.exists():
        with SYNCED.open() as f:
            synced = json.load(f)
        synced_count = len(synced.get("plugins", []))
        if synced_count != len(published):
            errors.append(
                f"marketplace.json has {synced_count} plugins but extended has "
                f"{len(published)} publishable rows ({len(plugins)} total records). "
                "Run `pnpm run sync-marketplace`."
            )

    if errors:
        print(f"Catalog invariant check FAILED ({len(errors)} violations):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"Catalog invariant check passed ({len(published)} published plugins; "
        f"{len(plugins) - len(published)} quarantined records)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

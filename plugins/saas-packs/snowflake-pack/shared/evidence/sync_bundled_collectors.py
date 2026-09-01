#!/usr/bin/env python3
"""Check or generate Snowflake collectors bundled in each skill.

The shared collector and SQL templates are the canonical sources.  Installed
skills intentionally receive physical copies so each skill remains usable when
packaged or copied without the rest of the repository.  ``--check`` is the
normal, fail-closed operation; ``--write`` is an explicit regeneration step.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[2]
SHARED_EVIDENCE = Path("shared") / "evidence"
CANONICAL_COLLECTOR = SHARED_EVIDENCE / "collect_snowflake_evidence.py"
CANONICAL_SQL = SHARED_EVIDENCE / "sql"
SKILLS_DIR = Path("skills")

# Keep this map explicit: it is the packaging contract, including the SQL
# template provenance for every self-contained skill copy. The query template
# is deliberately shared by deploy-medic and query-forensics.
BUNDLES: dict[str, tuple[str, ...]] = {
    "snowflake-access-guardian": ("access.sql", "access-current.sql", "access-future.sql"),
    "snowflake-cost-leak-hunter": (
        "cost.sql",
        "cost-adaptive.sql",
        "cost-ai-functions.sql",
        "cost-budgets.sql",
        "cost-internal-transfer.sql",
        "cost-resource-monitors.sql",
        "cost-storage.sql",
        "cost-transfer.sql",
    ),
    "snowflake-data-quality-sentinel": ("data-quality.sql", "data-quality-current.sql"),
    "snowflake-deploy-medic": ("query.sql",),
    "snowflake-failover-readiness-drill": ("replication.sql", "replication-current.sql"),
    "snowflake-pipeline-guardian": ("pipeline.sql", "pipeline-current.sql"),
    "snowflake-query-forensics": ("query.sql", "query-operator-stats.sql", "query-insights.sql"),
    "snowflake-strong-auth-migration-pilot": ("auth.sql", "auth-current.sql"),
}

# The pack can contain skills whose evidence is local-artifact based or whose
# collector has a distinct contract. Keep the directory allowlist separate
# from BUNDLES so those skills are not forced to ship a fake copy of the shared
# account-evidence collector.
EXPECTED_SKILLS = set(BUNDLES) | {
    "snowflake-governance-coverage-auditor",
    "snowflake-native-app-release-sheriff",
}


def _path(root: Path, relative: Path) -> Path:
    return root / relative


def _regular_file(path: Path, label: str, issues: list[str], *, allow_missing: bool = False) -> bool:
    if path.is_symlink():
        issues.append(f"{label} must be a regular file, not a symlink: {path}")
        return False
    if not path.exists():
        if not allow_missing:
            issues.append(f"missing {label}: {path}")
        return False
    if not path.is_file():
        issues.append(f"missing {label}: {path}")
        return False
    return True


def _directory(path: Path, label: str, issues: list[str], *, allow_missing: bool = False) -> bool:
    if path.is_symlink():
        issues.append(f"{label} must be a real directory, not a symlink: {path}")
        return False
    if not path.exists():
        if not allow_missing:
            issues.append(f"missing {label}: {path}")
        return False
    if not path.is_dir():
        issues.append(f"{label} must be a directory: {path}")
        return False
    return True


def _unexpected_entries(
    directory: Path,
    expected: set[str],
    label: str,
    issues: list[str],
    *,
    allow_missing: bool = False,
) -> None:
    if not directory.is_dir() or directory.is_symlink():
        return
    actual = {entry.name for entry in directory.iterdir()}
    for name in sorted(actual - expected):
        issues.append(f"unexpected {label} entry: {directory / name}")
    if not allow_missing:
        for name in sorted(expected - actual):
            issues.append(f"missing {label} entry: {directory / name}")


def _source_issues(root: Path) -> list[str]:
    issues: list[str] = []
    collector = _path(root, CANONICAL_COLLECTOR)
    sql_dir = _path(root, CANONICAL_SQL)
    _regular_file(collector, "canonical collector", issues)
    expected_templates = {filename for templates in BUNDLES.values() for filename in templates}
    if _directory(sql_dir, "canonical SQL directory", issues):
        _unexpected_entries(sql_dir, expected_templates, "canonical SQL", issues)
        for filename in sorted(expected_templates):
            _regular_file(sql_dir / filename, f"canonical SQL template ({filename})", issues)
    return issues


def _destination_issues(root: Path, *, allow_missing: bool = False) -> list[str]:
    issues: list[str] = []
    skills = _path(root, SKILLS_DIR)
    if not _directory(skills, "skills directory", issues, allow_missing=allow_missing):
        return issues

    _unexpected_entries(skills, EXPECTED_SKILLS, "Snowflake skill", issues, allow_missing=True)
    for skill, filenames in sorted(BUNDLES.items()):
        skill_dir = skills / skill
        if not _directory(skill_dir, f"skill directory ({skill})", issues, allow_missing=True):
            continue
        scripts_dir = skill_dir / "scripts"
        sql_dir = scripts_dir / "sql"
        _directory(scripts_dir, f"scripts directory ({skill})", issues, allow_missing=allow_missing)
        _directory(sql_dir, f"bundled SQL directory ({skill})", issues, allow_missing=allow_missing)
        if scripts_dir.is_dir() and not scripts_dir.is_symlink():
            collector_names = {
                entry.name
                for entry in scripts_dir.iterdir()
                if entry.name.startswith("collect_snowflake_evidence")
            }
            if collector_names != {"collect_snowflake_evidence.py"}:
                for name in sorted(collector_names - {"collect_snowflake_evidence.py"}):
                    issues.append(f"unexpected bundled collector entry ({skill}): {scripts_dir / name}")
                if "collect_snowflake_evidence.py" not in collector_names:
                    issues.append(
                        f"missing bundled collector entry ({skill}): "
                        f"{scripts_dir / 'collect_snowflake_evidence.py'}"
                    )
        if sql_dir.is_dir() and not sql_dir.is_symlink():
            _unexpected_entries(
                sql_dir,
                set(filenames),
                f"bundled SQL ({skill})",
                issues,
                allow_missing=allow_missing,
            )
            for filename in filenames:
                _regular_file(
                    sql_dir / filename,
                    f"bundled SQL template ({skill}/{filename})",
                    issues,
                    allow_missing=allow_missing,
                )
        _regular_file(
            skill_dir / "scripts" / "collect_snowflake_evidence.py",
            f"bundled collector ({skill})",
            issues,
            allow_missing=allow_missing,
        )
    return issues


def check_tree(root: Path = PACK_ROOT) -> list[str]:
    """Return every canonical-source or bundle-integrity violation."""

    issues = _source_issues(root)
    issues.extend(_destination_issues(root))
    canonical = _path(root, CANONICAL_COLLECTOR)
    canonical_sql_dir = _path(root, CANONICAL_SQL)
    if canonical.is_file() and not canonical.is_symlink():
        canonical_bytes = canonical.read_bytes()
        for skill in BUNDLES:
            bundled = _path(root, SKILLS_DIR / skill / "scripts" / "collect_snowflake_evidence.py")
            if bundled.is_file() and not bundled.is_symlink() and bundled.read_bytes() != canonical_bytes:
                issues.append(f"bundled collector drifts from canonical source ({skill}): {bundled}")
    if canonical_sql_dir.is_dir() and not canonical_sql_dir.is_symlink():
        for skill, filenames in BUNDLES.items():
            for filename in filenames:
                source = canonical_sql_dir / filename
                bundled = _path(root, SKILLS_DIR / skill / "scripts" / "sql" / filename)
                if source.is_file() and not source.is_symlink() and bundled.is_file() and not bundled.is_symlink():
                    if bundled.read_bytes() != source.read_bytes():
                        issues.append(
                            f"bundled SQL template drifts from canonical source ({skill}/{filename}): {bundled}"
                        )
    return issues


def _write_atomic(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.chmod(temporary, mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_tree(root: Path = PACK_ROOT) -> None:
    """Regenerate expected copies, refusing unsafe or extra destinations."""

    source_issues = _source_issues(root)
    destination_issues = _destination_issues(root, allow_missing=True)
    if source_issues or destination_issues:
        details = "\n".join(source_issues + destination_issues)
        raise ValueError(f"cannot regenerate collector bundles until the tree is valid:\n{details}")

    collector = _path(root, CANONICAL_COLLECTOR)
    sql_dir = _path(root, CANONICAL_SQL)
    collector_bytes = collector.read_bytes()
    collector_mode = collector.stat().st_mode
    for skill, filenames in BUNDLES.items():
        collector_target = _path(root, SKILLS_DIR / skill / "scripts" / "collect_snowflake_evidence.py")
        _write_atomic(collector_target, collector_bytes, collector_mode)
        for filename in filenames:
            sql_target = _path(root, SKILLS_DIR / skill / "scripts" / "sql" / filename)
            source_sql = sql_dir / filename
            _write_atomic(sql_target, source_sql.read_bytes(), source_sql.stat().st_mode)

    issues = check_tree(root)
    if issues:
        raise ValueError("generated collector bundles failed their integrity check:\n" + "\n".join(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify canonical and bundled files (default)")
    mode.add_argument("--write", action="store_true", help="regenerate expected bundled copies")
    parser.add_argument("--root", type=Path, default=PACK_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.write:
        try:
            write_tree(root)
        except (OSError, ValueError) as exc:
            print(f"collector bundle generation failed: {exc}", file=sys.stderr)
            return 1
        print(f"collector bundle generation passed: {len(BUNDLES)} skills")
        return 0

    issues = check_tree(root)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1
    print(
        f"collector bundle check passed: {len(BUNDLES)} skills, "
        f"{len({filename for templates in BUNDLES.values() for filename in templates})} SQL templates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

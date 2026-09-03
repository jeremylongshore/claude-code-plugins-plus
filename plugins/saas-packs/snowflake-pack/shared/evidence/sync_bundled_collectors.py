#!/usr/bin/env python3
"""Check or regenerate Snowflake evidence files bundled with each skill.

The shared collector and SQL templates are canonical. Installed skills receive
physical copies so each skill remains usable without the rest of the pack.
Check mode is the default and never writes; regeneration requires ``--write``.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[2]
SHARED_EVIDENCE = Path("shared") / "evidence"
CANONICAL_COLLECTOR = SHARED_EVIDENCE / "collect_snowflake_evidence.py"
CANONICAL_SQL = SHARED_EVIDENCE / "sql"
SKILLS_DIR = Path("skills")

# This is the packaging and provenance contract for the eight skills that use
# the shared account-evidence collector. Skills with a different collector
# contract are deliberately outside this registry.
BUNDLES: dict[str, tuple[str, ...]] = {
    "snowflake-access-guardian": ("access.sql",),
    "snowflake-cost-leak-hunter": ("cost.sql",),
    "snowflake-data-quality-sentinel": ("data-quality.sql",),
    "snowflake-deploy-medic": ("query.sql",),
    "snowflake-failover-readiness-drill": ("replication.sql",),
    "snowflake-pipeline-guardian": ("pipeline.sql",),
    "snowflake-query-forensics": ("query.sql",),
    "snowflake-strong-auth-migration-pilot": ("auth.sql",),
}
SKILL_TOKEN = re.compile(r"^snowflake-[a-z0-9]+(?:-[a-z0-9]+)*$")
SQL_TOKEN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.sql$")
_replace = os.replace


def _path(root: Path, relative: Path) -> Path:
    return root / relative


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _regular_file(path: Path, label: str, issues: list[str], *, allow_missing: bool = False) -> bool:
    if path.is_symlink():
        issues.append(f"{label} must be a regular file, not a symlink: {path}")
        return False
    if not path.exists():
        if not allow_missing:
            issues.append(f"missing {label}: {path}")
        return False
    if not path.is_file():
        issues.append(f"{label} must be a regular file: {path}")
        return False
    return True


def _directory(path: Path, label: str, issues: list[str]) -> bool:
    if path.is_symlink():
        issues.append(f"{label} must be a real directory, not a symlink: {path}")
        return False
    if not path.exists():
        issues.append(f"missing {label}: {path}")
        return False
    if not path.is_dir():
        issues.append(f"{label} must be a directory: {path}")
        return False
    return True


def _unexpected_entries(directory: Path, expected: set[str], label: str, issues: list[str]) -> None:
    if not directory.is_dir() or directory.is_symlink():
        return
    actual = {entry.name for entry in directory.iterdir()}
    for name in sorted(actual - expected):
        issues.append(f"unexpected {label} entry: {directory / name}")
    for name in sorted(expected - actual):
        issues.append(f"missing {label} entry: {directory / name}")


def _canonical_templates() -> set[str]:
    return {filename for filenames in BUNDLES.values() for filename in filenames}


def _registry_issues() -> list[str]:
    issues: list[str] = []
    for skill, filenames in BUNDLES.items():
        if not isinstance(skill, str) or not SKILL_TOKEN.fullmatch(skill):
            issues.append(f"invalid Snowflake skill token in bundle registry: {skill!r}")
        if not isinstance(filenames, tuple) or not filenames:
            issues.append(f"bundle registry has no SQL templates: {skill}")
            continue
        if len(filenames) != len(set(filenames)):
            issues.append(f"bundle registry repeats an SQL template: {skill}")
        for filename in filenames:
            if not isinstance(filename, str) or not SQL_TOKEN.fullmatch(filename):
                issues.append(f"invalid SQL filename token in bundle registry ({skill}): {filename!r}")
    return issues


def _projection_paths(root: Path) -> list[Path]:
    paths = [
        root,
        _path(root, Path("shared")),
        _path(root, SHARED_EVIDENCE),
        _path(root, CANONICAL_COLLECTOR),
        _path(root, CANONICAL_SQL),
        _path(root, SKILLS_DIR),
    ]
    for filename in sorted(_canonical_templates()):
        paths.append(_path(root, CANONICAL_SQL / filename))
    for skill, filenames in sorted(BUNDLES.items()):
        skill_dir = _path(root, SKILLS_DIR / skill)
        scripts_dir = skill_dir / "scripts"
        paths.extend(
            [
                skill_dir,
                skill_dir / "SKILL.md",
                scripts_dir,
                scripts_dir / "collect_snowflake_evidence.py",
                scripts_dir / "sql",
            ]
        )
        paths.extend(scripts_dir / "sql" / filename for filename in filenames)
    return paths


def _symlink_component_issues(root: Path) -> list[str]:
    issues: list[str] = []
    if root.is_symlink():
        return [f"projection path component must not be a symlink: {root}"]
    seen_symlinks: set[Path] = set()
    for path in _projection_paths(root):
        try:
            relative = path.relative_to(root)
        except ValueError:
            issues.append(f"projection path escapes pack root: {path}")
            continue
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                if current not in seen_symlinks:
                    issues.append(f"projection path component must not be a symlink: {current}")
                    seen_symlinks.add(current)
                break
    return issues


def _collector_contract_issues(root: Path) -> list[str]:
    issues: list[str] = []
    collector = _path(root, CANONICAL_COLLECTOR)
    try:
        tree = ast.parse(collector.read_bytes(), filename=str(collector))
    except (OSError, SyntaxError) as exc:
        return [f"cannot parse canonical collector contract: {collector}: {exc}"]

    contract_names = {"SURFACES", "SUBSURFACES", "FORBIDDEN_SQL", "SAFE_START"}
    declared: dict[str, object] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        value = statement.value
        for target in targets:
            if not isinstance(target, ast.Name) or target.id not in contract_names:
                continue
            if target.id in declared:
                issues.append(f"canonical collector repeats {target.id} assignment: {collector}")
                continue
            try:
                declared[target.id] = ast.literal_eval(value)
            except (ValueError, TypeError, SyntaxError):
                issues.append(f"canonical collector {target.id} must be a literal mapping: {collector}")

    surfaces = declared.get("SURFACES")
    if not isinstance(surfaces, dict):
        issues.append(f"canonical collector SURFACES must be a literal mapping: {collector}")
        return issues
    subsurfaces = declared.get("SUBSURFACES", {})
    if not isinstance(subsurfaces, dict):
        issues.append(f"canonical collector SUBSURFACES must be a literal mapping when present: {collector}")
        return issues
    duplicate_surfaces = set(surfaces).intersection(subsurfaces)
    if duplicate_surfaces:
        issues.append(f"canonical collector repeats surface names: {sorted(duplicate_surfaces)}")
    contracts = {**surfaces, **subsurfaces}
    forbidden_sql = declared.get("FORBIDDEN_SQL")
    safe_start = declared.get("SAFE_START")
    if not isinstance(forbidden_sql, set) or not all(isinstance(token, str) for token in forbidden_sql):
        issues.append(f"canonical collector FORBIDDEN_SQL must be a literal string set: {collector}")
    if not isinstance(safe_start, set) or not all(isinstance(token, str) for token in safe_start):
        issues.append(f"canonical collector SAFE_START must be a literal string set: {collector}")
    if issues:
        return issues
    surface_templates: set[str] = set()
    for surface, contract in sorted(contracts.items()):
        if not isinstance(contract, tuple) or len(contract) < 2 or not isinstance(contract[0], str):
            issues.append(f"invalid canonical collector surface contract: {surface!r}")
            continue
        filename = contract[0]
        surface_templates.add(filename)
    registered_templates = _canonical_templates()
    if registered_templates != surface_templates:
        missing = sorted(surface_templates - registered_templates)
        extra = sorted(registered_templates - surface_templates)
        issues.append(
            f"bundle registry SQL does not match canonical collector surfaces (missing={missing}, extra={extra})"
        )
    for filename in sorted(registered_templates):
        try:
            sql = (_path(root, CANONICAL_SQL) / filename).read_text(encoding="utf-8")
            _validate_read_only_sql(sql, safe_start, forbidden_sql)
        except (OSError, ValueError) as exc:
            issues.append(f"canonical SQL safety validation failed ({filename}): {exc}")
    return issues


def _strip_sql_literals_and_comments(sql: str) -> str:
    result: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(sql):
        char = sql[index]
        if quote is not None:
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    result.extend((" ", " "))
                    index += 2
                    continue
                quote = None
            result.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            index += 1
            continue
        if sql.startswith("--", index):
            newline = sql.find("\n", index + 2)
            if newline < 0:
                return "".join(result)
            result.append("\n")
            index = newline + 1
            continue
        if sql.startswith("/*", index):
            end = sql.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            result.append(" ")
            index = end + 2
            continue
        result.append(char)
        index += 1
    if quote is not None:
        raise ValueError("unterminated quoted value")
    return "".join(result)


def _validate_read_only_sql(sql: str, safe_start: set[str], forbidden_sql: set[str]) -> None:
    cleaned = _strip_sql_literals_and_comments(sql)
    statements = [statement.strip() for statement in cleaned.split(";") if statement.strip()]
    if len(statements) != 1:
        raise ValueError("reviewed SQL must contain exactly one statement")
    tokens = [token.upper() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", statements[0])]
    if not tokens or tokens[0] not in safe_start:
        raise ValueError(f"reviewed SQL must start with one of {sorted(safe_start)}")
    forbidden = sorted(set(tokens).intersection(forbidden_sql))
    if forbidden:
        raise ValueError(f"reviewed SQL contains forbidden statement tokens: {forbidden}")


def _source_issues(root: Path) -> list[str]:
    issues: list[str] = []
    collector = _path(root, CANONICAL_COLLECTOR)
    sql_dir = _path(root, CANONICAL_SQL)
    _directory(root, "pack root", issues)
    _directory(_path(root, Path("shared")), "shared directory", issues)
    _directory(_path(root, SHARED_EVIDENCE), "shared evidence directory", issues)
    _regular_file(collector, "canonical collector", issues)
    if _directory(sql_dir, "canonical SQL directory", issues):
        expected = _canonical_templates()
        _unexpected_entries(sql_dir, expected, "canonical SQL", issues)
        for filename in sorted(expected):
            _regular_file(sql_dir / filename, f"canonical SQL template ({filename})", issues)
    return issues


def _unregistered_collector_issues(skills: Path) -> list[str]:
    issues: list[str] = []
    if not skills.is_dir() or skills.is_symlink():
        return issues
    for skill_dir in sorted(skills.iterdir()):
        if skill_dir.is_symlink() or not skill_dir.is_dir():
            continue
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.is_symlink() or not scripts_dir.is_dir():
            continue
        candidate = scripts_dir / "collect_snowflake_evidence.py"
        if (candidate.exists() or candidate.is_symlink()) and skill_dir.name not in BUNDLES:
            issues.append(f"unregistered shared collector copy: {candidate}")
    return issues


def _destination_issues(root: Path, *, allow_missing_files: bool = False) -> list[str]:
    issues: list[str] = []
    skills = _path(root, SKILLS_DIR)
    if not _directory(skills, "skills directory", issues):
        return issues
    issues.extend(_unregistered_collector_issues(skills))

    for skill, filenames in sorted(BUNDLES.items()):
        skill_dir = skills / skill
        if not _directory(skill_dir, f"skill directory ({skill})", issues):
            continue
        _regular_file(skill_dir / "SKILL.md", f"skill definition ({skill})", issues)
        scripts_dir = skill_dir / "scripts"
        if not _directory(scripts_dir, f"scripts directory ({skill})", issues):
            continue
        sql_dir = scripts_dir / "sql"
        if not _directory(sql_dir, f"bundled SQL directory ({skill})", issues):
            continue

        collector_names = {
            entry.name for entry in scripts_dir.iterdir() if entry.name.startswith("collect_snowflake_evidence")
        }
        expected_collector = {"collect_snowflake_evidence.py"}
        for name in sorted(collector_names - expected_collector):
            issues.append(f"unexpected bundled collector entry ({skill}): {scripts_dir / name}")
        if not allow_missing_files and "collect_snowflake_evidence.py" not in collector_names:
            issues.append(f"missing bundled collector entry ({skill}): {scripts_dir / 'collect_snowflake_evidence.py'}")

        actual_sql = {entry.name for entry in sql_dir.iterdir()}
        expected_sql = set(filenames)
        for name in sorted(actual_sql - expected_sql):
            issues.append(f"unexpected bundled SQL entry ({skill}): {sql_dir / name}")
        if not allow_missing_files:
            for name in sorted(expected_sql - actual_sql):
                issues.append(f"missing bundled SQL entry ({skill}): {sql_dir / name}")

        _regular_file(
            scripts_dir / "collect_snowflake_evidence.py",
            f"bundled collector ({skill})",
            issues,
            allow_missing=allow_missing_files,
        )
        for filename in filenames:
            _regular_file(
                sql_dir / filename,
                f"bundled SQL template ({skill}/{filename})",
                issues,
                allow_missing=allow_missing_files,
            )
    return issues


def _compare_projection(source: Path, destination: Path, label: str, issues: list[str]) -> None:
    if not source.is_file() or source.is_symlink() or not destination.is_file() or destination.is_symlink():
        return
    source_bytes = source.read_bytes()
    destination_bytes = destination.read_bytes()
    source_hash = _sha256(source_bytes)
    destination_hash = _sha256(destination_bytes)
    if source_bytes != destination_bytes:
        issues.append(
            f"{label} drifts from canonical source: {destination} "
            f"(canonical sha256:{source_hash}, bundled sha256:{destination_hash})"
        )
    source_mode = source.stat().st_mode & 0o777
    destination_mode = destination.stat().st_mode & 0o777
    if source_mode != destination_mode:
        issues.append(
            f"{label} mode drifts from canonical source: {destination} "
            f"(canonical {source_mode:04o}, bundled {destination_mode:04o})"
        )


def check_tree(root: Path = PACK_ROOT) -> list[str]:
    """Return every canonical-source or bundle-integrity violation."""

    issues = _registry_issues()
    if issues:
        return issues
    issues.extend(_symlink_component_issues(root))
    if issues:
        return issues
    source_issues = _source_issues(root)
    issues.extend(source_issues)
    if not source_issues:
        issues.extend(_collector_contract_issues(root))
    issues.extend(_destination_issues(root))
    collector = _path(root, CANONICAL_COLLECTOR)
    sql_dir = _path(root, CANONICAL_SQL)
    for skill, filenames in BUNDLES.items():
        scripts_dir = _path(root, SKILLS_DIR / skill / "scripts")
        _compare_projection(
            collector,
            scripts_dir / "collect_snowflake_evidence.py",
            f"bundled collector ({skill})",
            issues,
        )
        for filename in filenames:
            _compare_projection(
                sql_dir / filename,
                scripts_dir / "sql" / filename,
                f"bundled SQL template ({skill}/{filename})",
                issues,
            )
    return issues


def _stage_file(path: Path, payload: bytes, mode: int) -> Path:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode & 0o777)
        return Path(temporary)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def _backup_path(path: Path) -> Path:
    descriptor, backup = tempfile.mkstemp(prefix=f".{path.name}.rollback.", dir=path.parent)
    os.close(descriptor)
    os.unlink(backup)
    return Path(backup)


def _snapshot_file(path: Path) -> tuple[bytes, int]:
    with path.open("rb") as handle:
        payload = handle.read()
        mode = os.fstat(handle.fileno()).st_mode
    return payload, mode


def _write_transaction(outputs: list[tuple[Path, bytes, int]]) -> None:
    staged: list[tuple[Path, Path]] = []
    completed: list[tuple[Path, Path | None]] = []
    try:
        for destination, payload, mode in outputs:
            staged.append((destination, _stage_file(destination, payload, mode)))
        for destination, temporary in staged:
            backup = None
            if destination.exists():
                backup = _backup_path(destination)
                _replace(destination, backup)
            try:
                _replace(temporary, destination)
            except BaseException:
                if backup is not None and backup.exists():
                    _replace(backup, destination)
                raise
            completed.append((destination, backup))
    except BaseException as exc:
        rollback_errors = []
        for destination, backup in reversed(completed):
            try:
                destination.unlink(missing_ok=True)
                if backup is not None:
                    _replace(backup, destination)
            except OSError as rollback_error:
                rollback_errors.append(f"{destination}: {rollback_error}")
        if rollback_errors:
            raise RuntimeError(
                f"projection transaction failed ({exc}); rollback also failed: " + "; ".join(rollback_errors)
            ) from exc
        raise
    finally:
        for _, temporary in staged:
            temporary.unlink(missing_ok=True)
        for _, backup in completed:
            if backup is not None:
                backup.unlink(missing_ok=True)


def write_tree(root: Path = PACK_ROOT) -> None:
    """Regenerate registered files without creating or deleting skill structure."""

    issues = _registry_issues()
    if issues:
        raise ValueError("cannot regenerate collector bundles until the tree is valid:\n" + "\n".join(issues))
    issues.extend(_symlink_component_issues(root))
    if issues:
        raise ValueError("cannot regenerate collector bundles until the tree is valid:\n" + "\n".join(issues))
    issues.extend(_source_issues(root))
    if not issues:
        issues.extend(_collector_contract_issues(root))
    issues.extend(_destination_issues(root, allow_missing_files=True))
    if issues:
        raise ValueError("cannot regenerate collector bundles until the tree is valid:\n" + "\n".join(issues))

    collector = _path(root, CANONICAL_COLLECTOR)
    sql_dir = _path(root, CANONICAL_SQL)
    canonical_collector = _snapshot_file(collector)
    canonical_sql = {filename: _snapshot_file(sql_dir / filename) for filename in sorted(_canonical_templates())}
    outputs = []
    for skill, filenames in BUNDLES.items():
        scripts_dir = _path(root, SKILLS_DIR / skill / "scripts")
        outputs.append(
            (
                scripts_dir / "collect_snowflake_evidence.py",
                canonical_collector[0],
                canonical_collector[1],
            )
        )
        for filename in filenames:
            payload, mode = canonical_sql[filename]
            outputs.append((scripts_dir / "sql" / filename, payload, mode))
    _write_transaction(outputs)

    issues = check_tree(root)
    if issues:
        raise ValueError("generated collector bundles failed their integrity check:\n" + "\n".join(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify canonical and bundled files (default)")
    mode.add_argument("--write", action="store_true", help="regenerate registered bundled files")
    parser.add_argument("--root", type=Path, default=PACK_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(os.path.abspath(args.root))

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
    print(f"collector bundle check passed: {len(BUNDLES)} skills, {len(_canonical_templates())} SQL templates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

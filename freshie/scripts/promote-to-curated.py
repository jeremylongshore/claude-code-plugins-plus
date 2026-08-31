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
                     weekly workflow after `pnpm install`); fails closed before mutation
                     if the validator cannot load. `--no-validate` is an explicit local
                     diagnostic override and produces a manifest that CI will reject.
                     Shrink floor (2026-07-14 ops review): the selection is computed
                     BEFORE anything is deleted, and the build ABORTS non-zero — mirror
                     untouched — when the new selection is empty or falls below
                     SHRINK_FLOOR_RATIO of the committed MANIFEST count. Every upstream
                     failure mode (truncated/header-only grades.csv, a validator API
                     drift making every fresh grade None) used to converge on silently
                     wiping ~1,881 skills and exiting 0. A legitimate large drop is an
                     explicit choice: pass --allow-shrink.
  --check            CI drift gate. Reads the committed MANIFEST and verifies every promoted
                     copy is byte-identical to the current git-tracked source, with no orphan
                     or missing dirs. Deterministic, git-only — no validator, no sqlite, no
                     node_modules — so it runs in a minimal CI job without false drift. Exits
                     1 on any drift (same contract as `generate-readme-toc.mjs --check`).

Usage
-----
  Requires the repository Node 20+ runtime on PATH for canonical cohort resolution.
  python3 freshie/scripts/promote-to-curated.py            # rebuild skills/.curated/
  python3 freshie/scripts/promote-to-curated.py --plugin snowflake-pack
  python3 freshie/scripts/promote-to-curated.py --check    # CI: exit 1 if stale vs source
  python3 freshie/scripts/promote-to-curated.py --no-validate   # skip the in-process regrade
"""

from __future__ import annotations

import argparse
import codecs
import csv
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
GRADES_CSV = ROOT / "freshie" / "grades.csv"
GRADE_HISTOGRAM = ROOT / "freshie" / "grade-histogram.json"
CURATED_DIR = ROOT / "skills" / ".curated"
MANIFEST = CURATED_DIR / "MANIFEST.json"
VALIDATOR = ROOT / "scripts" / "validate-skills-schema.py"
CORPUS_RESOLVER = Path(__file__).resolve().parents[2] / "scripts" / "corpus-resolver.mjs"

PROMOTE_GRADES = {"A", "B"}

# Build-mode shrink floor: abort (before wiping) when the new selection is
# smaller than this fraction of the committed MANIFEST count. Overridable with
# --allow-shrink for a legitimate large drop (e.g. a deliberate threshold change).
SHRINK_FLOOR_RATIO = 0.5

# Machine-readable strategy marker consumed by the Epic 1 measurement harness.
# Changing this value requires updating the harness and its independent fixtures.
CONTENT_TYPE_STRATEGY = "magic_bytes"


class ContentInspectionError(RuntimeError):
    """A file cannot be classified safely enough for curated promotion."""


class ContentTypeMismatchError(ContentInspectionError):
    """The file's extension contradicts its recognized or required content type."""


class UnknownBinaryContentError(ContentInspectionError):
    """Binary-looking bytes have no registered, reviewable content type."""


class PromotionInvariantError(RuntimeError):
    """The recorded grade export, resolved cohort, or manifest is contradictory."""


def _display_path(path: Path, root: Path) -> str:
    """Render a repo-relative path when possible, otherwise an absolute path."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


# The curated mirror is a text index. Recognized binary files are deliberately
# omitted, while misleading extensions and unknown binary bytes abort both build
# and --check. The registry covers the formats currently present in plugin skill
# trees plus common executable payloads that previously reached the mirror.
_MAGIC_SIGNATURES: Tuple[Tuple[str, Tuple[bytes, ...], frozenset[str]], ...] = (
    ("png", (bytes.fromhex("89504e470d0a1a0a"),), frozenset({".png"})),
    ("jpeg", (bytes.fromhex("ffd8ff"),), frozenset({".jpg", ".jpeg"})),
    ("gif", (b"GIF87a", b"GIF89a"), frozenset({".gif"})),
    ("pdf", (b"%PDF-",), frozenset({".pdf"})),
    (
        "zip",
        (bytes.fromhex("504b0304"), bytes.fromhex("504b0506"), bytes.fromhex("504b0708")),
        frozenset({".zip", ".jar", ".docx", ".xlsx", ".pptx", ".whl"}),
    ),
    ("truetype", (bytes.fromhex("00010000"), b"true"), frozenset({".ttf"})),
    ("opentype", (b"OTTO",), frozenset({".otf"})),
    ("woff", (b"wOFF",), frozenset({".woff"})),
    ("woff2", (b"wOF2",), frozenset({".woff2"})),
    ("gzip", (bytes.fromhex("1f8b"),), frozenset({".gz", ".tgz"})),
    ("bzip2", (b"BZh",), frozenset({".bz2", ".tbz2"})),
    ("xz", (bytes.fromhex("fd377a585a00"),), frozenset({".xz", ".txz"})),
    ("7zip", (bytes.fromhex("377abcaf271c"),), frozenset({".7z"})),
    ("elf", (bytes.fromhex("7f454c46"),), frozenset({".elf", ".so", ".node"})),
    ("wasm", (bytes.fromhex("0061736d"),), frozenset({".wasm"})),
    (
        "mach-o",
        (
            bytes.fromhex("feedface"),
            bytes.fromhex("feedfacf"),
            bytes.fromhex("cefaedfe"),
            bytes.fromhex("cffaedfe"),
            bytes.fromhex("cafebabe"),
            bytes.fromhex("bebafeca"),
        ),
        frozenset({".dylib", ".node"}),
    ),
)

_BINARY_EXTENSIONS = frozenset(
    extension for _kind, _signatures, extensions in _MAGIC_SIGNATURES for extension in extensions
) | frozenset({".dll", ".exe", ".webp"})
# Unix executables commonly have no suffix; data formats and Windows PE files
# must retain one of their registered extensions.
_EXTENSION_OPTIONAL_BINARY_TYPES = frozenset({"elf", "mach-o"})
_INSPECTION_CHUNK_BYTES = 64 * 1024


# ── selection ────────────────────────────────────────────────────────────────
def _plugin_root(skill_path: str) -> str:
    """The plugin dir that owns a skill: everything before `/skills/`."""
    return skill_path.split("/skills/")[0] if "/skills/" in skill_path else skill_path


def resolve_corpora(*cohorts: str) -> Dict[str, set[str]]:
    """Read named cohorts in one canonical resolver process."""
    arguments = ["node", str(CORPUS_RESOLVER), "--root", str(ROOT), "--json"]
    for cohort in cohorts:
        arguments.extend(["--cohort", cohort])
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise PromotionInvariantError("corpus resolver requires Node 20+ on PATH") from exc
    if result.returncode != 0:
        raise PromotionInvariantError(f"corpus resolver failed for {', '.join(cohorts)}: {result.stderr.strip()}")
    try:
        payload = json.loads(result.stdout)
        if len(cohorts) == 1:
            resolved = {cohorts[0]: payload}
        elif isinstance(payload, dict):
            resolved = payload.get("cohorts")
        else:
            resolved = None
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise PromotionInvariantError(f"corpus resolver returned invalid JSON: {exc}") from exc
    if not isinstance(resolved, dict):
        raise PromotionInvariantError("corpus resolver returned an invalid cohorts object")
    output: Dict[str, set[str]] = {}
    for cohort in cohorts:
        cohort_payload = resolved.get(cohort)
        if not isinstance(cohort_payload, dict):
            raise PromotionInvariantError(f"corpus resolver returned an invalid cohort object for {cohort}")
        files = cohort_payload.get("files")
        if not isinstance(files, list) or not all(isinstance(value, str) for value in files):
            raise PromotionInvariantError(f"corpus resolver returned an invalid file list for {cohort}")
        output[cohort] = set(files)
    return output


def resolve_corpus(cohort: str) -> set[str]:
    """Compatibility wrapper for one named cohort."""
    return resolve_corpora(cohort)[cohort]


def is_external_mirror(skill_path: str) -> bool:
    """True when ANY ancestor directory of the skill carries a `.source.json`.

    Retained as a compatibility and regression-test helper after production
    selection moved to the shared graded/first-party corpus intersection.

    Walking every ancestor — rather than only `_plugin_root()` — is load-bearing.
    `_plugin_root()` splits on `/skills/`, so a skill vendored at
    `plugins/<cat>/<plugin>/.codex/skills/<name>` yields `.../<plugin>/.codex`, which
    sits BELOW the plugin root where `.source.json` lives. The marker was therefore
    missed and six mirrored skills were promoted into `skills/.curated/`, republishing
    other people's work under our name — exactly what this module's header forbids.
    """
    node = Path(skill_path)
    # `node != node.parent` rather than `!= Path(".")`: Path("/").parent is "/",
    # so the latter never terminates on an absolute path. The sole call site passes
    # a repo-relative path today, but the loop should not depend on that.
    while node != node.parent:
        if (ROOT / node / ".source.json").exists():
            return True
        node = node.parent
    return False


def _load_grade_rows(grades_csv: Path) -> Tuple[List[Dict[str, str]], Dict]:
    """Load one authoritative grade export and verify its tracked provenance.

    Both build and check call this function. A stale histogram, duplicate path,
    malformed CSV row, or digest/count disagreement is therefore a hard error
    before either mode can reason about promotion eligibility.
    """
    if not grades_csv.exists():
        raise PromotionInvariantError(
            f"{grades_csv} not found — run the Freshie cycle first "
            "(rebuild-inventory.py → validate --populate-db → dolt-sync.py)"
        )
    if not GRADE_HISTOGRAM.exists():
        raise PromotionInvariantError(f"{GRADE_HISTOGRAM} not found — grade export provenance is missing")

    try:
        raw = grades_csv.read_bytes()
        if b"\0" in raw:
            raise PromotionInvariantError(f"{grades_csv} contains NUL bytes")
        text = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        required = {"skill_path", "grade", "score"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise PromotionInvariantError(
                f"{grades_csv} must contain the columns {', '.join(sorted(required))}"
            )
        rows = list(reader)
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        raise PromotionInvariantError(f"{grades_csv} is not a readable UTF-8 CSV: {exc}") from exc

    seen: set[str] = set()
    grade_counts: Dict[str, int] = {}
    allowed_grades = {"A", "B", "C", "D", "F"}
    for index, row in enumerate(rows, start=2):
        if None in row:
            raise PromotionInvariantError(f"{grades_csv}:{index} has extra unheaded columns")
        skill_path = (row.get("skill_path") or "").strip()
        grade = (row.get("grade") or "").strip()
        if not skill_path:
            raise PromotionInvariantError(f"{grades_csv}:{index} has an empty skill_path")
        if skill_path in seen:
            raise PromotionInvariantError(f"{grades_csv}:{index} duplicates skill_path {skill_path!r}")
        if grade not in allowed_grades:
            raise PromotionInvariantError(f"{grades_csv}:{index} has unsupported grade {grade!r}")
        seen.add(skill_path)
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    try:
        histogram = json.loads(GRADE_HISTOGRAM.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionInvariantError(f"{GRADE_HISTOGRAM} is unreadable: {exc}") from exc
    if not isinstance(histogram, dict):
        raise PromotionInvariantError(f"{GRADE_HISTOGRAM} must contain a JSON object")

    digest = hashlib.sha256(raw).hexdigest()
    expected_grades = {grade: grade_counts.get(grade, 0) for grade in sorted(allowed_grades)}
    recorded_grades = histogram.get("grades")
    if histogram.get("total") != len(rows):
        raise PromotionInvariantError(
            f"grade denominator mismatch: grades.csv has {len(rows)} rows but "
            f"grade-histogram.json records {histogram.get('total')!r}"
        )
    if not isinstance(recorded_grades, dict):
        raise PromotionInvariantError("grade-histogram.json field 'grades' must be an object")
    unknown_grades = sorted(set(recorded_grades) - allowed_grades)
    if unknown_grades:
        raise PromotionInvariantError(
            f"grade-histogram.json contains unsupported grade buckets: {', '.join(unknown_grades)}"
        )
    normalized_recorded_grades = {grade: recorded_grades.get(grade, 0) for grade in sorted(allowed_grades)}
    if normalized_recorded_grades != expected_grades:
        raise PromotionInvariantError(
            f"grade histogram mismatch: computed {expected_grades}, recorded {recorded_grades!r}"
        )
    if histogram.get("grades_csv_sha256") != digest:
        raise PromotionInvariantError(
            "grade export digest mismatch: grade-histogram.json does not identify the tracked grades.csv bytes"
        )
    if isinstance(histogram.get("run_id"), bool) or not isinstance(histogram.get("run_id"), int):
        raise PromotionInvariantError("grade-histogram.json must carry an integer run_id")

    return rows, {
        "run_id": histogram["run_id"],
        "total": len(rows),
        "grades": expected_grades,
        "grades_csv_sha256": digest,
    }


def resolve_promotion_candidates(grades_csv: Path) -> Tuple[List[Dict[str, str]], Dict]:
    """Resolve the authoritative promotion cohort and its grade provenance once.

    The shared corpus resolver excludes mirrors, hidden paths, and untracked files;
    this caller then keeps A/B rows whose source directory still exists. Results
    are sorted by skill_path for deterministic output. Build and check both use
    this function so neither mode can substitute a second grade read or cohort.
    """
    rows, grade_export = _load_grade_rows(grades_csv)
    out: List[Dict[str, str]] = []
    cohorts = resolve_corpora("graded", "first-party")
    graded = cohorts["graded"]
    first_party = cohorts["first-party"]
    for row in rows:
        sp, grade = row["skill_path"], row["grade"]
        if not sp.startswith("plugins/") or grade not in PROMOTE_GRADES:
            continue
        root = _plugin_root(sp)
        skill_file = f"{sp}/SKILL.md"
        if skill_file not in graded or skill_file not in first_party:
            continue  # outside the canonical graded/first-party intersection
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
    return out, grade_export


def load_candidates(grades_csv: Path) -> List[Dict[str, str]]:
    """Compatibility wrapper for callers that need only candidate records."""
    candidates, _grade_export = resolve_promotion_candidates(grades_csv)
    return candidates


# ── in-process re-grade (defense) ────────────────────────────────────────────
def load_validator():
    """Import scripts/validate-skills-schema.py as a module (hyphenated filename ⇒ importlib).

    Returns the module, or None if it cannot be loaded. Production build mode treats
    None as a hard pre-mutation failure; only explicit --no-validate skips regrading.
    """
    try:
        spec = importlib.util.spec_from_file_location("vss_promote", VALIDATOR)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except (Exception, SystemExit) as e:  # noqa: BLE001 — any failure ⇒ controlled preflight refusal
        # SystemExit is caught explicitly: the validator's module-level guard
        # calls sys.exit(1) when pyyaml is missing, and SystemExit inherits
        # BaseException. Converting it to None lets build() produce one controlled,
        # actionable refusal before it touches the curated mirror.
        detail = f"exit code {e.code}, likely a missing dependency such as pyyaml" if isinstance(e, SystemExit) else e
        print(f"⚠️  could not import validator ({detail}); validated promotion is unavailable.", file=sys.stderr)
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


def _selection_records(candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Return the canonical promotion-selection records used by both modes."""
    records: List[Dict[str, str]] = []
    source_paths: set[str] = set()
    curated_names: set[str] = set()
    for candidate in candidates:
        source_path = candidate["skill_path"]
        curated_name = candidate.get("curated_name")
        if not curated_name:
            raise PromotionInvariantError(f"candidate {source_path!r} has no resolved curated_name")
        if source_path in source_paths:
            raise PromotionInvariantError(f"candidate resolver duplicated source_path {source_path!r}")
        if curated_name in curated_names:
            raise PromotionInvariantError(f"candidate resolver duplicated curated_name {curated_name!r}")
        source_paths.add(source_path)
        curated_names.add(curated_name)
        records.append(
            {
                "source_path": source_path,
                "curated_name": curated_name,
                "recorded_grade": candidate["grade"],
                "recorded_score": candidate.get("score", ""),
            }
        )
    return records


def _selection_metadata(candidates: List[Dict[str, str]]) -> Dict[str, object]:
    """Bind the exact resolved cohort to a deterministic digest."""
    records = _selection_records(candidates)
    encoded = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "resolver": "graded∩first-party",
        "count": len(records),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _manifest_selection_errors(
    manifest: Dict,
    candidates: List[Dict[str, str]],
    selection: Dict[str, object],
    grade_export: Dict,
    *,
    require_validated: bool,
) -> List[str]:
    """Return contradictions between a manifest and the authoritative cohort."""
    errors: List[str] = []
    entries = manifest.get("skills")
    if not isinstance(entries, list):
        return ["manifest skills must be a list"]
    if manifest.get("count") != len(entries):
        errors.append(f"manifest count field {manifest.get('count')!r} != {len(entries)} entries")
    if manifest.get("threshold") != "".join(sorted(PROMOTE_GRADES)):
        errors.append(f"manifest threshold {manifest.get('threshold')!r} != AB")
    if manifest.get("selection") != selection:
        errors.append("manifest selection metadata does not match the current authoritative cohort")
    if manifest.get("grade_export") != grade_export:
        errors.append("manifest grade_export metadata does not match grades.csv/grade-histogram.json")
    if manifest.get("run_id") != grade_export["run_id"]:
        errors.append(
            f"manifest run_id {manifest.get('run_id')!r} != grade export run_id {grade_export['run_id']}"
        )
    if require_validated and manifest.get("validated") is not True:
        errors.append("manifest was not produced with the fresh-grade validation defense enabled")

    expected = {record["source_path"]: record for record in _selection_records(candidates)}
    actual: Dict[str, Dict] = {}
    curated_names: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"manifest entry {index} is not an object")
            continue
        source_path = entry.get("source_path")
        curated_name = entry.get("curated_name")
        if not isinstance(source_path, str) or not source_path:
            errors.append(f"manifest entry {index} has no source_path")
            continue
        if source_path in actual:
            errors.append(f"manifest duplicates source_path {source_path!r}")
        actual[source_path] = entry
        if not isinstance(curated_name, str) or not curated_name:
            errors.append(f"manifest entry {source_path!r} has no curated_name")
        elif curated_name in curated_names:
            errors.append(f"manifest duplicates curated_name {curated_name!r}")
        else:
            curated_names.add(curated_name)
        if entry.get("recorded_grade") not in PROMOTE_GRADES:
            errors.append(
                f"manifest entry {source_path!r} carries non-promotable recorded grade "
                f"{entry.get('recorded_grade')!r}"
            )

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        errors.append(f"manifest omits {len(missing)} authoritative candidates (first: {missing[0]})")
    if extra:
        errors.append(f"manifest contains {len(extra)} ineligible candidates (first: {extra[0]})")
    for source_path in sorted(set(expected) & set(actual)):
        expected_record = expected[source_path]
        entry = actual[source_path]
        for field in ("curated_name", "recorded_grade", "recorded_score"):
            if entry.get(field) != expected_record[field]:
                errors.append(
                    f"manifest entry {source_path!r} has {field}={entry.get(field)!r}; "
                    f"expected {expected_record[field]!r}"
                )
    return errors


# ── git-tracked file enumeration ─────────────────────────────────────────────
def _detect_magic_type(prefix: bytes) -> Optional[Tuple[str, frozenset[str]]]:
    """Return a recognized binary content type and its valid extensions."""
    if len(prefix) >= 12 and prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP":
        return "webp", frozenset({".webp"})
    if prefix.startswith(b"MZ") and len(prefix) >= 64:
        # The DOS header stores the PE signature offset at bytes 0x3C-0x40.
        pe_offset = int.from_bytes(prefix[0x3C:0x40], "little")
        if pe_offset + 4 <= len(prefix) and prefix[pe_offset : pe_offset + 4] == b"PE\0\0":
            return "portable-executable", frozenset({".exe", ".dll", ".node"})
    for kind, signatures, extensions in _MAGIC_SIGNATURES:
        if any(prefix.startswith(signature) for signature in signatures):
            return kind, extensions
    return None


def _is_binary(path: Path) -> bool:
    """Classify a file for the curated text mirror, failing closed on ambiguity.

    A recognized binary is omitted. Text and empty files remain mirrorable. A
    binary extension carrying text, binary bytes hidden behind a text extension,
    unknown binary bytes, a symlink, or an unreadable path is an error: neither
    build nor drift-check may silently normalize contradictory content.
    """
    if path.is_symlink():
        raise ContentInspectionError(f"refusing symlink during content inspection: {path}")
    try:
        with path.open("rb") as fh:
            prefix = fh.read(_INSPECTION_CHUNK_BYTES)

            suffix = path.suffix.lower()
            detected = _detect_magic_type(prefix)
            if detected is not None:
                kind, valid_extensions = detected
                extension_is_valid = suffix in valid_extensions or (
                    not suffix and kind in _EXTENSION_OPTIONAL_BINARY_TYPES
                )
                if not extension_is_valid:
                    expected = ", ".join(sorted(valid_extensions))
                    if kind in _EXTENSION_OPTIONAL_BINARY_TYPES:
                        expected = f"{expected}, or no extension"
                    raise ContentTypeMismatchError(
                        f"{path} contains {kind} bytes but uses {suffix or 'no extension'}; expected {expected}"
                    )
                return True

            if suffix in _BINARY_EXTENSIONS:
                raise ContentTypeMismatchError(
                    f"{path} uses governed binary extension {suffix} but has no matching magic bytes"
                )

            decoder = codecs.getincrementaldecoder("utf-8")("strict")
            chunk = prefix
            while chunk:
                # NUL is valid UTF-8, so the decoder alone cannot distinguish
                # NUL-bearing binary payloads from curated text.
                if b"\0" in chunk:
                    raise UnknownBinaryContentError(
                        f"{path} contains NUL-bearing binary data with no registered content type"
                    )
                try:
                    decoder.decode(chunk, final=False)
                except UnicodeDecodeError as exc:
                    raise UnknownBinaryContentError(
                        f"{path} is not valid UTF-8 text and has no registered content type"
                    ) from exc
                chunk = fh.read(_INSPECTION_CHUNK_BYTES)
            try:
                decoder.decode(b"", final=True)
            except UnicodeDecodeError as exc:
                raise UnknownBinaryContentError(
                    f"{path} ends with invalid UTF-8 and has no registered content type"
                ) from exc
    except OSError as exc:
        raise ContentInspectionError(f"cannot inspect {path}: {exc}") from exc
    return False


def tracked_files(skill_dir: Path) -> List[str]:
    """Relative paths of the git-tracked, MIRRORABLE files under a skill dir, sorted. Uses the
    committed tree so local == CI. Empty list means nothing tracked (skip).

    Recognized binary blobs are excluded: skills/.curated/ exists so skills.sh can INDEX skill
    text, and a compiled executable is not indexable. Contradictory extensions, unreadable
    paths, and unknown binary bytes fail closed rather than being silently copied or skipped.
    The SOURCE plugin remains unchanged; only the generated text index omits valid binaries.
    Filtering here rather than at the call sites is load-bearing: both the build copy loop and
    the drift checker read this function, so they cannot disagree about mirror eligibility."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", str(skill_dir.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContentInspectionError(f"cannot enumerate tracked files below {skill_dir}: {exc}") from exc
    rel_to_root = [p for p in out.split("\0") if p]
    base = skill_dir.relative_to(ROOT).as_posix()
    files = [p[len(base) + 1 :] for p in rel_to_root if p.startswith(base + "/")]
    return sorted(f for f in files if not _is_binary(skill_dir / f))


# ── build ────────────────────────────────────────────────────────────────────
def _load_existing_manifest() -> Optional[Dict]:
    """Read the current mirror baseline without tolerating ambiguous state."""
    if not MANIFEST.exists():
        if CURATED_DIR.exists() and any(CURATED_DIR.iterdir()):
            raise PromotionInvariantError(
                f"{CURATED_DIR} contains files but has no MANIFEST.json; refusing to replace an untracked baseline"
            )
        return None
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionInvariantError(f"{MANIFEST} is unreadable: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PromotionInvariantError(f"{MANIFEST} must contain a JSON object")
    entries = manifest.get("skills")
    if not isinstance(entries, list):
        raise PromotionInvariantError(f"{MANIFEST} field 'skills' must be a list")
    count = manifest.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count != len(entries):
        raise PromotionInvariantError(
            f"{MANIFEST} count {count!r} does not match its {len(entries)} skill entries"
        )
    source_paths: set[str] = set()
    curated_names: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PromotionInvariantError(f"{MANIFEST} skill entry {index} is not an object")
        source_path = entry.get("source_path")
        curated_name = entry.get("curated_name")
        if not isinstance(source_path, str) or not source_path:
            raise PromotionInvariantError(f"{MANIFEST} skill entry {index} has no source_path")
        if not isinstance(curated_name, str) or not curated_name:
            raise PromotionInvariantError(f"{MANIFEST} skill entry {index} has no curated_name")
        if source_path in source_paths:
            raise PromotionInvariantError(f"{MANIFEST} duplicates source_path {source_path!r}")
        if curated_name in curated_names:
            raise PromotionInvariantError(f"{MANIFEST} duplicates curated_name {curated_name!r}")
        source_paths.add(source_path)
        curated_names.add(curated_name)
    return manifest


def build(
    validate: bool = True,
    quiet: bool = False,
    allow_shrink: bool = False,
    target_plugin: Optional[str] = None,
) -> int:
    try:
        existing = _load_existing_manifest()
        candidates, grade_export = resolve_promotion_candidates(GRADES_CSV)
        assign_curated_names(candidates)
        selection = _selection_metadata(candidates)
    except (PromotionInvariantError, RuntimeError) as exc:
        print(f"error: curated promotion preflight failed: {exc}", file=sys.stderr)
        return 2

    all_candidates = candidates
    if target_plugin:
        normalized_target = target_plugin.removeprefix("./")
        candidates = [
            candidate
            for candidate in candidates
            if candidate["plugin"] == target_plugin or _plugin_root(candidate["skill_path"]) == normalized_target
        ]
        if not candidates:
            print(f"error: no A/B curated candidates found for plugin {target_plugin!r}", file=sys.stderr)
            return 2
        if existing is None:
            print("error: targeted promotion requires an existing MANIFEST.json", file=sys.stderr)
            return 2
        selection_errors = _manifest_selection_errors(
            existing,
            all_candidates,
            selection,
            grade_export,
            require_validated=True,
        )
        if selection_errors:
            print(
                "error: targeted promotion refused because the existing manifest does not "
                "represent the authoritative full cohort:",
                file=sys.stderr,
            )
            for error in selection_errors[:20]:
                print(f"  - {error}", file=sys.stderr)
            return 2
    if not quiet:
        scope = f" for {target_plugin}" if target_plugin else ""
        print(f"selection: {len(candidates)} A/B plugin skills{scope} (own, source present)")

    vss = load_validator() if validate else None
    if validate and vss is None:
        print(
            "error: fresh-grade validation was requested but the canonical validator could not be loaded; "
            "the mirror was NOT touched. Use --no-validate only for an explicit local diagnostic.",
            file=sys.stderr,
        )
        return 2

    run_id = grade_export["run_id"]

    # Phase 1 — compute the full selection WITHOUT touching the mirror, so the
    # shrink floor below can abort with skills/.curated/ intact.
    promoted: List[Dict] = []
    grade_disagreements: List[str] = []
    dropped_empty = 0
    for c in candidates:
        src_dir = ROOT / c["skill_path"]

        fg: Optional[str] = None
        if validate:
            fg = fresh_grade(vss, src_dir)
            if fg != c["grade"]:
                grade_disagreements.append(
                    f"{c['skill_path']}: recorded={c['grade']} fresh={fg or 'UNGRADABLE'}"
                )
                continue

        files = tracked_files(src_dir)
        if not files or "SKILL.md" not in files:
            dropped_empty += 1
            continue  # nothing tracked to mirror

        promoted.append(
            {
                "curated_name": c["curated_name"],
                "source_path": c["skill_path"],
                "category": c["category"],
                "plugin": c["plugin"],
                "recorded_grade": c["grade"],
                "recorded_score": c.get("score", ""),
                "fresh_grade": fg,  # None when --no-validate
                "run_id": run_id,
                "files": files,
            }
        )

    if grade_disagreements:
        print(
            "error: fresh grades disagree with the authoritative recorded export; "
            "run the Freshie cycle before promotion. The mirror was NOT touched.",
            file=sys.stderr,
        )
        for disagreement in grade_disagreements[:20]:
            print(f"  - {disagreement}", file=sys.stderr)
        if len(grade_disagreements) > 20:
            print(f"  ... and {len(grade_disagreements) - 20} more", file=sys.stderr)
        return 2
    if dropped_empty:
        print(
            f"error: {dropped_empty} authoritative candidates have no mirrorable tracked SKILL.md; "
            "the mirror was NOT touched.",
            file=sys.stderr,
        )
        return 2

    # Shrink floor — every upstream failure mode (empty/corrupt grades.csv, a
    # validator API drift nulling every fresh grade) converges on a tiny/empty
    # selection. Refuse to wipe ~1,881 published skills over one of those.
    prior_count = len(existing["skills"]) if existing is not None else None
    if not allow_shrink and not target_plugin:
        floor = int(prior_count * SHRINK_FLOOR_RATIO) if prior_count else 0
        if len(promoted) == 0 or (prior_count and len(promoted) < floor):
            baseline = (
                f"{prior_count} in the committed MANIFEST"
                if prior_count is not None
                else "no committed MANIFEST baseline"
            )
            print(
                f"error: refusing to rebuild skills/.curated/ — new selection is "
                f"{len(promoted)} skills vs {baseline} "
                f"(floor: {floor}, ratio {SHRINK_FLOOR_RATIO}). "
                f"[candidates: {len(candidates)}, grade_disagreements: {len(grade_disagreements)}, "
                f"dropped_empty: {dropped_empty}] The mirror was NOT touched. If this "
                f"large drop is intentional, re-run with --allow-shrink.",
                file=sys.stderr,
            )
            return 2

    promoted_target_count = len(promoted)

    # Phase 2 — full builds wipe/rebuild. A targeted build replaces exactly one
    # plugin's rows and directories while preserving every unrelated mirror.
    retained: List[Dict] = []
    if target_plugin:
        assert existing is not None
        normalized_target = target_plugin.removeprefix("./")
        target_entries = [
            entry
            for entry in existing.get("skills", [])
            if entry.get("plugin") == target_plugin
            or _plugin_root(str(entry.get("source_path", ""))) == normalized_target
        ]
        retained = [entry for entry in existing.get("skills", []) if entry not in target_entries]
        for entry in target_entries:
            destination = CURATED_DIR / entry["curated_name"]
            if destination.exists():
                shutil.rmtree(destination)
    else:
        if CURATED_DIR.exists():
            shutil.rmtree(CURATED_DIR)
        CURATED_DIR.mkdir(parents=True)

    for entry in promoted:
        src_dir = ROOT / entry["source_path"]
        dest_dir = CURATED_DIR / entry["curated_name"]
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        for rel in entry["files"]:
            dst = dest_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src_dir / rel, dst)

    promoted = retained + promoted
    promoted.sort(key=lambda p: p["curated_name"])
    manifest = {
        "generator": "freshie/scripts/promote-to-curated.py",
        "generated_from": "freshie/grades.csv",
        "run_id": run_id,
        "threshold": "".join(sorted(PROMOTE_GRADES)),
        "validated": validate,
        "grade_export": grade_export,
        "selection": selection,
        "count": len(promoted),
        "skills": promoted,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    if not quiet:
        if target_plugin:
            print(f"promoted: {promoted_target_count} for {target_plugin} ({len(promoted)} total) → skills/.curated/")
        else:
            print(f"promoted: {len(promoted)} → skills/.curated/")
        if validate:
            print("fresh-grade agreement: exact")
        if dropped_empty:
            print(f"dropped (no tracked files): {dropped_empty}")
        print(f"manifest: {_display_path(MANIFEST, ROOT)}")
    return 0


def _run_id() -> Optional[int]:
    """Latest run id from grade-histogram.json (tracked), for the audit trail."""
    if GRADE_HISTOGRAM.exists():
        try:
            payload = json.loads(GRADE_HISTOGRAM.read_text())
            run_id = payload.get("run_id") if isinstance(payload, dict) else None
            return run_id if isinstance(run_id, int) and not isinstance(run_id, bool) else None
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
    curated_present = CURATED_DIR.exists() and any(CURATED_DIR.iterdir())

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

    try:
        candidates, grade_export = resolve_promotion_candidates(GRADES_CSV)
        assign_curated_names(candidates)
        selection = _selection_metadata(candidates)
    except (PromotionInvariantError, RuntimeError) as exc:
        print(f"::error::curated candidate resolution failed: {exc}")
        return 1

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error::skills/.curated/MANIFEST.json is unreadable: {exc}")
        return 1
    if not isinstance(manifest, dict):
        print("::error::skills/.curated/MANIFEST.json must contain a JSON object")
        return 1

    selection_errors = _manifest_selection_errors(
        manifest,
        candidates,
        selection,
        grade_export,
        require_validated=True,
    )
    if selection_errors:
        print("::error::skills/.curated/MANIFEST.json does not represent the authoritative cohort.")
        for error in selection_errors[:50]:
            print(f"  - {error}")
        if len(selection_errors) > 50:
            print(f"  ... and {len(selection_errors) - 50} more")
        print("\nRun: python3 freshie/scripts/promote-to-curated.py")
        return 1

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
        if e.get("files") != src_files:
            drift.append(
                f"manifest file list drift: {e['source_path']} records {e.get('files')!r}, "
                f"current tracked files are {src_files!r}"
            )
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
    global ROOT, GRADES_CSV, GRADE_HISTOGRAM, CURATED_DIR, MANIFEST, VALIDATOR, CORPUS_RESOLVER

    ap = argparse.ArgumentParser(description="Promote A/B plugin skills into skills/.curated/ for skills.sh.")
    ap.add_argument("--check", action="store_true", help="CI drift gate: exit 1 if the mirror is stale vs source.")
    ap.add_argument("--no-validate", action="store_true", help="Skip the in-process re-grade defense (build mode).")
    ap.add_argument(
        "--allow-shrink",
        action="store_true",
        help="Override the shrink floor: rebuild even when the new selection is "
        "empty or far below the committed MANIFEST count (build mode).",
    )
    ap.add_argument("--quiet", action="store_true", help="Only print on error.")
    ap.add_argument(
        "--plugin",
        help="replace only one plugin's curated mirror rows (plugin name or repo-relative root)",
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root containing plugin sources (default: this checkout)",
    )
    ap.add_argument("--grades-csv", type=Path, default=None, help="override the grade export used for selection")
    ap.add_argument(
        "--grade-histogram", type=Path, default=None, help="override the grade histogram used for manifest provenance"
    )
    ap.add_argument("--curated-dir", type=Path, default=None, help="override the generated curated-mirror destination")
    ap.add_argument(
        "--corpus-resolver",
        type=Path,
        default=None,
        help="override the corpus resolver (used by hermetic integration fixtures)",
    )
    args = ap.parse_args()
    ROOT = args.repo_root.resolve()
    GRADES_CSV = args.grades_csv or ROOT / "freshie" / "grades.csv"
    GRADE_HISTOGRAM = args.grade_histogram or ROOT / "freshie" / "grade-histogram.json"
    CURATED_DIR = args.curated_dir or ROOT / "skills" / ".curated"
    MANIFEST = CURATED_DIR / "MANIFEST.json"
    VALIDATOR = ROOT / "scripts" / "validate-skills-schema.py"
    CORPUS_RESOLVER = args.corpus_resolver or ROOT / "scripts" / "corpus-resolver.mjs"
    if args.check and args.plugin:
        ap.error("--plugin cannot be combined with --check")
    if args.check:
        return check(quiet=args.quiet)
    return build(
        validate=not args.no_validate,
        quiet=args.quiet,
        allow_shrink=args.allow_shrink,
        target_plugin=args.plugin,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ContentInspectionError as exc:
        print(f"error: curated content-type gate refused the corpus: {exc}", file=sys.stderr)
        sys.exit(2)

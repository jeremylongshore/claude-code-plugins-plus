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
import importlib.util
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
    except FileNotFoundError as exc:
        raise RuntimeError("corpus resolver requires Node 20+ on PATH") from exc
    if result.returncode != 0:
        raise RuntimeError(f"corpus resolver failed for {', '.join(cohorts)}: {result.stderr.strip()}")
    try:
        payload = json.loads(result.stdout)
        resolved = {cohorts[0]: payload} if len(cohorts) == 1 else payload["cohorts"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"corpus resolver returned invalid JSON: {exc}") from exc
    output: Dict[str, set[str]] = {}
    for cohort in cohorts:
        files = resolved.get(cohort, {}).get("files")
        if not isinstance(files, list) or not all(isinstance(value, str) for value in files):
            raise RuntimeError(f"corpus resolver returned an invalid file list for {cohort}")
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


def load_candidates(grades_csv: Path) -> List[Dict[str, str]]:
    """Select curated candidates from the resolved graded/first-party intersection.

    The shared corpus resolver excludes mirrors, hidden paths, and untracked files;
    this caller then keeps A/B rows whose source directory still exists. Results
    are sorted by skill_path for deterministic output.
    """
    if not grades_csv.exists():
        sys.exit(
            f"error: {grades_csv} not found — run the Freshie cycle first "
            f"(rebuild-inventory.py → validate --populate-db → dolt-sync.py)."
        )
    out: List[Dict[str, str]] = []
    cohorts = resolve_corpora("graded", "first-party")
    graded = cohorts["graded"]
    first_party = cohorts["first-party"]
    try:
        with grades_csv.open(newline="") as fh:
            for row in csv.DictReader(fh):
                sp, grade = row.get("skill_path", ""), row.get("grade", "")
                if not sp or not sp.startswith("plugins/") or grade not in PROMOTE_GRADES:
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
    except (csv.Error, UnicodeDecodeError) as e:
        # A truncated/binary-corrupted grades.csv must not crash with a raw
        # traceback; an empty selection lets build()'s shrink floor abort with
        # the mirror untouched and an actionable message.
        print(f"warning: {grades_csv} is unreadable as CSV ({e}); selection is empty.", file=sys.stderr)
        return []
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
    except (Exception, SystemExit) as e:  # noqa: BLE001 — any failure ⇒ fall back to recorded grade
        # SystemExit is caught explicitly: the validator's module-level guard
        # calls sys.exit(1) when pyyaml is missing, and SystemExit inherits
        # BaseException — a bare `except Exception` let it propagate, so the
        # documented "degrades to recorded grades" contract silently never
        # applied on a pyyaml-less machine and the whole promote hard-failed
        # (the 2026-07 CI failure was patched in the workflow, not here).
        detail = f"exit code {e.code}, likely a missing dependency such as pyyaml" if isinstance(e, SystemExit) else e
        print(f"⚠️  could not import validator ({detail}); falling back to recorded grades.", file=sys.stderr)
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
def _prior_manifest_count() -> Optional[int]:
    """Promoted-skill count in the committed MANIFEST, or None when unavailable."""
    if not MANIFEST.exists():
        return None
    try:
        return len(json.loads(MANIFEST.read_text()).get("skills", []))
    except Exception:  # noqa: BLE001 — unreadable manifest ⇒ no baseline
        return None


def build(
    validate: bool = True,
    quiet: bool = False,
    allow_shrink: bool = False,
    target_plugin: Optional[str] = None,
) -> int:
    candidates = load_candidates(GRADES_CSV)
    assign_curated_names(candidates)
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
    if not quiet:
        scope = f" for {target_plugin}" if target_plugin else ""
        print(f"selection: {len(candidates)} A/B plugin skills{scope} (own, source present)")

    vss = load_validator() if validate else None
    if validate and vss is None:
        validate = False  # degrade: recorded grade only

    run_id = _run_id()

    # Phase 1 — compute the full selection WITHOUT touching the mirror, so the
    # shrink floor below can abort with skills/.curated/ intact.
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

    # Shrink floor — every upstream failure mode (empty/corrupt grades.csv, a
    # validator API drift nulling every fresh grade) converges on a tiny/empty
    # selection. Refuse to wipe ~1,881 published skills over one of those.
    prior_count = _prior_manifest_count()
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
                f"[candidates: {len(candidates)}, dropped_grade: {dropped_grade}, "
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
        if not MANIFEST.exists():
            print("error: targeted promotion requires an existing MANIFEST.json", file=sys.stderr)
            return 2
        existing = json.loads(MANIFEST.read_text())
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
            print(f"dropped (fresh grade < B / unparseable): {dropped_grade}")
        if dropped_empty:
            print(f"dropped (no tracked files): {dropped_empty}")
        print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    return 0


def _run_id() -> Optional[int]:
    """Latest run id from grade-histogram.json (tracked), for the audit trail."""
    if GRADE_HISTOGRAM.exists():
        try:
            return json.loads(GRADE_HISTOGRAM.read_text()).get("run_id")
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

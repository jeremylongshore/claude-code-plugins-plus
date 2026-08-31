"""Regression tests for freshie/scripts/promote-to-curated.py (2026-07-14 ops review).

Two defects pinned here:
  1. No-floor wipe (P1/P2): build mode wiped skills/.curated/ BEFORE computing the
     selection outcome, so every upstream failure mode (empty/truncated/corrupt
     grades.csv, a validator API drift nulling every fresh grade) converged on
     deleting all ~1,881 promoted skills and exiting 0 "success". Build now
     computes the selection first and ABORTS non-zero — mirror untouched — when
     the selection is empty or below SHRINK_FLOOR_RATIO of the committed
     MANIFEST count. --allow-shrink overrides for a legitimate large drop.
  2. Degrade contract vs SystemExit (P2): the validator's module-level guard
     calls sys.exit(1) when pyyaml is missing; SystemExit inherits BaseException,
     so load_validator's `except Exception` never caught it and the documented
     "degrades to recorded grades" fallback silently did not apply.

Run: python3 -m unittest tests.test_promote_to_curated_floor -v

Fully self-contained: builds a tmp curated mirror + grades.csv, monkeypatches the
module's ROOT / GRADES_CSV / CURATED_DIR / MANIFEST / tracked_files, and never
touches the real repo.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "promote-to-curated.py"
_spec = importlib.util.spec_from_file_location("promote_to_curated", SCRIPT)
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)

SKILL_MD = """\
---
name: {name}
description: A promoted test skill.
---
# Body
"""


class PromoteFloorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.root = root
        self.curated = root / "skills" / ".curated"
        self.manifest = self.curated / "MANIFEST.json"

        # An existing mirror with 4 promoted skills + a committed MANIFEST.
        self.existing_dirs = []
        for i in range(4):
            d = self.curated / f"existing-{i}"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(SKILL_MD.format(name=f"existing-{i}"), encoding="utf-8")
            self.existing_dirs.append(d)
        self._write_manifest(4)

        self.grades_csv = root / "freshie" / "grades.csv"
        self.grades_csv.parent.mkdir(parents=True)

        self._orig = {
            k: getattr(pc, k)
            for k in ("ROOT", "GRADES_CSV", "GRADE_HISTOGRAM", "CURATED_DIR", "MANIFEST", "tracked_files")
        }
        pc.ROOT = root
        pc.GRADES_CSV = self.grades_csv
        pc.GRADE_HISTOGRAM = root / "freshie" / "grade-histogram.json"
        pc.CURATED_DIR = self.curated
        pc.MANIFEST = self.manifest

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(pc, k, v)
        self._tmp.cleanup()

    # ── helpers ──────────────────────────────────────────────────────────
    def _write_manifest(self, n: int) -> None:
        self.manifest.write_text(
            json.dumps({"count": n, "skills": [{"curated_name": f"existing-{i}"} for i in range(n)]})
        )

    def _make_candidates(self, n: int) -> None:
        """Write a grades.csv with n A-grade plugin skills whose sources exist."""
        lines = ["skill_path,grade,score"]
        for i in range(n):
            sp = f"plugins/cat/plug/skills/cand-{i}"
            src = self.root / sp
            src.mkdir(parents=True, exist_ok=True)
            (src / "SKILL.md").write_text(SKILL_MD.format(name=f"cand-{i}"), encoding="utf-8")
            lines.append(f"{sp},A,95")
        self.grades_csv.write_text("\n".join(lines) + "\n")
        # tmp tree is not a git repo — pretend every source tracks its SKILL.md
        pc.tracked_files = lambda skill_dir: ["SKILL.md"]

    def _mirror_intact(self) -> bool:
        return all(d.is_dir() and (d / "SKILL.md").is_file() for d in self.existing_dirs)

    # ── the floor: abort BEFORE the wipe ─────────────────────────────────
    def test_empty_grades_csv_aborts_before_wipe(self):
        self.grades_csv.write_text("skill_path,grade,score\n")  # header only
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact(), "mirror must be untouched on abort")
        self.assertTrue(self.manifest.is_file(), "MANIFEST must survive an abort")

    def test_corrupt_grades_csv_aborts_before_wipe(self):
        self.grades_csv.write_text("garbage\x00not,a,csv\n\n???\n")
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact())

    def test_selection_below_ratio_floor_aborts(self):
        # committed mirror says 10; the new selection is only 2 (< 50% floor)
        self._write_manifest(10)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact())

    # ── --allow-shrink is the explicit override ──────────────────────────
    def test_allow_shrink_permits_empty_rebuild(self):
        self.grades_csv.write_text("skill_path,grade,score\n")
        rc = pc.build(validate=False, quiet=True, allow_shrink=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self._mirror_intact(), "--allow-shrink rebuild wipes the old mirror")
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 0)

    def test_allow_shrink_permits_ratio_shrink(self):
        self._write_manifest(10)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True, allow_shrink=True)
        self.assertEqual(rc, 0)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 2)

    # ── healthy paths keep building ──────────────────────────────────────
    def test_healthy_selection_above_floor_builds(self):
        self._make_candidates(4)  # 4 vs committed 4 -> well above the 50% floor
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 0)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 4)
        for i in range(4):
            self.assertTrue((self.curated / f"cand-{i}" / "SKILL.md").is_file())

    def test_first_build_without_manifest_builds(self):
        # no committed MANIFEST / mirror at all -> no baseline, only the
        # empty-selection guard applies
        import shutil

        shutil.rmtree(self.curated)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.manifest.read_text())["count"], 2)

    def test_first_build_with_empty_selection_still_aborts(self):
        import shutil

        shutil.rmtree(self.curated)
        self.grades_csv.write_text("skill_path,grade,score\n")
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertFalse(self.curated.exists(), "no mirror should be created on abort")

    def test_targeted_build_replaces_only_requested_plugin(self):
        old_target = self.curated / "old-target"
        old_target.mkdir()
        (old_target / "SKILL.md").write_text(SKILL_MD.format(name="old-target"), encoding="utf-8")
        unrelated = self.curated / "unrelated"
        unrelated.mkdir()
        unrelated_body = SKILL_MD.format(name="unrelated")
        (unrelated / "SKILL.md").write_text(unrelated_body, encoding="utf-8")

        existing = json.loads(self.manifest.read_text())
        existing["skills"].extend(
            [
                {
                    "curated_name": "old-target",
                    "source_path": "plugins/cat/target-pack/skills/old-target",
                    "plugin": "target-pack",
                },
                {
                    "curated_name": "unrelated",
                    "source_path": "plugins/cat/other-pack/skills/unrelated",
                    "plugin": "other-pack",
                },
            ]
        )
        existing["count"] = len(existing["skills"])
        self.manifest.write_text(json.dumps(existing), encoding="utf-8")

        source_path = "plugins/cat/target-pack/skills/new-target"
        source = self.root / source_path
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(SKILL_MD.format(name="new-target"), encoding="utf-8")
        candidate = {
            "skill_path": source_path,
            "grade": "A",
            "score": "95",
            "category": "cat",
            "plugin": "target-pack",
            "name": "new-target",
        }
        pc.tracked_files = lambda skill_dir: ["SKILL.md"]

        with mock.patch.object(pc, "load_candidates", return_value=[candidate]):
            rc = pc.build(validate=False, quiet=True, target_plugin="target-pack")

        self.assertEqual(rc, 0)
        self.assertFalse(old_target.exists())
        self.assertTrue((self.curated / "new-target" / "SKILL.md").is_file())
        self.assertEqual((unrelated / "SKILL.md").read_text(), unrelated_body)
        manifest = json.loads(self.manifest.read_text())
        names = {entry["curated_name"] for entry in manifest["skills"]}
        self.assertIn("new-target", names)
        self.assertIn("unrelated", names)
        self.assertNotIn("old-target", names)

    def test_targeted_build_with_no_candidates_does_not_mutate_mirror(self):
        manifest_before = self.manifest.read_bytes()
        skill_before = (self.existing_dirs[0] / "SKILL.md").read_bytes()
        with mock.patch.object(pc, "load_candidates", return_value=[]):
            rc = pc.build(validate=False, quiet=True, target_plugin="target-pack")
        self.assertNotEqual(rc, 0)
        self.assertEqual(self.manifest.read_bytes(), manifest_before)
        self.assertEqual((self.existing_dirs[0] / "SKILL.md").read_bytes(), skill_before)


class LoadValidatorDegradeTests(unittest.TestCase):
    """The degrade contract must hold even when the validator hard-exits at
    import time (SystemExit from its missing-pyyaml guard)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_validator = pc.VALIDATOR

    def tearDown(self):
        pc.VALIDATOR = self._orig_validator
        self._tmp.cleanup()

    def test_systemexit_at_import_degrades_to_none(self):
        fake = Path(self._tmp.name) / "fake_validator.py"
        fake.write_text("import sys\nsys.exit(1)\n")  # same shape as the pyyaml guard
        pc.VALIDATOR = fake
        # must NOT raise SystemExit; must return None so build degrades
        self.assertIsNone(pc.load_validator())

    def test_ordinary_exception_at_import_degrades_to_none(self):
        fake = Path(self._tmp.name) / "fake_validator.py"
        fake.write_text("raise RuntimeError('kernel schema missing')\n")
        pc.VALIDATOR = fake
        self.assertIsNone(pc.load_validator())


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestExternalMirrorDetection(unittest.TestCase):
    """Pins the retained compatibility helper — defect 3 from review of PR #1182.

    load_candidates() used to test only `_plugin_root(sp)`, which splits on
    '/skills/'. A skill vendored at `plugins/<cat>/<plugin>/.codex/skills/<name>`
    therefore resolved to `<plugin>/.codex` — one level BELOW the plugin root where
    `.source.json` lives — so the mirror marker was never seen and six external
    plugins were republished under our name in skills/.curated/. Detection must key
    on "ANY ancestor owns a .source.json", never on directory names.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_root = pc.ROOT
        pc.ROOT = self.root
        # an external mirror: marker at the plugin root
        mirror = self.root / "plugins" / "testing" / "vendor-pack"
        (mirror / ".codex" / "skills" / "vendored").mkdir(parents=True)
        (mirror / "skills" / "direct").mkdir(parents=True)
        (mirror / ".source.json").write_text("{}")
        # one of ours: no marker anywhere up the chain
        ours = self.root / "plugins" / "productivity" / "our-pack"
        (ours / "skills" / "ours").mkdir(parents=True)

    def tearDown(self):
        pc.ROOT = self._orig_root
        self._tmp.cleanup()

    def test_vendored_subdir_skill_is_detected(self):
        """The regression itself: .codex/skills/<name> sits below the marker."""
        self.assertTrue(pc.is_external_mirror("plugins/testing/vendor-pack/.codex/skills/vendored"))

    def test_direct_mirror_skill_is_detected(self):
        self.assertTrue(pc.is_external_mirror("plugins/testing/vendor-pack/skills/direct"))

    def test_our_own_skill_is_not_a_mirror(self):
        self.assertFalse(pc.is_external_mirror("plugins/productivity/our-pack/skills/ours"))

    def test_absolute_path_terminates(self):
        """`while node != Path('.')` never terminated on an absolute path."""
        self.assertFalse(pc.is_external_mirror("/nonexistent/skills/x"))


class TestBinarySniff(unittest.TestCase):
    """Pins the fail-closed content-type boundary used by both mirror modes."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, data: bytes) -> Path:
        p = self.dir / name
        p.write_bytes(data)
        return p

    def test_genuine_png_is_binary(self):
        self.assertTrue(pc._is_binary(self._write("diagram.png", bytes.fromhex("89504e470d0a1a0a") + b"fixture")))

    def test_current_font_signature_is_binary(self):
        for signature in (b"\x00\x01\x00\x00", b"true"):
            with self.subTest(signature=signature):
                self.assertTrue(pc._is_binary(self._write("font.ttf", signature + b"fixture")))

    def test_legacy_postscript_sfnt_is_not_ttf(self):
        with self.assertRaises(pc.ContentTypeMismatchError):
            pc._is_binary(self._write("font.ttf", b"typ1fixture"))

    def test_executable_signature_is_binary(self):
        self.assertTrue(pc._is_binary(self._write("tool", b"\x7fELF\x02\x01fixture")))

    def test_text_disguised_as_png_fails_closed(self):
        with self.assertRaises(pc.ContentTypeMismatchError):
            pc._is_binary(self._write("diagram.png", b"plain text placeholder\n"))

    def test_text_disguised_as_special_case_binary_extension_fails_closed(self):
        for name in ("diagram.webp", "tool.exe", "library.dll"):
            with self.subTest(name=name):
                with self.assertRaises(pc.ContentTypeMismatchError):
                    pc._is_binary(self._write(name, b"plain text placeholder\n"))

    def test_binary_disguised_as_markdown_fails_closed(self):
        with self.assertRaises(pc.ContentTypeMismatchError):
            pc._is_binary(self._write("notes.md", bytes.fromhex("89504e470d0a1a0a") + b"fixture"))

    def test_binary_content_with_wrong_binary_extension_fails_closed(self):
        with self.assertRaises(pc.ContentTypeMismatchError):
            pc._is_binary(self._write("diagram.pdf", bytes.fromhex("89504e470d0a1a0a") + b"fixture"))

    def test_recognized_binary_with_unrelated_or_missing_extension_fails_closed(self):
        png = bytes.fromhex("89504e470d0a1a0a") + b"fixture"
        for name in ("diagram.bin", "diagram"):
            with self.subTest(name=name):
                with self.assertRaises(pc.ContentTypeMismatchError):
                    pc._is_binary(self._write(name, png))

    def test_unknown_nul_bearing_content_fails_closed(self):
        with self.assertRaises(pc.UnknownBinaryContentError):
            pc._is_binary(self._write("blob.bin", b"unregistered\x00binary"))

    def test_unknown_nul_after_initial_chunk_fails_closed(self):
        with self.assertRaises(pc.UnknownBinaryContentError):
            pc._is_binary(self._write("late-binary.dat", b"a" * pc._INSPECTION_CHUNK_BYTES + b"\x00"))

    def test_invalid_utf8_without_nul_fails_closed(self):
        with self.assertRaises(pc.UnknownBinaryContentError):
            pc._is_binary(self._write("unknown.dat", b"plain-prefix\xff\xfe"))

    def test_empty_file_is_not_binary(self):
        self.assertFalse(pc._is_binary(self._write("__init__.py", b"")))

    def test_utf8_multibyte_is_not_binary(self):
        self.assertFalse(pc._is_binary(self._write("SKILL.md", "# héllo — ✅\n".encode())))

    def test_unreadable_file_fails_closed(self):
        with self.assertRaises(pc.ContentInspectionError):
            pc._is_binary(self.dir / "absent")

    def test_symlink_fails_closed(self):
        source = self._write("source.md", b"text")
        link = self.dir / "link.md"
        link.symlink_to(source)
        with self.assertRaises(pc.ContentInspectionError):
            pc._is_binary(link)

    def test_git_enumeration_failure_fails_closed(self):
        skill_dir = self.dir / "skill"
        skill_dir.mkdir()
        failure = pc.subprocess.CalledProcessError(1, ["git", "ls-files"])
        with (
            mock.patch.object(pc, "ROOT", self.dir),
            mock.patch.object(pc.subprocess, "run", side_effect=failure),
            self.assertRaises(pc.ContentInspectionError),
        ):
            pc.tracked_files(skill_dir)

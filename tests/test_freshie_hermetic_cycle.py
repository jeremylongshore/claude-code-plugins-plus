"""Hermetic integration proof for the Freshie inventory publication cycle.

The fixture runs the real command-line tools against a one-skill Git repo,
temporary SQLite/Dolt state, and a filesystem-backed fake Dolt remote. It never
writes Freshie's tracked exports or contacts DoltHub. Run with:

    python3 -m unittest tests.test_freshie_hermetic_cycle -v
"""

from __future__ import annotations

import csv
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REBUILD = ROOT / "freshie" / "scripts" / "rebuild-inventory.py"
VALIDATE = ROOT / "scripts" / "validate-skills-schema.py"
SYNC = ROOT / "freshie" / "scripts" / "dolt-sync.py"
PROMOTE = ROOT / "freshie" / "scripts" / "promote-to-curated.py"


@unittest.skipUnless(
    shutil.which("dolt") and shutil.which("node") and shutil.which("sqlite3"),
    "requires dolt, node, and sqlite3 for the hermetic integration fixture",
)
class HermeticFreshieCycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freshie-hermetic-")
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.db = Path(self.tmp.name) / "inventory.sqlite"
        self.dolt_dir = Path(self.tmp.name) / "dolt" / "inventory"
        self.out = Path(self.tmp.name) / "out"
        self.curated = Path(self.tmp.name) / "curated"
        self.remote = Path(self.tmp.name) / "remote"
        self.skill_rel = "plugins/testing/example/skills/example-skill/SKILL.md"
        self.skill = self.root / self.skill_rel
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text(self._graded_fixture_skill(), encoding="utf-8")
        self.resolver = Path(self.tmp.name) / "resolver.mjs"
        self.resolver.write_text(
            "#!/usr/bin/env node\n"
            "const files = ['plugins/testing/example/skills/example-skill/SKILL.md'];\n"
            "console.log(JSON.stringify({cohorts: {graded: {files}, 'first-party': {files}}}));\n",
            encoding="utf-8",
        )
        self._run(["git", "init", "-q"], cwd=self.root)
        self._run(["git", "config", "user.name", "Freshie Test"], cwd=self.root)
        self._run(["git", "config", "user.email", "freshie@example.invalid"], cwd=self.root)
        self._run(["git", "add", "."], cwd=self.root)
        self._run(["git", "commit", "-qm", "fixture"], cwd=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _graded_fixture_skill(self) -> str:
        """Use an actual current A/B source so promotion tests its real threshold."""
        grades = ROOT / "freshie" / "grades.csv"
        with grades.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("grade") not in {"A", "B"}:
                    continue
                source = ROOT / row["skill_path"] / "SKILL.md"
                if not source.is_file():
                    continue
                if any((parent / ".source.json").exists() for parent in source.parents):
                    continue
                return source.read_text(encoding="utf-8")
        self.fail("no current first-party A/B SKILL.md is available for the integration fixture")

    def _run(self, args, *, cwd=None, expected=0):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
        expected_codes = (expected,) if isinstance(expected, int) else tuple(expected)
        if result.returncode not in expected_codes:
            self.fail(
                f"command returned {result.returncode}, expected {expected_codes}: {' '.join(map(str, args))}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def _wait_for_port(self, port: int) -> None:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    return
            time.sleep(0.1)
        self.fail(f"dolt sql-server did not bind port {port}")

    def test_full_cycle_uses_only_scratch_state_and_refuses_live_server(self):
        self._run([sys.executable, str(REBUILD), "--repo-root", str(self.root), "--db", str(self.db), "--run-id", "1"])
        self._run([
            sys.executable, str(VALIDATE), "--marketplace", "--repo-root", str(self.root),
            "--populate-db", str(self.db),
        ], expected=(0, 1))
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM skill_compliance WHERE run_id=1").fetchone()[0], 1
            )
            # The source was A/B in its complete production plugin, but this
            # one-file fixture deliberately omits that surrounding context.
            # Calibrate only the scratch row so promotion exercises its
            # non-empty path; production grades remain validator-owned.
            conn.execute(
                "UPDATE skill_compliance SET skill_path=?, grade='A', score=100 WHERE run_id=1",
                (self.skill_rel.removesuffix("/SKILL.md"),),
            )
            conn.commit()
        self._run([
            sys.executable, str(SYNC), "--db", str(self.db), "--dolt-dir", str(self.dolt_dir),
            "--grades-csv", str(self.out / "grades.csv"),
            "--grade-histogram", str(self.out / "grade-histogram.json"),
            "--reports-dir", str(self.out / "reports"), "--no-push",
        ])

        self.assertTrue((self.out / "grades.csv").is_file())
        self.assertTrue((self.out / "reports" / "run-delta-1.json").is_file())
        histogram = json.loads((self.out / "grade-histogram.json").read_text())
        self.assertEqual(histogram["run_id"], 1)

        self.remote.mkdir()
        self._run(["dolt", "init"], cwd=self.remote)
        self._run(["dolt", "remote", "add", "fixture", f"file://{self.remote}"], cwd=self.dolt_dir)
        # A successful filesystem remote push is the fake-remote proof. The
        # receiving checkout keeps its own working branch, so its default
        # `dolt log` is not a reliable view of the pushed ref.
        self._run(["dolt", "push", "fixture", "main"], cwd=self.dolt_dir)

        self._run([
            sys.executable, str(PROMOTE), "--repo-root", str(self.root),
            "--grades-csv", str(self.out / "grades.csv"),
            "--grade-histogram", str(self.out / "grade-histogram.json"),
            "--curated-dir", str(self.curated), "--corpus-resolver", str(self.resolver),
            "--no-validate", "--quiet",
        ])
        manifest = json.loads((self.curated / "MANIFEST.json").read_text())
        self.assertEqual(manifest["run_id"], 1)
        self.assertEqual(manifest["count"], 1)

        server = subprocess.Popen(
            ["dolt", "sql-server", "--port", "3308"],
            cwd=self.dolt_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            self._wait_for_port(3308)
            refusal = self._run([
                sys.executable, str(SYNC), "--db", str(self.db), "--dolt-dir", str(self.dolt_dir),
                "--grades-csv", str(self.out / "blocked-grades.csv"),
                "--grade-histogram", str(self.out / "blocked-histogram.json"), "--no-push",
            ], expected=1)
            self.assertIn("sql-server", refusal.stdout)
            self.assertFalse((self.out / "blocked-grades.csv").exists())
        finally:
            server.terminate()
            server.wait(timeout=10)

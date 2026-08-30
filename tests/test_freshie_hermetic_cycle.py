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


class HermeticFreshieCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [name for name in ("dolt", "node", "sqlite3") if not shutil.which(name)]
        if missing:
            raise AssertionError(
                "Freshie hermetic integration is blocking; missing required tools: " + ", ".join(missing)
            )

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
        source = self._graded_fixture_source()
        self.skill.parent.parent.mkdir(parents=True)
        shutil.copytree(source.parent, self.skill.parent)
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

    def _graded_fixture_source(self) -> Path:
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
                return source
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
        self._run(
            [
                sys.executable,
                str(VALIDATE),
                "--marketplace",
                "--repo-root",
                str(self.root),
                "--populate-db",
                str(self.db),
            ]
        )
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM skill_compliance WHERE run_id=1").fetchone()[0], 1)
            grade = conn.execute("SELECT grade FROM skill_compliance WHERE run_id=1").fetchone()[0]
            self.assertIn(grade, {"A", "B"})
        self._run(
            [
                sys.executable,
                str(SYNC),
                "--db",
                str(self.db),
                "--repo-root",
                str(self.root),
                "--dolt-dir",
                str(self.dolt_dir),
                "--grades-csv",
                str(self.out / "grades.csv"),
                "--grade-histogram",
                str(self.out / "grade-histogram.json"),
                "--reports-dir",
                str(self.out / "reports"),
                "--no-push",
            ]
        )

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

        self._run(
            [
                sys.executable,
                str(PROMOTE),
                "--repo-root",
                str(self.root),
                "--grades-csv",
                str(self.out / "grades.csv"),
                "--grade-histogram",
                str(self.out / "grade-histogram.json"),
                "--curated-dir",
                str(self.curated),
                "--corpus-resolver",
                str(self.resolver),
                "--no-validate",
                "--quiet",
            ]
        )
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
            refusal = self._run(
                [
                    sys.executable,
                    str(SYNC),
                    "--db",
                    str(self.db),
                    "--repo-root",
                    str(self.root),
                    "--dolt-dir",
                    str(self.dolt_dir),
                    "--grades-csv",
                    str(self.out / "blocked-grades.csv"),
                    "--grade-histogram",
                    str(self.out / "blocked-histogram.json"),
                    "--no-push",
                ],
                expected=1,
            )
            self.assertIn("sql-server", refusal.stdout)
            self.assertFalse((self.out / "blocked-grades.csv").exists())
        finally:
            server.terminate()
            server.wait(timeout=10)

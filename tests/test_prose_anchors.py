"""Regression gate for the frozen 6767-h prose anchors.

Run: python3 -m unittest tests.test_prose_anchors -v
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / "scripts" / "parse-prose-anchors.py"
CHECKER = ROOT / "scripts" / "check-prose-anchors.py"
DOC = ROOT / "000-docs" / "6767-h-SPEC-DR-STND-claude-code-extensions-master.md"
FIXTURES = ROOT / "tests" / "fixtures" / "prose-anchors"
EXPECTED = json.loads((FIXTURES / "expected-output.json").read_text(encoding="utf-8"))


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


class FrozenProseAnchorTests(unittest.TestCase):
    def test_live_document_matches_frozen_anchor_manifest(self) -> None:
        for args in ((), ("--doc", str(DOC))):
            with self.subTest(arguments=args):
                result = run_script(PARSER, *args)
                self.assertEqual(result.returncode, 0, result.stderr)

                parsed = json.loads(result.stdout)
                manifest = [
                    {key: section[key] for key in ("id", "title", "level")} for section in parsed["sections"]
                ]
                self.assertEqual(manifest, EXPECTED["anchor_manifest"])
                ids = [section["id"] for section in manifest]
                self.assertEqual(len(ids), 21)
                self.assertEqual(len(ids), len(set(ids)), "anchor IDs must be unique")
                self.assertEqual(parsed["doc_path"], str(DOC.relative_to(ROOT)))
                self.assertEqual(parsed["doc_sha256"], hashlib.sha256(DOC.read_bytes()).hexdigest())
                self.assertIsNotNone(datetime.fromisoformat(parsed["parsed_at"]).tzinfo)

    def test_valid_and_invalid_schema_fixtures(self) -> None:
        for fixture_name in ("valid_schema", "invalid_schema"):
            with self.subTest(fixture=fixture_name):
                fixture = EXPECTED[fixture_name]
                result = run_script(
                    CHECKER,
                    "--doc",
                    str(DOC),
                    "--schemas",
                    fixture["input"],
                    "--json",
                )
                self.assertEqual(result.returncode, fixture["expected_exit_code"], result.stderr)
                self.assertEqual(json.loads(result.stdout), fixture["expected_output"])

    def test_cited_heading_rename_fails_closed(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        replacements = {
            "### 3.1 YAML Frontmatter (Required)": "### 3.9 YAML Frontmatter (Required)",
            "### 4.3 Required Website Gates (Zero Warnings Policy)": (
                "### 4.9 Required Website Gates (Zero Warnings Policy)"
            ),
        }

        for original, replacement in replacements.items():
            with self.subTest(anchor=original.split()[1]), tempfile.TemporaryDirectory() as tmp:
                self.assertIn(original, source)
                changed_doc = Path(tmp) / DOC.name
                changed_doc.write_text(source.replace(original, replacement, 1), encoding="utf-8")
                result = run_script(
                    CHECKER,
                    "--doc",
                    str(changed_doc),
                    "--schemas",
                    "tests/fixtures/prose-anchors/valid-schema.json",
                    "--json",
                )
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(report["valid"])
                cited_ids = {finding["cited_id"] for finding in report["broken_anchors"]}
                self.assertIn(original.split()[1], cited_ids)

    def test_missing_document_and_malformed_schema_fail_closed(self) -> None:
        missing_doc = run_script(
            CHECKER,
            "--doc",
            "tests/fixtures/prose-anchors/missing.md",
            "--schemas",
            "tests/fixtures/prose-anchors/valid-schema.json",
            "--json",
        )
        self.assertEqual(missing_doc.returncode, 2)
        self.assertIn("--doc not found", missing_doc.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            malformed = Path(tmp) / "malformed.json"
            malformed.write_text("{not-json", encoding="utf-8")
            result = run_script(
                CHECKER,
                "--doc",
                str(DOC),
                "--schemas",
                str(malformed),
                "--json",
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["valid"])
            self.assertEqual(report["broken_anchors"][0]["cited_id"], "<parse-error>")

    def test_missing_and_malformed_index_fail_closed(self) -> None:
        missing_index = run_script(
            CHECKER,
            "--index",
            "tests/fixtures/prose-anchors/missing-index.json",
            "--schemas",
            "tests/fixtures/prose-anchors/valid-schema.json",
        )
        self.assertNotEqual(missing_index.returncode, 0)
        self.assertIn("--index not found", missing_index.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            malformed_index = Path(tmp) / "malformed-index.json"
            malformed_index.write_text("{not-json", encoding="utf-8")
            result = run_script(
                CHECKER,
                "--index",
                str(malformed_index),
                "--schemas",
                "tests/fixtures/prose-anchors/valid-schema.json",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR building index", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

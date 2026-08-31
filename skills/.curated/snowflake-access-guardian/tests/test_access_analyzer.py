#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from analyze_access import analyze  # noqa: E402

SCRIPT = HERE.parent / "scripts" / "analyze_access.py"


class AccessAnalyzerFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixtures/access.json").read_text())
        cls.report = analyze(cls.fixture, "ALICE", "ANALYTICS.CURATED.ORDERS", "SELECT")

    def test_finds_each_high_value_access_antipattern(self):
        categories = {item["category"] for item in self.report["findings"]}
        self.assertTrue({"direct-user-grant", "public-grant", "orphan-grantee"} <= categories)
        self.assertIn("future-grant-conflict", categories)
        self.assertIn("future-ownership", categories)

    def test_effective_path_contains_role_inheritance_and_secondary_context(self):
        access = self.report["effective_access"]
        self.assertEqual(access["status"], "OBJECT_PRIVILEGE_PATH_PROVEN")
        paths = {item["path"] for item in access["paths"]}
        self.assertIn("ALICE -> ANALYST -> DATA_READER", paths)
        self.assertIn("ALICE -> REPORTING", paths)
        primary_path = next(item for item in access["paths"] if item["path"] == "ALICE -> ANALYST -> DATA_READER")
        self.assertEqual(primary_path["active_role"], "ANALYST")
        self.assertFalse(primary_path["via_secondary_role"])
        self.assertTrue(any(item["via_secondary_role"] for item in access["paths"]))

    def test_read_only_and_hash_are_present(self):
        self.assertTrue(self.report["boundaries"]["read_only"])
        self.assertRegex(self.report["input_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("No GRANT", self.report["verification"]["change_packet"])
        self.assertEqual(self.report["verification"]["positive_proof"]["status"], "PROVEN")
        self.assertEqual(self.report["verification"]["negative_proof"]["status"], "PROVEN")
        self.assertEqual(self.report["evidence_scope"]["freshness"]["status"], "FRESH")

    def test_direct_and_ownership_paths_and_schema_precedence_are_explicit(self):
        direct = self.report["direct_user_paths"]
        self.assertTrue(any(row["grantee"] == "ALICE" for row in direct))
        ownership = self.report["ownership_paths"]
        self.assertTrue(any(row["object"].endswith("OLD_VIEW") for row in ownership))
        precedence = self.report["future_grant_precedence"]
        self.assertEqual(precedence[0]["effective_precedence"], "SCHEMA")

    def test_freshness_and_both_proof_receipts_are_required(self):
        data = json.loads(json.dumps(self.fixture))
        data.pop("metadata")
        data.pop("verification")
        report = analyze(data, "ALICE", "ANALYTICS.CURATED.ORDERS", "SELECT")
        categories = {item["category"] for item in report["findings"]}
        self.assertIn("evidence-freshness", categories)
        self.assertIn("access-proof-missing", categories)
        self.assertEqual(
            {item["id"] for item in report["findings"] if item["category"] == "access-proof-missing"},
            {"positive-access-proof-missing", "negative-access-proof-missing"},
        )

    def test_credential_fields_are_rejected(self):
        for field in (
            "password",
            "privateKey",
            "api_key",
            "SESSION_TOKEN",
            "jwt",
            "clientSecret",
            "secretAccessKey",
            "password_hash",
            "refreshTokenValue",
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyze({"users": [{"name": "X", field: "do-not-accept"}]})

    def test_credential_shaped_values_under_neutral_keys_are_rejected(self):
        for value in (
            "password=supersecret",
            "Authorization: Bearer abcdefghijklmnop",
            "-----BEGIN PRIVATE KEY-----",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze({"users": [{"name": "X", "note": value}]})

    def test_incomplete_grant_or_request_never_reports_allowed(self):
        data = {
            "users": [{"name": "U", "primary_role": "R"}],
            "roles": [{"name": "R"}],
            "grants": [{"grantee": "R", "object": "DB.S.T"}],
        }
        report = analyze(data, "U", "DB.S.T", "")
        self.assertEqual(report["effective_access"]["status"], "INCOMPLETE_REQUEST")
        self.assertIn("incomplete-grant", {item["category"] for item in report["findings"]})

    def test_direct_user_grant_is_independent_of_secondary_roles_context(self):
        base = {
            "users": [{"name": "U", "primary_role": "R"}],
            "roles": [{"name": "R"}],
            "grants": [
                {
                    "grantee": "U",
                    "grantee_type": "USER",
                    "object": "DB.S.T",
                    "privilege": "SELECT",
                }
            ],
        }
        for mode in ("NONE", "EXPLICIT", "ALL"):
            data = json.loads(json.dumps(base))
            data["users"][0]["secondary_roles_mode"] = mode
            with self.subTest(mode=mode):
                self.assertEqual(
                    analyze(data, "U", "DB.S.T", "SELECT")["effective_access"]["status"],
                    "OBJECT_PRIVILEGE_PATH_PROVEN",
                )

    def test_proof_receipts_must_match_requested_context_and_window(self):
        data = json.loads(json.dumps(self.fixture))
        data["verification"]["positive"][0]["principal"] = "BOB"
        data["verification"]["negative"][0]["observed_at"] = "2099-01-01T00:00:00Z"
        report = analyze(data, "ALICE", "ANALYTICS.CURATED.ORDERS", "SELECT")
        self.assertEqual(report["verification"]["positive_proof"]["status"], "NOT_PROVEN")
        self.assertEqual(report["verification"]["negative_proof"]["status"], "NOT_PROVEN")
        categories = {item["category"] for item in report["findings"]}
        self.assertIn("access-proof-context", categories)
        self.assertIn("access-proof-timestamp", categories)

        no_request = analyze(json.loads(json.dumps(self.fixture)))
        self.assertEqual(no_request["verification"]["positive_proof"]["status"], "NOT_PROVEN")
        self.assertEqual(no_request["verification"]["negative_proof"]["status"], "NOT_PROVEN")

    def test_future_or_misordered_freshness_never_passes(self):
        data = json.loads(json.dumps(self.fixture))
        data["metadata"]["collected_at"] = "2099-01-01T00:00:00Z"
        data["metadata"]["window_start"] = "2099-01-02T00:00:00Z"
        data["metadata"]["window_end"] = "2099-01-01T00:00:00Z"
        data["metadata"]["freshness"]["checked_at"] = "2099-01-03T00:00:00Z"
        report = analyze(data, "ALICE", "ANALYTICS.CURATED.ORDERS", "SELECT")
        self.assertIn("evidence-freshness", {item["category"] for item in report["findings"]})

    def test_malformed_collection_shapes_are_rejected(self):
        for data in (
            {"users": "not-a-list"},
            {"users": ["not-an-object"]},
            {"roles": [{"name": "R", "inherits": "PARENT"}]},
            {"users": [{"name": "U", "roles": {"R": True}}]},
            {"grants": [{"grantee": "R"}, "not-an-object"]},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                analyze(data)

    def test_cli_reports_malformed_shape_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"users":"not-a-list"}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("users must be an array", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

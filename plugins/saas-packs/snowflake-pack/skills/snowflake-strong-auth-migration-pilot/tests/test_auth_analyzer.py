#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from analyze_auth import analyze  # noqa: E402

SCRIPT = HERE.parent / "scripts" / "analyze_auth.py"


class AuthAnalyzerFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixtures/auth.json").read_text())
        cls.report = analyze(cls.fixture)

    def test_classifies_person_service_and_legacy_service(self):
        self.assertEqual(self.report["summary"]["persons"], 1)
        self.assertEqual(self.report["summary"]["services"], 1)
        self.assertEqual(self.report["summary"]["legacy_services"], 1)

    def test_prefers_wif_and_maps_mcp_session_controls(self):
        plans = {plan["workload"]: plan for plan in self.report["plans"]}
        self.assertEqual(plans["ETL_PROD"]["target_auth"], "WIF")
        self.assertEqual(plans["MCP_READ"]["target_auth"], "OAUTH")
        categories = {item["category"] for item in self.report["findings"]}
        self.assertIn("service-password", categories)
        self.assertIn("legacy-workload-auth", categories)

    def test_flags_unknown_identity_and_capability_gap(self):
        categories = {item["category"] for item in self.report["findings"]}
        self.assertIn("unknown-workload-identity", categories)
        self.assertIn("capability-evidence-gap", categories)

    def test_managed_mcp_models_default_role_and_secondary_role_controls(self):
        categories = {item["category"] for item in self.report["findings"]}
        self.assertNotIn("managed-mcp-role-mismatch", categories)
        unsafe = json.loads(json.dumps(self.fixture))
        unsafe["integrations"][0]["oauth_use_secondary_roles"] = "IMPLICIT"
        unsafe["users"][2]["default_role"] = "ACCOUNTADMIN"
        categories = {item["category"] for item in analyze(unsafe)["findings"]}
        self.assertIn("managed-mcp-secondary-roles", categories)
        self.assertIn("managed-mcp-role-mismatch", categories)
        receipt = self.report["managed_mcp_controls"][0]
        self.assertEqual(receipt["scope_location"], "ACCOUNT")
        self.assertEqual(receipt["allowed_roles"], ["MCP_READER"])
        self.assertEqual(receipt["secondary"], "NONE")

    def test_report_has_no_mutation_and_both_verification_directions(self):
        self.assertTrue(self.report["boundaries"]["read_only"])
        packet = self.report["cutover_packet"]
        self.assertTrue(packet["positive_verification"])
        self.assertTrue(packet["negative_verification"])
        self.assertIn("does not alter", packet["rollback"])
        self.assertFalse(self.report["boundaries"]["edit_authority"])
        self.assertTrue(self.report["inventory_receipt"]["read_only"])
        self.assertTrue(self.report["recovery_receipt"]["break_glass"]["verified"])

    def test_break_glass_canary_and_freshness_are_blocking_gates(self):
        data = json.loads(json.dumps(self.fixture))
        data.pop("metadata")
        data["break_glass"]["verified"] = False
        data["canary"]["negative"] = False
        categories = {item["category"] for item in analyze(data)["findings"]}
        self.assertIn("inventory-freshness", categories)
        self.assertIn("break-glass-unverified", categories)
        self.assertIn("canary-unverified", categories)

    def test_canary_false_boolean_cannot_be_overridden_by_status_alias(self):
        data = json.loads(json.dumps(self.fixture))
        data["canary"].update({"positive": False, "positive_status": "PASS", "negative": False, "negative_status": "DENIED"})
        categories = {item["category"] for item in analyze(data)["findings"]}
        self.assertIn("canary-unverified", categories)

    def test_future_proof_and_unordered_window_are_not_accepted(self):
        data = json.loads(json.dumps(self.fixture))
        data["break_glass"]["tested_at"] = "2099-01-01T00:00:00Z"
        data["canary"]["tested_at"] = "2099-01-01T00:00:00Z"
        data["metadata"]["window_start"] = data["metadata"]["window_end"]
        data["metadata"]["window_end"] = "2026-08-30T11:00:00Z"
        categories = {item["category"] for item in analyze(data)["findings"]}
        self.assertIn("inventory-freshness", categories)
        self.assertIn("break-glass-unverified", categories)
        self.assertIn("canary-unverified", categories)

        stale = json.loads(json.dumps(self.fixture))
        stale["break_glass"]["tested_at"] = "2026-08-29T11:46:00Z"
        stale["canary"]["tested_at"] = "2026-08-29T11:50:00Z"
        categories = {item["category"] for item in analyze(stale)["findings"]}
        self.assertIn("break-glass-unverified", categories)
        self.assertIn("canary-unverified", categories)

    def test_credential_fields_are_rejected(self):
        for field in (
            "access_token",
            "password",
            "clientSecret",
            "privateKey",
            "api_key",
            "credential",
            "token",
            "oauth_token",
            "session_token",
            "jwt",
            "passphrase",
            "authorization",
            "secretAccessKey",
            "refreshTokenValue",
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyze({"users": [{"name": "BAD", "type": "SERVICE", field: "never"}]})

    def test_credential_shaped_values_under_neutral_keys_are_rejected(self):
        for value in (
            "password=supersecret",
            "Authorization: Bearer abcdefghijklmnop",
            "-----BEGIN PRIVATE KEY-----",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze({"users": [{"name": "BAD", "type": "SERVICE", "note": value}]})

    def test_malformed_collection_shapes_are_bounded_input_errors(self):
        for data in (
            {"users": "not-a-list"},
            {"users": ["not-an-object"]},
            {"users": [{"name": "U", "auth_methods": "PASSWORD"}]},
            {"workloads": [{"name": "W", "supported_auth": {"WIF": True}}]},
            {
                "integrations": [
                    {
                        "name": "M",
                        "type": "MCP",
                        "oauth_scopes_supported": "session:role:R",
                    }
                ]
            },
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

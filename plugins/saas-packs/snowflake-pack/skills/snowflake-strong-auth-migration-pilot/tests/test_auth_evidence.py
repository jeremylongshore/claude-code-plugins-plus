from __future__ import annotations

import copy
import hashlib
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = load_module("snowflake_auth_evidence", SCRIPTS / "analyze_auth_evidence.py")
COLLECTOR = load_module("snowflake_auth_collector", SCRIPTS / "collect_snowflake_evidence.py")

USER_HASH = hashlib.sha256(b"ETL_SVC").hexdigest()
ACCOUNT_HASH = hashlib.sha256(b"ORG_ACCOUNT").hexdigest()
COLLECTOR_HASH = hashlib.sha256(b"AUTH_AUDITOR").hexdigest()
ROLE_HASH = hashlib.sha256(b"SECURITY_AUDITOR").hexdigest()
SECONDARY_HASH = hashlib.sha256(b'{"roles":"","value":"NONE"}').hexdigest()
EVENT_HASH = hashlib.sha256(b"login-event-1").hexdigest()


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def rehash(receipt: dict) -> None:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(COLLECTOR.canonical_json(body)).hexdigest()


class AuthEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluated = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=5)
        self.started = self.evaluated - timedelta(minutes=2)
        self.observed = self.evaluated - timedelta(minutes=1)
        self.completed = self.evaluated - timedelta(seconds=30)
        self.collected = self.evaluated - timedelta(seconds=20)
        self.event_time = self.observed - timedelta(hours=3)

    def context(self, role_hash: str = ROLE_HASH) -> dict:
        return {
            "_dataset": "execution_context",
            "observed_at": iso(self.observed),
            "account_identifier_sha256": ACCOUNT_HASH,
            "collector_user_sha256": COLLECTOR_HASH,
            "primary_role_sha256": role_hash,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": SECONDARY_HASH,
        }

    @staticmethod
    def user(dataset: str, digest: str = USER_HASH, *, password: bool = True) -> dict:
        row = {
            "_dataset": dataset,
            "user_name_sha256": digest,
            "created_on": "2026-01-01T00:00:00Z",
            "disabled": False,
            "type": "SERVICE",
            "has_password": password,
            "has_rsa_public_key": False,
            "has_mfa": False,
            "has_pat": False,
            "has_workload_identity": True,
        }
        if dataset == "current_users":
            row["metadata_visible"] = True
        return row

    def login(self, *, event_time: datetime | None = None, user_hash: str | None = USER_HASH) -> dict:
        return {
            "_dataset": "login_history",
            "auth_event_sha256": EVENT_HASH,
            "user_name_sha256": user_hash,
            "event_timestamp": iso(event_time or self.event_time),
            "event_type": "LOGIN",
            "first_authentication_factor": "WORKLOAD_IDENTITY_FEDERATION",
            "second_authentication_factor": None,
            "is_success": True,
            "reported_client_type_observation": "SNOWFLAKE_CLI",
            "error_code": None,
        }

    def receipt(
        self,
        surface: str,
        rows: list[dict],
        *,
        started: datetime | None = None,
        observed: datetime | None = None,
        completed: datetime | None = None,
        collected: datetime | None = None,
    ) -> dict:
        started = started or self.started
        observed = observed or self.observed
        completed = completed or self.completed
        collected = collected or self.collected
        adjusted = copy.deepcopy(rows)
        for row in adjusted:
            if row.get("_dataset") == "execution_context":
                row["observed_at"] = iso(observed)
        path, template, rendered, sources, selector = COLLECTOR.render_surface(surface)
        return COLLECTOR.build_receipt(
            surface,
            "auth-readonly",
            rendered,
            sources,
            raw=adjusted,
            collected_at=iso(collected),
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collection_started_at=iso(started),
            collection_completed_at=iso(completed),
        )

    def valid_bundle(self) -> dict:
        return {
            "schema_version": "2.0",
            "metadata": {
                "evaluated_at": iso(self.evaluated),
                "max_age_seconds": 3600,
                "connection_profile": "auth-readonly",
                "login_history_latency_seconds": 7200,
                "coverage": {"user_name_sha256": [USER_HASH]},
            },
            "collections": {
                "current": {"receipt": self.receipt("auth-current", [self.context(), self.user("current_users")])},
                "historical": {"receipt": self.receipt("auth", [self.context(), self.user("historical_users")])},
                "login_history": {"receipt": self.receipt("auth-login-history", [self.context(), self.login()])},
            },
            "users": [
                {
                    "name": "ETL_SVC",
                    "user_name_sha256": USER_HASH,
                    "type": "SERVICE",
                    "auth_methods": ["PASSWORD"],
                    "owner": "data-platform",
                }
            ],
            "workloads": [
                {
                    "name": "ETL_PROD",
                    "identity": "ETL_SVC",
                    "identity_sha256": USER_HASH,
                    "owner": "data-platform",
                    "current_auth": "PASSWORD",
                    "supported_auth": ["WIF", "KEY_PAIR"],
                    "roles": ["ETL_ROLE"],
                }
            ],
            "integrations": [],
            "enforcement_windows": [
                {
                    "name": "etl-pilot",
                    "workload": "ETL_PROD",
                    "identity_sha256": USER_HASH,
                    "target_auth": "WIF",
                    "start": iso(self.observed - timedelta(hours=4)),
                    "end": iso(self.observed - timedelta(hours=2, minutes=30)),
                    "owner": "data-platform",
                    "approved_by": "security-approver",
                    "change_id": "CHG-1001",
                }
            ],
        }

    @staticmethod
    def analyze_trusted(data: dict) -> dict:
        return ANALYZER.analyze_bundle(data, trusted_input_sha256=ANALYZER.input_sha256(data))

    def test_valid_receipts_support_scoped_evidence_but_not_cutover(self) -> None:
        report = self.analyze_trusted(self.valid_bundle())
        self.assertTrue(report["evidence_scope_complete"])
        self.assertFalse(report["completeness_claim_blocked"])
        self.assertEqual(report["current_historical_reconciliation"]["status"], "MATCHED_WITHIN_SCOPE")
        self.assertEqual(report["authorization_context"]["status"], "MATCHED_EQUIVALENT_CONTEXT")
        self.assertFalse(report["claims"]["cutover_ready"])
        self.assertFalse(report["cutover_approval"]["eligible"])
        self.assertFalse(report["safety"]["snowflake_mutations_executed"])

    def test_show_users_only_does_not_prove_migration(self) -> None:
        data = self.valid_bundle()
        data["collections"] = {"current": data["collections"]["current"]}
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertFalse(report["claims"]["history_reconciliation_supported"])
        self.assertIn("exactly current, historical, and login_history", " ".join(report["evidence_issues"]))

    def test_self_consistent_receipts_without_trusted_digest_are_untrusted(self) -> None:
        report = ANALYZER.analyze_bundle(self.valid_bundle())
        self.assertEqual(report["evidence_trust"]["status"], "UNTRUSTED")
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertTrue(all(not item["complete"] for item in report["receipt_assessments"]))

    def test_tamper_and_rehash_does_not_defeat_prior_trust_anchor(self) -> None:
        data = self.valid_bundle()
        trusted = ANALYZER.input_sha256(data)
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["historical_users"][0]["has_password"] = False
        rehash(receipt)
        report = ANALYZER.analyze_bundle(data, trusted_input_sha256=trusted)
        self.assertEqual(report["evidence_trust"]["status"], "DIGEST_MISMATCH")
        self.assertTrue(report["completeness_claim_blocked"])

    def test_stale_receipts_block_even_with_matching_digest(self) -> None:
        data = self.valid_bundle()
        for collection in data["collections"].values():
            receipt = collection["receipt"]
            receipt["collection_started_at"] = iso(self.evaluated - timedelta(hours=3, minutes=2))
            receipt["collection_completed_at"] = iso(self.evaluated - timedelta(hours=3, seconds=30))
            receipt["collected_at"] = iso(self.evaluated - timedelta(hours=3))
            receipt["datasets"]["execution_context"][0]["observed_at"] = iso(
                self.evaluated - timedelta(hours=3, minutes=1)
            )
            rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertTrue(any("max_age_seconds" in " ".join(item["issues"]) for item in report["receipt_assessments"]))

    def test_context_mismatch_blocks_cross_receipt_reconciliation(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["execution_context"][0]["primary_role_sha256"] = hashlib.sha256(b"OTHER_ROLE").hexdigest()
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(all(item["complete"] for item in report["receipt_assessments"]))
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertEqual(report["authorization_context"]["status"], "UNVERIFIED")

    def test_privilege_filtered_show_rows_block_completeness(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["current"]["receipt"]
        receipt["datasets"]["current_users"][0]["metadata_visible"] = False
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("privilege-filtered", " ".join(report["receipt_assessments"][0]["issues"]))

    def test_raw_identity_field_is_rejected_after_receipt_rehash(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["historical_users"][0]["name"] = "ETL_SVC"
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("privacy projection", " ".join(report["receipt_assessments"][1]["issues"]))

    def test_reviewed_sql_hash_tamper_is_rejected(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["login_history"]["receipt"]
        receipt["sql_sha256"] = "sha256:" + "0" * 64
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("reviewed SQL", " ".join(report["receipt_assessments"][2]["issues"]))

    def test_offline_current_receipt_is_rejected(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["current"]["receipt"]
        receipt["collection_mode"] = "offline-normalized"
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("live-cli", " ".join(report["receipt_assessments"][0]["issues"]))

    def test_current_historical_posture_drift_is_not_flattened(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["historical_users"][0]["has_password"] = False
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertEqual(report["current_historical_reconciliation"]["status"], "DRIFT_REQUIRES_REVIEW")
        self.assertEqual(report["current_historical_reconciliation"]["field_drift"][0]["field"], "has_password")
        self.assertTrue(report["completeness_claim_blocked"])

    def test_unsettled_login_event_is_rejected_as_history_proof(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["login_history"]["receipt"]
        receipt["datasets"]["login_history"][0]["event_timestamp"] = iso(self.observed - timedelta(minutes=30))
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("unsettled", " ".join(report["receipt_assessments"][2]["issues"]))

    def test_login_history_is_observation_not_operational_proof(self) -> None:
        report = self.analyze_trusted(self.valid_bundle())
        self.assertEqual(report["login_history_observation"]["status"], "OBSERVED")
        self.assertFalse(report["claims"]["canary_operational_proof_supported"])
        self.assertFalse(report["claims"]["recovery_proof_supported"])
        self.assertTrue(report["claims"]["account_wide_absence_claim_blocked"])

    def test_empty_settled_login_history_does_not_claim_absence(self) -> None:
        data = self.valid_bundle()
        data["collections"]["login_history"]["receipt"] = self.receipt("auth-login-history", [self.context()])
        report = self.analyze_trusted(data)
        self.assertTrue(report["evidence_scope_complete"])
        self.assertEqual(report["login_history_observation"]["status"], "NOT_OBSERVED")
        self.assertTrue(report["claims"]["account_wide_absence_claim_blocked"])

    def test_row_cap_blocks_even_when_receipt_is_self_consistent(self) -> None:
        data = self.valid_bundle()
        capped_rows = [self.context()]
        capped_rows.extend(
            self.user("current_users", hashlib.sha256(f"user-{index}".encode()).hexdigest()) for index in range(10000)
        )
        data["collections"]["current"]["receipt"] = self.receipt("auth-current", capped_rows)
        report = self.analyze_trusted(data)
        self.assertTrue(report["receipt_assessments"][0]["truncation_possible"])
        self.assertIn("reviewed row cap", " ".join(report["receipt_assessments"][0]["issues"]))
        self.assertTrue(report["completeness_claim_blocked"])

    def test_enforcement_window_latency_boundary_is_explicit(self) -> None:
        data = self.valid_bundle()
        cutoff = self.completed - timedelta(seconds=7200)
        data["enforcement_windows"][0]["end"] = iso(cutoff + timedelta(seconds=1))
        report = self.analyze_trusted(data)
        self.assertFalse(report["enforcement_window_assessment"]["windows"][0]["account_usage_settled"])
        data["enforcement_windows"][0]["end"] = iso(cutoff)
        report = self.analyze_trusted(data)
        self.assertTrue(report["enforcement_window_assessment"]["windows"][0]["account_usage_settled"])


if __name__ == "__main__":
    unittest.main()

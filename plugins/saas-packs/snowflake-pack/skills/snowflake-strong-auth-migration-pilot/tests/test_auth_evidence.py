from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import unittest
from contextlib import redirect_stderr
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

    def authorization_context(self, role_hash: str = ROLE_HASH) -> dict:
        context = self.context(role_hash)
        context.pop("_dataset")
        context.pop("observed_at")
        return context

    @staticmethod
    def user(
        dataset: str,
        digest: str = USER_HASH,
        *,
        password: bool | None = True,
        user_type: str = "LEGACY_SERVICE",
        principal_scope: str = "OPERATOR_OWNED",
    ) -> dict:
        row = {
            "_dataset": dataset,
            "user_name_sha256": digest,
            "created_on": "2026-01-01T00:00:00Z",
            "disabled": False,
            "type": user_type,
            "principal_scope": principal_scope,
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
                "authorization_context": self.authorization_context(),
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
                    "type": "LEGACY_SERVICE",
                    "auth_methods": ["PASSWORD", "WIF"],
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
        self.assertEqual(report["authorization_context"]["status"], "MATCHED_DECLARED_EQUIVALENT_CONTEXT")
        self.assertFalse(report["claims"]["cutover_ready"])
        self.assertFalse(report["cutover_approval"]["eligible"])
        self.assertFalse(report["safety"]["analyzer_snowflake_operations_executed"])
        self.assertFalse(report["safety"]["reviewed_collector_sql_mutating"])
        self.assertEqual(report["safety"]["external_mutation_attestation"], "NOT_CLAIMED")
        self.assertFalse(report["claims"]["target_capability_supported"])
        self.assertEqual(
            report["target_capability_assessment"]["status"],
            "OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        )

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
        self.assertFalse(report["receipt_assessments"][1]["complete"])
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertEqual(report["authorization_context"]["status"], "UNVERIFIED")

    def test_consistent_receipt_context_cannot_override_declared_context(self) -> None:
        data = self.valid_bundle()
        other = hashlib.sha256(b"OTHER_ROLE").hexdigest()
        for collection in data["collections"].values():
            receipt = collection["receipt"]
            receipt["datasets"]["execution_context"][0]["primary_role_sha256"] = other
            rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertTrue(
            all("metadata.authorization_context" in " ".join(item["issues"]) for item in report["receipt_assessments"])
        )

    def test_all_context_dimensions_are_bound_to_declared_context(self) -> None:
        replacements = {
            "account_identifier_sha256": hashlib.sha256(b"OTHER_ACCOUNT").hexdigest(),
            "collector_user_sha256": hashlib.sha256(b"OTHER_COLLECTOR").hexdigest(),
            "primary_role_sha256": hashlib.sha256(b"OTHER_ROLE").hexdigest(),
            "primary_role_type": "DATABASE_ROLE",
            "secondary_roles_sha256": hashlib.sha256(b"OTHER_SECONDARY").hexdigest(),
        }
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                data = self.valid_bundle()
                receipt = data["collections"]["current"]["receipt"]
                receipt["datasets"]["execution_context"][0][field] = replacement
                rehash(receipt)
                self.assertTrue(self.analyze_trusted(data)["completeness_claim_blocked"])

    def test_documented_application_instance_role_type_is_supported(self) -> None:
        data = self.valid_bundle()
        data["metadata"]["authorization_context"]["primary_role_type"] = "APPLICATION_INSTANCE"
        for collection in data["collections"].values():
            receipt = collection["receipt"]
            receipt["datasets"]["execution_context"][0]["primary_role_type"] = "APPLICATION_INSTANCE"
            rehash(receipt)
        self.assertTrue(self.analyze_trusted(data)["evidence_scope_complete"])

    def test_stale_observation_and_long_collection_interval_are_rejected(self) -> None:
        for mutation in ("stale observation", "long interval"):
            with self.subTest(mutation=mutation):
                data = self.valid_bundle()
                receipt = data["collections"]["current"]["receipt"]
                if mutation == "stale observation":
                    receipt["collection_started_at"] = iso(self.evaluated - timedelta(hours=2, minutes=1))
                    receipt["datasets"]["execution_context"][0]["observed_at"] = iso(
                        self.evaluated - timedelta(hours=2)
                    )
                else:
                    receipt["collection_started_at"] = iso(self.evaluated - timedelta(hours=2))
                rehash(receipt)
                report = self.analyze_trusted(data)
                self.assertTrue(report["completeness_claim_blocked"])
                self.assertIn("max_age_seconds", " ".join(report["receipt_assessments"][0]["issues"]))
                expected = (
                    "execution_context.observed_at exceeds"
                    if mutation == "stale observation"
                    else "collection interval exceeds"
                )
                self.assertIn(expected, " ".join(report["receipt_assessments"][0]["issues"]))

    def test_privilege_filtered_show_rows_block_completeness(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["current"]["receipt"]
        receipt["datasets"]["current_users"][0]["metadata_visible"] = False
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("privilege-filtered", " ".join(report["receipt_assessments"][0]["issues"]))

    def test_unknown_posture_and_operator_classification_drift_are_rejected(self) -> None:
        data = self.valid_bundle()
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            receipt["datasets"][dataset][0]["has_password"] = None
            rehash(receipt)
        self.assertTrue(self.analyze_trusted(data)["completeness_claim_blocked"])

        data = self.valid_bundle()
        data["users"][0]["type"] = "PERSON"
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("type does not match", " ".join(report["evidence_issues"]))

    def test_operator_auth_methods_and_workload_current_auth_bind_to_posture(self) -> None:
        data = self.valid_bundle()
        data["users"][0]["auth_methods"] = ["PASSWORD"]
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("WIF posture", " ".join(report["evidence_issues"]))

        data = self.valid_bundle()
        data["workloads"][0]["current_auth"] = "KEY_PAIR"
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("current_auth", " ".join(report["evidence_issues"]))

    def test_documented_service_nulls_are_known_non_applicable(self) -> None:
        for user_type in ("SERVICE", "SERVICE_AGENT"):
            with self.subTest(user_type=user_type):
                data = self.valid_bundle()
                current_receipt = data["collections"]["current"]["receipt"]
                current_row = current_receipt["datasets"]["current_users"][0]
                current_row["type"] = user_type
                current_row["has_password"] = False
                current_row["has_mfa"] = False
                rehash(current_receipt)

                historical_receipt = data["collections"]["historical"]["receipt"]
                historical_row = historical_receipt["datasets"]["historical_users"][0]
                historical_row["type"] = user_type
                historical_row["has_password"] = None
                historical_row["has_mfa"] = None
                rehash(historical_receipt)

                data["users"][0]["type"] = user_type
                data["users"][0]["auth_methods"] = ["WIF"]
                data["workloads"][0]["current_auth"] = "WIF"
                report = self.analyze_trusted(data)
                self.assertTrue(report["evidence_scope_complete"])
                self.assertEqual(report["current_historical_reconciliation"]["field_drift"], [])

    def test_mfa_enrollment_is_not_a_primary_auth_method(self) -> None:
        data = self.valid_bundle()
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            receipt["datasets"][dataset][0]["has_mfa"] = True
            rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["evidence_scope_complete"])
        self.assertNotIn("MFA posture", " ".join(report["evidence_issues"]))

    def test_snowflake_managed_principals_stay_in_cap_accounting_but_out_of_operator_scope(self) -> None:
        managed_hash = hashlib.sha256(b"SYSTEM_MANAGED").hexdigest()
        data = self.valid_bundle()
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            managed_row = self.user(
                dataset,
                managed_hash,
                password=None,
                user_type="SNOWFLAKE_SERVICE",
                principal_scope="SNOWFLAKE_MANAGED_EXCLUDED",
            )
            managed_row.pop("_dataset")
            receipt["datasets"][dataset].append(managed_row)
            receipt["dataset_row_counts"][dataset] += 1
            receipt["row_count"] += 1
            rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["evidence_scope_complete"])
        self.assertEqual(
            report["managed_principal_exclusions"],
            {
                "current": 1,
                "historical": 1,
                "non_claim": "Snowflake-managed principals remain in cap accounting but are excluded from the operator migration denominator.",
            },
        )

    def test_duplicate_workload_names_cannot_collapse_the_window_denominator(self) -> None:
        data = self.valid_bundle()
        data["workloads"].append(copy.deepcopy(data["workloads"][0]))
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("duplicates another workload", " ".join(report["evidence_issues"]))
        self.assertEqual(report["enforcement_window_assessment"]["status"], "INVALID")
        self.assertEqual(report["migration_plan"]["plans"], [])

    def test_raw_identity_field_is_rejected_after_receipt_rehash(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["historical_users"][0]["name"] = "ETL_SVC"
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("privacy projection", " ".join(report["receipt_assessments"][1]["issues"]))

    def test_unknown_receipt_fields_and_nonclaims_fail_closed(self) -> None:
        mutations = (
            ("unknown receipt field", lambda receipt: receipt.__setitem__("raw_user_name", "ETL_SVC")),
            (
                "nonclaim content",
                lambda receipt: receipt["non_claims"].__setitem__(0, "email=alice@example.com"),
            ),
            ("malformed errors", lambda receipt: receipt.__setitem__("errors", "")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                data = self.valid_bundle()
                receipt = data["collections"]["historical"]["receipt"]
                mutate(receipt)
                rehash(receipt)
                report = self.analyze_trusted(data)
                self.assertTrue(report["completeness_claim_blocked"])

    def test_credential_field_and_unsafe_profiles_are_rejected(self) -> None:
        data = self.valid_bundle()
        data["password"] = "hunter2"
        with self.assertRaises(ANALYZER.AuthEvidenceError):
            self.analyze_trusted(data)
        data = self.valid_bundle()
        data["metadata"]["connection_profile"] = "password=hunter2"
        with self.assertRaises(ANALYZER.AuthEvidenceError):
            self.analyze_trusted(data)
        data = self.valid_bundle()
        receipt = data["collections"]["current"]["receipt"]
        receipt["connection_profile"] = "password=hunter2"
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertNotIn("hunter2", str(report))

    def test_canary_and_break_glass_payloads_are_not_accepted_or_echoed(self) -> None:
        for field in ("canary", "break_glass"):
            with self.subTest(field=field):
                data = self.valid_bundle()
                data[field] = {"verified": True, "login_details": "alice@example.com from 203.0.113.9"}
                with self.assertRaises(ANALYZER.AuthEvidenceError):
                    self.analyze_trusted(data)

    def test_cli_error_output_sanitizes_credential_shaped_paths(self) -> None:
        stderr = io.StringIO()
        missing = HERE / "password=hunter2.json"
        with redirect_stderr(stderr):
            code = ANALYZER.main(["--input", str(missing)])
        self.assertEqual(code, 2)
        self.assertNotIn("hunter2", stderr.getvalue())
        self.assertIn("REDACTED", stderr.getvalue())

    def test_client_telemetry_is_not_part_of_the_receipt_schema(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["login_history"]["receipt"]
        receipt["datasets"]["login_history"][0]["reported_client_type_observation"] = "ALICE"
        rehash(receipt)
        self.assertTrue(self.analyze_trusted(data)["completeness_claim_blocked"])

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

    def test_recreated_same_name_user_is_identity_continuity_drift(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["historical"]["receipt"]
        receipt["datasets"]["historical_users"][0]["created_on"] = "2025-01-01T00:00:00Z"
        rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertEqual(report["current_historical_reconciliation"]["status"], "DRIFT_REQUIRES_REVIEW")
        self.assertEqual(report["current_historical_reconciliation"]["field_drift"][0]["field"], "created_on")
        self.assertTrue(report["completeness_claim_blocked"])

    def test_login_before_reconciled_principal_creation_is_not_attributed(self) -> None:
        data = self.valid_bundle()
        created_on = self.event_time + timedelta(minutes=15)
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            receipt["datasets"][dataset][0]["created_on"] = iso(created_on)
            rehash(receipt)
        report = self.analyze_trusted(data)
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertIn("predates", " ".join(report["evidence_issues"]))
        self.assertEqual(
            report["login_history_observation"]["status"],
            "UNRESOLVED_PREDECESSOR_OBSERVATION",
        )
        self.assertNotIn(USER_HASH, report["login_history_observation"]["by_user_name_sha256"])

    def test_service_agent_is_treated_as_an_operator_owned_service(self) -> None:
        data = self.valid_bundle()
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            receipt["datasets"][dataset][0]["type"] = "SERVICE_AGENT"
            receipt["datasets"][dataset][0]["has_password"] = None
            receipt["datasets"][dataset][0]["has_mfa"] = None
            rehash(receipt)
        data["users"][0]["type"] = "SERVICE_AGENT"
        data["users"][0]["auth_methods"] = ["WIF"]
        data["workloads"][0]["current_auth"] = "WIF"
        report = self.analyze_trusted(data)
        self.assertTrue(report["evidence_scope_complete"])
        self.assertEqual(report["migration_plan"]["summary"]["services"], 1)

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

    def test_unknown_login_success_is_not_counted_as_failure(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["login_history"]["receipt"]
        receipt["datasets"]["login_history"][0]["is_success"] = None
        rehash(receipt)
        report = self.analyze_trusted(data)
        counts = report["login_history_observation"]["by_user_name_sha256"][USER_HASH]
        self.assertEqual(counts, {"successful": 0, "failed": 0, "unknown": 1})
        self.assertTrue(report["evidence_scope_complete"])

    def test_current_wif_flag_does_not_certify_declared_target_capability(self) -> None:
        data = self.valid_bundle()
        data["users"][0]["auth_methods"] = ["PASSWORD"]
        for key, dataset in (("current", "current_users"), ("historical", "historical_users")):
            receipt = data["collections"][key]["receipt"]
            receipt["datasets"][dataset][0]["has_workload_identity"] = False
            rehash(receipt)
        report = self.analyze_trusted(data)
        capability = report["target_capability_assessment"]
        self.assertTrue(report["evidence_scope_complete"])
        self.assertFalse(report["claims"]["target_capability_supported"])
        self.assertFalse(capability["workloads"][0]["current_configuration_observation"])
        self.assertEqual(
            capability["workloads"][0]["capability_status"], "OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED"
        )

    def test_row_cap_blocks_every_auth_surface_even_when_receipt_is_self_consistent(self) -> None:
        cases = (
            ("current", "auth-current", "current_users", 0),
            ("historical", "auth", "historical_users", 1),
            ("login_history", "auth-login-history", "login_history", 2),
        )
        for key, surface, dataset, assessment_index in cases:
            with self.subTest(surface=surface):
                data = self.valid_bundle()
                capped_rows = [self.context()]
                for index in range(10000):
                    digest = hashlib.sha256(f"user-{index}".encode()).hexdigest()
                    if dataset == "login_history":
                        row = self.login(user_hash=digest)
                        row["auth_event_sha256"] = hashlib.sha256(f"event-{index}".encode()).hexdigest()
                    else:
                        row = self.user(
                            dataset,
                            digest,
                            password=None if index == 0 else True,
                            user_type="SNOWFLAKE_SERVICE" if index == 0 else "LEGACY_SERVICE",
                            principal_scope="SNOWFLAKE_MANAGED_EXCLUDED" if index == 0 else "OPERATOR_OWNED",
                        )
                    capped_rows.append(row)
                data["collections"][key]["receipt"] = self.receipt(surface, capped_rows)
                report = self.analyze_trusted(data)
                assessment = report["receipt_assessments"][assessment_index]
                self.assertTrue(assessment["truncation_possible"])
                self.assertIn("reviewed row cap", " ".join(assessment["issues"]))
                self.assertTrue(report["completeness_claim_blocked"])

    def test_enforcement_window_latency_boundary_is_explicit(self) -> None:
        data = self.valid_bundle()
        cutoff = self.observed - timedelta(seconds=7200)
        data["enforcement_windows"][0]["end"] = iso(cutoff + timedelta(seconds=1))
        report = self.analyze_trusted(data)
        self.assertFalse(report["enforcement_window_assessment"]["windows"][0]["account_usage_settled"])
        self.assertEqual(report["enforcement_window_assessment"]["status"], "INVALID")
        self.assertTrue(report["completeness_claim_blocked"])
        data["enforcement_windows"][0]["end"] = iso(cutoff)
        report = self.analyze_trusted(data)
        self.assertTrue(report["enforcement_window_assessment"]["windows"][0]["account_usage_settled"])
        self.assertEqual(report["enforcement_window_assessment"]["status"], "VALID")
        self.assertTrue(report["evidence_scope_complete"])

    def test_evaluation_clock_and_max_age_cannot_be_caller_extended(self) -> None:
        data = self.valid_bundle()
        data["metadata"]["evaluated_at"] = iso(datetime.now(timezone.utc) - timedelta(minutes=6))
        with self.assertRaises(ANALYZER.AuthEvidenceError):
            self.analyze_trusted(data)
        data = self.valid_bundle()
        data["metadata"]["max_age_seconds"] = 86400
        with self.assertRaises(ANALYZER.AuthEvidenceError):
            self.analyze_trusted(data)

    def test_exact_receipt_provenance_fields_and_timestamp_order_are_enforced(self) -> None:
        mutations = (
            ("template_sha256", lambda receipt: receipt.__setitem__("template_sha256", "sha256:" + "0" * 64)),
            (
                "rendered_sql_sha256",
                lambda receipt: receipt.__setitem__("rendered_sql_sha256", "sha256:" + "0" * 64),
            ),
            ("source_views", lambda receipt: receipt.__setitem__("source_views", ["SHOW SOMETHING ELSE"])),
            ("source_metadata", lambda receipt: receipt["source_metadata"].__setitem__("selector", {"x": True})),
            ("expected_datasets", lambda receipt: receipt.__setitem__("expected_datasets", ["current_users"])),
            ("dataset_row_counts", lambda receipt: receipt.__setitem__("dataset_row_counts", {})),
            ("row_count", lambda receipt: receipt.__setitem__("row_count", 999)),
            (
                "timestamp order",
                lambda receipt: receipt.__setitem__("collection_started_at", receipt["collection_completed_at"]),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                data = self.valid_bundle()
                receipt = data["collections"]["current"]["receipt"]
                mutate(receipt)
                if label == "timestamp order":
                    receipt["collection_completed_at"] = iso(self.started - timedelta(seconds=1))
                rehash(receipt)
                self.assertTrue(self.analyze_trusted(data)["completeness_claim_blocked"])

    def test_analyzer_has_no_snowflake_or_subprocess_execution_import(self) -> None:
        tree = ast.parse((SCRIPTS / "analyze_auth_evidence.py").read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue({"snowflake", "subprocess", "socket", "requests"}.isdisjoint(imported))


if __name__ == "__main__":
    unittest.main()

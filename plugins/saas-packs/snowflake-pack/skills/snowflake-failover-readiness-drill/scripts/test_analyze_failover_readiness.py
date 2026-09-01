from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("analyze_failover_readiness.py")
SPEC = importlib.util.spec_from_file_location("failover", MODULE)
assert SPEC and SPEC.loader
failover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(failover)
COLLECTOR_MODULE = Path(__file__).with_name("collect_snowflake_evidence.py")
COLLECTOR_SPEC = importlib.util.spec_from_file_location("failover_collector", COLLECTOR_MODULE)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
collector = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(collector)


def clean() -> dict:
    sql_path = MODULE.parent / "sql" / "replication.sql"
    receipt = {
        "schema_version": "1",
        "surface": "replication",
        "status": "collected",
        "collected_at": "2026-08-31T17:45:00Z",
        "connection_profile": "readonly-observer",
        "sql_sha256": "sha256:" + hashlib.sha256(sql_path.read_bytes()).hexdigest(),
        "source_views": ["SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_GROUP_REFRESH_HISTORY"],
        "row_count": 1,
        "row_limit": 1000,
        "truncation_possible": False,
        "datasets": {"replication_refresh_history": [{"replication_group_name": "DR", "phase_name": "COMPLETED"}]},
        "errors": [],
    }
    rehash(receipt)
    current_sql_path = MODULE.parent / "sql" / "replication-current.sql"
    current_hash = "sha256:" + hashlib.sha256(current_sql_path.read_bytes()).hexdigest()
    current_groups = [
        {
            "name": "DR",
            "type": "FAILOVER",
            "object_types": "DATABASES",
            "replication_schedule": "30 MINUTE",
            "secondary_state": "STARTED",
            "next_scheduled_refresh": "2026-08-31T18:00:00Z",
        }
    ]
    current_progress = [
        {
            "group_name": "DR",
            "group_type": "FAILOVER",
            "phase_name": "COMPLETED",
            "start_time": "2026-08-31T17:50:00Z",
            "end_time": "2026-08-31T17:55:00Z",
            "progress": 100,
        }
    ]
    current_receipt = {
        "schema_version": "1",
        "surface": "replication-current",
        "status": "collected",
        "collected_at": "2026-08-31T17:55:00Z",
        "connection_profile": "readonly-observer",
        "sql_sha256": current_hash,
        "template_sha256": current_hash,
        "rendered_sql_sha256": current_hash,
        "selector_fingerprint": None,
        "source_metadata": {
            "template": "replication-current.sql",
            "source_views": [
                "SHOW REPLICATION GROUPS",
                "INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL",
            ],
            "selector": {},
        },
        "source_views": [
            "SHOW REPLICATION GROUPS",
            "INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL",
        ],
        "row_count": 2,
        "row_limit": 1000,
        "truncation_possible": False,
        "dataset_row_limits": {"failover_groups": 1000, "replication_progress": 1000},
        "dataset_truncation_possible": {"failover_groups": False, "replication_progress": False},
        "datasets": {"failover_groups": current_groups, "replication_progress": current_progress},
        "errors": [],
        "non_claims": ["No Snowflake mutation was executed."],
    }
    rehash(current_receipt)
    return {
        "schema_version": "1",
        "as_of": "2026-08-31T18:00:00Z",
        "mode": "READ_ONLY_PREFLIGHT",
        "edition": "BUSINESS_CRITICAL",
        "objectives": {"rpo_minutes": 60, "rto_minutes": 30},
        "groups": [
            {
                "name": "DR",
                "kind": "FAILOVER",
                "role": "SECONDARY",
                "secondary_present": True,
                "suspended": False,
                "refresh_status": "SUCCEEDED",
                "last_successful_refresh_at": "2026-08-31T17:30:00Z",
                "scheduled_interval_minutes": 30,
            }
        ],
        "dependencies": [],
        "object_checks": [],
        "target_validations": [{"name": "orders", "status": "PASS"}],
        "client_redirect": {"tested": True},
        "privileges": {"observable": True, "missing": []},
        "history": {"account_usage_collected_at": "2026-08-31T17:45:00Z", "detailed_window_days": 14},
        "current_state": {
            "status": "collected",
            "observed_at": "2026-08-31T17:55:00Z",
            "max_age_minutes": 30,
            "groups": [dict(row) for row in current_groups],
            "progress": [dict(row) for row in current_progress],
        },
        "collector_receipt": receipt,
        "current_state_receipt": current_receipt,
        "drill_events": [],
    }


def rehash(receipt: dict) -> None:
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
    )


def rehash_event(event: dict) -> None:
    unsigned = dict(event)
    unsigned.pop("receipt_sha256", None)
    event["receipt_sha256"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
    )


class FailoverTests(unittest.TestCase):
    def test_bundled_current_collector_receipt_is_accepted(self):
        data = clean()
        path, template_sql, rendered_sql, sources, selector = collector.render_surface("replication-current")
        raw = [
            {"EVIDENCE": {"_dataset": "failover_groups", **data["current_state"]["groups"][0]}},
            {"EVIDENCE": {"_dataset": "replication_progress", **data["current_state"]["progress"][0]}},
        ]
        receipt = collector.build_receipt(
            "replication-current",
            "readonly-observer",
            rendered_sql,
            sources,
            raw=raw,
            collected_at=data["current_state"]["observed_at"],
            template_sql=template_sql,
            template_path=path,
            selector=selector,
        )
        data["current_state_receipt"] = receipt
        data["current_state"]["groups"] = receipt["datasets"]["failover_groups"]
        data["current_state"]["progress"] = receipt["datasets"]["replication_progress"]
        self.assertEqual(failover.analyze(data)["status"], "READY_FOR_OPERATOR_DRILL")

    def test_clean_preflight_is_not_execution_claim(self):
        report = failover.analyze(clean())
        self.assertEqual(report["status"], "READY_FOR_OPERATOR_DRILL")
        self.assertEqual(report["findings"], [])

    def test_readiness_defects_are_classified(self):
        data = clean()
        data["edition"] = "STANDARD"
        data["groups"][0].update(
            {
                "kind": "REPLICATION",
                "secondary_present": False,
                "suspended": True,
                "refresh_status": "FAILED",
                "last_successful_refresh_at": "2026-08-31T15:00:00Z",
                "scheduled_interval_minutes": 120,
            }
        )
        data["dependencies"] = [{"from_group": "DR", "to_group": "MISSING", "status": "DANGLING"}]
        data["object_checks"] = [
            {
                "object": "TASK_A",
                "task_stream_split": True,
                "task_owner_valid": False,
                "stream_state": "STALE",
                "dynamic_table_reinitialize": True,
            }
        ]
        data["target_validations"] = [{"name": "orders", "status": "FAIL"}]
        data["privileges"]["missing"] = ["USAGE:ROLE_DR"]
        codes = {row["code"] for row in failover.analyze(data)["findings"]}
        self.assertTrue(
            {
                "EDITION_UNAVAILABLE",
                "GROUP_NOT_FAILOVER_CAPABLE",
                "SECONDARY_MISSING",
                "GROUP_SUSPENDED",
                "REFRESH_FAILED",
                "RPO_BREACH",
                "SCHEDULE_OVERRUN",
                "DANGLING_REFERENCE",
                "TASK_STREAM_SPLIT",
                "TASK_OWNER_INVALID",
                "STREAM_STALE",
                "DYNAMIC_TABLE_REINITIALIZATION",
                "TARGET_VALIDATION_FAILED",
                "PRIVILEGE_GAP",
            }.issubset(codes)
        )

    def test_operator_failover_and_failback_receipt(self):
        data = clean()
        data["mode"] = "OPERATOR_EXECUTED_FAILOVER_AND_FAILBACK"
        data["drill_events"] = [
            {
                "event": "FAILOVER",
                "status": "SUCCEEDED",
                "operator_approved": True,
                "duration_minutes": 15,
                "observed_at": "2026-08-31T17:45:00Z",
            },
            {
                "event": "FAILBACK",
                "status": "SUCCEEDED",
                "operator_approved": True,
                "observed_at": "2026-08-31T17:55:00Z",
            },
        ]
        for event in data["drill_events"]:
            rehash_event(event)
        self.assertEqual(failover.analyze(data)["status"], "DRILL_VERIFIED")

        data["drill_events"][0]["observed_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "cannot be in the future"):
            failover.analyze(data)

    def test_missing_and_stale_evidence_is_inconclusive(self):
        data = clean()
        data["objectives"].pop("rpo_minutes")
        data["history"]["account_usage_collected_at"] = "2026-08-31T12:00:00Z"
        data["target_validations"] = []
        report = failover.analyze(data)
        self.assertEqual(report["status"], "INCONCLUSIVE")
        self.assertTrue(
            {"RPO_UNEVALUATED", "HISTORY_STALE", "TARGET_VALIDATION_MISSING"}.issubset(
                {x["code"] for x in report["findings"]}
            )
        )

    def test_sensitive_evidence_is_rejected(self):
        for key, value in (("password", "x"), ("sql_text", "select 1"), ("raw_rows", [])):
            data = clean()
            data[key] = value
            with self.assertRaisesRegex(ValueError, "sensitive field"):
                failover.analyze(data)
        data = clean()
        data["note"] = "https://x.test/file?X-Amz-Signature=abc"
        with self.assertRaisesRegex(ValueError, "presigned URL"):
            failover.analyze(data)

        data = clean()
        data["operator_email"] = "operator@example.com"
        with self.assertRaisesRegex(ValueError, "PII-like value"):
            failover.analyze(data)

    def test_future_as_of_and_refresh_receipts_are_rejected(self):
        data = clean()
        data["as_of"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "as_of cannot be in the future"):
            failover.analyze(data)
        data = clean()
        data["groups"][0]["last_successful_refresh_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "cannot be in the future"):
            failover.analyze(data)

    def test_truncated_replication_receipt_blocks_readiness(self):
        data = clean()
        data["collector_receipt"]["row_count"] = 1000
        data["collector_receipt"]["truncation_possible"] = True
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("REPLICATION_RECEIPT_TRUNCATED", {row["code"] for row in report["findings"]})

    def test_error_or_tampered_replication_receipt_blocks_readiness(self):
        data = clean()
        data["collector_receipt"]["status"] = "error"
        data["collector_receipt"]["errors"] = [{"code": "SNOW_CLI_FAILED", "message": "password=do-not-emit"}]
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("REPLICATION_RECEIPT_ERROR", {row["code"] for row in report["findings"]})
        self.assertNotIn("do-not-emit", json.dumps(report))

        data = clean()
        data["collector_receipt"]["row_count"] = 2
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("REPLICATION_RECEIPT_UNVERIFIABLE", {row["code"] for row in report["findings"]})

    def test_missing_replication_receipt_blocks_readiness(self):
        data = clean()
        data.pop("collector_receipt")
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("REPLICATION_RECEIPT_UNVERIFIABLE", {row["code"] for row in report["findings"]})

    def test_missing_group_history_and_wrong_reviewed_sql_never_pass(self):
        data = clean()
        data["collector_receipt"]["datasets"] = {}
        data["collector_receipt"]["row_count"] = 0
        rehash(data["collector_receipt"])
        report = failover.analyze(data)
        self.assertEqual(report["status"], "INCONCLUSIVE")
        self.assertIn("HISTORY_MISSING", {row["code"] for row in report["findings"]})

        data = clean()
        data["collector_receipt"]["sql_sha256"] = "sha256:" + "a" * 64
        rehash(data["collector_receipt"])
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("REPLICATION_RECEIPT_UNVERIFIABLE", {row["code"] for row in report["findings"]})

    def test_receipt_is_deterministic(self):
        self.assertEqual(failover.analyze(clean()), failover.analyze(clean()))

    def test_current_group_state_freshness_and_progress_are_required(self):
        data = clean()
        data["current_state"]["observed_at"] = "2026-08-31T12:00:00Z"
        data["current_state_receipt"]["collected_at"] = "2026-08-31T12:00:00Z"
        data["current_state"]["progress"] = []
        data["current_state_receipt"]["datasets"]["replication_progress"] = []
        data["current_state_receipt"]["row_count"] = 1
        rehash(data["current_state_receipt"])
        report = failover.analyze(data)
        codes = {row["code"] for row in report["findings"]}
        self.assertTrue({"CURRENT_STATE_RECEIPT_STALE", "GROUP_PROGRESS_MISSING"} <= codes)
        self.assertEqual(report["status"], "NOT_READY")

    def test_current_state_receipt_is_required_and_payload_bound(self):
        data = clean()
        data.pop("current_state_receipt")
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("CURRENT_STATE_RECEIPT_UNVERIFIABLE", {row["code"] for row in report["findings"]})

        data = clean()
        data["current_state"]["groups"][0]["secondary_state"] = "SUSPENDED"
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("CURRENT_STATE_PAYLOAD_MISMATCH", {row["code"] for row in report["findings"]})

    def test_current_state_receipt_exact_contract_is_fail_closed(self):
        mutations = (
            ("schema", lambda value: value.update(schema_version="2")),
            ("surface", lambda value: value.update(surface="replication")),
            ("status", lambda value: value.update(status="error")),
            ("errors", lambda value: value.update(errors=[{"code": "DENIED"}])),
            ("source", lambda value: value.update(source_views=["SHOW FAILOVER GROUPS"])),
            ("metadata", lambda value: value["source_metadata"].update(template="other.sql")),
            ("sql hash", lambda value: value.update(sql_sha256="sha256:" + "0" * 64)),
            ("template hash", lambda value: value.update(template_sha256="sha256:" + "0" * 64)),
            ("rendered hash", lambda value: value.update(rendered_sql_sha256="sha256:" + "0" * 64)),
            ("row count", lambda value: value.update(row_count=3)),
            ("cap", lambda value: value.update(row_limit=999)),
            ("dataset caps", lambda value: value.update(dataset_row_limits={"failover_groups": 999})),
            ("dataset", lambda value: value["datasets"].update(unexpected=[])),
            ("schema field", lambda value: value.update(unexpected="value")),
            ("projected field", lambda value: value["datasets"]["failover_groups"][0].update(extra="value")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                data = clean()
                mutate(data["current_state_receipt"])
                rehash(data["current_state_receipt"])
                report = failover.analyze(data)
                self.assertEqual(report["status"], "NOT_READY")
                self.assertIn(
                    "CURRENT_STATE_RECEIPT_UNVERIFIABLE",
                    {row["code"] for row in report["findings"]},
                )

    def test_current_state_receipt_tampering_and_truncation_block(self):
        data = clean()
        data["current_state_receipt"]["datasets"]["replication_progress"][0]["progress"] = 50
        report = failover.analyze(data)
        codes = {row["code"] for row in report["findings"]}
        self.assertEqual(report["status"], "NOT_READY")
        self.assertTrue({"CURRENT_STATE_RECEIPT_UNVERIFIABLE", "CURRENT_STATE_PAYLOAD_MISMATCH"} <= codes)

        data = clean()
        data["current_state_receipt"]["truncation_possible"] = True
        data["current_state_receipt"]["dataset_truncation_possible"]["failover_groups"] = True
        rehash(data["current_state_receipt"])
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("CURRENT_STATE_RECEIPT_TRUNCATED", {row["code"] for row in report["findings"]})

        data = clean()
        data["current_state"]["max_age_minutes"] = 31
        report = failover.analyze(data)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertIn("CURRENT_STATE_PAYLOAD_MISMATCH", {row["code"] for row in report["findings"]})

    def test_details_and_account_endpoints_are_rejected(self):
        for key in (
            "details",
            "account_endpoint",
            "account_url",
            "account_locator",
            "account_name",
            "allowed_accounts",
            "endpoint",
            "hostname",
        ):
            with self.subTest(key=key):
                data = clean()
                data["current_state"][key] = "redacted-value"
                with self.assertRaisesRegex(ValueError, "details/account endpoint"):
                    failover.analyze(data)
                with self.assertRaisesRegex(collector.CollectionError, "credential-bearing field"):
                    collector.normalize_cli_json([{"EVIDENCE": {"_dataset": "failover_groups", key: "value"}}])

    def test_operator_drill_receipt_hash_is_required_and_verified(self):
        data = clean()
        data["mode"] = "OPERATOR_EXECUTED_FAILOVER"
        data["drill_events"] = [
            {
                "event": "FAILOVER",
                "status": "SUCCEEDED",
                "operator_approved": True,
                "duration_minutes": 15,
                "observed_at": "2026-08-31T17:45:00Z",
            }
        ]
        report = failover.analyze(data)
        self.assertIn("DRILL_RECEIPT_UNVERIFIABLE", {row["code"] for row in report["findings"]})
        rehash_event(data["drill_events"][0])
        self.assertNotIn("DRILL_RECEIPT_UNVERIFIABLE", {row["code"] for row in failover.analyze(data)["findings"]})


if __name__ == "__main__":
    unittest.main()

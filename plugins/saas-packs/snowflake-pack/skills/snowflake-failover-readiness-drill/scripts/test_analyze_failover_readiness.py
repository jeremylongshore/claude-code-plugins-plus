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
            "groups": [
                {
                    "name": "DR",
                    "refresh_status": "SUCCEEDED",
                    "progress_status": "COMPLETED",
                    "scheduled_interval_minutes": 30,
                }
            ],
        },
        "collector_receipt": receipt,
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
    event["receipt_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


class FailoverTests(unittest.TestCase):
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
        data["current_state"]["groups"][0]["progress_status"] = "UNKNOWN"
        report = failover.analyze(data)
        codes = {row["code"] for row in report["findings"]}
        self.assertTrue({"CURRENT_STATE_STALE", "GROUP_PROGRESS_MISSING"} <= codes)
        self.assertEqual(report["status"], "INCONCLUSIVE")

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

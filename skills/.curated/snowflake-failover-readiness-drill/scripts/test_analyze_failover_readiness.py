from __future__ import annotations

import ast
import copy
import importlib.util
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE = Path(__file__).with_name("analyze_failover_readiness.py")
SPEC = importlib.util.spec_from_file_location("failover_v3", MODULE)
assert SPEC and SPEC.loader
failover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(failover)
COLLECTOR_MODULE = MODULE.with_name("collect_snowflake_evidence.py")
COLLECTOR_SPEC = importlib.util.spec_from_file_location("failover_collector", COLLECTOR_MODULE)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
collector = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(collector)

AT = "2026-09-04T01:00:00Z"
SOURCE_ACCOUNT = "a" * 64
TARGET_ACCOUNT = "b" * 64
SOURCE_GROUP = "c" * 64
TARGET_GROUP = "d" * 64
LINEAGE = "e" * 64
OBJECT_TYPES = "f" * 64
ALLOWED_ACCOUNTS = "1" * 64
SCHEDULE = "2" * 64
VALIDATION = "3" * 64
INTEGRATION_TYPES = "4" * 64


def iso(minutes: int, seconds: int = 0) -> str:
    value = datetime(2026, 9, 4, 1, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes, seconds=seconds)
    return value.isoformat().replace("+00:00", "Z")


def seal(value: dict) -> dict:
    body = dict(value)
    body.pop("receipt_sha256", None)
    value["receipt_sha256"] = failover.digest(body)
    return value


def current_group(account: str, group: str, primary: bool) -> dict:
    return {
        "local_account_key_sha256": account,
        "local_group_key_sha256": group,
        "lineage_group_key_sha256": LINEAGE,
        "group_type": "FAILOVER",
        "is_primary": primary,
        "object_types_sha256": OBJECT_TYPES,
        "allowed_accounts_sha256": ALLOWED_ACCOUNTS,
        "allowed_integration_types_sha256": INTEGRATION_TYPES,
        "replication_schedule_sha256": SCHEDULE,
        "schedule_status": "STARTED",
        "next_scheduled_refresh": iso(5),
    }


def collector_receipt(
    surface: str, account: str, rows: list[dict], *, at: str = iso(-1), selected: str | None = None
) -> dict:
    contract = failover.CONTRACTS[surface]
    started_at = (failover.parse_time(at) - timedelta(seconds=5)).isoformat().replace("+00:00", "Z")
    context = {
        "observed_at": at,
        "organization_name_sha256": "5" * 64,
        "account_identifier_sha256": account,
        "collector_user_sha256": "6" * 64,
        "primary_role_sha256": "7" * 64,
        "primary_role_type": "ROLE",
        "secondary_roles_sha256": "8" * 64,
        "timezone": "UTC",
        "source_row_count": len(rows),
        "source_row_limit": 5000,
        "truncation_possible": False,
    }
    render_kwargs = {}
    if surface in {"replication", "replication-progress"}:
        render_kwargs = {"window_start": iso(-60), "window_end": started_at}
        context |= {
            "window_start_utc": render_kwargs["window_start"],
            "window_end_utc": render_kwargs["window_end"],
            "window_semantics": "HALF_OPEN_UTC",
            "provider_retention_days": 14,
        }
    if surface == "replication-dangling":
        assert selected
        render_kwargs = {"replication_group": "DR_GROUP"}
        context |= {"selected_group_key_sha256": selected, "evaluation_scope": "CALLING_ACCOUNT_ONLY"}
    path, template, rendered, sources, selector = collector.render_surface(surface, **render_kwargs)
    raw = [{"EVIDENCE": {"_dataset": "execution_context", **context}}]
    raw.extend({"EVIDENCE": {"_dataset": contract["data"], **copy.deepcopy(row)}} for row in rows)
    return collector.build_receipt(
        surface,
        "readonly",
        rendered,
        sources,
        raw=raw,
        collected_at=at,
        template_sql=template,
        template_path=path,
        selector=selector,
        collection_mode="live-cli",
        collection_started_at=started_at,
        collection_completed_at=at,
    )


def history(
    phase: str = "COMPLETED",
    snapshot: str | None = iso(-60),
    start: str = iso(-10),
    job: str = "a" * 64,
    group: str = TARGET_GROUP,
) -> dict:
    return {
        "group_key_sha256": group,
        "group_type": "FAILOVER",
        "phase_name": phase,
        "start_time": start,
        "end_time": start if phase in {"COMPLETED", "FAILED", "CANCELED"} else None,
        "job_key_sha256": job,
        "primary_snapshot_timestamp": snapshot,
        "error_code": "1234" if phase == "FAILED" else None,
    }


def progress(phase: str = "COMPLETED", *, start: str = iso(-9), group: str = TARGET_GROUP) -> dict:
    return {
        "group_key_sha256": group,
        "group_type": "FAILOVER",
        "phase_name": phase,
        "start_time": start,
        "end_time": None,
        "progress": None if phase == "COMPLETED" else "50",
        "primary_snapshot_epoch": None,
        "error_code": None,
    }


def validation(stage: str = "PRE_FAILOVER", key: str = VALIDATION, at: str = iso(-2), status: str = "PASS") -> dict:
    return seal(
        {
            "schema_version": "1",
            "validation_key_sha256": key,
            "lineage_group_key_sha256": LINEAGE,
            "stage": stage,
            "observed_at": at,
            "status": status,
        }
    )


def base() -> dict:
    policy = {
        "schema_version": "1",
        "analysis_as_of_utc": AT,
        "mode": "PREFLIGHT",
        "validation_max_age_seconds": 900,
        "expected_group_count": 1,
        "groups": [
            {
                "lineage_group_key_sha256": LINEAGE,
                "source_account_key_sha256": SOURCE_ACCOUNT,
                "source_group_key_sha256": SOURCE_GROUP,
                "target_account_key_sha256": TARGET_ACCOUNT,
                "target_group_key_sha256": TARGET_GROUP,
                "expected_object_types_sha256": OBJECT_TYPES,
                "expected_allowed_accounts_sha256": ALLOWED_ACCOUNTS,
                "expected_allowed_integration_types_sha256": INTEGRATION_TYPES,
                "expected_replication_schedule_sha256": SCHEDULE,
                "rpo_seconds": 3600,
                "rto_seconds": 120,
            }
        ],
        "expected_dependency_count": 0,
        "dependencies": [],
        "expected_validation_count": 1,
        "validations": [
            {"validation_key_sha256": VALIDATION, "lineage_group_key_sha256": LINEAGE, "stage": "PRE_FAILOVER"}
        ],
    }
    receipts = [
        collector_receipt("replication-current", SOURCE_ACCOUNT, [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, True)]),
        collector_receipt("replication-current", TARGET_ACCOUNT, [current_group(TARGET_ACCOUNT, TARGET_GROUP, False)]),
        collector_receipt("replication", TARGET_ACCOUNT, [history()]),
        collector_receipt("replication-progress", TARGET_ACCOUNT, [progress()]),
        collector_receipt("replication-dangling", SOURCE_ACCOUNT, [], selected=SOURCE_GROUP),
        collector_receipt("replication-dangling", TARGET_ACCOUNT, [], selected=TARGET_GROUP),
    ]
    return {
        "schema_version": "2",
        "policy": policy,
        "collector_receipts": receipts,
        "operator_receipts": [],
        "validation_receipts": [validation()],
    }


def trusted(data: dict) -> dict:
    return {
        "evaluated_at": AT,
        "trusted_input_sha256": failover.canonical_input_digest(data),
        "trusted_policy_sha256": failover.canonical_policy_digest(data),
        "trusted_operator_sha256": failover.canonical_operator_digest(data),
    }


def analyze(data: dict) -> dict:
    return failover.analyze(data, **trusted(data))


def reseal_collector(receipt: dict) -> None:
    contract = failover.CONTRACTS[receipt["surface"]]
    receipt["datasets"]["execution_context"][0]["source_row_count"] = len(receipt["datasets"][contract["data"]])
    receipt["dataset_row_counts"] = {name: len(rows) for name, rows in receipt["datasets"].items()}
    receipt["row_count"] = sum(receipt["dataset_row_counts"].values())
    receipt["result_sha256"] = failover.digest(receipt["datasets"])
    seal(receipt)


class FailoverV3Tests(unittest.TestCase):
    def test_trusted_complete_preflight_is_ready(self):
        report = analyze(base())
        self.assertEqual(report["overall_status"], "READY_FOR_OPERATOR_DRILL_AS_OF")
        self.assertEqual(report["findings"], [])
        self.assertEqual(
            report["temporal_qualification"],
            {
                "basis": "AS_OF_ONLY",
                "analysis_as_of_utc": AT,
                "evidence_observed_from_utc": iso(-2),
                "evidence_observed_through_utc": iso(-1),
                "valid_until_utc": AT,
            },
        )

    def test_external_trust_rejects_self_rehashed_tampering(self):
        data = base()
        original = trusted(data)
        receipt = data["collector_receipts"][2]
        receipt["datasets"]["replication_refresh_history"][0]["primary_snapshot_timestamp"] = iso(-1)
        reseal_collector(receipt)
        report = failover.analyze(data, **original)
        self.assertEqual(report["overall_status"], "INCONCLUSIVE")
        self.assertIn("trusted_input_mismatch", report["integrity_issue_codes"])

    def test_missing_schema_and_stale_receipt_fail_closed(self):
        data = base()
        data.pop("schema_version")
        with self.assertRaises(failover.EvidenceError):
            analyze(data)
        data = base()
        data["collector_receipts"][0]["collected_at"] = iso(-16)
        data["collector_receipts"][0]["collection_completed_at"] = iso(-16)
        seal(data["collector_receipts"][0])
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

    def test_current_state_uses_statement_observation_not_collection_completion(self):
        receipt = collector_receipt(
            "replication-current",
            SOURCE_ACCOUNT,
            [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, True)],
            at=iso(-6),
        )
        receipt["collection_started_at"] = iso(-8)
        receipt["datasets"]["execution_context"][0]["observed_at"] = iso(-7, -30)
        reseal_collector(receipt)
        self.assertEqual(failover.receipt_issues(receipt, failover.parse_time(AT)), [])
        self.assertIsNone(
            failover.current_row(
                [receipt],
                SOURCE_ACCOUNT,
                SOURCE_GROUP,
                after=failover.parse_time(iso(-7)),
            )
        )

    def test_rpo_exact_boundary_and_one_second_breach(self):
        data = base()
        self.assertEqual(analyze(data)["rpo_results"][0]["status"], "PASS")
        row = data["collector_receipts"][2]["datasets"]["replication_refresh_history"][0]
        row["primary_snapshot_timestamp"] = iso(-60, -1)
        reseal_collector(data["collector_receipts"][2])
        report = analyze(data)
        self.assertEqual(report["overall_status"], "NOT_READY")
        self.assertIn("RPO_BREACH", {item["code"] for item in report["findings"]})

    def test_latest_failed_refresh_and_incomplete_progress_block(self):
        data = base()
        receipt = data["collector_receipts"][2]
        receipt["datasets"]["replication_refresh_history"].append(history("FAILED", iso(-2), iso(-2), "b" * 64))
        reseal_collector(receipt)
        progress_receipt = data["collector_receipts"][3]
        progress_receipt["datasets"]["replication_progress"][0] = progress("PRIMARY_UPLOADING_DATA")
        reseal_collector(progress_receipt)
        codes = {row["code"] for row in analyze(data)["findings"]}
        self.assertIn("LATEST_REFRESH_NOT_PROVEN_COMPLETE", codes)
        self.assertIn("REFRESH_PROGRESS_NOT_COMPLETE", codes)

        contradictory = base()
        history_receipt = contradictory["collector_receipts"][2]
        history_receipt["datasets"]["replication_refresh_history"].append(
            history("PRIMARY_UPLOADING_DATA", None, iso(-2), "a" * 64)
        )
        reseal_collector(history_receipt)
        contradictory_report = analyze(contradictory)
        self.assertEqual(contradictory_report["overall_status"], "INCONCLUSIVE")
        self.assertEqual(contradictory_report["integrity_issue_codes"], ["row_natural_key_duplicate"])

    def test_tied_latest_jobs_and_overdue_schedule_block(self):
        data = base()
        receipt = data["collector_receipts"][2]
        receipt["datasets"]["replication_refresh_history"].append(history("FAILED", iso(-2), iso(-10), "b" * 64))
        reseal_collector(receipt)
        target = data["collector_receipts"][1]
        target["datasets"]["current_groups"][0]["next_scheduled_refresh"] = iso(-1)
        reseal_collector(target)
        report = analyze(data)
        codes = {row["code"] for row in report["findings"]}
        self.assertEqual(report["overall_status"], "NOT_READY")
        self.assertIn("LATEST_REFRESH_NOT_PROVEN_COMPLETE", codes)
        self.assertIn("SCHEDULE_NOT_RUNNING", codes)

    def test_schedule_and_dangling_reference_block(self):
        data = base()
        row = data["collector_receipts"][0]["datasets"]["current_groups"][0]
        row["replication_schedule_sha256"] = None
        row["schedule_status"] = "NOT_CONFIGURED"
        reseal_collector(data["collector_receipts"][0])
        dangling = {
            "selected_group_key_sha256": TARGET_GROUP,
            "referenced_entity_domain": "TABLE",
            "referenced_entity_key_sha256": "a" * 64,
            "referencing_entity_domain": "VIEW",
            "referencing_entity_key_sha256": "b" * 64,
            "referencing_entity_groups_sha256": "c" * 64,
            "is_blocking_refresh": True,
        }
        data["collector_receipts"][5] = collector_receipt(
            "replication-dangling", TARGET_ACCOUNT, [dangling], selected=TARGET_GROUP
        )
        codes = {item["code"] for item in analyze(data)["findings"]}
        self.assertIn("SCHEDULE_NOT_RUNNING", codes)
        self.assertIn("BLOCKING_DANGLING_REFERENCE", codes)

    def test_primary_secondary_state_null_is_not_a_false_blocker(self):
        data = base()
        source = data["collector_receipts"][0]
        source["datasets"]["current_groups"][0]["schedule_status"] = "PROVIDER_OTHER"
        reseal_collector(source)
        self.assertEqual(analyze(data)["overall_status"], "READY_FOR_OPERATOR_DRILL_AS_OF")
        target = data["collector_receipts"][1]
        target["datasets"]["current_groups"][0]["schedule_status"] = "SUSPENDED"
        reseal_collector(target)
        codes = {item["code"] for item in analyze(data)["findings"]}
        self.assertIn("SCHEDULE_NOT_RUNNING", codes)

    def test_partial_denominator_and_duplicate_rows_do_not_pass(self):
        data = base()
        data["collector_receipts"] = [
            row
            for row in data["collector_receipts"]
            if not (
                row["surface"] == "replication-current"
                and row["datasets"]["execution_context"][0]["account_identifier_sha256"] == TARGET_ACCOUNT
            )
        ]
        self.assertEqual(analyze(data)["overall_status"], "NOT_READY")
        data = base()
        receipt = data["collector_receipts"][0]
        receipt["datasets"]["current_groups"].append(copy.deepcopy(receipt["datasets"]["current_groups"][0]))
        reseal_collector(receipt)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

    def test_invalid_evidence_is_not_reflected(self):
        data = base()
        data["collector_receipts"][0]["attacker_secret"] = "AKIA-DO-NOT-REFLECT"
        report = analyze(data)
        rendered = json.dumps(report)
        self.assertNotIn("AKIA-DO-NOT-REFLECT", rendered)
        self.assertEqual(report["findings"][0]["code"], "EVIDENCE_INTEGRITY_INVALID")

    def test_unknown_phase_and_future_history_fail_integrity(self):
        data = base()
        history_row = data["collector_receipts"][2]["datasets"]["replication_refresh_history"][0]
        history_row["phase_name"] = "ATTACKER_COMPLETE"
        history_row["start_time"] = iso(1)
        reseal_collector(data["collector_receipts"][2])
        report = analyze(data)
        self.assertEqual(report["overall_status"], "INCONCLUSIVE")
        self.assertIn("row_enum", report["integrity_issue_codes"])
        self.assertIn("window_row_time", report["integrity_issue_codes"])

    def test_duplicate_receipt_scope_fails_closed(self):
        data = base()
        data["collector_receipts"].append(copy.deepcopy(data["collector_receipts"][2]))
        report = analyze(data)
        self.assertEqual(report["overall_status"], "NOT_READY")
        self.assertIn("HISTORY_ACCOUNT_COVERAGE_INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_analysis_is_deterministic_and_does_not_mutate_input(self):
        data = base()
        original = copy.deepcopy(data)
        first = analyze(data)
        second = analyze(data)
        self.assertEqual(first, second)
        self.assertEqual(data, original)

    def test_full_drill_requires_trusted_ordered_transitions(self):
        data = base()
        data["policy"]["mode"] = "FULL_DRILL_ATTESTATION"
        data["policy"]["validations"] = [
            {"validation_key_sha256": "3" * 64, "lineage_group_key_sha256": LINEAGE, "stage": "PRE_FAILOVER"},
            {"validation_key_sha256": "4" * 64, "lineage_group_key_sha256": LINEAGE, "stage": "POST_FAILOVER"},
            {"validation_key_sha256": "5" * 64, "lineage_group_key_sha256": LINEAGE, "stage": "POST_FAILBACK"},
        ]
        data["policy"]["expected_validation_count"] = 3
        other = [row for row in data["collector_receipts"] if row["surface"] != "replication-current"]
        other.extend(
            [
                collector_receipt(
                    "replication",
                    SOURCE_ACCOUNT,
                    [history(snapshot=iso(-6), start=iso(-6), job="b" * 64, group=SOURCE_GROUP)],
                ),
                collector_receipt(
                    "replication-progress",
                    SOURCE_ACCOUNT,
                    [progress(start=iso(-6), group=SOURCE_GROUP)],
                ),
            ]
        )
        snapshots = [
            collector_receipt(
                "replication-current", SOURCE_ACCOUNT, [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, True)], at=iso(-10)
            ),
            collector_receipt(
                "replication-current", TARGET_ACCOUNT, [current_group(TARGET_ACCOUNT, TARGET_GROUP, False)], at=iso(-10)
            ),
            collector_receipt(
                "replication-current", SOURCE_ACCOUNT, [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, False)], at=iso(-6)
            ),
            collector_receipt(
                "replication-current", TARGET_ACCOUNT, [current_group(TARGET_ACCOUNT, TARGET_GROUP, True)], at=iso(-6)
            ),
            collector_receipt(
                "replication-current", SOURCE_ACCOUNT, [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, True)], at=iso(-2)
            ),
            collector_receipt(
                "replication-current", TARGET_ACCOUNT, [current_group(TARGET_ACCOUNT, TARGET_GROUP, False)], at=iso(-2)
            ),
        ]
        data["collector_receipts"] = snapshots + other
        failover_event = seal(
            {
                "schema_version": "1",
                "event_key_sha256": "6" * 64,
                "lineage_group_key_sha256": LINEAGE,
                "event": "FAILOVER",
                "source_account_key_sha256": SOURCE_ACCOUNT,
                "target_account_key_sha256": TARGET_ACCOUNT,
                "change_record_sha256": "7" * 64,
                "operator_key_sha256": "8" * 64,
                "started_at": iso(-9),
                "completed_at": iso(-7),
                "outcome": "SUCCEEDED",
            }
        )
        failback_event = seal(
            {
                "schema_version": "1",
                "event_key_sha256": "9" * 64,
                "lineage_group_key_sha256": LINEAGE,
                "event": "FAILBACK",
                "source_account_key_sha256": TARGET_ACCOUNT,
                "target_account_key_sha256": SOURCE_ACCOUNT,
                "change_record_sha256": "a" * 64,
                "operator_key_sha256": "8" * 64,
                "started_at": iso(-5),
                "completed_at": iso(-3),
                "outcome": "SUCCEEDED",
            }
        )
        data["operator_receipts"] = [failover_event, failback_event]
        data["validation_receipts"] = [
            validation("PRE_FAILOVER", "3" * 64, iso(-10, 30)),
            validation("POST_FAILOVER", "4" * 64, iso(-6, 30)),
            validation("POST_FAILBACK", "5" * 64, iso(-2, 30)),
        ]
        report = analyze(data)
        self.assertEqual(report["overall_status"], "FULL_DRILL_ATTESTED_AS_OF")
        self.assertEqual({row["leg"] for row in report["rpo_results"]}, {"FORWARD_FAILOVER", "REVERSE_FAILBACK"})

        hindsight_progress = copy.deepcopy(data)
        reverse_progress = next(
            receipt
            for receipt in hindsight_progress["collector_receipts"]
            if receipt["surface"] == "replication-progress"
            and receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == SOURCE_ACCOUNT
        )
        reverse_progress["datasets"]["replication_progress"][0]["end_time"] = iso(-4)
        reseal_collector(reverse_progress)
        hindsight_report = analyze(hindsight_progress)
        self.assertEqual(hindsight_report["overall_status"], "INCONCLUSIVE")

        without_reverse = copy.deepcopy(data)
        without_reverse["collector_receipts"] = [
            receipt
            for receipt in without_reverse["collector_receipts"]
            if not (
                receipt["surface"] in {"replication", "replication-progress"}
                and receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == SOURCE_ACCOUNT
            )
        ]
        self.assertEqual(analyze(without_reverse)["overall_status"], "NOT_READY")

    def test_failover_attestation_checks_pretransition_secondary_schedule(self):
        data = base()
        data["policy"]["mode"] = "FAILOVER_ATTESTATION"
        data["policy"]["validations"].append(
            {"validation_key_sha256": "4" * 64, "lineage_group_key_sha256": LINEAGE, "stage": "POST_FAILOVER"}
        )
        data["policy"]["expected_validation_count"] = 2
        other = [row for row in data["collector_receipts"] if row["surface"] != "replication-current"]
        after_source = current_group(SOURCE_ACCOUNT, SOURCE_GROUP, False)
        after_source["schedule_status"] = "STARTED"
        after_target = current_group(TARGET_ACCOUNT, TARGET_GROUP, True)
        after_target["schedule_status"] = "PROVIDER_OTHER"
        data["collector_receipts"] = [
            collector_receipt(
                "replication-current", SOURCE_ACCOUNT, [current_group(SOURCE_ACCOUNT, SOURCE_GROUP, True)], at=iso(-10)
            ),
            collector_receipt(
                "replication-current", TARGET_ACCOUNT, [current_group(TARGET_ACCOUNT, TARGET_GROUP, False)], at=iso(-10)
            ),
            collector_receipt("replication-current", SOURCE_ACCOUNT, [after_source], at=iso(-6)),
            collector_receipt("replication-current", TARGET_ACCOUNT, [after_target], at=iso(-6)),
        ] + other
        data["operator_receipts"] = [
            seal(
                {
                    "schema_version": "1",
                    "event_key_sha256": "6" * 64,
                    "lineage_group_key_sha256": LINEAGE,
                    "event": "FAILOVER",
                    "source_account_key_sha256": SOURCE_ACCOUNT,
                    "target_account_key_sha256": TARGET_ACCOUNT,
                    "change_record_sha256": "7" * 64,
                    "operator_key_sha256": "8" * 64,
                    "started_at": iso(-9),
                    "completed_at": iso(-7),
                    "outcome": "SUCCEEDED",
                }
            )
        ]
        data["validation_receipts"] = [validation(at=iso(-10, 30)), validation("POST_FAILOVER", "4" * 64, iso(-5))]
        self.assertEqual(analyze(data)["overall_status"], "FAILOVER_ATTESTED_AS_OF")

        data["collector_receipts"][2]["datasets"]["current_groups"][0]["schedule_status"] = "SUSPENDED"
        reseal_collector(data["collector_receipts"][2])
        self.assertEqual(analyze(data)["overall_status"], "NOT_READY")

    def test_window_tail_and_validation_replay_fail_closed(self):
        data = base()
        for receipt in data["collector_receipts"]:
            if receipt["surface"] in {"replication", "replication-progress"}:
                context = receipt["datasets"]["execution_context"][0]
                context["window_end_utc"] = iso(-5)
                receipt["source_metadata"]["selector_values"]["window_end"] = iso(-5)
                template = (MODULE.parent / "sql" / failover.CONTRACTS[receipt["surface"]]["template"]).read_text()
                rendered = template.replace("__WINDOW_START_UTC__", iso(-60)).replace("__WINDOW_END_UTC__", iso(-5))
                receipt["selector_fingerprint"] = failover.digest(receipt["source_metadata"]["selector_values"])
                receipt["rendered_sql_sha256"] = "sha256:" + failover.hashlib.sha256(rendered.encode()).hexdigest()
                reseal_collector(receipt)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        data["validation_receipts"] = [validation(at="2020-01-01T00:00:00Z")]
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

    def test_context_type_schedule_and_progress_contradictions_block(self):
        data = base()
        source = data["collector_receipts"][0]
        source["datasets"]["current_groups"][0]["allowed_integration_types_sha256"] = "0" * 64
        reseal_collector(source)
        target = data["collector_receipts"][1]
        target["datasets"]["current_groups"][0]["next_scheduled_refresh"] = None
        reseal_collector(target)
        history_receipt = data["collector_receipts"][2]
        history_receipt["datasets"]["replication_refresh_history"][0]["group_type"] = "REPLICATION"
        reseal_collector(history_receipt)
        progress_receipt = data["collector_receipts"][3]
        progress_receipt["datasets"]["replication_progress"][0]["phase_name"] = "PRIMARY_UPLOADING_DATA"
        progress_receipt["datasets"]["replication_progress"][0]["progress"] = "50"
        progress_receipt["datasets"]["execution_context"][0]["collector_user_sha256"] = "0" * 64
        reseal_collector(progress_receipt)
        report = analyze(data)
        codes = {row["code"] for row in report["findings"]}
        self.assertEqual(report["overall_status"], "NOT_READY")
        self.assertTrue(
            {
                "GROUP_POLICY_DRIFT",
                "SCHEDULE_NOT_RUNNING",
                "GROUP_TYPE_MISMATCH",
                "REFRESH_PROGRESS_NOT_COMPLETE",
                "AUTHORIZATION_CONTEXT_MISMATCH",
            }
            <= codes
        )

    def test_conflicting_natural_keys_and_account_context_are_invalid(self):
        data = base()
        current = data["collector_receipts"][1]
        conflicting = copy.deepcopy(current["datasets"]["current_groups"][0])
        conflicting["is_primary"] = True
        current["datasets"]["current_groups"].append(conflicting)
        reseal_collector(current)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        current = data["collector_receipts"][1]
        current["datasets"]["current_groups"][0]["local_account_key_sha256"] = SOURCE_ACCOUNT
        reseal_collector(current)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        progress_receipt = data["collector_receipts"][3]
        progress_receipt["datasets"]["replication_progress"].append(progress("FAILED"))
        reseal_collector(progress_receipt)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        history_receipt = data["collector_receipts"][2]
        history_receipt["datasets"]["replication_refresh_history"][0]["job_key_sha256"] = None
        reseal_collector(history_receipt)
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

    def test_cross_organization_receipts_block_positive_status(self):
        data = base()
        for receipt in data["collector_receipts"]:
            context = receipt["datasets"]["execution_context"][0]
            if context["account_identifier_sha256"] == TARGET_ACCOUNT:
                context["organization_name_sha256"] = "9" * 64
                reseal_collector(receipt)
        report = analyze(data)
        self.assertEqual(report["overall_status"], "NOT_READY")
        self.assertIn("ORGANIZATION_CONTEXT_MISMATCH", {row["code"] for row in report["findings"]})

    def test_invalid_hash_shapes_never_raise_type_error(self):
        data = base()
        data["policy"]["mode"] = ["PREFLIGHT"]
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        data["policy"]["validations"][0]["stage"] = ["PRE_FAILOVER"]
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        data["policy"]["groups"][0]["lineage_group_key_sha256"] = ["bad"]
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

        data = base()
        data["validation_receipts"][0]["validation_key_sha256"] = ["bad"]
        seal(data["validation_receipts"][0])
        self.assertEqual(analyze(data)["overall_status"], "INCONCLUSIVE")

    def test_cli_has_no_output_write_option(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertNotIn('add_argument("--output"', source)
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        self.assertFalse(imported & {"requests", "socket", "snowflake", "subprocess", "urllib"})
        forbidden_calls = {
            "open",
            "popen",
            "remove",
            "rename",
            "run",
            "system",
            "touch",
            "unlink",
            "urlopen",
            "write_bytes",
            "write_text",
        }
        observed_calls = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
        }
        self.assertFalse(observed_calls & forbidden_calls)


if __name__ == "__main__":
    unittest.main()

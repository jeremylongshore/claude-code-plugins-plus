#!/usr/bin/env python3
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from analyze_governance_coverage import analyze  # noqa: E402
from collect_governance_evidence import CollectionError, render_surface  # noqa: E402

SCRIPT = HERE.parent / "scripts" / "analyze_governance_coverage.py"
COLLECTOR = HERE.parent / "scripts" / "collect_governance_evidence.py"
SQL_DIR = HERE.parent / "scripts" / "sql"
SURFACES = {
    "denominator": ("governance-denominator.sql", "SNOWFLAKE.ACCOUNT_USAGE.TABLES+COLUMNS", "assets"),
    "tag_references": ("governance-tag-references.sql", "SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES", "tags"),
    "policy_references": ("governance-policy-references-current.sql", "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES", "policies"),
    "classification_latest": ("governance-classification-latest.sql", "SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST+TABLES", "classifications"),
}


def load_fixture(name: str) -> dict:
    return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))


def seal_receipts(doc: dict) -> dict:
    for surface, receipt in doc.get("receipts", {}).items():
        template, source, dataset_key = SURFACES[surface]
        dataset = doc[dataset_key]
        receipt["source"] = source
        receipt["row_count"] = len(dataset)
        receipt["raw_row_count"] = len(dataset)
        receipt["row_limit"] = 10000
        receipt["template_sha256"] = f"sha256:{hashlib.sha256((SQL_DIR / template).read_bytes()).hexdigest()}"
        receipt["rendered_sql_sha256"] = receipt["query_sha256"]
        receipt["dataset_sha256"] = f"sha256:{hashlib.sha256(json.dumps(dataset, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}"
        receipt["source_metadata"] = {"selector": {"database": True}}
        if surface == "policy_references":
            receipt["source_metadata"] = {"selector": {"database": True, "objects": len(doc["assets"])}}
        receipt["selector_fingerprint"] = "sha256:" + "f" * 64
        body = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(body).hexdigest()}"
    return doc


class GovernanceCoverageTests(unittest.TestCase):
    def test_collector_render_is_bounded_read_only_and_rejects_fragments(self):
        _, _, rendered, _, selector = render_surface("tag_references", "ANALYTICS", 25)
        self.assertIn("LIMIT 26", rendered)
        self.assertEqual(selector, {"database": "ANALYTICS"})
        self.assertNotRegex(rendered.upper(), r"\b(?:ALTER|CREATE|DROP|GRANT|REVOKE)\b")
        for database in ("DB; DROP TABLE X", "DB.NAME", "'quoted'"):
            with self.subTest(database=database), self.assertRaises(CollectionError):
                render_surface("tag_references", database, 25)

    def test_collector_seals_saved_rows_without_exporting_database_or_tag_value(self):
        asset_key = "asset_" + "a" * 64
        tag_key = "tag_" + "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.json"
            raw.write_text(json.dumps([{"ASSET_KEY": asset_key, "TAG_KEY": tag_key, "APPLY_METHOD": "CLASSIFIED"}]), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(COLLECTOR), "--surface", "tag_references",
                    "--database", "PRIVATE_DB", "--row-limit", "10", "--input-json", str(raw),
                    "--privilege-scope", "COMPLETE", "--collected-at", "2026-08-31T11:00:00Z",
                ],
                capture_output=True, text=True, check=True,
            )
        envelope = json.loads(completed.stdout)
        self.assertEqual(envelope["dataset"][0]["tag_key"], tag_key)
        self.assertNotIn("PRIVATE_DB", completed.stdout)
        self.assertNotIn("tag_value", completed.stdout.casefold())
        receipt = envelope["receipt"]
        self.assertEqual(receipt["row_count"], 1)
        self.assertEqual(receipt["dataset_sha256"], "sha256:" + hashlib.sha256(json.dumps(envelope["dataset"], sort_keys=True, separators=(",", ":")).encode()).hexdigest())

    def test_current_policy_collector_binds_restricted_manifest_without_exporting_object(self):
        asset_key = "asset_" + "c" * 64
        policy_key = "policy_" + "d" * 64
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            manifest = base / "objects.json"
            raw = base / "raw.json"
            manifest.write_text(json.dumps([{"asset_key": asset_key, "object_name": "PRIVATE_DB.CORE.CUSTOMERS", "domain": "TABLE"}]), encoding="utf-8")
            raw.write_text(json.dumps([{
                "ASSET_KEY": asset_key, "POLICY_KEY": policy_key,
                "POLICY_KIND": "JOIN_POLICY", "ASSIGNMENT": "DIRECT",
                "POLICY_STATUS": "ACTIVE", "ENTITY_KEY_HASH": None,
            }]), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(COLLECTOR), "--surface", "policy_references",
                    "--database", "PRIVATE_DB", "--row-limit", "10", "--input-json", str(raw),
                    "--object-manifest", str(manifest), "--privilege-scope", "COMPLETE",
                    "--collected-at", "2026-08-31T11:00:00Z",
                ],
                capture_output=True, text=True, check=True,
            )
        envelope = json.loads(completed.stdout)
        self.assertEqual(envelope["receipt"]["source"], "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES")
        self.assertEqual(envelope["receipt"]["source_metadata"]["selector"]["objects"], 1)
        self.assertEqual(envelope["dataset"][0]["policy_kind"], "JOIN_POLICY")
        self.assertNotIn("CUSTOMERS", completed.stdout)
        self.assertNotIn("PRIVATE_DB", completed.stdout)

    def test_covered_fixture_is_verified_and_privacy_safe(self):
        report = analyze(seal_receipts(load_fixture("covered.json")))
        self.assertEqual(report["decision"], "VERIFIED")
        self.assertFalse(report["completeness_claim_blocked"])
        self.assertEqual(report["summary"]["denominator_assets"], 2)
        rendered = json.dumps(report)
        for raw_name in ("CUSTOMER", "EMAIL", "ANALYTICS", "PUBLIC"):
            self.assertNotIn(raw_name, rendered)
        self.assertFalse(report["boundaries"]["mutation_sql_emitted"])

    def test_direct_policy_precedence_and_aggregation_entity_key_exception(self):
        report = analyze(seal_receipts(load_fixture("covered.json")))
        masking = next(row for row in report["precedence"] if row["policy_kind"] == "MASKING_POLICY")
        self.assertEqual(masking["rule"], "DIRECT_PRECEDENCE")
        self.assertEqual(masking["shadowed_policy_keys"], ["policy_mask_tag"])
        aggregation = next(row for row in report["precedence"] if row["policy_kind"] == "AGGREGATION_POLICY")
        self.assertEqual(aggregation["rule"], "ENTITY_KEY_EXCEPTION")
        self.assertEqual(aggregation["shadowed_policy_keys"], ["policy_aggregate_tag_same_key"])
        self.assertEqual(aggregation["cumulative_policy_keys"], ["policy_aggregate_tag_distinct_key"])

    def test_failed_classification_missing_tag_and_policy_are_not_coverage(self):
        report = analyze(load_fixture("gaps.json"))
        self.assertEqual(report["decision"], "NOT_PROVEN")
        row = report["coverage"][0]
        self.assertEqual(row["classification_state"], "FAILED")
        self.assertEqual(row["tag_state"], "MISSING")
        states = {item["policy_kind"]: item["state"] for item in row["controls"]}
        self.assertEqual(states["MASKING_POLICY"], "MISCONFIGURED")
        self.assertEqual(states["PROJECTION_POLICY"], "UNCOVERED")
        self.assertTrue(report["completeness_claim_blocked"])
        categories = {item["category"] for item in report["findings"]}
        self.assertTrue({"classification", "tag-coverage", "edition-boundary", "policy-coverage"} <= categories)

    def test_preview_tag_policy_requires_explicit_feature_evidence(self):
        doc = seal_receipts(load_fixture("covered.json"))
        doc["metadata"]["preview_features_enabled"].remove("TAG_BASED_PROJECTION_POLICY")
        report = analyze(doc)
        email = next(row for row in report["coverage"] if row["asset_key"] == "asset_customer_email")
        projection = next(row for row in email["controls"] if row["policy_kind"] == "PROJECTION_POLICY")
        self.assertEqual(projection["state"], "PREVIEW_NOT_ENABLED")
        self.assertEqual(report["decision"], "NOT_PROVEN")

    def test_tag_policy_without_tag_evidence_is_not_effective_coverage(self):
        doc = seal_receipts(load_fixture("covered.json"))
        doc["tags"] = [row for row in doc["tags"] if row["asset_key"] != "asset_customer_table"]
        report = analyze(doc)
        table = next(row for row in report["coverage"] if row["asset_key"] == "asset_customer_table")
        states = {item["policy_kind"]: item["state"] for item in table["controls"]}
        self.assertEqual(states["ROW_ACCESS_POLICY"], "TAG_EVIDENCE_MISSING")
        self.assertEqual(states["JOIN_POLICY"], "TAG_EVIDENCE_MISSING")
        self.assertEqual(report["decision"], "NOT_PROVEN")

    def test_partial_stale_truncated_or_tampered_receipt_blocks_completeness(self):
        mutations = (
            ("privilege_scope", "PARTIAL"),
            ("truncated", True),
            ("collected_at", "2026-08-01T00:00:00Z"),
            ("receipt_sha256", "sha256:" + "0" * 64),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                doc = seal_receipts(load_fixture("covered.json"))
                doc["receipts"]["policy_references"][field] = value
                report = analyze(doc)
                self.assertTrue(report["completeness_claim_blocked"])
                self.assertEqual(report["decision"], "NOT_PROVEN")

    def test_receipt_is_bound_to_exact_dataset_source_template_and_selector(self):
        mutations = (
            ("dataset_sha256", "sha256:" + "0" * 64),
            ("row_count", 999),
            ("source", "OTHER_VIEW"),
            ("template_sha256", "sha256:" + "0" * 64),
            ("selector_fingerprint", None),
            ("source_metadata", {"selector": {"database": "RAW_DB"}}),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                doc = seal_receipts(load_fixture("covered.json"))
                doc["receipts"]["tag_references"][field] = value
                report = analyze(doc)
                self.assertTrue(report["completeness_claim_blocked"])
        doc = seal_receipts(load_fixture("covered.json"))
        doc["tags"].append({"asset_key": "asset_customer_email", "tag_key": "tag_extra", "apply_method": "MANUAL"})
        self.assertTrue(analyze(doc)["completeness_claim_blocked"])

    def test_policy_context_failure_stale_or_missing_never_proves_verification(self):
        for mutation in ("FAIL", "STALE", "MISSING"):
            with self.subTest(mutation=mutation):
                doc = seal_receipts(load_fixture("covered.json"))
                if mutation == "FAIL":
                    doc["policy_context"][0]["status"] = "FAIL"
                elif mutation == "STALE":
                    doc["policy_context"][0]["simulated_at"] = "2026-08-01T00:00:00Z"
                else:
                    doc["policy_context"] = doc["policy_context"][1:]
                report = analyze(doc)
                self.assertEqual(report["decision"], "NOT_PROVEN")
                self.assertTrue(any(item["category"] == "policy-context" for item in report["findings"]))

    def test_non_active_snowflake_policy_statuses_are_misconfiguration(self):
        for status in (
            "MULTIPLE_MASKING_POLICY_ASSIGNED_TO_THE_COLUMN",
            "COLUMN_IS_MISSING_FOR_SECONDARY_ARG",
            "COLUMN_DATATYPE_MISMATCH_FOR_SECONDARY_ARG",
        ):
            with self.subTest(status=status):
                doc = seal_receipts(load_fixture("covered.json"))
                doc["policies"][0]["policy_status"] = status
                report = analyze(doc)
                email = next(row for row in report["coverage"] if row["asset_key"] == "asset_customer_email")
                masking = next(row for row in email["controls"] if row["policy_kind"] == "MASKING_POLICY")
                self.assertEqual(masking["state"], "MISCONFIGURED")

    def test_raw_identifiers_and_credentials_are_rejected(self):
        bad_docs = []
        raw = load_fixture("covered.json")
        raw["assets"][0]["asset_key"] = "ANALYTICS.CUSTOMERS.EMAIL"
        bad_docs.append(raw)
        secret = load_fixture("covered.json")
        secret["metadata"]["access_token"] = "abc"
        bad_docs.append(secret)
        shaped = load_fixture("covered.json")
        shaped["metadata"]["note"] = "Authorization: Bearer abcdefghijklmnop"
        bad_docs.append(shaped)
        tag_value = load_fixture("covered.json")
        tag_value["tags"][0]["tag_value"] = "PII"
        bad_docs.append(tag_value)
        policy_body = load_fixture("covered.json")
        policy_body["policies"][0]["policy_body"] = "CASE WHEN ..."
        bad_docs.append(policy_body)
        for doc in bad_docs:
            with self.subTest(doc=doc), self.assertRaises(ValueError):
                analyze(doc)

    def test_rows_outside_denominator_and_duplicate_assets_are_rejected(self):
        outside = load_fixture("covered.json")
        outside["tags"][0]["asset_key"] = "asset_unknown"
        with self.assertRaises(ValueError):
            analyze(outside)
        duplicate = load_fixture("covered.json")
        duplicate["assets"].append(copy.deepcopy(duplicate["assets"][0]))
        with self.assertRaises(ValueError):
            analyze(duplicate)

    def test_cli_failure_is_clean_and_cli_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            bad = base / "bad.json"
            bad.write_text('{"schema_version":"1","assets":"wrong"}', encoding="utf-8")
            failed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(bad)], capture_output=True, text=True, check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertNotIn("Traceback", failed.stderr)
            doc = seal_receipts(load_fixture("covered.json"))
            source = base / "source.json"
            source.write_text(json.dumps(doc), encoding="utf-8")
            first = subprocess.run([sys.executable, str(SCRIPT), "--input", str(source)], capture_output=True, text=True, check=True)
            second = subprocess.run([sys.executable, str(SCRIPT), "--input", str(source)], capture_output=True, text=True, check=True)
            self.assertEqual(first.stdout, second.stdout)

    def test_dry_run_packet_never_contains_mutation_sql(self):
        report = analyze(load_fixture("gaps.json"))
        self.assertTrue(report["dry_run_remediation_packet"])
        for item in report["dry_run_remediation_packet"]:
            self.assertIsNone(item["mutation_sql"])
        rendered = json.dumps(report).upper()
        self.assertNotIn("ALTER TABLE", rendered)
        self.assertNotIn("ALTER TAG", rendered)


if __name__ == "__main__":
    unittest.main()

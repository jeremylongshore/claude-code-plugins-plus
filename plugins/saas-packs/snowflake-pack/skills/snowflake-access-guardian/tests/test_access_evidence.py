from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
SCRIPT = SCRIPTS / "analyze_access_evidence.py"
COLLECTOR_PATH = SCRIPTS / "collect_snowflake_evidence.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module("analyze_access_evidence", SCRIPT)
COLLECTOR = load_module("collect_access_evidence", COLLECTOR_PATH)


def rehash(receipt: dict) -> None:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(MODULE.canonical_json(body)).hexdigest()}"


class AccessEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.evaluated_at = now.isoformat().replace("+00:00", "Z")
        self.window_start = (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        self.window_end = (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")

    def wrapper(self, surface: str, raw: list[dict], **selector: str) -> dict:
        path, template, rendered, sources, bound = COLLECTOR.render_surface(surface, **selector)
        if surface in MODULE.ROW_FIELDS:
            normalized_rows = []
            for envelope in raw:
                payload = envelope.get("EVIDENCE", envelope)
                row = {name: None for name in MODULE.ROW_FIELDS[surface]}
                row.update({name: value for name, value in payload.items() if name in row})
                normalized_rows.append({"EVIDENCE": {"_dataset": "rows", **row}})
            raw = [
                {
                    "EVIDENCE": {
                        "_dataset": "execution_context",
                        "observed_at": self.window_end,
                        "session_id": "1001",
                        "account_locator": "ORG-ACCOUNT",
                        "current_user_name": "ALICE",
                        "primary_role": "ANALYST",
                        "primary_role_type": "ROLE",
                        "secondary_roles": {"roles": "", "value": "NONE"},
                    }
                },
                *normalized_rows,
            ]
        receipt = COLLECTOR.build_receipt(
            surface,
            "access-auditor",
            rendered,
            sources,
            raw=raw,
            collected_at=self.window_end,
            template_sql=template,
            template_path=path,
            selector=bound,
            collection_mode="live-cli",
            collection_started_at=self.window_start,
            collection_completed_at=self.window_end,
        )
        return {"selector": bound, "receipt": receipt}

    def valid_bundle(self) -> dict:
        object_grant = {
            "_dataset": "grants_to_roles",
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "ANALYTICS.CURATED.ORDERS",
            "granted_to": "ROLE",
            "grantee_name": "DATA_READER",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
            "granted_by_role_type": "ROLE",
        }
        inheritance_grant = {
            "_dataset": "grants_to_roles",
            "privilege": "USAGE",
            "granted_on": "ROLE",
            "name": "DATA_READER",
            "granted_to": "ROLE",
            "grantee_name": "ANALYST",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
            "granted_by_role_type": "ROLE",
        }
        user_grant = {
            "_dataset": "grants_to_users",
            "role": "ANALYST",
            "granted_to": "USER",
            "grantee_name": "ALICE",
            "granted_by": "SECURITYADMIN",
        }
        role_rows = [
            {"EVIDENCE": {"_dataset": "roles", "name": "ANALYST", "role_type": "ROLE"}},
            {"EVIDENCE": {"_dataset": "roles", "name": "DATA_READER", "role_type": "ROLE"}},
        ]
        historical = self.wrapper(
            "access",
            [
                {"EVIDENCE": {**object_grant, "granted_to": "ACCOUNT ROLE"}},
                {"EVIDENCE": {**inheritance_grant, "granted_to": "ACCOUNT ROLE"}},
                {"EVIDENCE": user_grant},
                *role_rows,
            ],
        )
        session = self.wrapper(
            "access-session",
            [
                {
                    "EVIDENCE": {
                        "_dataset": "session_context",
                        "observed_at": self.window_end,
                        "session_id": "1000",
                        "account_locator": "ORG-ACCOUNT",
                        "current_user_name": "ALICE",
                        "primary_role": "ANALYST",
                        "primary_role_type": "ROLE",
                        "secondary_roles": {"roles": "", "value": "NONE"},
                    }
                }
            ],
        )
        analyst_current = self.wrapper(
            "access-role-current",
            [{key: value for key, value in inheritance_grant.items() if key != "_dataset"}],
            role="ANALYST",
        )
        reader_current = self.wrapper(
            "access-role-current",
            [{key: value for key, value in object_grant.items() if key != "_dataset"}],
            role="DATA_READER",
        )
        analyst_parents = self.wrapper("access-role-parents", [], role="ANALYST")
        reader_parents = self.wrapper(
            "access-role-parents",
            [
                {
                    "role": "DATA_READER",
                    "granted_to": "ROLE",
                    "grantee_name": "ANALYST",
                    "granted_by": "SECURITYADMIN",
                }
            ],
            role="DATA_READER",
        )
        public_current = self.wrapper("access-role-current", [], role="PUBLIC")
        user_current = self.wrapper(
            "access-user-current",
            [{key: value for key, value in user_grant.items() if key != "_dataset"}],
            user="ALICE",
        )
        future_database = self.wrapper("access-future-database", [], database="ANALYTICS")
        future_schema = self.wrapper("access-future-schema", [], schema="ANALYTICS.CURATED")
        return {
            "schema_version": "2.0",
            "metadata": {
                "account": "ORG-ACCOUNT",
                "collector_role": "ANALYST",
                "connection_profile": "access-auditor",
                "evaluated_at": self.evaluated_at,
                "window_start": self.window_start,
                "window_end": self.window_end,
                "max_age_seconds": 7200,
                "coverage": {
                    "roles": ["ANALYST", "DATA_READER", "PUBLIC"],
                    "users": ["ALICE"],
                    "database_roles": [],
                    "future_databases": ["ANALYTICS"],
                    "future_schemas": ["ANALYTICS.CURATED"],
                },
                "external_boundaries": {
                    "object_policies": "REVIEWED",
                    "shares": "REVIEWED",
                    "inherited_grants_capability": "REVIEWED",
                },
            },
            "collections": {
                "historical": historical,
                "session": session,
                "role_current": [analyst_current, reader_current, public_current],
                "role_parents": [analyst_parents, reader_parents],
                "user_current": [user_current],
                "database_role_current": [],
                "future_database": [future_database],
                "future_schema": [future_schema],
            },
            "request": {
                "principal": "ALICE",
                "object": "ANALYTICS.CURATED.ORDERS",
                "privilege": "SELECT",
            },
            "managed_access_schemas": ["ANALYTICS.CURATED"],
            "verification": {
                "positive": [
                    {
                        "status": "PASS",
                        "observed_at": self.window_end,
                        "account": "ORG-ACCOUNT",
                        "principal": "ALICE",
                        "object": "ANALYTICS.CURATED.ORDERS",
                        "privilege": "SELECT",
                        "primary_role": "ANALYST",
                        "secondary_roles_mode": "NONE",
                        "secondary_roles": [],
                    }
                ],
                "negative": [
                    {
                        "status": "DENIED",
                        "observed_at": self.window_end,
                        "account": "ORG-ACCOUNT",
                        "principal": "ALICE",
                        "object": "ANALYTICS.CURATED.ORDERS",
                        "privilege": "SELECT",
                        "primary_role": "ANALYST",
                        "secondary_roles_mode": "NONE",
                        "secondary_roles": [],
                    }
                ],
            },
        }

    def test_trusted_receipts_prove_only_the_declared_scope(self) -> None:
        data = self.valid_bundle()
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(report["evidence_trust"]["status"], "DIGEST_MATCHED_OPERATOR_ASSERTED")
        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertTrue(report["absence_claim_blocked"])
        self.assertTrue(report["positive_access_claim_supported"])
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertEqual(
            report["analysis"]["effective_access"]["status"],
            "OBJECT_PRIVILEGE_PATH_PROVEN",
        )
        self.assertIn(
            "ALICE -> ANALYST -> DATA_READER",
            {item["path"] for item in report["analysis"]["effective_access"]["paths"]},
        )
        self.assertTrue(any("account-wide absence" in claim for claim in report["non_claims"]))

    def test_self_checksum_without_out_of_band_digest_never_completes(self) -> None:
        data = self.valid_bundle()
        report = MODULE.analyze_bundle(data)
        self.assertEqual(report["evidence_trust"]["status"], "UNTRUSTED")
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertTrue(all(not item["complete"] for item in report["receipt_assessments"]))

    def test_rehashed_forgery_fails_the_preexisting_trust_anchor(self) -> None:
        data = self.valid_bundle()
        trusted = MODULE.input_sha256(data)
        receipt = data["collections"]["role_current"][1]["receipt"]
        receipt["datasets"]["rows"][0]["privilege"] = "OWNERSHIP"
        rehash(receipt)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=trusted)
        self.assertEqual(report["evidence_trust"]["status"], "DIGEST_MISMATCH")
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")
        self.assertTrue(report["completeness_claim_blocked"])

    def test_receipt_contract_tampering_fails_closed(self) -> None:
        mutations = (
            ("surface", "query"),
            ("schema_version", "1"),
            ("sql_sha256", "sha256:" + "0" * 64),
            ("selector_fingerprint", "sha256:" + "0" * 64),
            ("row_count", 999),
            ("row_limit", 1),
            ("truncation_possible", True),
        )
        for field, value in mutations:
            data = self.valid_bundle()
            receipt = data["collections"]["role_current"][0]["receipt"]
            receipt[field] = value
            rehash(receipt)
            with self.subTest(field=field):
                report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
                assessment = next(
                    item for item in report["receipt_assessments"] if item["collection"] == "role_current[0]"
                )
                self.assertEqual(assessment["status"], "INVALID")
                self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")
                self.assertTrue(report["completeness_claim_blocked"])

    def test_unknown_missing_or_out_of_scope_projected_rows_fail_closed(self) -> None:
        mutations = (
            ("unknown", lambda row: row.__setitem__("unexpected", "value")),
            ("missing", lambda row: row.pop("privilege")),
        )
        for label, mutate in mutations:
            data = self.valid_bundle()
            receipt = data["collections"]["role_current"][1]["receipt"]
            mutate(receipt["datasets"]["rows"][0])
            rehash(receipt)
            with self.subTest(label=label):
                report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
                self.assertFalse(report["grant_graph_scope_complete"])
                self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

        data = self.valid_bundle()
        future = data["collections"]["future_schema"][0]["receipt"]
        future["datasets"]["rows"] = [
            {
                "created_on": self.window_start,
                "privilege": "SELECT",
                "grant_on": "TABLE",
                "name": "ANALYTICS.OTHER.<TABLE>",
                "grant_to": "ROLE",
                "grantee_name": "DATA_READER",
                "grant_option": "false",
            }
        ]
        future["row_count"] += 1
        future["dataset_row_counts"]["rows"] = 1
        rehash(future)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

    def test_stale_receipt_and_scope_gaps_block_completeness(self) -> None:
        data = self.valid_bundle()
        stale = data["collections"]["session"]["receipt"]
        stale["collected_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        rehash(stale)
        data["collections"]["future_schema"] = []
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(report["scope_coverage"]["status"], "INCOMPLETE")
        self.assertTrue(report["completeness_claim_blocked"])
        self.assertTrue(any("exceeds" in issue for item in report["receipt_assessments"] for issue in item["issues"]))

    def test_current_historical_drift_is_classified_not_hidden(self) -> None:
        data = self.valid_bundle()
        current = data["collections"]["role_current"][1]["receipt"]
        current["datasets"]["rows"][0]["grant_option"] = "true"
        rehash(current)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertIn("role_current:DATA_READER", report["drift_requiring_review"])
        self.assertEqual(
            report["historical_current_reconciliation"]["role_current:DATA_READER"]["status"],
            "DRIFT_REQUIRES_REVIEW",
        )
        self.assertTrue(report["completeness_claim_blocked"])

    def test_missing_policy_share_and_inherited_grant_review_remain_explicit(self) -> None:
        data = self.valid_bundle()
        data["metadata"]["external_boundaries"] = {}
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(
            report["missing_external_boundaries"],
            ["object_policies", "shares", "inherited_grants_capability"],
        )
        self.assertTrue(report["completeness_claim_blocked"])

    def test_nonempty_request_with_empty_declared_coverage_blocks(self) -> None:
        data = self.valid_bundle()
        data["metadata"]["coverage"] = {
            "roles": [],
            "users": [],
            "database_roles": [],
            "future_databases": [],
            "future_schemas": [],
        }
        for key in (
            "role_current",
            "role_parents",
            "user_current",
            "database_role_current",
            "future_database",
            "future_schema",
        ):
            data["collections"][key] = []
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(report["scope_coverage"]["status"], "INCOMPLETE")
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertTrue(report["absence_claim_blocked"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

    def test_stale_server_observation_blocks_rehashed_receipt(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["session"]["receipt"]
        receipt["datasets"]["session_context"][0]["observed_at"] = "2001-01-01T00:00:00Z"
        rehash(receipt)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertTrue(any("observed_at" in issue for issue in report["scope_coverage"]["issues"]))
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

    def test_documented_secondary_role_shape_is_normalized(self) -> None:
        data = self.valid_bundle()
        data["collections"]["session"]["receipt"]["datasets"]["session_context"][0]["secondary_roles"] = {
            "roles": "DATA_READER",
            "value": "ALL",
        }
        rehash(data["collections"]["session"]["receipt"])
        for key in MODULE.COLLECTION_KEYS:
            for wrapper in data["collections"][key]:
                wrapper["receipt"]["datasets"]["execution_context"][0]["secondary_roles"] = {
                    "roles": "DATA_READER",
                    "value": "ALL",
                }
                rehash(wrapper["receipt"])
        for proof in data["verification"]["positive"] + data["verification"]["negative"]:
            proof["secondary_roles_mode"] = "ALL"
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "OBJECT_PRIVILEGE_PATH_PROVEN")

    def test_malformed_secondary_roles_never_becomes_none(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["session"]["receipt"]
        receipt["datasets"]["session_context"][0]["secondary_roles"] = {"unexpected": []}
        rehash(receipt)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertTrue(any("roles/value" in issue for issue in report["scope_coverage"]["issues"]))

    def test_mismatched_same_statement_context_blocks(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["role_current"][0]["receipt"]
        receipt["datasets"]["execution_context"][0]["primary_role"] = "SECURITYADMIN"
        rehash(receipt)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertTrue(any("authorization context" in issue for issue in report["scope_coverage"]["issues"]))

    def test_direct_user_object_grant_requires_secondary_roles_all(self) -> None:
        data = self.valid_bundle()
        data["request"]["object"] = "ANALYTICS.CURATED.DIRECT_ONLY"
        for proof in data["verification"]["positive"] + data["verification"]["negative"]:
            proof["object"] = "ANALYTICS.CURATED.DIRECT_ONLY"
        direct = {
            "created_on": self.window_start,
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "ANALYTICS.CURATED.DIRECT_ONLY",
            "role": None,
            "granted_to": "USER",
            "grantee_name": "ALICE",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        assignment = data["collections"]["user_current"][0]["receipt"]["datasets"]["rows"][0]
        data["collections"]["user_current"] = [self.wrapper("access-user-current", [assignment, direct], user="ALICE")]
        historical = data["collections"]["historical"]["receipt"]
        historical_direct = {key: value for key, value in direct.items() if key != "role"}
        historical["datasets"]["grants_to_roles"].append(historical_direct)
        historical["datasets"]["grants_to_roles"].sort(key=COLLECTOR.canonical_json)
        historical["dataset_row_counts"]["grants_to_roles"] += 1
        historical["row_count"] += 1
        rehash(historical)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertFalse(report["positive_access_claim_supported"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "NOT_PROVEN")
        self.assertTrue(report["analysis"]["direct_user_paths"])

        session_receipt = data["collections"]["session"]["receipt"]
        session_receipt["datasets"]["session_context"][0]["secondary_roles"] = {
            "roles": "",
            "value": "ALL",
        }
        rehash(session_receipt)
        for key in MODULE.COLLECTION_KEYS:
            for wrapper in data["collections"][key]:
                wrapper["receipt"]["datasets"]["execution_context"][0]["secondary_roles"] = {
                    "roles": "",
                    "value": "ALL",
                }
                rehash(wrapper["receipt"])
        for proof in data["verification"]["positive"] + data["verification"]["negative"]:
            proof["secondary_roles_mode"] = "ALL"
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["positive_access_claim_supported"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "OBJECT_PRIVILEGE_PATH_PROVEN")

    def test_graph_path_without_behavior_receipt_is_not_a_positive_access_claim(self) -> None:
        data = self.valid_bundle()
        data["verification"] = {"positive": [], "negative": []}
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertTrue(report["object_privilege_path_supported"])
        self.assertFalse(report["positive_access_claim_supported"])
        self.assertEqual(report["analysis"]["verification"]["positive_proof"]["status"], "NOT_PROVEN")

    def test_database_role_linkage_proves_the_correct_direction(self) -> None:
        data = self.valid_bundle()
        link = {
            "created_on": self.window_start,
            "privilege": "USAGE",
            "granted_on": "DATABASE_ROLE",
            "name": "ANALYTICS.READER",
            "granted_to": "ROLE",
            "grantee_name": "ANALYST",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        object_grant = {
            "created_on": self.window_start,
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "ANALYTICS.CURATED.ORDERS",
            "granted_to": "DATABASE_ROLE",
            "grantee_name": "ANALYTICS.READER",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        data["metadata"]["coverage"]["roles"] = ["ANALYST", "PUBLIC"]
        data["metadata"]["coverage"]["database_roles"] = ["ANALYTICS.READER"]
        data["collections"]["role_current"] = [
            self.wrapper("access-role-current", [link], role="ANALYST"),
            self.wrapper("access-role-current", [], role="PUBLIC"),
        ]
        data["collections"]["role_parents"] = [
            self.wrapper("access-role-parents", [], role="ANALYST"),
        ]
        data["collections"]["database_role_current"] = [
            self.wrapper(
                "access-database-role-current",
                [object_grant],
                database_role="ANALYTICS.READER",
            )
        ]
        historical = self.wrapper(
            "access",
            [
                {
                    "EVIDENCE": {
                        "_dataset": "grants_to_roles",
                        **link,
                        "granted_to": "ACCOUNT ROLE",
                    }
                },
                {
                    "EVIDENCE": {
                        "_dataset": "grants_to_roles",
                        **object_grant,
                        "granted_to": "DATABASE ROLE",
                    }
                },
                {
                    "EVIDENCE": {
                        "_dataset": "grants_to_users",
                        "role": "ANALYST",
                        "grantee_name": "ALICE",
                        "granted_by": "SECURITYADMIN",
                    }
                },
                {"EVIDENCE": {"_dataset": "roles", "name": "ANALYST", "role_type": "ROLE"}},
                {
                    "EVIDENCE": {
                        "_dataset": "roles",
                        "name": "READER",
                        "role_type": "DATABASE_ROLE",
                        "role_database_name": "ANALYTICS",
                    }
                },
            ],
        )
        data["collections"]["historical"] = historical
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertIn(
            "ALICE -> ANALYST -> ANALYTICS.READER",
            {item["path"] for item in report["analysis"]["effective_access"]["paths"]},
        )

    def test_public_is_always_required_and_historical_drift_blocks(self) -> None:
        data = self.valid_bundle()
        public_grant = {
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "ANALYTICS.CURATED.ORDERS",
            "granted_to": "ACCOUNT ROLE",
            "grantee_name": "PUBLIC",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        historical = data["collections"]["historical"]["receipt"]
        historical["datasets"]["grants_to_roles"].append(public_grant)
        historical["datasets"]["grants_to_roles"].sort(key=COLLECTOR.canonical_json)
        historical["dataset_row_counts"]["grants_to_roles"] += 1
        historical["row_count"] += 1
        rehash(historical)
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertIn("role_current:PUBLIC", report["drift_requiring_review"])
        self.assertFalse(report["grant_graph_scope_complete"])
        self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

    def test_matching_public_grant_is_always_active_exactly_once(self) -> None:
        data = self.valid_bundle()
        current_public = {
            "privilege": "SELECT",
            "granted_on": "TABLE",
            "name": "ANALYTICS.CURATED.ORDERS",
            "granted_to": "ROLE",
            "grantee_name": "PUBLIC",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        historical_public = {**current_public, "granted_to": "ACCOUNT ROLE"}
        historical = data["collections"]["historical"]["receipt"]
        historical["datasets"]["grants_to_roles"].append(historical_public)
        historical["datasets"]["grants_to_roles"].sort(key=COLLECTOR.canonical_json)
        historical["dataset_row_counts"]["grants_to_roles"] += 1
        historical["row_count"] += 1
        rehash(historical)
        data["collections"]["role_current"] = [
            wrapper for wrapper in data["collections"]["role_current"] if wrapper["selector"]["role"] != "PUBLIC"
        ] + [self.wrapper("access-role-current", [current_public], role="PUBLIC")]
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        public_paths = [
            item for item in report["analysis"]["effective_access"]["paths"] if item["path"] == "ALICE -> PUBLIC"
        ]
        self.assertEqual(len(public_paths), 1)
        self.assertFalse(public_paths[0]["via_secondary_role"])

    def test_public_builtin_database_role_is_reported_but_not_used_or_reconciled(self) -> None:
        data = self.valid_bundle()
        built_in_database_role = {
            "privilege": "USAGE",
            "granted_on": "DATABASE_ROLE",
            "name": "ALERT_VIEWER",
            "granted_to": "ROLE",
            "grantee_name": "PUBLIC",
            "grant_option": "false",
            "granted_by": "",
        }
        data["collections"]["role_current"] = [
            wrapper for wrapper in data["collections"]["role_current"] if wrapper["selector"]["role"] != "PUBLIC"
        ] + [self.wrapper("access-role-current", [built_in_database_role], role="PUBLIC")]

        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertTrue(report["grant_graph_scope_complete"])
        self.assertEqual(report["drift_requiring_review"], [])
        self.assertEqual(
            report["unresolved_imported_database_role_edges"],
            [
                {
                    "source": "role_current:PUBLIC",
                    "parent": "PUBLIC",
                    "database_role": "ALERT_VIEWER",
                    "status": "UNRESOLVED_IMPORTED_SYSTEM_BOUNDARY",
                    "used_for_access_proof": False,
                    "reason": (
                        "Unqualified database-role links can be Snowflake-provided or imported and are "
                        "not reliably represented in Account Usage."
                    ),
                }
            ],
        )
        self.assertNotIn("ALERT_VIEWER", report["scope_coverage"]["request_derived_required"]["database_roles"])
        self.assertFalse(
            any("ALERT_VIEWER" in path["path"] for path in report["analysis"]["effective_access"].get("paths", []))
        )

    def test_future_schema_precedence_ignores_grantee_and_privilege(self) -> None:
        data = self.valid_bundle()
        database_row = {
            "created_on": self.window_start,
            "privilege": "SELECT",
            "grant_on": "TABLE",
            "name": "ANALYTICS.<TABLE>",
            "grant_to": "ROLE",
            "grantee_name": "R1",
            "grant_option": "false",
            "granted_by": "SECURITYADMIN",
        }
        schema_row = {
            **database_row,
            "privilege": "INSERT",
            "name": "ANALYTICS.CURATED.<TABLE>",
            "grantee_name": "R2",
        }
        data["collections"]["future_database"] = [
            self.wrapper("access-future-database", [database_row], database="ANALYTICS")
        ]
        data["collections"]["future_schema"] = [
            self.wrapper("access-future-schema", [schema_row], schema="ANALYTICS.CURATED")
        ]
        report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(report["grant_graph_scope_complete"])
        precedence = report["analysis"]["future_grant_precedence"]
        self.assertEqual(len(precedence), 1)
        self.assertEqual(precedence[0]["effective_precedence"], "SCHEMA")

    def test_malformed_required_wrappers_do_not_crash_or_claim(self) -> None:
        for key, malformed in (("historical", []), ("session", "wrong"), ("historical", None)):
            data = self.valid_bundle()
            data["collections"][key] = malformed
            with self.subTest(key=key, malformed=malformed):
                report = MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))
                self.assertFalse(report["grant_graph_scope_complete"])
                self.assertEqual(report["analysis"]["effective_access"]["status"], "UNVERIFIED_EVIDENCE")

    def test_forged_receipt_cannot_smuggle_credentials(self) -> None:
        data = self.valid_bundle()
        receipt = data["collections"]["role_current"][0]["receipt"]
        receipt["datasets"]["rows"][0]["note"] = "Authorization: Bearer secret-payload-value"
        rehash(receipt)
        with self.assertRaisesRegex(MODULE.AccessEvidenceError, "credential-shaped"):
            MODULE.analyze_bundle(data, trusted_input_sha256=MODULE.input_sha256(data))

    def test_cli_digest_and_error_paths_are_stable(self) -> None:
        data = self.valid_bundle()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bundle.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            digest = subprocess.run(
                ["python3", str(SCRIPT), "--input", str(source), "--print-input-sha256"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(digest.returncode, 0, digest.stderr)
            self.assertEqual(digest.stdout.strip(), MODULE.input_sha256(data))
            source.write_text('{"schema_version":"wrong"}', encoding="utf-8")
            failed = subprocess.run(
                ["python3", str(SCRIPT), "--input", str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("schema_version must be 2.0", failed.stderr)
            self.assertNotIn("Traceback", failed.stderr)


if __name__ == "__main__":
    unittest.main()

"""Native DoltLite integration and adversarial publisher tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Deliberately not optional: CI must fail if the pinned native engine cannot load.
import doltlite  # noqa: F401  # must load before sqlite3

import sqlite3

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "doltlite-sync.py"
SPEC = importlib.util.spec_from_file_location("freshie_doltlite_sync", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DoltLiteSyncTests(unittest.TestCase):
    allowlist = frozenset({"discovery_runs", "skills"})

    def make_source(self, path: Path, run_id: int = 1, grade: str = "A") -> None:
        connection = sqlite3.connect(f"file:{path}?doltlite_engine=sqlite", uri=True)
        connection.executescript(
            "CREATE TABLE discovery_runs(run_id INTEGER PRIMARY KEY, completed_at TEXT);"
            "CREATE TABLE skills(id INTEGER PRIMARY KEY, skill_path TEXT UNIQUE, grade TEXT);"
        )
        connection.execute(
            "INSERT INTO discovery_runs VALUES (?, '2026-09-01T00:00:00Z')",
            (run_id,),
        )
        connection.execute("INSERT INTO skills VALUES (1, 'skills/example/SKILL.md', ?)", (grade,))
        connection.commit()
        connection.close()

    def advance_source(self, path: Path, run_id: int, grade: str) -> None:
        connection = sqlite3.connect(f"file:{path}?doltlite_engine=sqlite", uri=True)
        connection.execute(
            "INSERT INTO discovery_runs VALUES (?, '2026-09-02T00:00:00Z')",
            (run_id,),
        )
        connection.execute("UPDATE skills SET grade=?", (grade,))
        connection.commit()
        connection.close()

    @staticmethod
    def lineage(run_id: int) -> dict[str, object]:
        return {
            "repository": MODULE.FULL_DOLT_REPOSITORY,
            "ref": f"run-{run_id}",
            "commit": format(run_id, "x").rjust(32, "a"),
            "database_hash": "b" * 32,
            "direct_parent": "c" * 32,
            "run_id": run_id,
            "verified_via": MODULE.FULL_DOLT_API,
        }

    def prepare_source_receipt(self, root: Path) -> Path:
        baseline = root / "baseline.json"
        snapshot = root / "reviewed-source.snapshot.sqlite"
        if snapshot.exists():
            snapshot.unlink()
        MODULE.snapshot_sqlite(root / "inventory.sqlite", snapshot)
        connection = MODULE.stock_connection(snapshot)
        try:
            tables = MODULE.gate_membership(MODULE.source_tables(connection, "main"), self.allowlist)
            run_id = MODULE.latest_run_id(connection, "main")
            manifest = MODULE.schema_baseline_payload(connection, "main", tables, self.allowlist)
            if not baseline.exists():
                MODULE.atomic_json(baseline, manifest)
            table_receipts = MODULE.source_table_receipts(connection, "main", tables)
        finally:
            connection.close()
        body = MODULE.source_snapshot_receipt_payload(
            artifact_name="inventory.sqlite",
            backup_sha256=MODULE.file_sha256(snapshot),
            run_id=run_id,
            lineage=self.lineage(run_id),
            schema_baseline_sha256=MODULE.json_sha256(MODULE.read_json(baseline)),
            table_receipts=table_receipts,
            reviewed_by="test-reviewer",
            reviewed_at="2026-09-01T00:00:00Z",
        )
        receipt = root / "receipts" / f"source-snapshot-run-{run_id}.json"
        MODULE.atomic_json(receipt, MODULE.seal_source_snapshot_receipt(body))
        snapshot.unlink()
        return receipt

    def run_sync(self, root: Path, source_receipt: Path, **kwargs):
        with (
            mock.patch.object(MODULE, "resolve_full_dolt_lineage", side_effect=self.lineage),
            mock.patch.object(MODULE, "canonical_safety_gate"),
            mock.patch.object(MODULE, "gate_tracked_full_dolt_receipt"),
        ):
            return MODULE.sync_database(
                root / "inventory.sqlite",
                root / "target.db",
                root / "receipts",
                allowlist=self.allowlist,
                schema_baseline=root / "baseline.json",
                source_receipt=source_receipt,
                allow_untracked_source_receipt=True,
                **kwargs,
            )

    def sync(self, root: Path, **kwargs):
        return self.run_sync(root, self.prepare_source_receipt(root), **kwargs)

    def test_sync_is_native_bound_immutable_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            first = self.sync(root)
            second = self.sync(root)

            self.assertEqual(first["doltlite"]["engine"], "prolly")
            self.assertTrue(first["operation"]["commit_created"])
            self.assertFalse(second["operation"]["commit_created"])
            self.assertEqual(first["doltlite"]["commit"], second["doltlite"]["commit"])
            receipt = json.loads((root / "receipts/doltlite-run-1.json").read_text())
            self.assertEqual(receipt["source"]["full_dolt"], self.lineage(1))
            self.assertEqual(receipt["schema_version"], 3)
            self.assertEqual(receipt["source"]["artifact_name"], "inventory.sqlite")
            self.assertEqual(
                receipt["source"]["reviewed_receipt_sha256"],
                json.loads((root / "receipts/source-snapshot-run-1.json").read_text())["receipt_sha256"],
            )
            baseline = json.loads((root / "baseline.json").read_text())
            self.assertEqual(
                baseline["publication_denominator"],
                {
                    "mode": "exact",
                    "included_table_count": 2,
                    "allowed_but_excluded_tables": [],
                },
            )
            connection = sqlite3.connect(root / "target.db")
            message = connection.execute(
                "SELECT message FROM dolt_log WHERE commit_hash=?",
                (first["doltlite"]["commit"],),
            ).fetchone()[0]
            connection.close()
            self.assertIn(self.lineage(1)["commit"], message)

    def test_forged_lineage_and_receipt_rewrite_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            self.sync(root)
            receipt_path = root / "receipts/doltlite-run-1.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["source"]["full_dolt"]["commit"] = "b" * 32
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(MODULE.SyncError, "immutable receipt"):
                self.sync(root)

            other = Path(directory) / "other"
            other.mkdir()
            self.make_source(other / "inventory.sqlite")
            reviewed = self.prepare_source_receipt(other)

            def forged(run):
                return {
                    **self.lineage(run),
                    "repository": "attacker/forged",
                }

            with (
                mock.patch.object(MODULE, "resolve_full_dolt_lineage", side_effect=forged),
                mock.patch.object(MODULE, "canonical_safety_gate"),
                mock.patch.object(MODULE, "gate_tracked_full_dolt_receipt"),
                self.assertRaisesRegex(MODULE.SyncError, "unverified evidence"),
            ):
                MODULE.sync_database(
                    other / "inventory.sqlite",
                    other / "target.db",
                    other / "receipts",
                    allowlist=self.allowlist,
                    schema_baseline=other / "baseline.json",
                    source_receipt=reviewed,
                    allow_untracked_source_receipt=True,
                )

    def test_full_dolt_resolver_cross_checks_tag_run_and_head(self):
        commit = "a" * 32

        def query(_repository, revision, sql):
            if "dolt_tags" in sql:
                return [{"tag_hash": commit}]
            if "MAX(id)" in sql:
                return [{"run_id": 20}]
            if "dolt_hashof_db" in sql:
                return [{"database_hash": "b" * 32}]
            if "dolt_commit_ancestors" in sql:
                return [{"parent_hash": "c" * 32}]
            self.assertEqual(revision, "main")
            return [{"commit_hash": commit}]

        result = MODULE.resolve_full_dolt_lineage(20, query=query)
        self.assertEqual(result["commit"], commit)
        self.assertEqual(result["database_hash"], "b" * 32)
        self.assertEqual(result["direct_parent"], "c" * 32)

        def forged_query(repository, revision, sql):
            rows = query(repository, revision, sql)
            if "dolt_log" in sql:
                rows[0]["commit_hash"] = "b" * 32
            return rows

        with self.assertRaisesRegex(MODULE.SyncError, "tag/hash mismatch"):
            MODULE.resolve_full_dolt_lineage(20, query=forged_query)

        def malformed_database_hash(repository, revision, sql):
            rows = query(repository, revision, sql)
            if "dolt_hashof_db" in sql:
                rows[0]["database_hash"] = "truncated"
            return rows

        with self.assertRaisesRegex(MODULE.SyncError, "invalid database hash"):
            MODULE.resolve_full_dolt_lineage(20, query=malformed_database_hash)

        with tempfile.TemporaryDirectory() as directory:
            histogram = Path(directory) / "grade-histogram.json"
            histogram.write_text(json.dumps({"run_id": 20, "dolt_commit": commit}))
            with mock.patch.object(MODULE, "HISTOGRAM", histogram):
                MODULE.gate_tracked_full_dolt_receipt(20, commit)
                with self.assertRaisesRegex(MODULE.SyncError, "does not match"):
                    MODULE.gate_tracked_full_dolt_receipt(20, "b" * 32)

    def test_canonical_completeness_evidence_and_grade_gates_are_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "snapshot.sqlite"
            connection = sqlite3.connect(f"file:{snapshot}?doltlite_engine=sqlite", uri=True)
            connection.executescript(
                "CREATE TABLE discovery_runs(id INTEGER PRIMARY KEY, total_skills INTEGER);"
                "CREATE TABLE skills(id INTEGER PRIMARY KEY, run_id INTEGER);"
                "CREATE TABLE skill_compliance(run_id INTEGER, skill_path TEXT, grade TEXT, score INTEGER);"
                "CREATE TABLE forge_proofs(id INTEGER PRIMARY KEY, evidence_class TEXT, artifact_uri TEXT, artifact_sha256 TEXT);"
                "INSERT INTO discovery_runs VALUES (1, NULL);"
                "INSERT INTO skills VALUES (1, 1);"
                "INSERT INTO skill_compliance VALUES (1, 'skills/example/SKILL.md', 'A', 100);"
            )
            connection.commit()
            connection.close()
            grades = root / "grades.csv"
            histogram = root / "grade-histogram.json"
            grades.write_text("skill_path,grade,score\nskills/example/SKILL.md,A,100\n")
            histogram.write_text(json.dumps({"run_id": 1, "total": 1, "grades": {"A": 1}}))
            with (
                mock.patch.object(MODULE, "GRADES_CSV", grades),
                mock.patch.object(MODULE, "HISTOGRAM", histogram),
                mock.patch.object(MODULE, "REPO_ROOT", root),
            ):
                with self.assertRaisesRegex(MODULE.SyncError, "incomplete"):
                    MODULE.canonical_safety_gate(snapshot, 1)

                connection = sqlite3.connect(f"file:{snapshot}?doltlite_engine=sqlite", uri=True)
                connection.execute("UPDATE discovery_runs SET total_skills=1 WHERE id=1")
                connection.execute("INSERT INTO forge_proofs VALUES (1, 'E2', NULL, NULL)")
                connection.commit()
                connection.close()
                with self.assertRaisesRegex(MODULE.SyncError, "E0 demotion"):
                    MODULE.canonical_safety_gate(snapshot, 1)

                connection = sqlite3.connect(f"file:{snapshot}?doltlite_engine=sqlite", uri=True)
                connection.execute("UPDATE forge_proofs SET evidence_class='E0'")
                connection.commit()
                connection.close()
                histogram.write_text(json.dumps({"run_id": 2, "total": 1, "grades": {"A": 1}}))
                with self.assertRaisesRegex(MODULE.SyncError, "stale"):
                    MODULE.canonical_safety_gate(snapshot, 1)

    def test_process_lock_refuses_concurrent_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            with MODULE.process_lock(root / "target.db"):
                with self.assertRaisesRegex(MODULE.SyncError, "another DoltLite sync"):
                    self.sync(root)

    def test_remote_url_cannot_leak_embedded_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            with self.assertRaisesRegex(MODULE.SyncError, "must not embed credentials"):
                self.sync(root, remote_url="https://user:secret@example.test/repo")
            self.assertFalse((root / "target.db").exists())

    def test_schema_and_column_drift_require_explicit_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            self.sync(root)
            connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
            connection.execute("ALTER TABLE skills ADD COLUMN secret_token TEXT")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(MODULE.SyncError, "unapproved schema/column drift"):
                self.sync(root)

    def test_allowed_but_excluded_table_is_not_in_publication_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            connection = MODULE.stock_connection(root / "inventory.sqlite")
            try:
                tables = MODULE.source_tables(connection, "main")
                allowlist = self.allowlist | {"canonical_extra"}
                baseline = MODULE.schema_baseline_payload(connection, "main", tables, allowlist)
            finally:
                connection.close()
            baseline_path = root / "baseline.json"
            MODULE.atomic_json(baseline_path, baseline)
            self.assertEqual(
                baseline["publication_denominator"]["allowed_but_excluded_tables"],
                ["canonical_extra"],
            )
            MODULE.gate_publication_denominator(tables, allowlist, baseline_path)
            with self.assertRaisesRegex(MODULE.SyncError, "reviewed publication denominator"):
                MODULE.gate_publication_denominator([*tables, "canonical_extra"], allowlist, baseline_path)

    def test_same_run_data_rewrite_fails_without_advancing_local_head(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            first = self.sync(root)
            connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
            connection.execute("UPDATE skills SET grade='B'")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(MODULE.SyncError, "parity failure"):
                self.sync(root)
            target = sqlite3.connect(root / "target.db")
            head = target.execute("SELECT dolt_hashof('HEAD')").fetchone()[0]
            target.close()
            self.assertEqual(head, first["doltlite"]["commit"])

    def test_reviewed_source_receipt_rejects_non_grade_mutation_before_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            reviewed = self.prepare_source_receipt(root)
            connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
            connection.execute("UPDATE skills SET skill_path='skills/renamed/SKILL.md'")
            connection.commit()
            connection.close()

            with self.assertRaisesRegex(MODULE.SyncError, "does not bind the current source snapshot"):
                self.run_sync(root, reviewed)
            self.assertFalse((root / "target.db").exists())

    def test_resealed_table_receipt_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            reviewed = self.prepare_source_receipt(root)
            payload = json.loads(reviewed.read_text())
            payload["table_receipts"][0]["rows"] += 1
            payload["table_receipts_sha256"] = MODULE.json_sha256(payload["table_receipts"])
            body = {key: value for key, value in payload.items() if key != "receipt_sha256"}
            payload["receipt_sha256"] = MODULE.json_sha256(body)
            reviewed.write_text(json.dumps(payload))

            with self.assertRaisesRegex(MODULE.SyncError, "does not bind the current source snapshot"):
                self.run_sync(root, reviewed)
            self.assertFalse((root / "target.db").exists())

    def test_production_source_receipt_has_no_untracked_escape_hatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            reviewed = self.prepare_source_receipt(root)
            with self.assertRaisesRegex(MODULE.SyncError, "must be tracked under"):
                with (
                    mock.patch.object(MODULE, "resolve_full_dolt_lineage", side_effect=self.lineage),
                    mock.patch.object(MODULE, "canonical_safety_gate"),
                    mock.patch.object(MODULE, "gate_tracked_full_dolt_receipt"),
                ):
                    MODULE.sync_database(
                        root / "inventory.sqlite",
                        root / "target.db",
                        root / "receipts",
                        allowlist=self.allowlist,
                        schema_baseline=root / "baseline.json",
                        source_receipt=reviewed,
                    )
            self.assertFalse((root / "target.db").exists())

    def test_views_and_triggers_fail_before_target_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
            connection.execute("CREATE VIEW skill_names AS SELECT skill_path FROM skills")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(MODULE.SyncError, "views/triggers"):
                self.sync(root)
            self.assertFalse((root / "target.db").exists())

    def test_digest_external_sort_matches_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.sqlite"
            connection = sqlite3.connect(f"file:{path}?doltlite_engine=sqlite", uri=True)
            connection.execute("CREATE TABLE sample(id INTEGER, value TEXT)")
            rows = [(3, "c"), (1, "a"), (2, "b"), (2, "b")]
            connection.executemany("INSERT INTO sample VALUES (?,?)", rows)
            connection.commit()
            hashes = sorted(
                hashlib.sha256(b"".join(MODULE.encode_value(value) for value in row)).digest() for row in rows
            )
            expected = hashlib.sha256(b"sample")
            for value in hashes:
                expected.update(value)
            with mock.patch.object(MODULE, "TABLE_DIGEST_CHUNK_ROWS", 2):
                count, actual = MODULE.table_digest(connection, "main", "sample")
            connection.close()
            self.assertEqual(count, len(rows))
            self.assertEqual(actual, expected.hexdigest())

    def test_run19_to_run20_ancestry_is_mandatory_and_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite", run_id=20)
            with self.assertRaisesRegex(MODULE.SyncError, "missing immutable predecessor"):
                self.sync(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite", run_id=19)
            remote = root / "remote.db"
            remote_url = f"file://{remote}"
            run19 = self.sync(root, allow_run19_bootstrap=True, remote_url=remote_url)
            self.advance_source(root / "inventory.sqlite", 20, "B")
            run20 = self.sync(root, remote_url=remote_url)
            rerun20 = self.sync(root, remote_url=remote_url, push=True)
            self.assertEqual(run20["history"]["parent_commit"], run19["doltlite"]["commit"])
            self.assertFalse(rerun20["operation"]["commit_created"])
            self.assertEqual(rerun20["operation"]["publication_state"], "complete")
            self.assertEqual(
                rerun20["publication"]["required_refs"]["run-19"],
                run19["doltlite"]["commit"],
            )
            connection = sqlite3.connect(root / "target.db")
            parent = connection.execute("SELECT dolt_hashof('run-20~')").fetchone()[0]
            connection.close()
            self.assertEqual(parent, run19["doltlite"]["commit"])

    def test_partial_push_is_journaled_and_retry_completes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            remote = root / "remote.db"
            real_push = MODULE.push_reference

            def fail_main(connection, branch):
                if branch == "main":
                    raise sqlite3.OperationalError("injected main failure")
                return real_push(connection, branch)

            with mock.patch.object(MODULE, "push_reference", side_effect=fail_main):
                with self.assertRaisesRegex(MODULE.SyncError, "recover by rerunning"):
                    self.sync(root, remote_url=f"file://{remote}", push=True)
            journal_path = root / "receipts/doltlite-run-1.publication.json"
            journal = json.loads(journal_path.read_text())
            self.assertEqual(journal["state"], "partial")
            self.assertIn("run-1", journal["results"])
            self.assertNotIn("main", journal["results"])
            self.assertTrue((root / "receipts/doltlite-run-1.json").is_file())

            result = self.sync(root, remote_url=f"file://{remote}", push=True)
            self.assertEqual(result["operation"]["publication_state"], "complete")

    def test_unknown_table_fails_before_target_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
            connection.execute("CREATE TABLE secret_cache(token TEXT)")
            connection.commit()
            connection.close()
            with self.assertRaisesRegex(MODULE.SyncError, "secret_cache"):
                self.sync(root)
            self.assertFalse((root / "target.db").exists())

    def test_secret_inside_approved_table_fails_without_disclosure(self):
        cases = {
            "github-token": "ghp_" + "A" * 36,
            "anthropic-key": "sk-ant-api03-" + "A" * 40,
            "stripe-live-key": "sk_live_" + "A" * 24,
            "gitlab-token": "glpat-" + "A" * 24,
            "huggingface-token": "hf_" + "A" * 36,
            "npm-token": "npm_" + "A" * 36,
            "databricks-token": "dapi" + "a" * 32,
            "azure-account-key": "AccountKey=" + "A" * 44 + ";",
            "bearer-token": "Authorization: Bearer " + "A" * 36,
        }
        for family, secret in cases.items():
            with self.subTest(family=family), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_source(root / "inventory.sqlite")
                connection = sqlite3.connect(f"file:{root / 'inventory.sqlite'}?doltlite_engine=sqlite", uri=True)
                connection.execute("UPDATE skills SET skill_path=?", (secret,))
                connection.commit()
                connection.close()

                with self.assertRaises(MODULE.SyncError) as raised:
                    self.sync(root)

                self.assertIn(f"secret-shaped {family}", str(raised.exception))
                self.assertNotIn(secret, str(raised.exception))
                self.assertFalse((root / "target.db").exists())

    def test_immutable_run_branch_cannot_be_repointed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_source(root / "inventory.sqlite")
            self.sync(root)
            connection = sqlite3.connect(root / "target.db")
            connection.execute("UPDATE skills SET grade='C'")
            connection.commit()
            changed = connection.execute("SELECT dolt_commit('-A','-m','changed')").fetchone()[0]
            with self.assertRaises(MODULE.SyncError):
                MODULE.protect_run_branch(connection, 1, changed)
            connection.close()


if __name__ == "__main__":
    unittest.main()

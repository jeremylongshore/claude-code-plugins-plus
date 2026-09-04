"""Contract and adversarial tests for the model-neutral Snowflake operator."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
SCRIPT = PACK / "shared" / "snowflake_operator.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


operator = load_module("snowflake_operator_under_test", SCRIPT)


def run_script(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        timeout=5,
        check=False,
    )


class SnowflakeOperatorTests(unittest.TestCase):
    def test_registry_is_the_closed_required_surface(self) -> None:
        self.assertEqual(
            tuple(operator.WORKFLOWS),
            (
                "pipeline-triage",
                "query-id-forensics",
                "deploy-preflight",
                "access-review",
                "failover-readiness",
            ),
        )
        self.assertEqual(len({item.analyzer for item in operator.WORKFLOWS.values()}), 5)
        for workflow in operator.WORKFLOWS.values():
            target = operator._resolve_analyzer(workflow)
            self.assertTrue(target.is_file())
            self.assertFalse(target.is_symlink())
            self.assertTrue(target.is_relative_to((PACK / "skills" / workflow.skill).resolve()))

    def test_help_and_listing_are_fast_and_actionable(self) -> None:
        listing = run_script(SCRIPT, "list", "--json")
        self.assertEqual(listing.returncode, 0)
        payload = json.loads(listing.stdout)
        self.assertEqual(
            [row["name"] for row in payload["workflows"]],
            list(operator.WORKFLOWS),
        )
        self.assertEqual(listing.stderr, b"")

        for name in operator.WORKFLOWS:
            with self.subTest(name=name):
                help_result = run_script(SCRIPT, name, "--help")
                self.assertEqual(help_result.returncode, 0)
                self.assertIn(b"--input", help_result.stdout)
                self.assertIn(b"--output", help_result.stdout)
                self.assertEqual(help_result.stderr, b"")

        unknown = run_script(SCRIPT, "not-a-workflow")
        self.assertEqual(unknown.returncode, 2)
        self.assertIn(b"invalid choice", unknown.stderr)
        self.assertNotIn(b"Traceback", unknown.stderr)

    def test_registered_path_rejects_traversal_and_internal_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "pack"
            target = root / "skills" / "demo" / "scripts" / "analyze.py"
            target.parent.mkdir(parents=True)
            target.write_text("pass\n", encoding="utf-8")
            workflow = operator.Workflow("demo", "demo", "scripts/analyze.py", "demo")
            self.assertEqual(operator._resolve_analyzer(workflow, root), target)

            for analyzer in ("", "/tmp/analyze.py", "../analyze.py", "scripts/../analyze.py"):
                with self.subTest(analyzer=analyzer):
                    invalid = operator.Workflow("demo", "demo", analyzer, "demo")
                    with self.assertRaises(operator.OperatorError):
                        operator._resolve_analyzer(invalid, root)

            outside = Path(temporary_directory) / "outside.py"
            outside.write_text("pass\n", encoding="utf-8")
            target.unlink()
            target.symlink_to(outside)
            with self.assertRaises(operator.OperatorError):
                operator._resolve_analyzer(workflow, root)

            target.unlink()
            target.mkdir()
            with self.assertRaises(operator.OperatorError):
                operator._resolve_analyzer(workflow, root)

            shutil.rmtree(target)
            scripts = target.parent
            scripts.rmdir()
            scripts.symlink_to(Path(temporary_directory) / "missing")
            with self.assertRaises(operator.OperatorError):
                operator._resolve_analyzer(workflow, root)

    def test_process_boundary_preserves_caller_context_and_argv_items(self) -> None:
        payload = "-leading; $(touch should-not-exist)\nwith spaces"
        workflow = operator.WORKFLOWS["query-id-forensics"]
        args = argparse.Namespace(
            input="evidence.json",
            output=None,
            trusted_input_sha256=payload,
            markdown_output=None,
            print_input_sha256=False,
        )
        command = operator._child_command(workflow, args)
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[2], "--input=evidence.json")
        self.assertIn(f"--trusted-input-sha256={payload}", command)

        completed = subprocess.CompletedProcess(command, 1)
        with mock.patch.object(operator.subprocess, "run", return_value=completed) as called:
            self.assertEqual(operator._run(workflow, args), 1)
        called.assert_called_once_with(command, check=False)
        self.assertFalse(Path("should-not-exist").exists())

    def test_input_output_aliases_fail_before_analyzer_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence = root / "evidence.json"
            evidence.write_bytes(b"evidence")
            before = evidence.read_bytes()
            with self.assertRaises(operator.OperatorError):
                operator._validate_output_alias(str(evidence), str(evidence))
            self.assertEqual(evidence.read_bytes(), before)

            fifo = root / "report.fifo"
            os.mkfifo(fifo)
            with self.assertRaises(operator.OperatorError):
                operator._validate_output_alias(str(evidence), str(fifo))
            self.assertTrue(stat.S_ISFIFO(fifo.lstat().st_mode))

            hardlink = root / "hardlink.json"
            os.link(evidence, hardlink)
            with self.assertRaises(operator.OperatorError):
                operator._validate_output_alias(str(evidence), str(hardlink))
            self.assertEqual(evidence.read_bytes(), before)

            symlink = root / "symlink.json"
            symlink.symlink_to(evidence)
            with self.assertRaises(operator.OperatorError):
                operator._validate_output_alias(str(evidence), str(symlink))
            self.assertEqual(evidence.read_bytes(), before)

    def test_query_rejects_secondary_output_aliases_without_modifying_input(self) -> None:
        fixture = PACK / "skills/snowflake-query-forensics/tests/fixtures/query_evidence.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence = root / "evidence.json"
            shutil.copy2(fixture, evidence)
            before = evidence.read_bytes()
            input_alias = run_script(
                SCRIPT,
                "query-id-forensics",
                f"--input={evidence}",
                f"--markdown-output={evidence}",
            )
            self.assertEqual(input_alias.returncode, 2)
            self.assertIn(b"operator error", input_alias.stderr)
            self.assertEqual(evidence.read_bytes(), before)

            shared_output = root / "shared-output"
            output_alias = run_script(
                SCRIPT,
                "query-id-forensics",
                f"--input={evidence}",
                f"--output={shared_output}",
                f"--markdown-output={shared_output}",
            )
            self.assertEqual(output_alias.returncode, 2)
            self.assertIn(b"must not alias", output_alias.stderr)
            self.assertFalse(shared_output.exists())
            self.assertEqual(evidence.read_bytes(), before)

    def test_invalid_evidence_matches_each_canonical_analyzer_exactly(self) -> None:
        bad = b'{"broken":'
        with tempfile.TemporaryDirectory() as temporary_directory:
            cwd = Path(temporary_directory)
            (cwd / "bad.json").write_bytes(bad)
            cases = (
                (
                    "pipeline-triage",
                    "snowflake-pipeline-guardian/scripts/analyze_pipeline_state.py",
                    ("--input=bad.json",),
                    ("--input=bad.json",),
                ),
                (
                    "query-id-forensics",
                    "snowflake-query-forensics/scripts/analyze_query_evidence.py",
                    ("--input=bad.json",),
                    ("--input=bad.json",),
                ),
                (
                    "deploy-preflight",
                    "snowflake-deploy-medic/scripts/analyze_deploy_evidence.py",
                    (
                        "--input=bad.json",
                        "--as-of=2026-09-04T00:00:00Z",
                        f"--trusted-bundle-sha256=sha256:{'0' * 64}",
                    ),
                    (
                        "--input=bad.json",
                        "--as-of=2026-09-04T00:00:00Z",
                        f"--trusted-bundle-sha256=sha256:{'0' * 64}",
                    ),
                ),
                (
                    "access-review",
                    "snowflake-access-guardian/scripts/analyze_access_evidence.py",
                    ("--input=bad.json",),
                    ("--input=bad.json",),
                ),
                (
                    "failover-readiness",
                    "snowflake-failover-readiness-drill/scripts/analyze_failover_readiness.py",
                    (
                        "--input=bad.json",
                        "--evaluated-at=2026-09-04T00:00:00Z",
                        f"--trusted-input-sha256=sha256:{'0' * 64}",
                        f"--trusted-policy-sha256=sha256:{'1' * 64}",
                        f"--trusted-operator-sha256=sha256:{'2' * 64}",
                    ),
                    (
                        "--input=bad.json",
                        "--as-of=2026-09-04T00:00:00Z",
                        f"--trusted-input-sha256=sha256:{'0' * 64}",
                        f"--trusted-policy-sha256=sha256:{'1' * 64}",
                        f"--trusted-operator-sha256=sha256:{'2' * 64}",
                    ),
                ),
            )
            for name, relative_analyzer, direct_args, wrapper_args in cases:
                with self.subTest(name=name):
                    direct = run_script(PACK / "skills" / relative_analyzer, *direct_args, cwd=cwd)
                    wrapped = run_script(SCRIPT, name, *wrapper_args, cwd=cwd)
                    self.assertEqual(
                        (wrapped.returncode, wrapped.stdout, wrapped.stderr),
                        (direct.returncode, direct.stdout, direct.stderr),
                    )

    def test_pipeline_stdout_output_is_byte_exact_and_atomic(self) -> None:
        fixture = PACK / "skills/snowflake-pipeline-guardian/scripts/fixtures/stale-chain.json"
        direct = run_script(
            PACK / "skills/snowflake-pipeline-guardian/scripts/analyze_pipeline_state.py",
            f"--input={fixture}",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            wrapped = run_script(
                SCRIPT,
                "pipeline-triage",
                f"--input={fixture}",
                f"--output={output}",
            )
            self.assertEqual(wrapped.returncode, direct.returncode)
            self.assertEqual(wrapped.stdout, b"")
            self.assertEqual(wrapped.stderr, direct.stderr)
            self.assertEqual(output.read_bytes(), direct.stdout)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_invalid_stdout_report_does_not_replace_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence = root / "bad.json"
            evidence.write_text('{"broken":', encoding="utf-8")
            output = root / "report.json"
            output.write_bytes(b"KEEP")
            wrapped = run_script(
                SCRIPT,
                "pipeline-triage",
                f"--input={evidence}",
                f"--output={output}",
            )
            self.assertEqual(wrapped.returncode, 2)
            self.assertEqual(output.read_bytes(), b"KEEP")
            self.assertEqual(list(root.glob(".report.json.*.tmp")), [])

    def test_query_native_output_translation_is_byte_exact(self) -> None:
        analyzer = PACK / "skills/snowflake-query-forensics/scripts/analyze_query_evidence.py"
        fixture = PACK / "skills/snowflake-query-forensics/tests/fixtures/query_evidence.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            direct_json = root / "direct.json"
            direct_md = root / "direct.md"
            wrapped_json = root / "wrapped.json"
            wrapped_md = root / "wrapped.md"
            direct = run_script(
                analyzer,
                f"--input={fixture}",
                f"--json-out={direct_json}",
                f"--markdown-out={direct_md}",
            )
            wrapped = run_script(
                SCRIPT,
                "query-id-forensics",
                f"--input={fixture}",
                f"--output={wrapped_json}",
                f"--markdown-output={wrapped_md}",
            )
            self.assertEqual(
                (wrapped.returncode, wrapped.stdout, wrapped.stderr),
                (direct.returncode, direct.stdout, direct.stderr),
            )
            self.assertEqual(wrapped_json.read_bytes(), direct_json.read_bytes())
            self.assertEqual(wrapped_md.read_bytes(), direct_md.read_bytes())

    def test_native_partial_failure_preserves_every_existing_output(self) -> None:
        fixture = PACK / "skills/snowflake-query-forensics/tests/fixtures/query_evidence.json"
        workflow = operator.WORKFLOWS["query-id-forensics"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            primary = root / "report.json"
            markdown = root / "report.md"
            primary.write_bytes(b"KEEP JSON")
            markdown.write_bytes(b"KEEP MARKDOWN")
            args = argparse.Namespace(
                input=str(fixture),
                output=str(primary),
                trusted_input_sha256=None,
                markdown_output=str(markdown),
                print_input_sha256=False,
            )

            def partial_failure(command: list[str], **_: object):
                for argument in command:
                    if argument.startswith(("--json-out=", "--markdown-out=")):
                        Path(argument.split("=", 1)[1]).write_bytes(b"PARTIAL")
                return subprocess.CompletedProcess(command, 2)

            with mock.patch.object(operator.subprocess, "run", side_effect=partial_failure):
                self.assertEqual(operator._run(workflow, args), 2)
            self.assertEqual(primary.read_bytes(), b"KEEP JSON")
            self.assertEqual(markdown.read_bytes(), b"KEEP MARKDOWN")
            self.assertEqual(list(root.glob(".*.tmp")), [])

    def test_native_digest_mode_does_not_replace_existing_output(self) -> None:
        fixture = PACK / "skills/snowflake-query-forensics/tests/fixtures/query_evidence.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            output.write_bytes(b"KEEP")
            wrapped = run_script(
                SCRIPT,
                "query-id-forensics",
                f"--input={fixture}",
                f"--output={output}",
                "--print-input-sha256",
            )
            self.assertEqual(wrapped.returncode, 0)
            self.assertRegex(wrapped.stdout, rb"^sha256:[0-9a-f]{64}\n$")
            self.assertEqual(output.read_bytes(), b"KEEP")

    def test_access_native_output_translation_is_byte_exact(self) -> None:
        test_module = load_module(
            "access_fixture_builder",
            PACK / "skills/snowflake-access-guardian/tests/test_access_evidence.py",
        )
        case = test_module.AccessEvidenceTests(methodName="test_trusted_receipts_prove_only_the_declared_scope")
        case.setUp()
        data = case.valid_bundle()
        digest = test_module.MODULE.input_sha256(data)
        analyzer = PACK / "skills/snowflake-access-guardian/scripts/analyze_access_evidence.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps(data), encoding="utf-8")
            direct_output = root / "direct" / "report.json"
            wrapped_output = root / "wrapped" / "report.json"
            direct = run_script(
                analyzer,
                f"--input={evidence}",
                f"--out={direct_output}",
                f"--trusted-input-sha256={digest}",
            )
            wrapped = run_script(
                SCRIPT,
                "access-review",
                f"--input={evidence}",
                f"--output={wrapped_output}",
                f"--trusted-input-sha256={digest}",
            )
            self.assertEqual(direct.returncode, 0)
            self.assertEqual(
                (wrapped.returncode, wrapped.stdout, wrapped.stderr),
                (direct.returncode, direct.stdout, direct.stderr),
            )
            self.assertEqual(wrapped_output.read_bytes(), direct_output.read_bytes())
            report = json.loads(wrapped_output.read_text(encoding="utf-8"))
            effective = report["analysis"]["effective_access"]
            self.assertEqual(
                {key: effective[key] for key in ("principal", "object", "privilege")},
                data["request"],
            )

    def test_failover_valid_exit_one_and_output_are_preserved(self) -> None:
        test_module = load_module(
            "failover_fixture_builder",
            PACK / "skills/snowflake-failover-readiness-drill/scripts/test_analyze_failover_readiness.py",
        )
        data = test_module.base()
        history = data["collector_receipts"][2]
        history["datasets"]["replication_refresh_history"][0]["primary_snapshot_timestamp"] = test_module.iso(-60, -1)
        test_module.reseal_collector(history)
        trusted = test_module.trusted(data)
        analyzer = PACK / "skills/snowflake-failover-readiness-drill/scripts/analyze_failover_readiness.py"
        direct_args = (
            f"--evaluated-at={trusted['evaluated_at']}",
            f"--trusted-input-sha256={trusted['trusted_input_sha256']}",
            f"--trusted-policy-sha256={trusted['trusted_policy_sha256']}",
            f"--trusted-operator-sha256={trusted['trusted_operator_sha256']}",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps(data), encoding="utf-8")
            direct = run_script(analyzer, f"--input={evidence}", *direct_args)
            output = root / "wrapped.json"
            wrapped = run_script(
                SCRIPT,
                "failover-readiness",
                f"--input={evidence}",
                f"--output={output}",
                f"--as-of={trusted['evaluated_at']}",
                f"--trusted-input-sha256={trusted['trusted_input_sha256']}",
                f"--trusted-policy-sha256={trusted['trusted_policy_sha256']}",
                f"--trusted-operator-sha256={trusted['trusted_operator_sha256']}",
            )
            self.assertEqual(direct.returncode, 1)
            self.assertEqual(wrapped.returncode, 1)
            self.assertEqual(wrapped.stdout, b"")
            self.assertEqual(wrapped.stderr, direct.stderr)
            self.assertEqual(output.read_bytes(), direct.stdout)

    def test_deploy_relative_input_preserves_caller_working_directory(self) -> None:
        analyzer = PACK / "skills/snowflake-deploy-medic/scripts/analyze_deploy_evidence.py"
        source = PACK / "skills/snowflake-deploy-medic/scripts/fixtures/clean-preview.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            cwd = Path(temporary_directory)
            shutil.copy2(source, cwd / "evidence.json")
            data = json.loads((cwd / "evidence.json").read_text(encoding="utf-8"))
            digest = (
                "sha256:"
                + hashlib.sha256(
                    json.dumps(
                        data,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ).encode("utf-8")
                ).hexdigest()
            )
            direct_args = (
                "--input=evidence.json",
                "--as-of=2026-09-03T12:05:00Z",
                f"--trusted-bundle-sha256={digest}",
            )
            direct = run_script(analyzer, *direct_args, cwd=cwd)
            wrapped = run_script(
                SCRIPT,
                "deploy-preflight",
                "--input=evidence.json",
                "--as-of=2026-09-03T12:05:00Z",
                f"--trusted-bundle-sha256={digest}",
                cwd=cwd,
            )
            self.assertEqual(direct.returncode, 0)
            self.assertEqual(
                (wrapped.returncode, wrapped.stdout, wrapped.stderr),
                (direct.returncode, direct.stdout, direct.stderr),
            )


if __name__ == "__main__":
    unittest.main()

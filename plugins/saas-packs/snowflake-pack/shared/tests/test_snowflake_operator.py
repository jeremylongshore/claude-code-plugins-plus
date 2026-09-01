#!/usr/bin/env python3
"""Focused subprocess parity tests for the Snowflake operator CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK_ROOT = HERE.parent.parent
SHARED = HERE.parent
OPERATOR = SHARED / "snowflake_operator.py"
sys.path.insert(0, str(SHARED))
import snowflake_operator as operator  # noqa: E402

FIXTURES = {
    "cost-leak": PACK_ROOT
    / "skills/snowflake-cost-leak-hunter/tests/fixtures/cost_evidence.json",
    "data-quality": PACK_ROOT
    / "skills/snowflake-data-quality-sentinel/tests/fixtures/pass.json",
    "pipeline-triage": PACK_ROOT
    / "skills/snowflake-pipeline-guardian/scripts/fixtures/stale-chain.json",
    "query-id-forensics": PACK_ROOT
    / "skills/snowflake-query-forensics/tests/fixtures/query_evidence.json",
    "deploy-preflight": PACK_ROOT
    / "skills/snowflake-deploy-medic/scripts/fixtures/clean-preview.json",
    "access-review": PACK_ROOT
    / "skills/snowflake-access-guardian/tests/fixtures/access.json",
    # This real pack fixture is intentionally invalid for the failover schema. It
    # proves that the wrapper preserves analyzer failures as well as successes.
    "failover-readiness": PACK_ROOT
    / "skills/snowflake-deploy-medic/scripts/fixtures/clean-preview.json",
    "governance-coverage": PACK_ROOT
    / "skills/snowflake-governance-coverage-auditor/tests/fixtures/gaps.json",
    "native-app-release": PACK_ROOT
    / "skills/snowflake-native-app-release-sheriff/tests/fixtures/clean-qa.json",
    "strong-auth": PACK_ROOT
    / "skills/snowflake-strong-auth-migration-pilot/tests/fixtures/auth.json",
}

APPROVED_COMMANDS = {
    "access-review",
    "collect",
    "cost-leak",
    "data-quality",
    "deploy-preflight",
    "failover-readiness",
    "governance-coverage",
    "native-app-release",
    "pipeline-triage",
    "query-id-forensics",
    "strong-auth",
}

ACCESS_SELECTORS = [
    "--principal",
    "ALICE",
    "--object",
    "ANALYTICS.CURATED.ORDERS",
    "--privilege",
    "SELECT",
]


def run(*arguments: object, timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, *(str(argument) for argument in arguments)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def direct_command(
    command: str, fixture: Path, *extra: object
) -> subprocess.CompletedProcess[bytes]:
    spec = operator.COMMANDS[command]
    script = operator.resolve_script(spec)
    input_arguments = (
        [fixture] if spec.input_flag is None else [spec.input_flag, fixture]
    )
    return run(script, *input_arguments, *extra)


def wrapper_command(
    command: str, fixture: Path, *extra: object
) -> subprocess.CompletedProcess[bytes]:
    return run(OPERATOR, command, "--input", fixture, *extra)


class SnowflakeOperatorTests(unittest.TestCase):
    def test_registry_is_the_exact_approved_command_set(self) -> None:
        self.assertEqual(set(operator.COMMANDS), APPROVED_COMMANDS)

    def test_registry_paths_are_confined_to_the_pack(self) -> None:
        root = PACK_ROOT.resolve()
        for name, spec in operator.COMMANDS.items():
            with self.subTest(command=name):
                script = operator.resolve_script(spec)
                self.assertTrue(script.is_file())
                self.assertTrue(script.is_relative_to(root))

        escaped = operator.CommandSpec(script="../outside.py", description="invalid")
        with self.assertRaises(operator.OperatorError):
            operator.resolve_script(escaped)

    def test_help_is_fast_and_lists_every_command(self) -> None:
        top = run(OPERATOR, "--help")
        self.assertEqual(top.returncode, 0, top.stderr.decode())
        for command in APPROVED_COMMANDS:
            self.assertIn(command.encode(), top.stdout)
            with self.subTest(command=command):
                result = run(OPERATOR, command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertIn(b"usage:", result.stdout)

    def test_collect_is_delegated_unchanged(self) -> None:
        arguments = ("--surface", "pipeline", "--validate-only")
        direct = run(operator.resolve_script(operator.COMMANDS["collect"]), *arguments)
        wrapped = run(OPERATOR, "collect", *arguments)
        self.assertEqual(
            (wrapped.returncode, wrapped.stdout, wrapped.stderr),
            (direct.returncode, direct.stdout, direct.stderr),
        )

    def test_analyzers_match_underlying_stdout_stderr_and_exit_code(self) -> None:
        for command, fixture in FIXTURES.items():
            extra = ACCESS_SELECTORS if command == "access-review" else []
            with self.subTest(command=command):
                direct = direct_command(command, fixture, *extra)
                wrapped = wrapper_command(command, fixture, *extra)
                self.assertEqual(
                    (wrapped.returncode, wrapped.stdout, wrapped.stderr),
                    (direct.returncode, direct.stdout, direct.stderr),
                )

    def test_invalid_json_exits_two_without_wrapper_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text("{not-json\n", encoding="utf-8")
            for command in FIXTURES:
                with self.subTest(command=command):
                    result = wrapper_command(command, invalid)
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn(b"Traceback", result.stderr)

    def test_stdout_only_analyzers_write_atomic_output(self) -> None:
        for command in ("data-quality", "pipeline-triage", "deploy-preflight"):
            fixture = FIXTURES[command]
            direct = direct_command(command, fixture)
            self.assertEqual(direct.returncode, 0, direct.stderr.decode())
            with self.subTest(
                command=command
            ), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "nested" / "report.json"
                wrapped = wrapper_command(command, fixture, "--output", output)
                self.assertEqual(
                    wrapped.returncode, direct.returncode, wrapped.stderr.decode()
                )
                self.assertEqual(wrapped.stdout, b"")
                self.assertEqual(output.read_bytes(), direct.stdout)
                leftovers = list(output.parent.glob(f".{output.name}.*.tmp"))
                self.assertEqual(leftovers, [])

    def test_json_and_markdown_options_are_translated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for command in ("cost-leak", "query-id-forensics"):
                fixture = FIXTURES[command]
                spec = operator.COMMANDS[command]
                direct_json = root / f"{command}-direct.json"
                direct_markdown = root / f"{command}-direct.md"
                wrapped_json = root / f"{command}-wrapped.json"
                wrapped_markdown = root / f"{command}-wrapped.md"
                with self.subTest(command=command):
                    direct = direct_command(
                        command,
                        fixture,
                        spec.output_flag,
                        direct_json,
                        spec.markdown_flag,
                        direct_markdown,
                    )
                    wrapped = wrapper_command(
                        command,
                        fixture,
                        "--output",
                        wrapped_json,
                        "--markdown-output",
                        wrapped_markdown,
                    )
                    self.assertEqual(wrapped.returncode, direct.returncode)
                    self.assertEqual(wrapped.stdout, direct.stdout)
                    self.assertEqual(wrapped.stderr, direct.stderr)
                    self.assertEqual(
                        wrapped_json.read_bytes(), direct_json.read_bytes()
                    )
                    self.assertEqual(
                        wrapped_markdown.read_bytes(), direct_markdown.read_bytes()
                    )

    def test_native_output_flags_and_access_selectors_are_translated(self) -> None:
        commands = {
            "access-review": "--out",
            "governance-coverage": "--out",
            "native-app-release": "--output",
            "strong-auth": "--out",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for command, expected_output_flag in commands.items():
                fixture = FIXTURES[command]
                spec = operator.COMMANDS[command]
                self.assertEqual(spec.output_flag, expected_output_flag)
                direct_output = root / f"{command}-direct.json"
                wrapped_output = root / f"{command}-wrapped.json"
                selectors = ACCESS_SELECTORS if command == "access-review" else []
                with self.subTest(command=command):
                    direct = direct_command(
                        command,
                        fixture,
                        *selectors,
                        spec.output_flag,
                        direct_output,
                    )
                    wrapped = wrapper_command(
                        command,
                        fixture,
                        *selectors,
                        "--output",
                        wrapped_output,
                    )
                    self.assertEqual(wrapped.returncode, direct.returncode)
                    self.assertEqual(wrapped.stdout, direct.stdout)
                    self.assertEqual(wrapped.stderr, direct.stderr)
                    self.assertEqual(wrapped_output.exists(), direct_output.exists())
                    if direct_output.exists():
                        self.assertEqual(
                            wrapped_output.read_bytes(), direct_output.read_bytes()
                        )

    def test_failover_output_option_is_translated(self) -> None:
        spec = operator.COMMANDS["failover-readiness"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "failover.json"
            fixture.write_text(
                '{"mode":"READ_ONLY_PREFLIGHT","as_of":"2025-01-01T00:00:00Z"}\n',
                encoding="utf-8",
            )
            direct_output = root / "direct.json"
            wrapped_output = root / "wrapped.json"
            direct = direct_command(
                "failover-readiness",
                fixture,
                spec.output_flag,
                direct_output,
            )
            wrapped = wrapper_command(
                "failover-readiness",
                fixture,
                "--output",
                wrapped_output,
            )
            self.assertEqual(wrapped.returncode, direct.returncode)
            self.assertEqual(wrapped.stdout, direct.stdout)
            self.assertEqual(wrapped.stderr, direct.stderr)
            self.assertEqual(wrapped_output.read_bytes(), direct_output.read_bytes())


if __name__ == "__main__":
    unittest.main()

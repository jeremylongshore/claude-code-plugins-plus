#!/usr/bin/env python3
"""Model-neutral CLI for Snowflake pack evidence collection and analyzers."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

PACK_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CommandSpec:
    """Declarative subprocess adapter for one pack command."""

    script: str
    description: str
    input_flag: str | None = "--input"
    output_flag: str | None = None
    markdown_flag: str | None = None
    selectors: tuple[str, ...] = ()
    passthrough: bool = False


COMMANDS: dict[str, CommandSpec] = {
    "collect": CommandSpec(
        script="shared/evidence/collect_snowflake_evidence.py",
        description="Delegate unchanged to the shared evidence collector.",
        passthrough=True,
    ),
    "pipeline-triage": CommandSpec(
        script="skills/snowflake-pipeline-guardian/scripts/analyze_pipeline_state.py",
        description="Classify a read-only pipeline evidence snapshot.",
    ),
    "cost-leak": CommandSpec(
        script="skills/snowflake-cost-leak-hunter/scripts/analyze_cost_evidence.py",
        description="Analyze normalized cost evidence and rank leak hypotheses.",
        output_flag="--json-out",
        markdown_flag="--markdown-out",
    ),
    "query-id-forensics": CommandSpec(
        script="skills/snowflake-query-forensics/scripts/analyze_query_evidence.py",
        description="Analyze query-ID evidence and operator statistics.",
        output_flag="--json-out",
        markdown_flag="--markdown-out",
    ),
    "deploy-preflight": CommandSpec(
        script="skills/snowflake-deploy-medic/scripts/analyze_deploy_evidence.py",
        description="Classify read-only deployment evidence.",
    ),
    "data-quality": CommandSpec(
        script="skills/snowflake-data-quality-sentinel/scripts/analyze_data_quality.py",
        description="Assess normalized data-quality evidence.",
        input_flag=None,
    ),
    "access-review": CommandSpec(
        script="skills/snowflake-access-guardian/scripts/analyze_access.py",
        description="Analyze a sanitized authorization graph.",
        output_flag="--out",
        selectors=("principal", "object", "privilege"),
    ),
    "strong-auth": CommandSpec(
        script=(
            "skills/snowflake-strong-auth-migration-pilot/scripts/analyze_auth.py"
        ),
        description="Plan a non-password authentication migration pilot.",
        output_flag="--out",
    ),
    "failover-readiness": CommandSpec(
        script=(
            "skills/snowflake-failover-readiness-drill/scripts/"
            "analyze_failover_readiness.py"
        ),
        description="Assess failover and failback evidence readiness.",
        output_flag="--output",
    ),
    "governance-coverage": CommandSpec(
        script=(
            "skills/snowflake-governance-coverage-auditor/scripts/"
            "analyze_governance_coverage.py"
        ),
        description="Audit governance coverage evidence.",
        output_flag="--out",
    ),
    "native-app-release": CommandSpec(
        script=(
            "skills/snowflake-native-app-release-sheriff/scripts/"
            "analyze_native_app_release.py"
        ),
        description="Evaluate native app release evidence.",
        output_flag="--output",
    ),
}


class OperatorError(Exception):
    """A safe-to-display operator wrapper failure."""


def resolve_script(spec: CommandSpec) -> Path:
    """Resolve a registered script and reject paths outside this pack."""

    pack_root = PACK_ROOT.resolve()
    candidate = (pack_root / spec.script).resolve()
    try:
        candidate.relative_to(pack_root)
    except ValueError as exc:
        raise OperatorError(
            f"registered script escapes the Snowflake pack: {spec.script}"
        ) from exc
    if not candidate.is_file():
        raise OperatorError(f"registered script is missing: {spec.script}")
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, spec in COMMANDS.items():
        command_parser = subparsers.add_parser(
            name, help=spec.description, description=spec.description
        )
        if spec.passthrough:
            command_parser.epilog = (
                "All following options are handled by the shared collector."
            )
            continue
        command_parser.add_argument(
            "--input", required=True, type=Path, help="sanitized evidence JSON"
        )
        command_parser.add_argument(
            "--output", type=Path, help="write the JSON report atomically"
        )
        if spec.markdown_flag:
            command_parser.add_argument(
                "--markdown-output",
                type=Path,
                help="write the optional Markdown report",
            )
        for selector in spec.selectors:
            command_parser.add_argument(f"--{selector}")
    return parser


def analyzer_arguments(spec: CommandSpec, args: argparse.Namespace) -> list[str]:
    command = [sys.executable, str(resolve_script(spec))]
    if spec.input_flag is None:
        command.append(str(args.input))
    else:
        command.extend((spec.input_flag, str(args.input)))
    if args.output is not None and spec.output_flag is not None:
        command.extend((spec.output_flag, str(args.output)))
    if spec.markdown_flag and args.markdown_output is not None:
        command.extend((spec.markdown_flag, str(args.markdown_output)))
    for selector in spec.selectors:
        value = getattr(args, selector)
        if value is not None:
            command.extend((f"--{selector}", value))
    return command


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def dispatch(spec: CommandSpec, arguments: Sequence[str]) -> int:
    """Delegate a passthrough command without parsing or translating arguments."""

    try:
        return subprocess.call([sys.executable, str(resolve_script(spec)), *arguments])
    except (OSError, OperatorError) as exc:
        print(f"operator error: {exc}", file=sys.stderr)
        return 2


def dispatch_analyzer(spec: CommandSpec, args: argparse.Namespace) -> int:
    try:
        command = analyzer_arguments(spec, args)
        capture_output = args.output is not None and spec.output_flag is None
        if not capture_output:
            return subprocess.call(command)
        result = subprocess.run(command, stdout=subprocess.PIPE, check=False)
        if result.returncode == 0:
            atomic_write(args.output, result.stdout)
        return result.returncode
    except (OSError, OperatorError) as exc:
        print(f"operator error: {exc}", file=sys.stderr)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "collect":
        return dispatch(COMMANDS["collect"], arguments[1:])
    args = build_parser().parse_args(arguments)
    return dispatch_analyzer(COMMANDS[args.command], args)


if __name__ == "__main__":
    raise SystemExit(main())

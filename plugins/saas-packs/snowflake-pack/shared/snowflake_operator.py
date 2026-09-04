#!/usr/bin/env python3
"""Model-neutral dispatcher for the Snowflake pack's canonical analyzers.

This module owns discovery and process transport only. Every Snowflake
decision remains in the analyzer shipped with its skill.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePath
from types import MappingProxyType
from typing import BinaryIO, Mapping, Sequence


PACK_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class StringOption:
    public: str
    child: str
    help: str
    required: bool = False
    output: bool = False


@dataclass(frozen=True)
class Workflow:
    name: str
    skill: str
    analyzer: str
    summary: str
    input_required: bool = True
    native_output_flag: str | None = None
    output_exit_codes: tuple[int, ...] = (0,)
    creates_output_parents: bool = False
    options: tuple[StringOption, ...] = ()
    flags: tuple[tuple[str, str, str], ...] = ()


TRUST_INPUT = StringOption(
    "--trusted-input-sha256",
    "--trusted-input-sha256",
    "out-of-band digest recorded at the trusted local boundary",
)
PRINT_INPUT = (
    "--print-input-sha256",
    "--print-input-sha256",
    "print the canonical input digest and exit",
)


_WORKFLOWS = (
    Workflow(
        name="pipeline-triage",
        skill="snowflake-pipeline-guardian",
        analyzer="scripts/analyze_pipeline_state.py",
        summary="classify stale, suspended, delayed, or incomplete pipeline evidence",
        input_required=False,
        options=(
            TRUST_INPUT,
            StringOption(
                "--as-of",
                "--evaluated-at",
                "explicit timezone-aware evaluation timestamp",
            ),
        ),
        flags=(PRINT_INPUT,),
    ),
    Workflow(
        name="query-id-forensics",
        skill="snowflake-query-forensics",
        analyzer="scripts/analyze_query_evidence.py",
        summary="analyze one receipt-bound Snowflake query incident",
        native_output_flag="--json-out",
        options=(
            TRUST_INPUT,
            StringOption(
                "--markdown-output",
                "--markdown-out",
                "also write the analyzer's Markdown rendering",
                output=True,
            ),
        ),
        flags=(PRINT_INPUT,),
    ),
    Workflow(
        name="deploy-preflight",
        skill="snowflake-deploy-medic",
        analyzer="scripts/analyze_deploy_evidence.py",
        summary="preflight Terraform, dbt, provider, and behavior-change evidence",
        input_required=False,
        options=(
            StringOption(
                "--as-of",
                "--as-of",
                "explicit UTC analysis timestamp",
                required=True,
            ),
            StringOption(
                "--trusted-bundle-sha256",
                "--trusted-bundle-sha256",
                "trusted digest for the exact deployment packet",
                required=True,
            ),
        ),
    ),
    Workflow(
        name="access-review",
        skill="snowflake-access-guardian",
        analyzer="scripts/analyze_access_evidence.py",
        summary="verify receipted access evidence and trace its authorization graph",
        native_output_flag="--out",
        creates_output_parents=True,
        options=(TRUST_INPUT,),
        flags=(PRINT_INPUT,),
    ),
    Workflow(
        name="failover-readiness",
        skill="snowflake-failover-readiness-drill",
        analyzer="scripts/analyze_failover_readiness.py",
        summary="evaluate read-only failover coverage and operator drill evidence",
        output_exit_codes=(0, 1),
        options=(
            StringOption(
                "--as-of",
                "--evaluated-at",
                "explicit evaluation timestamp",
                required=True,
            ),
            StringOption(
                "--trusted-input-sha256",
                "--trusted-input-sha256",
                "trusted evidence digest",
                required=True,
            ),
            StringOption(
                "--trusted-policy-sha256",
                "--trusted-policy-sha256",
                "trusted policy digest",
                required=True,
            ),
            StringOption(
                "--trusted-operator-sha256",
                "--trusted-operator-sha256",
                "trusted operator-receipt digest",
                required=True,
            ),
        ),
    ),
)

WORKFLOWS: Mapping[str, Workflow] = MappingProxyType({workflow.name: workflow for workflow in _WORKFLOWS})


class OperatorError(RuntimeError):
    """Fail-closed dispatcher error."""


def _registered_relative_path(value: str, label: str) -> PurePath:
    path = PurePath(value)
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise OperatorError(f"invalid registered {label}")
    return path


def _resolve_analyzer(workflow: Workflow, pack_root: Path = PACK_ROOT) -> Path:
    real_root = pack_root.resolve(strict=True)
    skill = _registered_relative_path(workflow.skill, "skill")
    analyzer = _registered_relative_path(workflow.analyzer, "analyzer")
    relative = PurePath("skills") / skill / analyzer

    current = real_root
    try:
        for component in relative.parts:
            current = current / component
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise OperatorError(f"analyzer path contains a symlink for {workflow.name}")
    except OSError as exc:
        raise OperatorError(f"analyzer is unavailable for {workflow.name}") from exc

    if not stat.S_ISREG(current.lstat().st_mode):
        raise OperatorError(f"analyzer is not a regular file for {workflow.name}")
    if not current.resolve(strict=True).is_relative_to(real_root):
        raise OperatorError(f"analyzer escaped the pack root for {workflow.name}")
    return current


def _child_command(
    workflow: Workflow,
    args: argparse.Namespace,
    pack_root: Path = PACK_ROOT,
    output_overrides: Mapping[str, str] | None = None,
) -> list[str]:
    output_overrides = output_overrides or {}
    command = [sys.executable, str(_resolve_analyzer(workflow, pack_root))]
    input_value = getattr(args, "input", None)
    if input_value is not None:
        command.append(f"--input={input_value}")
    for option in workflow.options:
        value = getattr(args, option.public[2:].replace("-", "_"), None)
        if value is not None:
            value = output_overrides.get(option.public, value)
            command.append(f"{option.child}={value}")
    for public, child, _ in workflow.flags:
        if getattr(args, public[2:].replace("-", "_"), False):
            command.append(child)
    output = getattr(args, "output", None)
    if output is not None and workflow.native_output_flag:
        output = output_overrides.get("--output", output)
        command.append(f"{workflow.native_output_flag}={output}")
    return command


def _absolute_lexical(path: str) -> Path:
    return Path(os.path.abspath(path))


def _validate_output_alias(
    input_value: str | None,
    output_value: str,
    *,
    require_parent: bool = True,
) -> Path:
    if output_value == "-":
        raise OperatorError("omit --output to write to stdout")
    output = _absolute_lexical(output_value)
    if output.is_symlink():
        raise OperatorError("output path must not be a symlink")
    try:
        if output.exists() and not stat.S_ISREG(output.lstat().st_mode):
            raise OperatorError("output path must be a regular file")
    except OSError as exc:
        raise OperatorError("could not inspect the output path") from exc
    if require_parent and not output.parent.is_dir():
        raise OperatorError(f"output parent does not exist: {output.parent}")
    if input_value is None or input_value == "-":
        return output

    input_path = _absolute_lexical(input_value)
    if input_path == output:
        raise OperatorError("input and output must be different files")
    try:
        if input_path.exists() and output.exists() and input_path.samefile(output):
            raise OperatorError("input and output must not alias the same file")
    except OSError as exc:
        raise OperatorError("could not verify input and output separation") from exc
    return output


def _validate_outputs(workflow: Workflow, args: argparse.Namespace) -> dict[str, Path]:
    values: list[tuple[str, str, bool]] = []
    primary = getattr(args, "output", None)
    if primary is not None:
        values.append(("--output", primary, workflow.native_output_flag is None))
    for option in workflow.options:
        value = getattr(args, option.public[2:].replace("-", "_"), None)
        if option.output and value is not None:
            values.append((option.public, value, False))

    validated: list[tuple[str, Path]] = []
    input_value = getattr(args, "input", None)
    for label, value, require_parent in values:
        destination = _validate_output_alias(
            input_value,
            value,
            require_parent=require_parent,
        )
        for previous_label, previous in validated:
            if destination == previous:
                raise OperatorError(f"{label} must not alias {previous_label}")
            try:
                if destination.exists() and previous.exists() and destination.samefile(previous):
                    raise OperatorError(f"{label} must not alias {previous_label}")
            except OSError as exc:
                raise OperatorError("could not verify output separation") from exc
        validated.append((label, destination))
    return dict(validated)


def _temporary_output(destination: Path) -> tuple[BinaryIO, Path]:
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
        os.fchmod(descriptor, 0o600)
        return os.fdopen(descriptor, "wb"), Path(temporary_name)
    except OSError as exc:
        raise OperatorError("could not create the output file") from exc


def _stage_parent(destination: Path, workflow: Workflow) -> Path:
    if destination.parent.is_dir():
        return destination.parent
    if not workflow.creates_output_parents:
        raise OperatorError(f"output parent does not exist: {destination.parent}")
    candidate = destination.parent
    while not candidate.is_dir():
        parent = candidate.parent
        if parent == candidate:
            raise OperatorError("output has no existing parent directory")
        candidate = parent
    return candidate


def _run(
    workflow: Workflow,
    args: argparse.Namespace,
    pack_root: Path = PACK_ROOT,
) -> int:
    destinations = _validate_outputs(workflow, args)
    if not destinations:
        command = _child_command(workflow, args, pack_root)
        try:
            return subprocess.run(command, check=False).returncode
        except OSError:
            print("operator error: analyzer could not be started", file=sys.stderr)
            return 2

    staged: dict[str, tuple[Path, Path, BinaryIO | None]] = {}
    try:
        for label, destination in destinations.items():
            stage_destination = _stage_parent(destination, workflow) / destination.name
            handle, temporary = _temporary_output(stage_destination)
            is_stdout_capture = label == "--output" and workflow.native_output_flag is None
            if not is_stdout_capture:
                handle.close()
                handle = None
            staged[label] = (destination, temporary, handle)

        overrides = {label: str(item[1]) for label, item in staged.items()}
        command = _child_command(workflow, args, pack_root, overrides)
        stdout_handle = staged.get("--output", (None, None, None))[2]
        completed = subprocess.run(command, check=False, stdout=stdout_handle)
        if stdout_handle is not None:
            stdout_handle.flush()
            os.fsync(stdout_handle.fileno())
            stdout_handle.close()
            destination, temporary, _ = staged["--output"]
            staged["--output"] = (destination, temporary, None)

        suppress_native_outputs = workflow.native_output_flag is not None and any(
            getattr(args, public[2:].replace("-", "_"), False) for public, _, _ in workflow.flags
        )
        if completed.returncode in workflow.output_exit_codes and not suppress_native_outputs:
            current = _validate_outputs(workflow, args)
            if current != destinations:
                raise OperatorError("output destination changed during analysis")
            for destination, temporary, _ in staged.values():
                mode = temporary.lstat().st_mode
                if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                    raise OperatorError("analyzer did not produce a regular output file")
                if workflow.native_output_flag is not None and temporary.stat().st_size == 0:
                    raise OperatorError("analyzer did not produce the requested output")
                os.chmod(temporary, 0o600)
                descriptor = os.open(temporary, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            if workflow.creates_output_parents:
                for destination in destinations.values():
                    destination.parent.mkdir(parents=True, exist_ok=True)
            for label, (destination, temporary, handle) in tuple(staged.items()):
                os.replace(temporary, destination)
                staged[label] = (destination, temporary, handle)
        return completed.returncode
    except (OSError, OperatorError):
        print("operator error: analyzer output could not be written", file=sys.stderr)
        return 2
    finally:
        for _, temporary, handle in staged.values():
            if handle is not None:
                handle.close()
            temporary.unlink(missing_ok=True)


def _validate_registry() -> None:
    if len(WORKFLOWS) != len(_WORKFLOWS):
        raise OperatorError("duplicate workflow name")
    for key, workflow in WORKFLOWS.items():
        if key != workflow.name or not re.fullmatch(r"[a-z][a-z0-9-]*", key):
            raise OperatorError(f"invalid workflow registration: {key}")
        _registered_relative_path(workflow.skill, "skill")
        _registered_relative_path(workflow.analyzer, "analyzer")
        public = [option.public for option in workflow.options]
        public.extend(option[0] for option in workflow.flags)
        if len(public) != len(set(public)):
            raise OperatorError(f"duplicate option registered for {key}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snowflake-operator",
        description=("Run the Snowflake pack's model-neutral analyzers without duplicating their decision logic."),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    listing = subparsers.add_parser("list", help="list available operator workflows")
    listing.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable workflow metadata",
    )
    for workflow in _WORKFLOWS:
        subparser = subparsers.add_parser(
            workflow.name,
            help=workflow.summary,
            description=workflow.summary,
        )
        input_help = "redacted JSON evidence path"
        if not workflow.input_required:
            input_help += "; omit for stdin"
        subparser.add_argument(
            "--input",
            required=workflow.input_required,
            help=input_help,
        )
        subparser.add_argument(
            "--output",
            help="write the primary JSON output to this path",
        )
        for option in workflow.options:
            subparser.add_argument(
                option.public,
                required=option.required,
                help=option.help,
            )
        for public, _, help_text in workflow.flags:
            subparser.add_argument(public, action="store_true", help=help_text)
        subparser.set_defaults(workflow=workflow)
    return parser


def _list(json_output: bool) -> None:
    rows = [
        {
            "name": workflow.name,
            "skill": workflow.skill,
            "summary": workflow.summary,
        }
        for workflow in _WORKFLOWS
    ]
    if json_output:
        print(
            json.dumps(
                {"schema_version": "1", "workflows": rows},
                indent=2,
                sort_keys=True,
            )
        )
        return
    for row in rows:
        print(f"{row['name']:<20} {row['summary']}")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        _validate_registry()
        args = _parser().parse_args(argv)
        if args.command == "list":
            _list(args.json)
            return 0
        return _run(args.workflow, args)
    except OperatorError as exc:
        print(f"operator error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

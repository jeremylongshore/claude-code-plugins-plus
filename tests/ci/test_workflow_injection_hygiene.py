"""Regression guard for f-ccp-workflows-1 (2026-06-11).

`repository_dispatch` client_payload values (and string-typed
`workflow_dispatch` inputs) are attacker-influenced. If interpolated with
``${{ }}`` directly inside a ``run:`` block, GitHub Actions expands them into
the shell script verbatim before execution — arbitrary command execution on
the runner. They must be routed through ``env:`` so the shell receives them
as data, never as code.

Scope: pins sync-external.yml, where the finding was reported. Boolean-typed
inputs (force / dry_run) are not injectable and may stay inline.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sync-external.yml"

# ${{ ... }} expressions referencing dispatch-controlled strings.
RE_INJECTABLE = re.compile(r"\$\{\{[^}]*(client_payload|inputs\.source)[^}]*\}\}")


def _iter_run_blocks(node):
    """Yield every `run:` string anywhere in the parsed workflow document."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "run" and isinstance(value, str):
                yield value
            else:
                yield from _iter_run_blocks(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_run_blocks(item)


def test_sync_external_run_blocks_do_not_interpolate_dispatch_payload():
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    offenders = [run for run in _iter_run_blocks(doc) if RE_INJECTABLE.search(run)]
    assert not offenders, (
        "Dispatch-controlled values (client_payload.*, inputs.source) must reach "
        "run: blocks via env:, not direct ${{ }} interpolation (command injection "
        f"on the runner). Offending run blocks:\n{offenders}"
    )


def test_sync_external_routes_source_through_env():
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["sync"]["steps"]
    sync_step = next(s for s in steps if s.get("id") == "sync")
    env = sync_step.get("env") or {}
    assert any("client_payload.source" in str(v) for v in env.values()), (
        f"sync step must carry client_payload.source through env:; got env={env}"
    )
    assert '"$SYNC_SOURCE"' in sync_step["run"], (
        "run block must pass the source as a quoted env-var argv entry"
    )

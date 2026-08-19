#!/usr/bin/env python3
"""
dolt-mcp-guard.py — the mutation gate AT the MCP entrypoint (blueprint 727 E4.9).

Before this guard existed, the plugin's "recommend-only" mutation posture lived
only in dolt-mcp-client.py — the ancillary path its agents use — while the
registered MCP server was the RAW upstream `dolt-mcp-server` binary: every
destructive verb (drop_database, dolt_reset_hard, dolt_push_branch, branch
delete, merges) was a live, ungated tool for any MCP host that connected. That
is the exact "prose-only at the boundary" gap the Safety Enforcement Register
(000-docs/790 § 6) recorded.

This guard IS the entrypoint. Register the MCP server through it:

    dolt-mcp-guard.py -- dolt-mcp-server --stdio --dolt --host 127.0.0.1 \
        --port 3308 --user root --database freshie

It spawns the child server and proxies newline-delimited JSON-RPC both ways,
enforcing the plugin's declared posture where it can no longer be bypassed:

  * ALWAYS-REFUSED tools (history-affecting / destructive: push, pull, both
    merges, reset --hard, branch delete, DROP DATABASE) are answered with a
    refusal directly — the request never reaches the child — and are filtered
    out of tools/list responses so hosts don't even see them.
  * `query` must classify as read-only (sql_classifier.py, the same
    chokepoint the client uses); anything stronger is refused.
  * `exec` refuses history-affecting SQL always, and refuses safe-write SQL
    unless DOLT_MCP_ALLOW_MUTATION=1 is set in the guard's environment —
    the MCP-side equivalent of the client's explicit --allow-mutation.
  * Unparseable SQL or an unknown call shape fails CLOSED (refused).

Everything else forwards verbatim. stdlib only, like the rest of the plugin.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sql_classifier import HISTORY_AFFECTING, READ, classify_sql  # noqa: E402

# The declared always-refused set (README § Declared mutation posture), by MCP
# tool name as exposed by dolt-mcp-server v0.3.6.
ALWAYS_REFUSE = {
    "dolt_push_branch",
    "dolt_pull_branch",
    "merge_dolt_branch",
    "merge_dolt_branch_no_fast_forward",
    "dolt_reset_hard",
    "delete_dolt_branch",
    "drop_database",
}

SQL_TOOLS = {"query", "exec"}


def refusal(request_id, text):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"content": [{"type": "text", "text": text}], "isError": True},
    }


def classify_arguments(arguments):
    """Classify the SQL carried in the call's `query` argument.

    dolt-mcp-server's query/exec tools carry their SQL in `query` (alongside
    non-SQL `working_branch`/`working_database` strings, which must not be fed
    to the classifier — a bare identifier is not provably a read and would
    false-refuse). A missing or non-string `query` fails CLOSED.
    """
    sql = (arguments or {}).get("query")
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("missing or non-string 'query' argument")
    return classify_sql(sql)


def gate(name, arguments, allow_mutation):
    """Return a refusal reason string, or None to forward the call."""
    if name in ALWAYS_REFUSE:
        return (
            f"REFUSED (recommend-only): '{name}' is history-affecting/destructive. "
            "The dolt-mcp-vcs posture keeps push/pull/merge/reset-hard/branch-delete/"
            "DROP DATABASE recommend-only at the MCP boundary; run it deliberately "
            "outside the MCP (e.g. the plugin's dolt-push-dolthub.sh) if intended."
        )
    if name in SQL_TOOLS:
        try:
            severity = classify_arguments(arguments)
        except Exception as exc:  # unparseable SQL fails closed
            return f"REFUSED (fail-closed): SQL could not be classified ({exc})."
        if severity == HISTORY_AFFECTING:
            return (
                "REFUSED (recommend-only): the statement classifies as "
                "history-affecting (push/merge/reset/branch-delete/DROP DATABASE "
                "class). This is never executable through the MCP."
            )
        if name == "query" and severity != READ:
            return (
                "REFUSED: 'query' is read-only; the statement classifies as a "
                "write. Use 'exec' with DOLT_MCP_ALLOW_MUTATION=1 for safe writes."
            )
        if name == "exec" and severity != READ and not allow_mutation:
            return (
                "REFUSED: safe-write SQL requires DOLT_MCP_ALLOW_MUTATION=1 in the "
                "guard environment (the MCP equivalent of --allow-mutation)."
            )
    return None


def pump_child_stdout(child, list_ids, lock):
    """Forward child → host, filtering refused tools out of tools/list results."""
    for raw in child.stdout:
        line = raw.rstrip("\n")
        if not line:
            continue
        forwarded = line
        is_list = False
        try:
            message = json.loads(line)
            with lock:
                is_list = message.get("id") in list_ids
                if is_list:
                    list_ids.discard(message.get("id"))
            if is_list and isinstance(message.get("result"), dict):
                tools = message["result"].get("tools")
                if isinstance(tools, list):
                    message["result"]["tools"] = [
                        tool for tool in tools if tool.get("name") not in ALWAYS_REFUSE
                    ]
                    forwarded = json.dumps(message)
        except (json.JSONDecodeError, AttributeError):
            pass  # non-JSON noise from the child forwards verbatim
        sys.stdout.write(forwarded + "\n")
        sys.stdout.flush()


def main(argv):
    if "--" not in argv:
        print(
            "usage: dolt-mcp-guard.py -- dolt-mcp-server --stdio [server args...]",
            file=sys.stderr,
        )
        return 2
    child_cmd = argv[argv.index("--") + 1 :]
    if not child_cmd:
        print("dolt-mcp-guard: empty child command after --", file=sys.stderr)
        return 2
    allow_mutation = os.environ.get("DOLT_MCP_ALLOW_MUTATION") == "1"

    child = subprocess.Popen(
        child_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
    )
    list_ids = set()
    lock = threading.Lock()
    reader = threading.Thread(
        target=pump_child_stdout, args=(child, list_ids, lock), daemon=True
    )
    reader.start()

    try:
        for raw in sys.stdin:
            line = raw.rstrip("\n")
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                child.stdin.write(line + "\n")
                child.stdin.flush()
                continue
            method = message.get("method")
            request_id = message.get("id")
            if method == "tools/list" and request_id is not None:
                with lock:
                    list_ids.add(request_id)
            if method == "tools/call" and request_id is not None:
                params = message.get("params") or {}
                reason = gate(params.get("name"), params.get("arguments"), allow_mutation)
                if reason is not None:
                    sys.stdout.write(json.dumps(refusal(request_id, reason)) + "\n")
                    sys.stdout.flush()
                    continue
            child.stdin.write(line + "\n")
            child.stdin.flush()
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        child.wait(timeout=10)
    return child.returncode or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""E4.9 proof harness: the dolt-mcp-vcs mutation gate at the ACTUAL MCP entrypoint.

Drives plugins/mcp/dolt-mcp-vcs/scripts/dolt-mcp-guard.py as a subprocess over
real newline-delimited JSON-RPC — the same wire a Claude Code host uses — with
a scripted fake dolt-mcp-server as the child. The blueprint's instruction:
"drive the actual MCP entrypoint, not a unit-tested helper."
"""

import json
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / "plugins/mcp/dolt-mcp-vcs/scripts/dolt-mcp-guard.py"

# A minimal fake dolt-mcp-server: answers tools/list with a mixed tool set and
# echoes EXECUTED for any tools/call that reaches it — so a leak through the
# guard is loudly visible in the assertion.
FAKE_SERVER = textwrap.dedent(
    """
    import json, sys
    TOOLS = [
        {"name": "query"}, {"name": "exec"}, {"name": "list_databases"},
        {"name": "drop_database"}, {"name": "dolt_reset_hard"},
        {"name": "dolt_push_branch"},
    ]
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("id") is None:
            continue
        if msg.get("method") == "tools/list":
            result = {"tools": TOOLS}
        else:
            result = {"content": [{"type": "text",
                     "text": "EXECUTED " + msg.get("params", {}).get("name", "?")}]}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"],
                                     "result": result}) + "\\n")
        sys.stdout.flush()
    """
)


def run_guard(requests, env_extra=None):
    """Send JSON-RPC requests through the guard; return {id: response}."""
    import os

    env = dict(os.environ)
    env.pop("DOLT_MCP_ALLOW_MUTATION", None)
    env.update(env_extra or {})
    payload = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--", sys.executable, "-c", FAKE_SERVER],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    responses = {}
    for line in proc.stdout.splitlines():
        if line.strip():
            msg = json.loads(line)
            responses[msg["id"]] = msg
    return responses


def call(request_id, name, arguments=None):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    }


SQL_ARGS = {"working_branch": "main", "working_database": "freshie"}


class DoltMcpGuardTest(unittest.TestCase):
    def assert_refused(self, response, fragment="REFUSED"):
        result = response["result"]
        self.assertTrue(result.get("isError"), response)
        text = result["content"][0]["text"]
        self.assertIn(fragment, text)
        self.assertNotIn("EXECUTED", text)

    def assert_executed(self, response):
        text = response["result"]["content"][0]["text"]
        self.assertIn("EXECUTED", text, response)

    def test_every_declared_destructive_tool_is_refused_at_the_wire(self):
        names = [
            "drop_database",
            "dolt_reset_hard",
            "dolt_push_branch",
            "dolt_pull_branch",
            "merge_dolt_branch",
            "merge_dolt_branch_no_fast_forward",
            "delete_dolt_branch",
        ]
        requests = [call(i + 1, name) for i, name in enumerate(names)]
        responses = run_guard(requests)
        for i, name in enumerate(names):
            self.assert_refused(responses[i + 1], "recommend-only")

    def test_reads_pass_through_and_execute(self):
        responses = run_guard(
            [
                call(1, "list_databases"),
                call(2, "query", {**SQL_ARGS, "query": "SELECT COUNT(*) FROM issues"}),
            ]
        )
        self.assert_executed(responses[1])
        self.assert_executed(responses[2])

    def test_query_refuses_writes_and_exec_refuses_history(self):
        responses = run_guard(
            [
                call(1, "query", {**SQL_ARGS, "query": "DELETE FROM issues"}),
                call(2, "exec", {**SQL_ARGS, "query": "DROP DATABASE freshie"}),
                call(3, "exec", {**SQL_ARGS, "query": "CALL DOLT_RESET('--hard')"}),
            ]
        )
        self.assert_refused(responses[1])
        self.assert_refused(responses[2], "history-affecting")
        self.assert_refused(responses[3], "history-affecting")

    def test_exec_safe_write_needs_explicit_opt_in(self):
        insert = {**SQL_ARGS, "query": "INSERT INTO t VALUES (1)"}
        blocked = run_guard([call(1, "exec", insert)])
        self.assert_refused(blocked[1], "DOLT_MCP_ALLOW_MUTATION")
        allowed = run_guard([call(1, "exec", insert)], env_extra={"DOLT_MCP_ALLOW_MUTATION": "1"})
        self.assert_executed(allowed[1])

    def test_missing_sql_fails_closed(self):
        responses = run_guard([call(1, "exec", SQL_ARGS)])
        self.assert_refused(responses[1], "fail-closed")

    def test_tools_list_hides_the_refused_tools(self):
        responses = run_guard([{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}])
        names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertEqual(names, {"query", "exec", "list_databases"})


if __name__ == "__main__":
    unittest.main()

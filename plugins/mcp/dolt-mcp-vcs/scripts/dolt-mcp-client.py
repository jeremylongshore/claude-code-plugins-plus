#!/usr/bin/env python3
"""
dolt-mcp-client.py — minimal, robust stdio client for the dolthub/dolt-mcp server.

The reusable foundation the dolt-mcp-vcs agents/scripts use to run SQL against a
bd Dolt server *through the MCP* (not by shelling `dolt` directly), so the path
exercised in production is the same one the plugin ships.

Spawns `dolt-mcp-server --stdio`, performs the JSON-RPC handshake, calls one tool,
prints the tool's text result, and exits. Reads until the matching response id
arrives (no sleep-based timing).

This client is the plugin's mutation chokepoint (blueprint §3 / blocker B1): every
`query`/`exec` SQL string is run through the verb-class statement classifier
(`sql_classifier.py`) and gated BEFORE it reaches the server. Reads execute freely;
safe-writes require `--allow-mutation` on a non-`main` agent branch and a GA flavor;
history-affecting statements (push / merge / reset --hard / branch-delete / DROP
DATABASE / unknown CALL) are always refused (recommend-only).

Requires: python3 (stdlib only) + a PINNED `dolt-mcp-server` on PATH. The plugin
  pins the binary (blocker B4) — do NOT install `@latest`:
    go install github.com/dolthub/dolt-mcp/mcp/cmd/dolt-mcp-server@v0.3.6
  Pinned: github.com/dolthub/dolt-mcp v0.3.6
  Module checksum (verified by `go install @v0.3.6` against sum.golang.org):
    h1:uwjh1zf0er51VBT6uY3tI7JLj5pYxWyk9uB6CYQOhfU=
  A bump is proposed only by the dolt-watch routine (never auto-trusted).

Usage:
  dolt-mcp-client.py --port 35579 --database beads query "SELECT COUNT(*) FROM issues"
  dolt-mcp-client.py --port 35579 list_databases
  echo "SELECT ..." | dolt-mcp-client.py --port 35579 --database beads query -
  # a safe-write must opt in AND target an agent branch (never main):
  dolt-mcp-client.py --port 35579 --database beads --allow-mutation \
      --branch agent/my-task exec "INSERT INTO issues ..."

Connection defaults come from env when flags are omitted:
  DOLT_HOST (127.0.0.1), DOLT_PORT, DOLT_USER (root), DOLT_DATABASE, DOLT_PASSWORD ('')
  DOLT_MATURITY (ga) — alpha/experimental restrict the connection to read-only.
Exit codes: 0 ok · 2 bad usage · 3 binary missing · 4 connection/tool error ·
            5 timeout · 6 mutation refused by the verb-class gate
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sql_classifier import gate_decision  # noqa: E402

BIN = "dolt-mcp-server"
PINNED_VERSION = "v0.3.6"  # blocker B4 — see module docstring; bump only via dolt-watch
INSTALL_HINT = (f"go install github.com/dolthub/dolt-mcp/mcp/cmd/"
                f"dolt-mcp-server@{PINNED_VERSION}")


def eprint(*a):
    print(*a, file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="stdio client for dolthub/dolt-mcp")
    ap.add_argument("--host", default=os.environ.get("DOLT_HOST", "127.0.0.1"))
    ap.add_argument("--port", default=os.environ.get("DOLT_PORT"))
    ap.add_argument("--user", default=os.environ.get("DOLT_USER", "root"))
    ap.add_argument("--database", default=os.environ.get("DOLT_DATABASE", "information_schema"))
    ap.add_argument("--branch", default=os.environ.get("DOLT_BRANCH", "main"),
                    help="working branch (the dolt-mcp query/exec tools require it; default main)")
    ap.add_argument("--password", default=os.environ.get("DOLT_PASSWORD", ""))
    ap.add_argument("--maturity", default=os.environ.get("DOLT_MATURITY", "ga"),
                    help="flavor maturity (ga|beta|alpha|experimental); pre-GA is read-only")
    ap.add_argument("--allow-mutation", action="store_true",
                    help="opt in to safe-write SQL (still refused on main / pre-GA / for "
                         "history-affecting statements)")
    ap.add_argument("--timeout", type=float, default=25.0, help="seconds")
    ap.add_argument("tool", help="MCP tool name, e.g. query, exec, list_databases, list_dolt_commits")
    ap.add_argument("sql", nargs="?", help="SQL for query/exec ('-' to read from stdin)")
    args = ap.parse_args()

    if not args.port:
        eprint("error: --port (or DOLT_PORT) is required")
        return 2
    if not shutil.which(BIN):
        eprint(f"error: '{BIN}' not found on PATH. Install (pinned): {INSTALL_HINT}")
        return 3

    # Build tool arguments
    tool_args = {}
    if args.tool in ("query", "exec"):
        sql = args.sql
        if sql == "-" or (sql is None and not sys.stdin.isatty()):
            sql = sys.stdin.read()
        if not sql or not sql.strip():
            eprint(f"error: tool '{args.tool}' requires a SQL string")
            return 2
        sql = sql.strip()
        # The mutation chokepoint (blocker B1): classify + gate BEFORE the server call.
        allowed, verb_class, reason = gate_decision(
            sql, allow_mutation=args.allow_mutation,
            branch=args.branch, maturity=args.maturity)
        if not allowed:
            eprint(f"refused [{verb_class}]: {reason}")
            return 6
        tool_args["query"] = sql
        tool_args["working_database"] = args.database
        tool_args["working_branch"] = args.branch  # server enforces this for query/exec
    elif args.tool in ("list_dolt_commits", "list_dolt_branches", "show_tables"):
        tool_args["working_database"] = args.database
        if args.tool == "list_dolt_commits":
            tool_args["working_branch"] = args.branch

    cmd = [BIN, "--stdio", "--dolt",
           "--host", args.host, "--port", str(args.port),
           "--user", args.user, "--database", args.database]
    env = dict(os.environ)
    if args.password:
        env["DOLT_PASSWORD"] = args.password

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "dolt-mcp-client", "version": "0.1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": args.tool, "arguments": tool_args}},
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
    except OSError as e:
        eprint(f"error: failed to spawn {BIN}: {e}")
        return 3

    # Watchdog: kill the process if it runs past the timeout
    timer = threading.Timer(args.timeout, proc.kill)
    timer.start()
    try:
        for r in requests:
            proc.stdin.write(json.dumps(r) + "\n")
        proc.stdin.flush()

        result_text, err = None, None
        for line in proc.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("id") == 2:
                if "error" in o:
                    err = o["error"].get("message", str(o["error"]))
                else:
                    res = o.get("result", {})
                    parts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
                    result_text = "\n".join(parts)
                    if res.get("isError"):
                        err = result_text or "tool reported isError"
                        result_text = None
                break
    finally:
        timer.cancel()
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.terminate()

    if not timer.is_alive() and result_text is None and err is None:
        eprint(f"error: timed out after {args.timeout}s")
        return 5
    if err is not None:
        eprint(f"MCP error: {err}")
        return 4
    if result_text is None:
        eprint("error: no result returned (connection failed?). stderr:")
        eprint((proc.stderr.read() or "").strip()[:500])
        return 4
    print(result_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

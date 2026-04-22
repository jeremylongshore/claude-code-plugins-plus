# Role-scoped Tool Allowlist

Bind only the tools the current user's role is permitted to call. Forbidden tools must not be passed to `create_agent` — the model never sees them in its tool catalog, so it cannot call them.

## Why allowlist at bind time, not at tool-call time

Three common patterns fail in production:

1. **Bind everything, reject at tool execution** — the model still attempts the call, burns tokens generating arguments, and the rejection surfaces as a confusing error. P32 (tool allowlist not enforced when agents synthesize tool names from strings) bites here.
2. **Check role inside each tool's implementation** — duplicates the allowlist across N tools; drift is inevitable when a new tool is added.
3. **Wrap each tool with a decorator that reads role from global state** — global state in an async server means race conditions and wrong-tenant tools.

The structural fix: make the allowlist a property of how the agent is built, not how each tool behaves. The agent built for a viewer has a strictly smaller tool catalog than the agent built for an admin.

## The allowlist map

```python
ROLE_TOOLS: dict[str, set[str]] = {
    "viewer": {"search_docs"},
    "editor": {"search_docs", "create_note"},
    "admin":  {"search_docs", "create_note", "delete_note", "export_audit"},
}
```

Source this from your IAM system — Okta groups, Auth0 roles, a custom claim — not from a hardcoded dict in the chain code. The example above is for illustration.

## Building the agent per-request

```python
from langgraph.prebuilt import create_agent

ALL_TOOLS = {t.name: t for t in [search_docs, create_note, delete_note, export_audit]}

def agent_for(user_role: str):
    allowed_names = ROLE_TOOLS.get(user_role, set())
    if not allowed_names:
        raise PermissionError(f"role {user_role!r} has no tool access")
    tools = [ALL_TOOLS[n] for n in allowed_names if n in ALL_TOOLS]
    return create_agent(model, tools=tools)
```

Call `agent_for(user_role)` inside the request handler, not at import. The cost of `create_agent` is small (a handful of ms); the safety of a per-request build is large.

## Denylist for dangerous argument patterns

The allowlist bounds *which* tools run. The denylist bounds *what arguments* those tools accept. Patterns to reject via a pre-execution hook or a tool wrapper:

| Tool shape | Deny pattern | Why |
|---|---|---|
| SQL query | `\b(DROP|TRUNCATE|ALTER)\b` case-insensitive | Writes / schema changes from a read tool |
| Shell / subprocess | `rm -rf`, `sudo`, `> /dev/`, backticks | Destructive commands |
| HTTP fetch | `169.254.169.254`, `localhost`, `127.0.0.1`, `.internal` | Cloud metadata / SSRF |
| File read | `../`, absolute paths outside a whitelist | Path traversal |
| Python eval | Any use at all in a production tool | RCE surface; use JSON tool args instead |

Apply the denylist at the tool wrapper layer, not inside the tool:

```python
import re
from langchain_core.tools import tool

SQL_DENY = re.compile(r"\b(DROP|TRUNCATE|ALTER|GRANT|REVOKE)\b", re.IGNORECASE)

def wrap_sql_tool(raw_tool):
    @tool(name=raw_tool.name, description=raw_tool.description)
    def safe(query: str) -> str:
        if SQL_DENY.search(query):
            raise PermissionError(f"forbidden SQL keyword in query")
        return raw_tool.invoke({"query": query})
    return safe
```

The raise surfaces to the audit log via the `try / finally` pattern (see [Audit-log schema](audit-log-schema.md)) with `outcome: "tool_denied"` and the offending pattern.

## Pre-model hook for per-turn enforcement

LangGraph `create_agent` accepts a `pre_model_hook` — a chance to inspect state before each model call. Use it to enforce that the tool catalog hasn't been mutated and to strip any tool messages from prior turns that violated a since-revoked permission.

```python
def pre_model_hook(state):
    # Filter out tool results for tools the current role can no longer access.
    # Useful when a long-running session has a role change mid-flight.
    role = state.get("user_role")
    allowed = ROLE_TOOLS.get(role, set())
    messages = [
        m for m in state["messages"]
        if not (m.type == "tool" and m.name not in allowed)
    ]
    return {"messages": messages}

agent = create_agent(model, tools=tools, pre_model_hook=pre_model_hook)
```

## Testing the allowlist

```python
def test_viewer_cannot_delete():
    agent = agent_for(user_role="viewer")
    # The delete_note tool is simply not in the agent's catalog.
    assert "delete_note" not in [t.name for t in agent.get_tools()]

def test_sql_deny_pattern():
    wrapped = wrap_sql_tool(raw_sql_tool)
    with pytest.raises(PermissionError, match="forbidden SQL"):
        wrapped.invoke({"query": "DROP TABLE users"})
```

## Anti-patterns

- Building the agent once at module scope, mutating its tool list per request — race condition, tools bleed across requests
- Trusting the model's own "role" awareness — models comply most of the time, not all of the time; never a security boundary
- Logging the denylist hit but still executing the tool — negates the protection
- Regex-only denylists for shell commands — bash parsing is non-regular, use shlex and allowlist the binary instead

## Related

- [Retriever-per-request](retriever-per-request.md) — same per-request pattern for retrievers
- [Audit-log schema](audit-log-schema.md) — `outcome: "tool_denied"` entries for every deny
- [Multi-tenant regression tests](multi-tenant-regression-tests.md) — test fixtures for allowlist / denylist

# Error Propagation in LangGraph Agents

The headline change from legacy `AgentExecutor` to `create_react_agent` is
error semantics: legacy swallowed everything (P09); new raises by default.
This reference covers when to keep that, when to degrade gracefully, and how
to build a custom error-handler node for partial tolerance.

## The three error classes

1. **Tool validation errors** (`ValidationError` from Pydantic `args_schema`).
   Raised before the tool body runs. By default `create_react_agent` converts
   these to a `ToolMessage` with the error text and lets the model retry. This
   is the right default.

2. **Tool runtime errors** (`ValueError`, `HTTPError`, anything your tool
   raises). By default these *also* become `ToolMessage` entries — the model
   sees the exception string as the observation. On the legacy `AgentExecutor`
   with `handle_parsing_errors=True`, empty-string exceptions led to silent
   loops (P09). On `create_react_agent`, empty strings still happen but the
   failure surfaces in traces.

3. **Model errors** (`anthropic.RateLimitError`, `openai.APIError`, etc).
   Propagate up from `agent.invoke()`. These should be caught at the API
   boundary and mapped to HTTP 429 / 503 / retry.

## Default behavior (the raise-by-default contract)

```python
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

@tool
def get_user(user_id: str) -> dict:
    """Fetch a user by ID."""
    if not user_id:
        raise ValueError("user_id is required")
    return db.get(user_id)  # may raise KeyError

agent = create_react_agent(model, [get_user])
result = agent.invoke({"messages": [{"role": "user", "content": "get user bob"}]})
```

What happens if `db.get("bob")` raises `KeyError: 'bob'`:

- The exception is caught by LangGraph's `ToolNode`.
- A `ToolMessage` is created with `content="Error: KeyError('bob')"`.
- The model sees it in the next step and can recover ("I couldn't find that
  user. Could you check the ID?").

What happens if you set `handle_tool_errors=False`:

- The exception propagates out of `agent.invoke()`.
- Your API handler catches it.

## When to change the default

### Pattern 1: Tool returns a string on recoverable failures

The tool is the right place to decide "this error is the model's business":

```python
@tool
def search_kb(query: str) -> str:
    """Search the KB. Returns results as text, or a 'no results' notice."""
    try:
        hits = kb.search(query)
    except ConnectionError:
        return "KB temporarily unavailable. Ask the user to try again later."
    if not hits:
        return f"No results for {query!r}. Try different keywords."
    return "\n".join(f"- {h.title}: {h.snippet}" for h in hits[:5])
```

The model reads "KB temporarily unavailable" and gracefully communicates it.
You never propagate the `ConnectionError` — it is expected, not exceptional.

### Pattern 2: Tool raises for un-recoverable failures

If an error means the entire session should abort (security violation, tenant
mismatch, missing auth), raise a custom exception:

```python
class TenantViolationError(Exception):
    pass

@tool
def lookup_account(account_id: str, *, config) -> dict:
    tenant = config["configurable"]["tenant_id"]
    if not account_id.startswith(f"{tenant}:"):
        raise TenantViolationError(f"Cross-tenant lookup: {account_id}")
    return db.fetch(account_id)

# In your handler:
try:
    result = agent.invoke(...)
except TenantViolationError as e:
    alert_security(e)
    return {"error": "forbidden"}, 403
```

To bypass LangGraph's default error-capture, set `handle_tool_errors=False` on
the `ToolNode` — but with the prebuilt agent, the cleaner path is to subclass
the exception and catch at the boundary:

```python
# The ToolNode will still catch it and emit a ToolMessage, but the model
# should reliably fail the next step. Safer to build a custom graph:
from langgraph.prebuilt import ToolNode
tool_node = ToolNode([lookup_account], handle_tool_errors=False)
# ...then wire into a custom StateGraph.
```

### Pattern 3: Custom error-handler node

For a real recovery policy — "on tool failure, route to a fallback tool or a
graceful-response node" — a custom `StateGraph` is the right level:

```python
from langgraph.graph import StateGraph, END, START
from langgraph.graph import MessagesState

def check_tool_error(state: MessagesState) -> str:
    last = state["messages"][-1]
    if last.type == "tool" and last.content.startswith("Error:"):
        return "error_handler"
    return "model"

def error_handler(state: MessagesState):
    return {"messages": [{"role": "assistant", "content":
        "I hit a problem with my tools. Let me try a different approach."}]}

graph = StateGraph(MessagesState)
graph.add_node("model", model_node)
graph.add_node("tools", tool_node)
graph.add_node("error_handler", error_handler)
graph.add_edge(START, "model")
graph.add_conditional_edges("model", route_after_model, {"tools": "tools", "end": END})
graph.add_conditional_edges("tools", check_tool_error, {
    "error_handler": "error_handler",
    "model": "model",
})
graph.add_edge("error_handler", END)
```

## Migrating from `handle_parsing_errors=True`

The legacy flag did three things:

1. Caught parsing errors (bad JSON from the model).
2. Caught tool exceptions.
3. Fed the error back as the next observation.

In LangGraph 1.0:

- **Parsing errors:** Not an issue. `create_react_agent` uses provider-native
  tool calling, so the provider rejects invalid JSON before it reaches you.
- **Tool exceptions:** Default is the same behavior (error as observation),
  but the error text is the full exception `repr`, not an empty string.
- **Silent empty-string bug (P09):** Fixed — the exception's `repr()` is
  never empty.

If you relied on `handle_parsing_errors="Check your output"` (a custom
message), move that logic into the tool itself:

```python
@tool
def strict_tool(x: int) -> str:
    """Do the thing. x must be a positive int."""
    if x <= 0:
        # Explicit message the model will see
        return "Error: x must be > 0. Please retry with a positive integer."
    return _work(x)
```

## Observability

In production, every tool error should:

1. Log the full exception with the session `thread_id`.
2. Emit a metric (`tool_error_total{tool="search_kb"}`).
3. Leave the `ToolMessage` in the trace.

```python
import logging
logger = logging.getLogger("agent.tools")

@tool
def search_kb(query: str) -> str:
    """Search the KB."""
    try:
        return _search(query)
    except Exception as e:
        logger.exception("search_kb failed", extra={"query": query})
        return f"KB error: {type(e).__name__}. Try a different query."
```

The tool returns a user-safe string; your logs have the full traceback. The
agent never silently drops an error; you never leak internals to the model.

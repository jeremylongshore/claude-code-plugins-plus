# `AgentExecutor` → `create_react_agent` Migration

LangChain 1.0 removed `initialize_agent` (P41) and changed the shape of
`intermediate_steps` (P42). This reference is the concrete before/after.

## Import changes

```python
# BEFORE (0.2.x)
from langchain.agents import initialize_agent, AgentExecutor, AgentType
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

# AFTER (1.0.x)
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
```

Attempting to import `initialize_agent` in 1.0 raises
`ImportError: cannot import name 'initialize_agent' from 'langchain.agents'`.

## Agent construction

### Before

```python
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    max_iterations=10,
    verbose=True,
)
```

### After

```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=30, max_retries=2)
agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=MemorySaver(),
)
```

## Parameter translations

| Old `AgentExecutor` / `initialize_agent` | New `create_react_agent` |
|---|---|
| `max_iterations=10` | Pass `recursion_limit=20` on invocation (doubled: each iteration = 2 node visits) |
| `handle_parsing_errors=True` | Not a param. Errors raise by default. Wrap tools to return strings for tolerant behavior. |
| `return_intermediate_steps=True` | Not needed. `result["messages"]` contains all `ToolMessage` entries. |
| `verbose=True` | Use LangSmith tracing or `stream()` / `astream()` instead. |
| `agent=AgentType.OPENAI_FUNCTIONS` | Implicit — `create_react_agent` uses provider-native tool calling. |
| `early_stopping_method="generate"` | Not a param. Implement via custom `StateGraph` with a conditional edge to `END`. |
| `max_execution_time=30` | Apply at the API boundary with `asyncio.wait_for` or your framework's request timeout. |

## Invocation shape

### Before

```python
result = agent.invoke({"input": "look up account abc"})
print(result["output"])
for action, observation in result["intermediate_steps"]:
    print(f"Tool: {action.tool}")       # AgentAction.tool
    print(f"Input: {action.tool_input}")  # AgentAction.tool_input
    print(f"Output: {observation}")
```

### After

```python
result = agent.invoke(
    {"messages": [{"role": "user", "content": "look up account abc"}]},
    config={"configurable": {"thread_id": "t1"}, "recursion_limit": 10},
)

# Final answer
print(result["messages"][-1].content)

# Tool invocation history
for m in result["messages"]:
    if m.type == "ai" and getattr(m, "tool_calls", None):
        for tc in m.tool_calls:
            print(f"Tool: {tc['name']}")   # ToolCall.name (or tc['name'] on dict form)
            print(f"Args: {tc['args']}")   # ToolCall.args (renamed from tool_input)
    elif m.type == "tool":
        print(f"Output: {m.content}")
```

## `intermediate_steps` shape change (P42)

The single biggest source of migration bugs — attribute names moved:

| 0.2.x `AgentAction` | 1.0.x `ToolCall` |
|---|---|
| `.tool` (str) | `.name` (str) — also `["name"]` on dict form |
| `.tool_input` (dict or str) | `.args` (dict) — also `["args"]` |
| N/A | `.id` (str) — new, used for matching ToolCall ↔ ToolMessage |
| N/A | `.type` — always `"tool_call"` on typed form |

The structure also changes: instead of a flat `list[tuple[AgentAction, str]]`
under `result["intermediate_steps"]`, you walk `result["messages"]` and match
`AIMessage.tool_calls` to subsequent `ToolMessage` entries by `id`.

Helper for legacy-shape consumers:

```python
def legacy_intermediate_steps(messages):
    """Adapter: return [(tool_name, args, output), ...] from a 1.0 messages list."""
    out = []
    tool_calls_by_id = {}
    for m in messages:
        if m.type == "ai" and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls_by_id[tc["id"]] = (tc["name"], tc["args"])
        elif m.type == "tool":
            call = tool_calls_by_id.get(m.tool_call_id)
            if call:
                name, args = call
                out.append((name, args, m.content))
    return out
```

## Streaming shape change

### Before

```python
for chunk in agent.stream({"input": "..."}):
    if "actions" in chunk:
        for action in chunk["actions"]:
            print(action.tool)
    elif "steps" in chunk:
        for step in chunk["steps"]:
            print(step.observation)
    elif "output" in chunk:
        print(chunk["output"])
```

### After

```python
# Node-level streaming (default): each chunk is {node_name: state_update}
for chunk in agent.stream({"messages": [...]}, config=config):
    for node, update in chunk.items():
        if "messages" in update:
            last = update["messages"][-1]
            print(f"[{node}] {last.type}: {getattr(last, 'content', '')[:80]}")

# Token-level streaming: use astream_events(version="v2")
async for event in agent.astream_events({"messages": [...]}, config=config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="", flush=True)
```

## What to grep for in your codebase

Before a migration PR, scan for these patterns — each is a breaking change:

| Grep pattern | Migrate to |
|---|---|
| `initialize_agent` | `create_react_agent` |
| `AgentExecutor(` | `create_react_agent(...)` |
| `handle_parsing_errors=` | Remove; handle in tools |
| `return_intermediate_steps=` | Remove; walk `result["messages"]` |
| `.intermediate_steps` | Walk messages, match by `tool_call_id` |
| `action.tool` (where `action` is an AgentAction) | `tc["name"]` or `tc.name` on `ToolCall` |
| `action.tool_input` | `tc["args"]` or `tc.args` |
| `max_iterations=N` | `recursion_limit=2*N` on invocation |
| `result["output"]` | `result["messages"][-1].content` |
| `AgentType.` | Remove; `create_react_agent` has no type enum |

After the mechanical replacement, re-run your eval harness. The recursion-limit
doubling is the most common source of false "it got slower" bug reports —
old `max_iterations=10` ≈ new `recursion_limit=20`, not 10.

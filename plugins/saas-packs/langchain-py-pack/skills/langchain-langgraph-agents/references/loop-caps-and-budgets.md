# Loop Caps and Budgets for LangGraph Agents

`create_react_agent` has exactly one built-in cap: `recursion_limit=25`. That is
not enough. This reference covers the three layers of defense: the recursion
cap, a token budget, and a repeated-tool-call early-stop node — the stack that
prevents P10 ("agent loops exceed 15 iterations on vague prompts").

## Layer 1: `recursion_limit`

A recursion step is one node visit. Each tool round-trip is two visits (model
node → tool node → model node). So `recursion_limit=25` ≈ 12 tool rounds.

| Agent kind | `recursion_limit` | Approx tool calls allowed |
|---|---|---|
| Chat with 1-3 tools | 5-10 | 2-5 |
| Task-completion flow | 10-15 | 4-7 |
| Planner / research | 20-30 | 10-15 |
| Multi-agent supervisor | 40+ | Coordinator rounds; budget worker calls separately |

Apply on invocation:

```python
result = agent.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": "t1"}, "recursion_limit": 10},
)
```

On exhaustion: `GraphRecursionError`. Catch it at the API boundary and surface
a user message ("I couldn't complete the request in time"). Do not auto-retry.

## Layer 2: Per-session token budget

The recursion cap does not bound cost. One tool returning a 50K-token document
plus a long completion can cost more than 20 cheap rounds. Enforce a token
ceiling with a callback:

```python
from langchain_core.callbacks import BaseCallbackHandler

class TokenBudget(BaseCallbackHandler):
    def __init__(self, max_tokens: int = 50_000):
        self.used = 0
        self.max = max_tokens

    def on_llm_end(self, response, **kwargs):
        # LangChain 1.0: token_usage is nested under llm_output or generations
        usage = {}
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {}) or {}
        elif response.generations:
            gen = response.generations[0][0]
            meta = getattr(gen.message, "usage_metadata", None) or {}
            usage = {
                "total_tokens": meta.get("input_tokens", 0) + meta.get("output_tokens", 0),
            }
        self.used += usage.get("total_tokens", 0)
        if self.used > self.max:
            raise RuntimeError(f"Token budget exceeded: {self.used}/{self.max}")

budget = TokenBudget(max_tokens=30_000)
result = agent.invoke(
    {"messages": [...]},
    config={
        "configurable": {"thread_id": "t1"},
        "recursion_limit": 10,
        "callbacks": [budget],
    },
)
```

### Suggested budgets

| Agent use case | Token ceiling | Approx $ on Claude Sonnet |
|---|---|---|
| Interactive chat | 30K | ~$0.15 |
| Customer support | 50K | ~$0.25 |
| Task completion | 100K | ~$0.50 |
| Background planner | 250K | ~$1.25 |
| Research agent | 500K | ~$2.50 |

Multiply by your volume. An agent billed at $0.25 per session running 10K
sessions/day is $75K/month — real money if you don't cap.

## Layer 3: Repeated-tool-call early stop

A common loop pattern: the model calls `search_kb("help")`, gets 5 vague
results, calls `search_kb("assistance")`, gets the same 5 results, repeats.
The recursion cap will eventually fire — but we can detect the loop earlier
by watching for repeated tool calls with similar args.

Custom `StateGraph` approach (not the prebuilt):

```python
from langgraph.graph import StateGraph, END, START
from langgraph.graph import MessagesState

class State(MessagesState):
    tool_call_history: list[tuple[str, str]]  # (tool_name, args_hash)

def model_node(state: State):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def repeated_check(state: State) -> str:
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"
    call = last.tool_calls[0]
    import hashlib, json
    args_hash = hashlib.md5(json.dumps(call["args"], sort_keys=True).encode()).hexdigest()[:8]
    history = state.get("tool_call_history", [])
    if sum(1 for (n, h) in history if n == call["name"] and h == args_hash) >= 2:
        return "end"  # same tool + same args 3 times → stop
    return "tools"

# ...wire with graph.add_conditional_edges("model", repeated_check, {"tools": "tools", "end": END})
```

For the prebuilt `create_react_agent`, you can achieve the same effect with a
callback that tracks tool calls and raises when a threshold is hit:

```python
class RepeatedToolStopper(BaseCallbackHandler):
    def __init__(self, max_repeats: int = 3):
        self.calls: dict[tuple[str, str], int] = {}
        self.max = max_repeats

    def on_tool_start(self, serialized, input_str, **kwargs):
        key = (serialized.get("name", "?"), input_str[:200])
        self.calls[key] = self.calls.get(key, 0) + 1
        if self.calls[key] >= self.max:
            raise RuntimeError(f"Tool {key[0]} called {self.max}x with same args — likely stuck")
```

## Combining all three layers

```python
result = agent.invoke(
    {"messages": [...]},
    config={
        "configurable": {"thread_id": "t1"},
        "recursion_limit": 10,         # layer 1: step cap
        "callbacks": [
            TokenBudget(max_tokens=30_000),    # layer 2: cost cap
            RepeatedToolStopper(max_repeats=3),  # layer 3: loop detection
        ],
    },
)
```

Wrap in `try`/`except` at the API boundary:

```python
try:
    result = agent.invoke(...)
except GraphRecursionError:
    return "I couldn't complete that in the time I had. Could you rephrase?"
except RuntimeError as e:
    if "Token budget" in str(e):
        return "This request is more complex than I can handle in one step. Try breaking it down."
    if "called" in str(e) and "same args" in str(e):
        return "I kept trying the same search. Could you give me a more specific question?"
    raise
```

The three messages above are user-facing bailouts, each mapped to one failure
mode. Log the full error to observability — the customer sees a friendly line,
your on-call sees the stack.

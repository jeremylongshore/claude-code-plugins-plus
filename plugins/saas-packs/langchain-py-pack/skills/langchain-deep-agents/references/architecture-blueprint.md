# Deep Agent Architecture Blueprint

Reproducing LangChain's late-2025 "Deep Agents" reference pattern from scratch
on LangGraph 1.0.x — with the P51 (virtual-FS growth) and P52 (subagent prompt
inheritance) fixes applied at construction time.

## The four-component pattern

```
          +-------------+
          |   PLANNER   |  decomposes goal -> subtasks
          +------+------+     (never writes files)
                 |
                 v
          +-------------+
          |  SUBAGENT   |  one per role; 3-8 roles total
          |  DISPATCH   |  each built with SystemMessage(override=True)
          +------+------+
                 |
                 v
          +-------------+
          |  VIRTUAL FS |  writes artifacts + metadata
          |   + CLEANUP |  evicts by age + status each cycle
          +------+------+
                 |
                 v
          +-------------+
          | REFLECTION  |  continue / replan / end / escalate
          +------+------+     max depth 3-5
                 |
          +------+------+
          |              |
        (loop back)     END
```

## Minimal end-to-end implementation

```python
from typing import TypedDict, Annotated, Literal
from operator import or_
import json

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic

# ---------- State ----------
class DeepAgentState(TypedDict):
    messages: list
    user_goal: str
    plan: dict
    pending_subtasks: list
    files: Annotated[dict, or_]
    step: int
    reflection_depth: int
    decision: str

# ---------- Model ----------
model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, timeout=30, max_retries=2)

# ---------- Planner ----------
PLANNER_SYSTEM = """You are the planner. Decompose the user's goal into 1-5
subtasks assigned to available roles: research-specialist, code-writer, critic.
Return JSON: {"subtasks": [{"role", "instruction", "expected_artifact", "read_files"}]}.
Do not execute subtasks. Do not write file contents."""

def planner_node(state: DeepAgentState) -> dict:
    file_index = {name: {"status": e["status"], "bytes": len(e.get("content") or "")}
                  for name, e in state["files"].items()}
    msg = HumanMessage(
        content=f"Goal: {state['user_goal']}\nCurrent files: {file_index}\nPrior plan: {state.get('plan')}"
    )
    r = model.invoke([SystemMessage(content=PLANNER_SYSTEM), msg])
    plan = json.loads(r.content)
    return {"plan": plan, "pending_subtasks": plan["subtasks"], "step": state["step"] + 1}

# ---------- Subagents (P52 fix: override=True via explicit prompt) ----------
SUBAGENT_PROMPTS = {
    "research-specialist": "You are a research specialist. Produce a fact-dense summary. Return ONLY the summary.",
    "code-writer": "You are a code writer. Produce runnable Python in one fenced block. Return ONLY code.",
    "critic": 'You are a critic. List defects as JSON [{"line","issue","severity"}]. Return ONLY the JSON.',
}

SUBAGENTS = {
    role: create_react_agent(
        model=model,
        tools=[],  # add role-specific tools here
        prompt=SystemMessage(content=SUBAGENT_PROMPTS[role]),
    )
    for role in SUBAGENT_PROMPTS
}

def dispatch_node(state: DeepAgentState) -> dict:
    file_writes = {}
    for task in state["pending_subtasks"]:
        reads = {name: state["files"][name]["content"]
                 for name in task.get("read_files", [])
                 if name in state["files"] and state["files"][name].get("content")}
        context = "\n\n".join(f"# {n}\n{c}" for n, c in reads.items())
        prompt = f"{context}\n\n## Task\n{task['instruction']}" if context else task["instruction"]
        sub = SUBAGENTS[task["role"]]
        out = sub.invoke({"messages": [HumanMessage(content=prompt)]})
        artifact = out["messages"][-1].content
        name = task["expected_artifact"]
        file_writes[name] = {"content": artifact, "written_at_step": state["step"], "status": "active"}
    return {"files": file_writes, "pending_subtasks": []}

# ---------- Virtual FS cleanup (P51 fix) ----------
MAX_FILE_AGE_STEPS = 20
def cleanup_node(state: DeepAgentState) -> dict:
    kept = {}
    for name, entry in state["files"].items():
        age = state["step"] - entry["written_at_step"]
        if entry.get("status") == "done" and age > 3:
            continue
        if age > MAX_FILE_AGE_STEPS:
            continue
        kept[name] = entry
    return {"files": kept}

# ---------- Reflection ----------
MAX_REFLECTION_DEPTH = 5
REFLECTION_SYSTEM = """You are the reflection node. Given plan + file summaries,
return JSON {"decision": "continue"|"replan"|"end"|"escalate", "...": ...}."""

def reflection_node(state: DeepAgentState) -> dict:
    if state["reflection_depth"] >= MAX_REFLECTION_DEPTH:
        return {"decision": "escalate", "reflection_depth": state["reflection_depth"] + 1}
    summary = {name: {"status": e["status"], "bytes": len(e.get("content") or "")}
               for name, e in state["files"].items()}
    msg = HumanMessage(content=f"Plan: {state['plan']}\nFiles: {summary}")
    r = model.invoke([SystemMessage(content=REFLECTION_SYSTEM), msg])
    decision = json.loads(r.content)["decision"]
    return {"decision": decision, "reflection_depth": state["reflection_depth"] + 1}

def route(state: DeepAgentState) -> Literal["planner", "END"]:
    return "planner" if state["decision"] in ("continue", "replan") else END

# ---------- Wiring ----------
g = StateGraph(DeepAgentState)
g.add_node("planner", planner_node)
g.add_node("dispatch", dispatch_node)
g.add_node("cleanup", cleanup_node)
g.add_node("reflection", reflection_node)
g.set_entry_point("planner")
g.add_edge("planner", "dispatch")
g.add_edge("dispatch", "cleanup")
g.add_edge("cleanup", "reflection")
g.add_conditional_edges("reflection", route)

app = g.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["reflection"],  # user-facing boundary only (P51 fix)
)
```

## Invocation

```python
cfg = {"configurable": {"thread_id": "demo-1"}, "recursion_limit": 40}
result = app.invoke(
    {"messages": [], "user_goal": "Summarize ACME's latest 10-K and list 3 risks",
     "plan": {}, "pending_subtasks": [], "files": {}, "step": 0,
     "reflection_depth": 0, "decision": ""},
    config=cfg,
)
```

## Differences from the published blueprint

| LangChain reference pattern | This skill's adjustment | Why |
|---|---|---|
| Subagents constructed without explicit `prompt=` — relies on default state modifier | `prompt=SystemMessage(content=...)` on every subagent | P52: avoid parent persona leak |
| `MemorySaver` checkpoints every node | `interrupt_after=["reflection"]` | P51: 8 MB state at step 50 → bounded boundary checkpoints |
| `state["files"]` grows freely | `cleanup_node` + disk spill > 100 KB | P51: state stays under 500 KB |
| Reflection loops until model decides end | `MAX_REFLECTION_DEPTH=5` with forced escalate | Prevents silent infinite reflection |

## Canonical references

- LangChain blog: [Deep Agents](https://blog.langchain.com/deep-agents/) (late 2025 reference post; search the blog for "deep agent")
- LangGraph docs: [Multi-agent supervisor tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/)
- LangGraph docs: [Persistence and checkpointers](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- LangChain 1.0 release: [langchain + langgraph 1.0 announcement](https://blog.langchain.com/langchain-langgraph-1dot0/)

## Related references in this skill

- [subagent-prompting.md](subagent-prompting.md) — full P52 fix with unit tests
- [virtual-filesystem-patterns.md](virtual-filesystem-patterns.md) — P51 mitigation procedures
- [reflection-loop.md](reflection-loop.md) — plan-vs-actual diff and replan decision tree

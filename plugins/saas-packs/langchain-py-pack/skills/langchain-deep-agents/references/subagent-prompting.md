# Subagent Prompting — Explicit System Override (P52 fix)

Every subagent in a Deep Agent must be built so its system prompt REPLACES,
never APPENDS to, the planner's persona. This reference covers the exact
mechanics on LangGraph 1.0.x, the handoff format, and a unit test that catches
regressions.

## Why the default composition leaks (P52)

In the naive Deep Agent blueprint, the planner and subagents are built from
the same `create_react_agent` factory with a shared `state_modifier` that
prepends a persona. When a subagent is invoked with the parent's message
history (including the planner's `SystemMessage`), the provider sees:

```
SystemMessage("You are a senior planner coordinating subagents...")
SystemMessage("You are a research specialist...")   # appended
HumanMessage("Find ACME's 10-K filing")
```

Anthropic, OpenAI, and Gemini all resolve message-list system messages by
concatenation. The earlier planner persona dominates — it's longer, more
specific, and first. The subagent replies as the planner.

Observable symptoms:
- Research subagent returns `"I'll decompose this into subtasks: ..."` instead of facts
- Code-writer subagent asks clarifying questions instead of emitting code
- Critic subagent produces generic plans instead of defect lists

## The fix — `prompt=SystemMessage(...)` + fresh message list

Two contracts, both required.

### Contract 1 — build subagent with `prompt=`, not `state_modifier=`

```python
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

SUBAGENT_PROMPTS = {
    "research-specialist": (
        "You are a research specialist. Given an instruction and reference "
        "files, produce a fact-dense summary with inline citations. "
        "Return ONLY the summary. Do NOT plan, delegate, or ask questions."
    ),
    "code-writer": (
        "You are a code writer. Given a spec, produce runnable Python. "
        "Return ONLY code in one fenced block. Do NOT explain or plan."
    ),
    "critic": (
        'You are a critic. Given an artifact and a spec, list concrete '
        'defects as JSON: [{"line": int, "issue": str, "severity": str}]. '
        "Return ONLY the JSON. Do NOT rewrite the artifact."
    ),
}

def build_subagent(role: str, model, tools=None):
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=SystemMessage(content=SUBAGENT_PROMPTS[role]),
    )
```

On LangGraph 1.0.x, the `prompt=` parameter is the supported surface for
pinning a subagent's persona. It replaces the default state modifier instead
of composing with it.

### Contract 2 — never pass parent message history into a subagent

Build a fresh `HumanMessage` per subagent invocation. Do not splice the
planner's `messages` into the subagent's input.

```python
from langchain_core.messages import HumanMessage

def invoke_subagent(subagent, instruction: str, read_files: dict) -> str:
    # Build from scratch — parent history never touches this list.
    context = "\n\n".join(f"# {name}\n{content}" for name, content in read_files.items())
    task_msg = HumanMessage(content=f"{context}\n\n## Task\n{instruction}" if context else instruction)
    result = subagent.invoke({"messages": [task_msg]})
    return result["messages"][-1].content
```

## Handoff format — structured output back to planner

The subagent's return MUST be a single artifact or a structured JSON blob,
never the full message trace. This keeps `state["files"]` bounded and the
planner's reflection prompt short.

```python
from pydantic import BaseModel, Field

class SubagentResult(BaseModel):
    artifact_name: str = Field(..., description="Filename to write into virtual FS")
    content: str = Field(..., description="The produced artifact")
    status: str = Field("active", description='"active" | "done" | "failed"')
    notes: str | None = Field(None, description="Short handoff note, <= 200 chars")

# Wrap the subagent to enforce this shape.
def invoke_subagent_structured(subagent, instruction, read_files, artifact_name) -> SubagentResult:
    content = invoke_subagent(subagent, instruction, read_files)
    return SubagentResult(artifact_name=artifact_name, content=content, status="active")
```

If the subagent's raw output does not fit the contract (e.g., critic returned
prose instead of JSON), reject + retry once with a reminder, then mark
`status="failed"` and surface to reflection.

## Unit test — regression test for P52

```python
import pytest
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

@pytest.mark.parametrize("role,probe,expected_keywords,forbidden_keywords", [
    ("research-specialist",
     "What is the capital of France?",
     ["paris"],
     ["decompose", "subtask", "delegate", "i'll plan"]),
    ("code-writer",
     "Write a function that returns the sum of two integers.",
     ["def ", "return"],
     ["decompose", "subtask", "clarifying question"]),
    ("critic",
     'Review this code: `def add(a,b): return a-b`. Spec: add two numbers.',
     ['"issue"', '"severity"'],
     ["decompose", "let me plan"]),
])
def test_subagent_persona_does_not_leak_planner(role, probe, expected_keywords, forbidden_keywords):
    sub = build_subagent(role, model)
    out = invoke_subagent(sub, probe, read_files={})
    lo = out.lower()
    for kw in expected_keywords:
        assert kw.lower() in lo, f"{role}: missing expected keyword {kw!r} in output"
    for kw in forbidden_keywords:
        assert kw.lower() not in lo, f"{role}: planner-persona keyword {kw!r} leaked — P52 regression"
```

Run this test in CI whenever you touch subagent construction.

## Anti-patterns

| Anti-pattern | Why it fails | Replace with |
|---|---|---|
| Shared `state_modifier` function for planner and subagents | Composes personas, produces P52 leak | Per-role `prompt=SystemMessage(...)` |
| Passing `state["messages"]` into the subagent invocation | Parent persona and prior turns pollute the subagent | `{"messages": [HumanMessage(task)]}` — fresh list |
| Subagent returns the full message history to the planner | Inflates `state["files"]` and reflection prompt | Return a single artifact string or `SubagentResult` pydantic model |
| One subagent per user turn (reused instance) with mutated state | Hidden state from previous invocation leaks into the next | Subagents are stateless wrappers; all memory lives in the graph state |

## Related

- [architecture-blueprint.md](architecture-blueprint.md) — how subagents wire into the planner → dispatch → cleanup → reflection graph
- [reflection-loop.md](reflection-loop.md) — how reflection consumes subagent outputs
- Pain catalog: **P52** — Subagent in Deep Agent pattern inherits parent's system prompt

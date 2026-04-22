# Reflection Loop — Plan-vs-Actual Diff and Bounded Self-Critique

The reflection node closes the Deep Agent loop. It reads the current plan,
compares it to the artifacts the subagents actually produced, and emits one
of four decisions: **continue**, **replan**, **end**, **escalate**. This
reference covers the prompt skeleton, the decision tree, the plan-diff
procedure, and the depth-cap that prevents infinite self-critique.

## Why bounded depth (3-5) matters

Unbounded reflection is where Deep Agents burn cost silently. A typical
failure: the critic finds 3 defects, the planner replans, the code-writer
produces a new version, the critic finds 3 more defects (different ones),
and the loop keeps going. After 15 rounds the agent has spent $4 and the
final artifact is no better than round 2.

**Cap at 3-5 rounds per user-facing turn.** When hit, force `escalate` —
surface the partial artifact plus a specific question to the human. This is
the correct ceiling for research/synthesis workflows; raise to 10 only for
autonomous coding agents where you accept the cost-vs-depth trade-off.

## Reflection prompt skeleton

```python
REFLECTION_SYSTEM = """You are the reflection node of a Deep Agent.

Given:
- The current plan (JSON: subtasks + expected artifacts)
- A summary of files currently in virtual FS (names, status, byte counts — NOT contents)
- Step count and reflection depth so far

Decide and return ONE of:
  {"decision": "continue"}
      -- Plan is still on track; more subtasks remain. Proceed.

  {"decision": "replan", "reason": "<30-word diagnosis>"}
      -- Plan is wrong. Examples: wrong tool chosen, subtask failed,
         artifact exists but does not answer the goal.

  {"decision": "end", "final_answer": "<1-3 sentence answer referring to artifact names>"}
      -- Goal is achieved. At least one artifact has status=="done" and
         satisfies the expected_artifact for the goal.

  {"decision": "escalate", "question": "<specific question for the human>"}
      -- Ambiguity you cannot resolve without more input, OR a subagent
         failed twice on the same subtask.

Rules:
- Base the decision ONLY on plan + file summaries. Do not invent facts.
- Do NOT rewrite files. Do NOT create a new plan (that's the planner's job).
- If the user's goal is ambiguous, prefer escalate over guessing.
"""
```

## Feeding the model summaries, not contents

**Critical for P51.** Do not pass raw file contents into the reflection
prompt — that re-serializes the full virtual FS into every reflection call
and inflates both cost and state size.

```python
def summarize_files(state) -> dict:
    return {
        name: {
            "status": entry["status"],
            "bytes": len(entry.get("content") or ""),
            "age_steps": state["step"] - entry["written_at_step"],
        }
        for name, entry in state["files"].items()
    }

def reflection_node(state, model) -> dict:
    if state["reflection_depth"] >= MAX_REFLECTION_DEPTH:
        return {"decision": "escalate",
                "escalation_question": f"Reflection depth {MAX_REFLECTION_DEPTH} reached without converging."}
    msg = HumanMessage(content=(
        f"User goal: {state['user_goal']}\n"
        f"Current plan: {state['plan']}\n"
        f"File summaries: {summarize_files(state)}\n"
        f"Step: {state['step']}, Reflection depth: {state['reflection_depth']}"
    ))
    r = model.invoke([SystemMessage(content=REFLECTION_SYSTEM), msg])
    parsed = json.loads(r.content)
    return {
        "decision": parsed["decision"],
        "reflection_depth": state["reflection_depth"] + 1,
        "decision_payload": parsed,
    }
```

## The decision tree

```
Is reflection_depth >= MAX?
  yes -> decision = escalate (forced, with "depth cap reached")
  no  -> Ask model. Then:
         - continue  -> route back to planner (next subtask in pending_subtasks)
         - replan    -> route to planner (clear pending_subtasks, replan from current files)
         - end       -> validate: at least one file has status=="done"; if not, override to replan
         - escalate  -> interrupt graph; surface question + current files to human
```

## Plan-vs-actual diff

Use a small diff helper to make the "is the plan converging" judgment more
reliable than asking the model "is this done?"

```python
def plan_actual_diff(plan: dict, files: dict) -> dict:
    expected = {task["expected_artifact"] for task in plan.get("subtasks", [])}
    produced = set(files.keys())
    return {
        "expected_not_produced": sorted(expected - produced),
        "produced_not_expected": sorted(produced - expected),
        "overlap": sorted(expected & produced),
        "completion_ratio": len(expected & produced) / max(len(expected), 1),
    }
```

Feed the diff into the reflection prompt. A `completion_ratio == 1.0` AND
`all(files[n]["status"] in ("done","active") for n in overlap)` is a strong
signal for `end`. A ratio < 0.5 after 3 rounds is a strong signal for
`replan` — the plan shape itself is wrong.

## Self-critique patterns (when to re-engage a subagent)

| Situation | Signal from files | Reflection decision |
|---|---|---|
| Expected artifact missing | `expected_not_produced = ["x.md"]` | `replan` — planner re-dispatches subagent for x.md |
| Artifact present but subagent returned an error string | `files["x.md"]["status"] == "failed"` | `replan` — change subagent role or split subtask |
| Critic listed defects on an artifact | `files["x_critique.json"]["status"] == "active"` | `continue` — dispatch code-writer to fix defects |
| Same defect reported twice in a row | Track defect hashes across reflections | `escalate` — pattern unresolvable; ask human |
| All subtasks complete, final synthesis produced | `completion_ratio == 1.0` and `final_answer.md` present | `end` — return final answer |

## Escalation format

When reflection returns `escalate`, the graph interrupts (via the
`interrupt_after=["reflection"]` configured on compile) and surfaces:

```python
{
    "question": "ACME has two 10-K filings indexed under the same ticker for 2024 and 2024/R. Which should I summarize?",
    "artifacts_ready_for_review": ["acme_10k_summary_v1.md"],
    "suggested_responses": ["use 2024 only", "use 2024/R only", "summarize both"],
    "reflection_depth": 3,
}
```

The user's response re-enters the graph as a new `HumanMessage`, the planner
incorporates it, and the loop continues.

## Depth-cap tuning

| Workload | Recommended `MAX_REFLECTION_DEPTH` |
|---|---|
| Interactive Q&A over documents | 2 |
| Research synthesis | 3 |
| Long-horizon coding agent | 5 |
| Multi-artifact report generation | 4 |
| Autonomous bug-hunting | 5-7 (with explicit cost cap) |

Never exceed 10. Beyond that the agent is spinning, not reflecting.

## Related

- [architecture-blueprint.md](architecture-blueprint.md) — reflection's position in the graph
- [subagent-prompting.md](subagent-prompting.md) — subagent outputs are the input to reflection
- [virtual-filesystem-patterns.md](virtual-filesystem-patterns.md) — file summaries (not contents) into reflection
- Cross-skill: `langchain-eval-harness` — trajectory-level eval covers the full reflection loop

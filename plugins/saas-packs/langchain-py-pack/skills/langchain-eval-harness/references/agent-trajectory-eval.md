# Agent Trajectory Evaluation for LangGraph

Agents are harder to eval than chains. The "correct answer" may be reachable
via multiple tool-call paths; paths differ in efficiency, cost, and safety.
Scoring only the final answer misses the process — an agent that arrives at
the right answer after 14 redundant tool calls is not the same as one that
takes 3.

## What to score

Four complementary signals, from cheap to expensive:

1. **Final-answer correctness** — standard eval (exact match, LLM-as-judge)
2. **Trajectory match** — did the tool-call sequence match the expected path?
3. **Efficiency** — number of tool calls, total tokens, wall-clock latency
4. **Safety** — did the agent avoid disallowed tool calls or side effects?

## Capturing the trajectory from LangGraph

LangGraph gives you the execution trace via the state history:

```python
from langgraph.graph import StateGraph
from langchain_core.messages import ToolMessage, AIMessage

def extract_trajectory(final_state: dict) -> list[dict]:
    """Extract the tool-call sequence from a LangGraph run."""
    trajectory = []
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                trajectory.append({
                    "tool": tc["name"],
                    "args": tc["args"],
                })
    return trajectory
```

For streaming runs, use `graph.astream(..., stream_mode="updates")` and
collect tool-call events incrementally.

## Trajectory match with partial credit

Exact-sequence match is too strict — an agent that calls `search` then `fetch`
is functionally the same as `fetch` then `search` for many tasks. Score
trajectories on three axes:

```python
def trajectory_score(expected: list[str], actual: list[str]) -> dict:
    """
    Returns scores in [0, 1] for three dimensions.
    expected / actual are tool-name sequences (ignoring args for now).
    """
    expected_set = set(expected)
    actual_set = set(actual)

    # 1. Coverage — did the agent call every required tool at least once?
    coverage = len(expected_set & actual_set) / len(expected_set) if expected_set else 1.0

    # 2. Precision — what fraction of actual calls were expected?
    precision = len(expected_set & actual_set) / len(actual_set) if actual_set else 0.0

    # 3. Order — Kendall's tau on the subsequence of shared tools
    shared = [t for t in actual if t in expected_set]
    order = kendall_tau(expected, shared) if len(shared) >= 2 else 1.0

    return {"coverage": coverage, "precision": precision, "order": order}


def kendall_tau(expected: list[str], actual: list[str]) -> float:
    """Normalized Kendall's tau in [0, 1]. 1.0 = same order, 0.0 = reversed."""
    idx = {t: i for i, t in enumerate(expected)}
    pairs = [(idx[a], idx[b]) for a, b in zip(actual, actual[1:]) if a in idx and b in idx]
    if not pairs:
        return 1.0
    concordant = sum(1 for a, b in pairs if a < b)
    return concordant / len(pairs)
```

Interpret:

- `coverage=1.0, precision=1.0, order=1.0` — exact match
- `coverage=1.0, precision=0.5, order=1.0` — agent over-explored (extra tools) but got all required
- `coverage=0.6, precision=1.0, order=1.0` — agent skipped required tools
- `coverage=1.0, precision=1.0, order=0.3` — agent called the right tools in a bad order

For a single composite score, weighted sum:
`0.5 * coverage + 0.3 * precision + 0.2 * order`

## Args-level matching (optional)

Tool-name matching misses cases where the agent called `search(query="wrong")`
instead of `search(query="right")`. For args-level:

```python
def args_match(expected_call: dict, actual_call: dict, judge=None) -> bool:
    """Judge whether actual_call.args is equivalent to expected_call.args."""
    if expected_call["tool"] != actual_call["tool"]:
        return False
    # Exact match is too strict for free-form args
    if judge is None:
        return expected_call["args"] == actual_call["args"]
    # LLM-as-judge for paraphrased query args
    return judge.invoke(
        f"Are these tool-call args semantically equivalent?\n"
        f"Expected: {expected_call['args']}\n"
        f"Actual: {actual_call['args']}\n"
        f"Reply with only 'yes' or 'no'."
    ).content.strip().lower() == "yes"
```

## Efficiency and safety

```python
def efficiency_score(trajectory: list, max_calls: int = 10) -> float:
    """Penalize trajectories longer than the expected optimum."""
    return max(0.0, 1.0 - max(0, len(trajectory) - max_calls) / max_calls)


FORBIDDEN_TOOLS = {"delete_user", "send_email"}  # adjust per task

def safety_pass(trajectory: list[dict]) -> bool:
    return not any(call["tool"] in FORBIDDEN_TOOLS for call in trajectory)
```

Safety is pass/fail, not a score — one forbidden call fails the run.

## LLM-as-judge fallback for free-form agents

When the trajectory is non-deterministic (a chat agent exploring a knowledge
base) and coverage/precision are too strict, use LLM-as-judge on the full
trajectory:

```python
from langchain_anthropic import ChatAnthropic

judge = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

def judge_trajectory(goal: str, trajectory: list[dict], final_answer: str) -> dict:
    prompt = f"""You are scoring an LLM agent's execution trajectory.

Goal: {goal}

Trajectory (tool calls in order):
{chr(10).join(f'  {i+1}. {c["tool"]}({c["args"]})' for i, c in enumerate(trajectory))}

Final answer: {final_answer}

Score these on a 1-5 scale and return JSON:
- goal_achievement: did the final answer achieve the goal?
- efficiency: was the trajectory efficient (no redundant calls)?
- safety: did the agent avoid unnecessary or risky actions?

Return only JSON: {{"goal_achievement": N, "efficiency": N, "safety": N, "reasoning": "..."}}.
"""
    response = judge.invoke(prompt)
    import json
    return json.loads(response.content)
```

**Variance warning:** LLM-as-judge on trajectories is higher-variance than on
final answers alone (±0.5 on a 5-point scale across runs). Average over 3+
judge runs and report the mean with SD. See `ci-integration.md` for the
quorum pattern.

## Visualizing mismatches

When a run fails, a diff view helps. A simple Markdown render:

```python
def render_trajectory_diff(expected: list[dict], actual: list[dict]) -> str:
    lines = ["## Expected", ""]
    for i, c in enumerate(expected, 1):
        lines.append(f"{i}. `{c['tool']}({c.get('args', '')})`")
    lines += ["", "## Actual", ""]
    for i, c in enumerate(actual, 1):
        mark = "✓" if i <= len(expected) and c["tool"] == expected[i-1]["tool"] else "✗"
        lines.append(f"{i}. {mark} `{c['tool']}({c.get('args', '')})`")
    return "\n".join(lines)
```

Post this to the LangSmith trace comment or the PR CI output. Engineers can
spot a wrong-tool call faster than they can parse a 0.6 coverage score.

## Non-determinism and seeding

LangGraph agents with `temperature > 0` produce different trajectories across
runs. For reproducible eval:

- Set `temperature=0` for the eval run even if production uses higher.
- Pin `seed` on providers that support it (`ChatOpenAI(seed=42)`; Anthropic
  does not expose seed but temperature=0 is usually deterministic enough).
- Run each example N=3 times and report the trajectory-score variance —
  high variance means the agent's policy is unstable on that example.

## Common failure modes

- **Early termination** — agent returns "I don't know" after 1 call when it
  should have kept searching. Coverage drops to 0. Adjust agent's stopping
  criteria before declaring the policy broken.
- **Loop on a failing tool** — agent retries the same failing tool 10 times.
  Catch with `efficiency_score` threshold (< 0.2 is a failure) or a
  `max_tool_calls` guard in the graph itself.
- **Wrong-tool drift** — after a prompt update, agent switches to a less-
  accurate tool for a task. Detect by monitoring per-tool-call frequency
  over eval runs.

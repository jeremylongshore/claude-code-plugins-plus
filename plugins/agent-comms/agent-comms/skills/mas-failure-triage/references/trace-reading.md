# Reading a multi-agent trace

## Segmenting

A usable trace has, per turn: which agent acted, what it received, what it produced, and which tools it
called. Where turns are not labelled, recover the segmentation before analysing anything — an
unsegmented trace hides exactly the handoff boundaries where FC2 failures live.

Useful anchors when grepping a log:

| Anchor | Finds |
| --- | --- |
| Role or agent-name labels | Turn boundaries |
| Handoff or delegation markers | The edges in the actual graph |
| Tool-call records | What an agent did, as distinct from what it said it would do |
| Termination or completion markers | Whether the stop condition was ever evaluated |
| Retry or backoff records | Repetition that presents as normal operation |

## What each category looks like in a trace

**FC1 system design.** Compare the agent's input against its output. A constraint present in the input
and violated in the output is FM-1.1. An agent producing work assigned to a different role is FM-1.2.
The same tool call with identical arguments in consecutive turns is FM-1.3. A statement contradicting an
earlier established fact is FM-1.4. A run past its stated goal, or with no stop evaluation anywhere, is
FM-1.5.

**FC2 inter-agent misalignment.** These live **at handoff boundaries**, so read the boundary itself, not
the turns on either side:

- Compare what agent A **knew** against what A **passed**. A gap is FM-2.4 information withholding — the
  single most valuable diff in multi-agent debugging.
- Compare what agent B **received** against what B **did**. No causal connection is FM-2.5 ignored input.
- Compare what an agent **said it would do** against its **tool calls**. A mismatch is FM-2.6.
- Look for a turn where earlier context vanishes entirely — FM-2.1 conversation reset.
- Look for an ambiguity that was resolved by assumption rather than a question — FM-2.2.

**FC3 task verification.** Search for a verification step at all. Its absence is FM-3.2 and is more
common than a broken one. Where a verifier ran, check *what property* it checked — a verifier confirming
output exists rather than output being correct is FM-3.3, and it is worse than none because it
manufactures confidence.

## The two diffs that find most FC2 failures

```text
diff A.knowledge  A.handoff     → gap = FM-2.4 information withholding
diff B.received   B.behaviour   → no effect = FM-2.5 ignored input
```

Neither is visible from a single agent's transcript. Both require the boundary. This is the concrete
reason single-agent debugging misses the majority of the inter-agent category.

## Common reading errors

- **Starting from the symptom.** Reading backward from bad output finds the last thing that touched it,
  which is rarely the cause.
- **Treating confident output as correct output.** Confidence is uncorrelated with correctness and is
  precisely what FM-3.1 and FM-3.3 produce.
- **Assuming a quiet agent is idle.** An agent that received a message and produced nothing may be
  FM-2.5, not waiting.
- **Reading a summary instead of the trace.** A run summary is written by the system that failed. Read
  the turns.
- **Ignoring the error paths.** The graph is often acyclic in the happy path and cyclic exactly under
  failure. Trace the error handlers as live edges.

## Provisional findings

State a finding as provisional whenever the trace is missing agents, missing turns, or missing tool-call
records. Include three things in the same block: what is missing, what the current best diagnosis is,
and what the missing evidence would change.

A provisional finding reported as final is worse than no finding — it routes the fix to a level with
unearned confidence, and the next run fails the same way with the evidence now consumed.

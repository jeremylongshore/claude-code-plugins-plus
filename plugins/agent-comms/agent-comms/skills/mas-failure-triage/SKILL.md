---
name: mas-failure-triage
description: |
  Diagnose a broken multi-agent run against the published multi-agent failure taxonomy
  known as mast — 14 named failure modes across
  three categories, derived from over 1,600 annotated traces of real multi-agent systems. Turns
  "the agents got confused" into a specific mode with a specific fix, and separates the failures
  that live inside one agent from the ones that live in the conversation between agents, which no
  amount of prompt tuning on either side will repair. Use when a multi-agent run produced a wrong
  or empty result, when agents looped or terminated early, when one agent ignored another, or when
  reviewing a trace to check what actually went wrong. Trigger with "why did my agents fail",
  "multi-agent postmortem", "agents ignored each other", "agent run terminated early",
  "mast failure mode", "debug multi-agent trace".
allowed-tools: Read, Glob, Grep
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; no runtime dependencies. Works from any trace, transcript, or log of a multi-agent run.
tags: [multi-agent, debugging, failure-analysis, mast, postmortem]
model: inherit
---

# Multi-Agent Failure Triage — Name the Mode, Then Fix It

"The agents got confused" is not a diagnosis. The published taxonomy gives 14 named modes in three
categories, built from over 1,600 annotated traces across multiple frameworks, and naming the mode is
what makes the fix decidable.

The categories matter as much as the modes. A failure in **inter-agent misalignment** lives in the
conversation, not in either agent — so improving either agent's prompt is work that cannot succeed.

## Overview

Three categories, fourteen modes. Full definitions in `references/mast-taxonomy.md`.

| Category | Modes | Where the defect lives |
| --- | --- | --- |
| **FC1 System design** | 5 | Specification, roles, termination — the setup |
| **FC2 Inter-agent misalignment** | 6 | The conversation between agents |
| **FC3 Task verification** | 3 | Whether the result was checked at all |

The category determines who can fix it: FC1 is the system author, FC2 is the topology and protocol,
FC3 is a missing or broken verifier. Fixing at the wrong level is the most common wasted effort in
multi-agent debugging.

## Prerequisites

- A trace, transcript, or log of the failed run, including each agent's inputs and outputs.
- The intended task specification and each agent's assigned role.
- The termination condition the system was supposed to reach.
- No credentials. This skill reads local artifacts and calls no external service.

## Instructions

### Step 1: Establish ground truth

Record what the run was supposed to produce and what it produced. Without both, every subsequent step
is guesswork dressed up as analysis.

### Step 2: Locate the divergence point

Read the trace forward and mark the first turn where the run left the intended path. Glob the run
directory for every artifact the trace references, then Grep for role labels and handoff markers to
segment the trace by agent. **The first divergence is the diagnosis; everything after it is
consequence.** Triaging the loudest symptom instead of the first divergence is the classic error.

Where turn labels are absent, alternatively segment on tool-call boundaries and adapt the anchors in
`references/trace-reading.md` to whatever the log format optionally provides.

### Step 3: Classify by category first

Ask three questions in this order and stop at the first yes:

1. Did an agent violate the task or role it was given, repeat a step, lose history, or fail to
   recognise the stop condition? → **FC1**.
2. Did agents talk past each other — reset context, withhold information, ignore input, derail, act
   against their own stated reasoning, or fail to ask a needed question? → **FC2**.
3. Did the run end without a correct check of its own output? → **FC3**.

### Step 4: Name the mode

Match the divergence against the 14 modes in `references/mast-taxonomy.md` and cite the mode
identifier. Two modes may co-occur; report the one at the divergence point as primary.

### Step 5: Route the fix to the right level

Fix at the level the category names, using `references/triage-playbook.md`:

| Category | Level | Typical fix |
| --- | --- | --- |
| FC1 | System author | Sharper specification, explicit termination condition, history management |
| FC2 | Topology and protocol | Structured handoff, an acknowledgment step, or removing the edge |
| FC3 | Verification | Add a verifier, or fix the one that is passing bad output |

## Examples

A run that stopped early with a plausible-looking partial result:

```text
INTENDED   research 12 sources, synthesize, verify citations
ACTUAL     synthesized from 3 sources, no verification, returned confidently
DIVERGENCE turn 7 — researcher emitted a summary while its own queue held 9 unread sources
CATEGORY   FC3 task verification
MODE       FM-3.1 premature termination
FIX        verification step is missing, not weak — add the check, do not tune the researcher
```

The most expensive misdiagnosis in the set, shown side by side:

```text
SYMPTOM    writer produced an off-topic section
WRONG      "the writer's prompt is bad" → tune the writer → recurs next run
RIGHT      turn 4: researcher's handoff omitted the constraint it had already found
CATEGORY   FC2 inter-agent misalignment
MODE       FM-2.4 information withholding
FIX        make the handoff carry the constraint explicitly; the writer was never at fault
```

A loop that a rate limiter would only have made cheaper:

```text
SYMPTOM    supervisor and worker exchanged 40 messages, no progress
CATEGORY   FC1 system design
MODE       FM-1.5 unaware of termination conditions
FIX        define the stop condition — then hand the graph to topology-safety for the cycle
```

## Error handling

- **Trace is incomplete** — report which agents and turns are missing. A diagnosis from a partial trace
  must be labelled provisional; a confident wrong mode sends the fix to the wrong level.
- **Multiple modes co-occur** — report the mode at the divergence point as primary and the rest as
  downstream. Fixing a downstream mode leaves the cause in place.
- **No divergence found** — the run may have followed a flawed specification correctly. That is FC1, not
  an unexplained failure.
- **Symptom is a loop or runaway cost** — classify the mode here, then hand the graph to the
  `topology-safety` skill. Naming the mode and breaking the cycle are two different jobs.

## Validation

1. Verify the divergence turn is cited by number, not described in prose.
2. Check that exactly one primary mode is named, with its identifier.
3. Verify the fix is routed to the level the category implies, and say why the other two levels are
   wrong for this failure.
4. Check that the diagnosis explains the observed output — a mode that does not account for what the
   run actually produced is the wrong mode.

## Output

Emit one triage block: intended versus actual, the divergence turn number, category, primary mode with
its identifier, any co-occurring modes as downstream, the fix and its level, and one line on why the
other two levels would not have helped. Provisional diagnoses carry the reason they are provisional in
the same block, not in a footnote.

## Boundaries

This skill classifies failures against a published taxonomy. It does not rewrite agents, redesign the
topology, or implement verifiers — those route to `comms-topology`, `topology-safety`, and the system
author respectively. The taxonomy is descriptive: it names what went wrong, and it does not predict
what will.

## References

- `references/mast-taxonomy.md` — the three categories and all 14 modes, with signatures.
- `references/triage-playbook.md` — divergence-first procedure and the fix-level routing table.
- `references/trace-reading.md` — segmenting a trace, spotting handoff loss, and provisional findings.

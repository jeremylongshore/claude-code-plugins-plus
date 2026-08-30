---
name: lindy-performance-tuning
description: 'Optimize Lindy AI agent execution speed, reliability, and cost efficiency.

  Use when agents are slow, consuming too many credits,

  or producing inconsistent results.

  Trigger with phrases like "lindy performance", "lindy slow",

  "optimize lindy", "lindy latency", "lindy speed".

  '
allowed-tools: Read, Write, Edit
version: 1.19.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- performance
compatibility: Compatible with AI coding agents that can read Markdown and analyze workflow measurements
---
# Lindy Performance Tuning

## Overview

Improve a Lindy workflow through controlled, workspace-specific experiments. Measure
the current workflow in Tasks, preserve approval and security boundaries, change one
variable, run the same sanitized fixture/eval cohort, and keep the change only when
predeclared latency, quality, reliability, and cost criteria pass.

## Prerequisites

- Lindy workspace with active agents
- Access to agent Tasks tab (view step-by-step execution history)
- A representative, data-minimized fixture set and offline eval cohort
- Permission to inspect Tasks and restore a saved version
- An owner-approved list of invariants: confirmations, authorization, redaction,
  retention, and side-effect limits

## Instructions

### Step 1: Define the Experiment Contract

Before editing, record:

- one workflow class and representative sanitized fixtures;
- the exact variable to change and why it should help;
- baseline sample window and sample count;
- duration median/p95, outcome ratio, eval score, and workspace-reported usage/cost;
- acceptance and rollback thresholds; and
- security/approval invariants that must remain unchanged.

Use the Tasks view and Get Task Details to identify the slowest or least reliable
block. Do not infer universal latency or credit values from this skill.

### Step 2: Save a Rollback Point

Open Version History and identify the last known-good version. Record its timestamp
or label. Restoring a version creates a new editable version; it does not erase the
current history. Keep production activation and side-effecting actions unchanged
until the candidate passes the evaluation lane.

### Step 3: Choose One Variable

Prioritize the measured bottleneck:

| Bottleneck | Symptom | Fix |
|-----------|---------|-----|
| AI step dominates duration/usage | One step is the measured hotspot | Compare one available model/configuration while holding prompt/tools fixed |
| Repeated reasoning steps | Same context is processed repeatedly | Test a single structured step while preserving required checks |
| Broad autonomous scope | Variable paths or tool calls | Narrow skills and define measurable exit conditions |
| Knowledge retrieval dominates | Too many/large results | Reduce result scope while measuring answer quality |
| Independent list work is sequential | Per-item waiting dominates | Test a bounded loop and respect downstream rate limits |
| Trigger volume is noisy | Many irrelevant tasks | Add a precise trigger filter and verify recall |

Do not remove confirmation, authorization, validation, redaction, audit, or fallback
steps merely to improve speed. Model availability, behavior, and pricing change; use
the models currently offered in the workspace and compare them on the same cohort.

### Step 4: Make the Candidate Change

Example: consolidate repeated reasoning without exposing customer data.

Before:

```
Step 1: Classify a sanitized support fixture
Step 2: Extract approved routing fields
Step 3: Draft an internal response recommendation
```

Candidate:

```
Step 1: Return validated JSON containing classification, approved routing fields,
        and an internal response recommendation
```

Use placeholders or synthetic data in fixtures:

```json
{
  "classification": "technical",
  "productCode": "PRODUCT-A",
  "issueType": "access",
  "recommendation": "Send the approved access troubleshooting guide."
}
```

Exclude names, email addresses, full messages, account numbers, credentials, and
unnecessary conversation history. Keep any external communication in draft or Ask
for Confirmation mode while testing.

### Step 5: Run the Same Evaluation Lane

1. Run offline evals against the same selected historical/reference tasks. Lindy
   documents these evals as simulation that does not execute real actions.
2. Use the Test Panel only with test data and sandbox/test integrations. Lindy
   documents Test Panel actions as real, including API calls and side effects.
3. Inspect candidate Tasks/Get Task Details for duration and failures.
4. Compare the same metrics and cohort definition to baseline.
5. Reject the candidate immediately if any security/approval invariant changed.

### Step 6: Decide and Roll Out

Accept only when every predeclared criterion passes. Example decision policy:

| Gate | Example criterion selected before the run |
|---|---|
| Quality | Eval score is no lower than baseline |
| Reliability | Failure ratio does not exceed the agreed tolerance |
| Performance | Candidate p95 improves by the agreed minimum |
| Cost | Workspace-reported usage/cost does not regress beyond tolerance |
| Safety | Confirmation, permissions, redaction, and audit evidence are unchanged |

Roll out gradually, watch Tasks against the same thresholds, and restore the saved
version if a rollback criterion fires. Then change the next variable in a new
experiment; never combine results from several simultaneous edits.

## Optimization Patterns

### Prefer Deterministic Actions for Predictable Fields

Replace AI-powered fields with **Set Manually** mode when values are predictable:

| Field | Instead of AI Prompt | Use Set Manually |
|-------|---------------------|------------------|
| Slack channel | "Post to the support channel" | `#support-triage` |
| Internal category | "Choose an appropriate queue" | `support-triage` |
| Sheet column | "Determine the right column" | Column A |

Measure the actual change; do not attach a fixed credit saving to it.

### Bound Knowledge Base Queries

- Select the smallest result set that still passes the eval cohort.
- Use specific product/issue placeholders rather than full customer messages.
- Change result count, query text, or retrieval configuration one at a time.

### Filter Triggers

Add a filter based on business-owned metadata, then test both included and excluded
fixtures. Confirm that filtering reduces irrelevant tasks without dropping required
work. Do not claim a percentage saving until the workspace task history proves it.

### Bound Agent Steps and Loops

Use an Agent Step only when the next action genuinely requires adaptive reasoning.
Keep a focused skill set, measurable exit conditions, and a fallback. For lists, set
Max Cycles from the expected bounded input plus a small safety margin. Set Max
Concurrent according to dependency and third-party rate limits; use `1` when order or
shared state requires serialization.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Candidate appears faster but quality drops | Metric optimized in isolation | Reject using the predeclared eval gate |
| Test sends a real message/update | Test Panel used with production integration | Stop, restore affected state, use sandbox data and confirmation |
| Cost comparison is unclear | Cohorts/windows differ | Re-run with the same fixtures and workspace billing source |
| Loop overloads an integration | Concurrency exceeds dependency limit | Roll back and lower Max Concurrent |
| Change removes an approval step | Safety treated as latency overhead | Reject and restore the known-good version |

## Output

Return a performance experiment record containing:

- workflow, sanitized cohort, sample count, and measurement window;
- baseline median/p95 duration, outcome ratio, eval score, and workspace usage/cost;
- one changed variable, hypothesis, and version rollback point;
- acceptance/rollback thresholds and unchanged security/approval invariants;
- candidate measurements using the same cohort; and
- a decision of accept, reject, or insufficient evidence, with a gradual rollout plan.

## Examples

An email-routing workflow shows one reasoning block as the p95 hotspot. Save the
known-good version, replace only three repeated reasoning steps with one
schema-constrained step, and test the same redacted fixtures. Keep Ask for
Confirmation on outbound email. Accept only if the chosen p95 target is met, offline
eval quality does not regress, failure tolerance passes, and workspace-reported cost
does not exceed the declared threshold; otherwise restore the saved version.

## Resources

- [Lindy Prompt Guide](https://docs.lindy.ai/fundamentals/lindy-101/prompt-guide)
- [Agent Steps](https://docs.lindy.ai/fundamentals/lindy-101/ai-agents)
- [Monitor Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Evals](https://docs.lindy.ai/fundamentals/lindy-101/evals)
- [Human in Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Version History](https://docs.lindy.ai/testing/version-history)
- [Looping](https://docs.lindy.ai/fundamentals/lindy-101/looping)

## Next Steps

Use the accepted experiment receipt as the measured input to `lindy-cost-tuning`;
do not substitute generic model, latency, or credit assumptions.

# Lindy Performance Tuning - Experiment Guide

## Measurement Sources

Use the Lindy UI surfaces that expose the actual workspace behavior:

- **Tasks** for run history, status, step order, inputs/outputs, and timestamps;
- **Get Task Details** for block-level analysis in a monitoring workflow;
- **Evals** for repeatable offline quality scoring on selected historical tasks;
- **Test Panel** for controlled testing, remembering that actions execute for real;
- **Version History** for a known-good rollback point; and
- the workspace billing/usage view for current cost evidence.

Do not poll an assumed run-history REST endpoint or request a generic workspace API
key. That surface is not the documented tuning path used here.

## Experiment Worksheet

Complete this record before making a change:

| Field | Entry |
|---|---|
| Workflow and class | Stable internal names |
| Sanitized fixture/eval cohort | IDs stored only in approved system |
| Baseline window and sample count | Same definition for candidate |
| Median / p95 duration | Measured from Tasks/Get Task Details |
| Outcome ratio and eval score | Measured from Tasks and offline evals |
| Usage/cost | Current workspace-reported value and unit |
| One changed variable | Prompt, model/config, result count, filter, or concurrency |
| Hypothesis | Why this variable targets the measured bottleneck |
| Acceptance / rollback criteria | Values chosen before candidate run |
| Known-good version | Version History receipt |
| Locked invariants | Confirmation, access, redaction, retention, audit, fallbacks |

## Controlled Sequence

1. Freeze the fixture cohort and metric definitions.
2. Save or identify the known-good version.
3. Change one variable only.
4. Keep outbound communication in draft/confirmation mode and use test integrations.
5. Run offline evals on the same cohort.
6. Use the Test Panel only with synthetic or redacted inputs; real actions execute.
7. Collect candidate Tasks using the baseline definitions.
8. Compare all gates. A latency win cannot compensate for quality or safety failure.
9. Roll out gradually or restore the known-good version.

## Data-Minimized Fixture

```json
{
  "fixtureId": "routing-technical-001",
  "message": "[SYNTHETIC] User cannot access PRODUCT-A after a routine change.",
  "expected": {
    "queue": "support-triage",
    "issueType": "access",
    "requiresApproval": true
  }
}
```

Do not place real names, addresses, account numbers, credentials, contracts, or full
customer conversations in the worksheet. If the source task contains sensitive data,
create an equivalent sanitized fixture and retain only aggregate measurements.

## Change Patterns

| Candidate change | Hold constant | Reject when |
|---|---|---|
| Compare another available model/config | Prompt, skills, cohort, approvals | Eval/reliability/safety gate fails |
| Consolidate repeated reasoning | Output schema and validations | Required check disappears |
| Reduce retrieval results | Query, cohort, answer criteria | Grounding/quality regresses |
| Add trigger filter | Downstream workflow | Required fixture no longer triggers |
| Raise loop concurrency | Items and downstream system | Errors, rate limiting, or ordering defects rise |

Model names, availability, pricing, and runtime behavior change. Record what the
workspace offered at experiment time instead of embedding a permanent recommendation.

## Decision Receipt

The completed receipt must show baseline and candidate values side by side, the exact
single change, unchanged invariants, eval evidence, task evidence, workspace cost
evidence, decision, owner, and rollback version. Mark the result `insufficient
evidence` when the cohort is too small or measurements are not comparable.

## Official References

- [Monitor Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Evals](https://docs.lindy.ai/fundamentals/lindy-101/evals)
- [Human in Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Version History](https://docs.lindy.ai/testing/version-history)
- [Looping](https://docs.lindy.ai/fundamentals/lindy-101/looping)

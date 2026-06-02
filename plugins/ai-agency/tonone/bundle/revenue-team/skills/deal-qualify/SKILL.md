---
name: deal-qualify
description: MEDDPICC-based deal qualification worksheet — guide Deal through structured qualification of any opportunity and produce a filled card + recommended next action. Use when asked to "qualify this deal", "run MEDDPICC on this opportunity", "should we pursue this", or "is this deal real".
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion
version: 0.1.0
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Deal Qualification (MEDDPICC)

You are Deal — the revenue & sales engineer on the Product Team. Qualify any opportunity using the MEDDPICC framework before committing sales resources.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Gather Deal Context

Ask for any missing inputs:

- Company name, size, industry
- How did they enter the pipeline? (inbound / outbound / referral)
- What product or tier are they evaluating?
- What do you know so far about their pain?
- Who have you spoken with?
- What is the estimated ACV?
- Stated timeline to decision?

### Step 1: Run the MEDDPICC Worksheet

Score each component: CONFIRMED (evidence in hand), PARTIAL (some signal, gaps remain), MISSING (unknown or not addressed).

| Component             | Definition                                                                             | Status | Evidence | Gap / Next Action |
| --------------------- | -------------------------------------------------------------------------------------- | ------ | -------- | ----------------- |
| **Metrics**           | Quantified business impact the buyer expects. ROI, cost reduction, time saved.         |        |          |                   |
| **Economic Buyer**    | Person with budget authority who can sign. Not just a champion.                        |        |          |                   |
| **Decision Criteria** | Formal or informal criteria they use to evaluate vendors.                              |        |          |                   |
| **Decision Process**  | Steps from evaluation to signed contract. Who approves each step?                      |        |          |                   |
| **Paper Process**     | Legal, procurement, security review requirements and timeline.                         |        |          |                   |
| **Identify Pain**     | Specific, buyer-level pain. Must be felt by the economic buyer, not just the user.     |        |          |                   |
| **Champion**          | Internal advocate with influence who sells on your behalf when you're not in the room. |        |          |                   |
| **Competition**       | Who else is in the evaluation? What are the alternatives (including do nothing)?       |        |          |                   |

### Step 2: Score the Deal

Count each component's status:

```
CONFIRMED:  [N] / 8
PARTIAL:    [N] / 8
MISSING:    [N] / 8
```

Score interpretation:

| Score                       | Verdict                      | Action                                              |
| --------------------------- | ---------------------------- | --------------------------------------------------- |
| 7-8 CONFIRMED               | Strong — pursue              | Advance to proposal stage                           |
| 5-6 CONFIRMED, rest PARTIAL | Qualified — conditions apply | Advance with gap-closing plan                       |
| 3-4 CONFIRMED               | Soft — needs work            | Stay at discovery, don't invest proposal effort yet |
| <3 CONFIRMED                | Weak — do not advance        | Disqualify or park for 60 days                      |

### Step 3: Identify the Critical Gap

The single most dangerous missing component is the qualification blocker. It is usually one of:

- **No economic buyer contact** — champion is real but has no budget authority
- **No pain at buyer level** — user pain only, not executive pain
- **No champion** — multiple contacts but none selling internally for you
- **No metrics** — they want value but haven't quantified it

Name the blocker explicitly.

### Step 4: Produce the Qualification Card

```
## Qualification Card — [Company Name]

ACV: $[X] | Stage: [pipeline stage] | Motion: [inbound/outbound/referral]
MEDDPICC Score: [N] CONFIRMED / [N] PARTIAL / [N] MISSING

### Verdict: [PURSUE / CONDITIONAL / SOFT / DISQUALIFY]

### Critical Gap
[The one thing that must be resolved before advancing]

### MEDDPICC Summary
| Component        | Status    | Key Evidence                    |
|------------------|-----------|---------------------------------|
| Metrics          | [status]  | [one line]                      |
| Economic Buyer   | [status]  | [one line]                      |
| Decision Criteria| [status]  | [one line]                      |
| Decision Process | [status]  | [one line]                      |
| Paper Process    | [status]  | [one line]                      |
| Pain             | [status]  | [one line]                      |
| Champion         | [status]  | [one line]                      |
| Competition      | [status]  | [one line]                      |

### Next 3 Actions
1. [Most urgent gap-closing action — who does it, by when]
2. [Second action]
3. [Third action]
```

## Delivery

Output the qualification card to CLI. If the deal is CONDITIONAL or SOFT, append a gap-closing sequence (3 next actions, owner, due date). If output exceeds 40 lines, delegate to /atlas-report.

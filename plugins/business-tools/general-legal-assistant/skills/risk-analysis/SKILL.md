---
name: risk-analysis
description: 'Performs deep clause-by-clause risk scoring across 10 categories with

  poison pill detection and financial exposure estimation. Use when a user

  needs to understand the specific risks in a contract before signing.

  Trigger with "/risk-analysis" or "what are the risks in this contract".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- risk
- analysis
- due-diligence
- compliance
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Risk Analysis — Clause-by-Clause Risk Scoring

Standalone deep-dive skill that scores every material clause in a contract
against ten risk categories, flags poison pills, and estimates financial
exposure. Designed to surface the clauses that could cost the most money or
create the most liability.

## Overview

Every contract contains trade-offs. This skill systematically identifies which
trade-offs are reasonable and which are dangerous by scoring clauses on a 1-10
severity scale across ten categories. It specifically hunts for "poison pills" —
clauses that appear innocuous but create disproportionate risk when triggered.

Unlike a general review, this skill produces a quantified risk profile: a heat
map of where the danger lives, what it could cost, and what to do about it.

## Prerequisites

- A contract must be provided as a file path or pasted text.
- The user should ideally specify which party's perspective to analyze from
  (e.g., "I am the service provider" or "I am the client"). If not specified,
  the analysis defaults to the party that did not draft the contract.

## Instructions

1. **Read the full contract.** Use the Read tool if a file path is provided.

2. **Identify all material clauses.** Extract each numbered section or clause
   that creates obligations, rights, restrictions, or liabilities.

3. **Score each clause across 10 risk categories** (1 = minimal risk,
   10 = extreme risk):

   | # | Category | What to Evaluate |
   |---|----------|------------------|
   | 1 | **Financial Liability** | Uncapped damages, liquidated damages, penalty clauses |
   | 2 | **Indemnification** | Scope, carve-outs, caps, duty to defend vs. hold harmless |
   | 3 | **Intellectual Property** | Work-for-hire, assignment breadth, background IP protection |
   | 4 | **Termination** | For-cause vs. convenience, cure periods, termination fees |
   | 5 | **Non-Compete / Non-Solicit** | Duration, geographic scope, industry breadth |
   | 6 | **Confidentiality** | Duration, scope of "confidential," residual knowledge carve-outs |
   | 7 | **Limitation of Liability** | Cap amount, exclusion of consequential damages, mutual vs. one-sided |
   | 8 | **Data & Privacy** | Data ownership, breach notification, sub-processor controls |
   | 9 | **Dispute Resolution** | Arbitration vs. litigation, venue, fee allocation, class action waiver |
   | 10 | **Regulatory / Compliance** | Representations of compliance, audit rights, change-in-law provisions |

4. **Detect poison pills.** Scan for these specific patterns:
   - Clauses buried in definitions that create substantive obligations
   - Cross-references that expand scope (e.g., "including but not limited to"
     chains that remove boundaries)
   - Survival clauses that extend obligations indefinitely post-termination
   - Automatic renewal with silent rollover and difficult opt-out
   - Unilateral amendment rights ("Company may modify these terms at any time")
   - Fee escalation triggers hidden in appendices or schedules
   - Broad assignment rights that allow transfer to unknown third parties
   - Waiver of jury trial buried in boilerplate

5. **Estimate financial exposure.** For each high-risk clause (score >= 7),
   estimate the potential financial impact:
   - **Direct costs:** Stated penalties, liquidated damages, fee caps
   - **Indirect costs:** Lost IP value, opportunity cost of non-compete,
     litigation expenses
   - **Worst-case scenario:** Maximum realistic exposure if the clause triggers

6. **Build the risk heat map.** Rank all clauses by composite risk score
   (severity x probability). Flag the top 5 as "Critical Attention Required."

7. **Generate recommendations.** For each high-risk clause, provide:
   - What to negotiate (specific language changes)
   - Fallback position if negotiation fails
   - Walk-away threshold

## Output

**Filename:** `RISK-ANALYSIS-{YYYY-MM-DD}.md`

```
# Risk Analysis Report
## Contract Summary
## Risk Perspective: [which party]
## Risk Heat Map
| Clause | Section | Category | Severity (1-10) | Probability | Composite |
## Poison Pill Alerts
## Financial Exposure Summary
| Risk | Best Case | Expected | Worst Case |
## Top 5 Critical Risks (detailed analysis)
## Negotiation Recommendations
## Overall Risk Rating: [LOW / MODERATE / HIGH / CRITICAL]
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| Missing party perspective | User did not specify their role | Ask which party they represent before proceeding |
| Incomplete contract | Schedules or exhibits referenced but not provided | Note the gaps explicitly; score only what is available |
| Ambiguous clause language | Deliberately vague or circular definitions | Flag as a risk in itself; score higher for intentional ambiguity |
| No financial terms stated | Contract omits dollar amounts | Estimate exposure qualitatively (low/medium/high) instead of dollar amounts |
| Multiple governing laws | Contract references conflicting jurisdictions | Flag the conflict as a dispute-resolution risk |

## Examples

**Example 1 — SaaS Agreement risk analysis:**

> User: Analyze the risks in this SaaS agreement. I am the customer.

```
Top Risks:
1. Section 9.3 — Indemnification: 9/10
   Customer indemnifies vendor for "any claims arising from use" with no cap.
   Exposure: Potentially unlimited. Negotiate mutual indemnification with cap.

2. Section 14.1 — Unilateral Amendment: 8/10
   "Company may modify terms with 30 days notice." No opt-out except
   termination. Poison pill: effectively allows price increases mid-term.
   Negotiate: Require mutual consent for material changes.

3. Section 5.2 — Data Ownership: 8/10
   "Customer grants Company a perpetual, irrevocable license to use
   Customer Data for product improvement." Survives termination.
   Negotiate: Limit to anonymized, aggregated data only.

Overall Risk Rating: HIGH
```

**Example 2 — Employment agreement:**

> User: What are the risks in ~/contracts/offer-letter.pdf? I am the employee.

```
Poison Pill Detected:
Section 12(c) — "Inventions Assignment" includes work created
"using any Company equipment" with no time-of-day limitation.
Combined with Section 3(a) requiring use of company laptop,
this effectively assigns ALL inventions to employer — including
personal side projects.
```

## Resources

- [CommonPaper Risk Assessment Framework](https://commonpaper.com/) —
  Open-source contract analysis patterns (CC BY 4.0).
- [American Bar Association — Indemnification Provisions](https://www.americanbar.org/)
  — Model clauses and risk allocation guidance.
- [FTC Unfair Contract Terms Guidance](https://www.ftc.gov/) — Federal Trade
  Commission guidance on unfair or deceptive contract practices.
- [Restatement (Second) of Contracts, Sections 205-208](https://www.ali.org/)
  — Unconscionability and duty of good faith standards.

---

**Legal Disclaimer:** This skill provides AI-generated risk analysis for
informational and educational purposes only. It does not constitute legal
advice, create an attorney-client relationship, or substitute for consultation
with a qualified attorney. Risk scores are heuristic estimates, not legal
determinations. Actual risk depends on jurisdiction, specific facts, and
applicable law. Always consult a licensed attorney before making decisions
based on this analysis.

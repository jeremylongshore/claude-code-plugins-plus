---
name: freelancer-review
description: 'Reviews contracts from a freelancer''s perspective across 14 evaluation

  lenses including misclassification risk, IP ownership, payment terms,

  kill fees, and non-compete scope. Use when a freelancer or independent

  contractor needs to evaluate a client agreement. Trigger with

  "/freelancer-review" or "review this contract as a freelancer".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- freelancer
- contractor
- misclassification
- gig-economy
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Freelancer Review — Independent Contractor Contract Analysis

Specialized contract review that evaluates agreements through 14 freelancer-
specific lenses, flags worker misclassification risk using IRS criteria, and
scores the contract on a Freelancer Fairness Score. Built for the 73+ million
Americans who freelance and routinely sign contracts drafted by the hiring
party's attorneys.

## Overview

Freelancer contracts are almost always drafted by the client. This creates a
structural power imbalance: the contract protects the client's interests by
default, and freelancers — who typically cannot afford legal counsel for every
engagement — sign terms they do not fully understand.

This skill flips the perspective. It reads the contract as if the freelancer's
attorney were reviewing it, specifically looking for the patterns that most
commonly harm independent workers: misclassification traps, overbroad IP
assignments, missing payment protections, punitive non-competes, and scope
creep enablers.

It also checks for worker misclassification risk — whether the contract's terms
suggest the relationship is actually employment disguised as contracting, which
creates tax and legal liability for both parties.

## Prerequisites

- A contract or engagement agreement must be provided as a file path or pasted
  text.
- The user is assumed to be the freelancer/contractor unless stated otherwise.
- Helpful context (if available): the freelancer's industry, typical rate, and
  whether they have other active clients.

## Instructions

1. **Read the full contract.** Use the Read tool if a file path is provided.

2. **Evaluate through 14 freelancer lenses.** Score each lens 1-10 (1 = high
   risk to freelancer, 10 = well-protected):

   | # | Lens | Key Questions |
   |---|------|---------------|
   | 1 | **Misclassification Risk** | Does the contract create an employment relationship in disguise? Control over how/when/where? Exclusivity? Benefits? |
   | 2 | **IP Ownership** | Does the freelancer retain any IP? Is background IP carved out? Is work-for-hire scope limited to deliverables? |
   | 3 | **Payment Terms** | Net-30 or less? Late payment penalties? Milestone-based? Deposit required? |
   | 4 | **Payment Amount** | Is the rate fair for scope? Are expenses covered? Is there a rate for revisions beyond scope? |
   | 5 | **Kill Fee / Cancellation** | What happens if the client cancels? Compensation for work in progress? Minimum payment guarantee? |
   | 6 | **Scope Definition** | Is scope specific enough to prevent creep? Are deliverables clearly defined? What is the change order process? |
   | 7 | **Scope Creep Protection** | Is there a process for additional work? Are out-of-scope requests billable? Who approves scope changes? |
   | 8 | **Non-Compete Clause** | Duration, geographic scope, industry breadth? Does it prevent earning a living? Is it enforceable? |
   | 9 | **Non-Solicitation** | Can the freelancer work with the client's clients independently? Duration? |
   | 10 | **Confidentiality Burden** | Is the NDA mutual? Duration reasonable? Does it prevent portfolio use? Residual knowledge carve-out? |
   | 11 | **Termination Rights** | Can the freelancer terminate? What notice is required? Are there termination penalties? |
   | 12 | **Liability Exposure** | Is liability capped? Indemnification mutual or one-sided? Insurance requirements reasonable? |
   | 13 | **Dispute Resolution** | Is arbitration mandatory? Who pays? Is the venue accessible? Class action waiver? |
   | 14 | **Credit and Portfolio** | Can the freelancer show the work in their portfolio? Is the client credited/anonymous? |

3. **Run the IRS 20-Factor Test for misclassification.** Evaluate the contract
   against IRS criteria for determining worker classification:

   | Factor | Indicator of Employment | Look For in Contract |
   |--------|------------------------|---------------------|
   | Instructions | Must comply with instructions on when, where, how | "Contractor shall follow Company's procedures" |
   | Training | Required training provided | Mandatory onboarding or methodology requirements |
   | Integration | Services integral to business | Exclusivity requirements, dedicated hours |
   | Personal services | Must personally perform | No right to subcontract or delegate |
   | Hiring assistants | Cannot hire own help | Prohibition on using subcontractors |
   | Continuing relationship | Ongoing, not project-based | Auto-renewal, indefinite term |
   | Set hours | Required work schedule | Core hours, attendance requirements |
   | Full-time required | Limits on other work | Exclusivity or "best efforts" clauses |
   | Work on premises | Required location | Office presence requirements |
   | Order of work | Prescribed sequence | Step-by-step procedures mandated |
   | Reports required | Regular progress reports | Daily standups, time tracking mandated |
   | Payment method | Hourly/salary vs. project | Hourly with timesheets vs. milestone |
   | Expenses | Company pays expenses | Equipment and software provided |
   | Tools/materials | Company provides tools | Required use of company systems/licenses |
   | Investment | No significant investment | No requirement for own tools/office |
   | Profit/loss | No risk of loss | Guaranteed minimum payment |
   | Multiple clients | Works for one client | Non-compete or exclusivity |
   | Public availability | Not available to public | Cannot market services |
   | Right to fire | Can be fired at will | At-will termination without cause |
   | Right to quit | Can quit without penalty | No termination fees for contractor |

   Count employment indicators. Score:
   - 0-5 indicators: LOW misclassification risk
   - 6-10 indicators: MODERATE risk — some terms suggest employment
   - 11-15 indicators: HIGH risk — contract likely creates employment
   - 16-20 indicators: CRITICAL — near-certain misclassification

4. **Apply the 20-item Freelancer Bill of Rights checklist.**

   | # | Right | Present? |
   |---|-------|----------|
   | 1 | Right to set own schedule | |
   | 2 | Right to work for other clients | |
   | 3 | Right to subcontract with notice | |
   | 4 | Right to work from own location | |
   | 5 | Right to use own tools and methods | |
   | 6 | Right to retain background IP | |
   | 7 | Right to portfolio use of deliverables | |
   | 8 | Right to timely payment (net-30 or less) | |
   | 9 | Right to late payment penalties | |
   | 10 | Right to kill fee on cancellation | |
   | 11 | Right to defined scope with change orders | |
   | 12 | Right to charge for out-of-scope work | |
   | 13 | Right to reasonable revision limits | |
   | 14 | Right to terminate with notice | |
   | 15 | Right to mutual (not one-sided) NDA | |
   | 16 | Right to reasonable non-compete (or none) | |
   | 17 | Right to capped liability | |
   | 18 | Right to accessible dispute resolution | |
   | 19 | Right to written scope changes only | |
   | 20 | Right to credit/attribution for work | |

5. **Calculate the Freelancer Fairness Score (0-100).**

   | Component | Weight | Calculation |
   |-----------|--------|-------------|
   | 14 Lens Scores | 50% | Average of all 14 lens scores, scaled to 50 points |
   | Misclassification (inverse) | 20% | LOW=20, MODERATE=12, HIGH=6, CRITICAL=0 |
   | Bill of Rights coverage | 20% | (Rights present / 20) x 20 |
   | Payment protection | 10% | Composite of payment terms, kill fee, late penalties |

   Letter grades: A (90-100), B (80-89), C (70-79), D (60-69), F (< 60).

6. **Generate the negotiation playbook.** For each lens scoring 5 or below,
   provide:
   - What to ask for (specific contract language change)
   - How to frame the ask (language that preserves the relationship)
   - Walk-away signal (when the term is too unfavorable to accept)

## Output

**Filename:** `FREELANCER-REVIEW-{YYYY-MM-DD}.md`

```
# Freelancer Contract Review
## Contract Summary
## Freelancer Fairness Score: [score]/100 ([grade])
## 14-Lens Evaluation
| # | Lens | Score (1-10) | Key Finding |
## Misclassification Risk Assessment
### IRS 20-Factor Test Results
| Factor | Indicator Present? | Evidence |
### Risk Level: [LOW / MODERATE / HIGH / CRITICAL]
## Freelancer Bill of Rights Checklist
| # | Right | Status | Notes |
## Top Concerns (detailed analysis)
## Negotiation Playbook
### Lens: [name]
**Current term:** [quote]
**Ask for:** [specific language]
**Frame it as:** [collaborative framing]
**Walk away if:** [threshold]
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| Not a freelance contract | Document is employment or B2B agreement | Note the mismatch; suggest the appropriate review skill instead |
| Missing payment terms | Contract does not address compensation | Flag as CRITICAL; payment terms must be explicit |
| Hybrid arrangement | Mix of employment and contractor indicators | Explain the hybrid risk; recommend legal consultation |
| Multi-party contract | More than two parties involved | Identify which party is the freelancer equivalent and analyze from that perspective |
| Non-US jurisdiction | IRS factors may not apply directly | Note jurisdiction; apply the factors as heuristics while flagging that local law governs classification |

## Examples

**Example 1 — Red-flag freelance agreement:**

> User: Review this contract from a new client. I am a freelance designer.

```
Freelancer Fairness Score: 41/100 (F)

CRITICAL FINDINGS:

Misclassification Risk: HIGH (13/20 employment indicators)
- Section 3: "Contractor shall work from Company offices during
  business hours" — sets location and schedule
- Section 4: "Contractor shall devote full-time efforts" — prevents
  other clients
- Section 7: "Company shall provide all necessary equipment" — no
  freelancer investment

IP Ownership: Score 2/10
- Section 9: ALL work product assigned to client, including
  "concepts, sketches, and preliminary designs" created "in
  connection with" the engagement. No background IP carve-out.
  Cannot use deliverables in portfolio (Section 9.4).

Kill Fee: Score 1/10
- Section 12: Client may terminate "at any time for any reason"
  with 5 days notice. No compensation for work in progress.
  No kill fee. No minimum payment.

Negotiation Playbook:
1. IP: "I'd like to retain the right to show this work in my
   portfolio after launch. This is standard industry practice and
   helps me continue to attract quality clients — which benefits
   our working relationship."
2. Kill Fee: "To protect both of us, I'd like to add a provision
   that if the project is cancelled, I'm compensated for completed
   work plus 25% of the remaining scope."
```

**Example 2 — Well-structured contractor agreement:**

> User: /freelancer-review ~/contracts/techcorp-contractor.pdf

```
Freelancer Fairness Score: 87/100 (B)

Misclassification Risk: LOW (3/20 indicators)
Bill of Rights: 17/20 present

Missing Rights:
- No late payment penalty clause (Right #9)
- No explicit revision limit (Right #13)
- No portfolio use provision (Right #7)

These are all RECOMMENDED additions — not deal-breakers.
Overall, this is a well-drafted contractor agreement that
respects the independent nature of the relationship.
```

## Resources

- [IRS Publication 15-A: Employer's Supplemental Tax Guide](https://www.irs.gov/publications/p15a)
  — Official IRS guidance on worker classification, including the common-law
  test for determining employment status.
- [IRS Form SS-8: Determination of Worker Status](https://www.irs.gov/forms-pubs/about-form-ss-8)
  — IRS form and instructions for resolving classification disputes.
- [U.S. Department of Labor — Misclassification](https://www.dol.gov/agencies/whd/flsa/misclassification)
  — DOL guidance on the Fair Labor Standards Act and misclassification.
- [Freelancers Union — Contract Resources](https://www.freelancersunion.org/)
  — Model freelance contracts and rights advocacy resources.
- [CommonPaper Contractor Agreement](https://commonpaper.com/) — Open-source
  contractor agreement template with balanced protections (CC BY 4.0).
- [FTC — Gig Economy Guidance](https://www.ftc.gov/) — Federal Trade
  Commission guidance relevant to independent contractor relationships.

---

**Legal Disclaimer:** This skill provides AI-generated contract analysis for
informational and educational purposes only. Worker classification is a complex
legal determination that depends on the totality of the actual working
relationship, not just contract language. The IRS 20-Factor Test is applied
heuristically — actual classification disputes are resolved by examining all
facts and circumstances. This does not constitute legal or tax advice, create
an attorney-client relationship, or substitute for consultation with a
qualified employment attorney or tax professional. Classification errors carry
significant penalties for both parties. Always consult a licensed professional
for classification concerns.

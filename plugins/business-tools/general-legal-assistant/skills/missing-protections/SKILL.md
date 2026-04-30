---
name: missing-protections
description: 'Audits a contract against type-specific protection checklists to find

  gaps, then provides ready-to-insert clause language for each missing

  protection. Use when a user wants to know what protections are absent

  from their contract. Trigger with "/missing-protections" or "what

  protections is this contract missing".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- gap-analysis
- protections
- compliance
- checklist
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Missing Protections — Contract Gap Finder

Audits a contract against a comprehensive checklist of protections that should
be present based on the contract type, flags every gap, rates its urgency, and
provides ready-to-insert clause language drawn from industry-standard templates.

## Overview

What a contract does not say is often more dangerous than what it does. Silence
on key protections means the default rules of the governing jurisdiction apply
— and those defaults rarely favor the weaker party.

This skill checks the contract against 15 universal protections that every
agreement should contain, plus type-specific protections tailored to the
contract category. For each missing protection, it explains the risk of
omission and provides suggested clause language based on CommonPaper open-source
templates (CC BY 4.0) and widely accepted market standards.

## Prerequisites

- A contract must be provided as a file path or pasted text.
- The user should specify which party they represent. If not specified, the
  analysis defaults to the party that did not draft the contract.

## Instructions

1. **Read the full contract.** Use the Read tool if a file path is provided.

2. **Classify the contract type** to select the appropriate checklist:
   - Employment Agreement
   - Independent Contractor / Freelance Agreement
   - Non-Disclosure Agreement (NDA)
   - Master Services Agreement (MSA)
   - Software License / SaaS Agreement
   - Terms of Service / Terms of Use
   - Partnership / Joint Venture Agreement
   - Other (apply universal checklist only)

3. **Check the 15 universal protections.** Every contract should address:

   | # | Protection | What to Look For |
   |---|-----------|-----------------|
   | 1 | **Limitation of Liability** | Cap on total damages (ideally mutual) |
   | 2 | **Indemnification Scope** | Clear boundaries on who indemnifies whom and for what |
   | 3 | **Termination for Convenience** | Either party can exit with reasonable notice |
   | 4 | **Termination for Cause** | Right to terminate if the other party breaches, with cure period |
   | 5 | **Cure Period** | Time to fix a breach before termination triggers |
   | 6 | **Notice Requirements** | How and where notices must be delivered |
   | 7 | **Force Majeure** | Excuse for non-performance due to extraordinary events |
   | 8 | **Dispute Resolution** | Defined process (mediation, arbitration, or litigation) |
   | 9 | **Governing Law** | Which jurisdiction's law applies |
   | 10 | **Assignment Restrictions** | Cannot assign without consent |
   | 11 | **Amendment Requirements** | Changes require written mutual agreement |
   | 12 | **Severability** | Invalid clauses do not void the entire contract |
   | 13 | **Entire Agreement** | Contract supersedes prior discussions |
   | 14 | **Confidentiality** | Protection for sensitive information exchanged |
   | 15 | **Data Protection** | Compliance with applicable privacy laws (GDPR, CCPA) |

4. **Check type-specific protections.** Apply the additional checklist for the
   classified contract type:

   **Employment Agreements:** Background IP carve-out, overtime/exempt
   classification, benefits vesting schedule, post-termination obligations
   clarity, whistleblower protections, non-compete geographic/temporal limits.

   **Freelance/Contractor Agreements:** Payment timeline (net-30 or less),
   kill fee / cancellation fee, scope change process, deliverable acceptance
   criteria, independent contractor status affirmation, equipment/expense
   reimbursement.

   **NDAs:** Mutual vs. unilateral clarity, residual knowledge carve-out,
   compelled disclosure exception, return/destruction of materials, reasonable
   duration (2-3 years standard), carve-out for publicly available information.

   **SaaS/Software Agreements:** SLA with uptime commitment, data portability
   on termination, data breach notification timeline, sub-processor disclosure,
   price change notice period, API deprecation notice.

   **MSAs:** SOW incorporation mechanism, change order process, acceptance
   testing period, warranty period, insurance requirements.

5. **Rate each missing protection by urgency:**

   | Rating | Criteria |
   |--------|----------|
   | **CRITICAL** | Absence creates immediate, significant financial or legal risk. Must be added before signing. |
   | **IMPORTANT** | Absence creates meaningful risk that should be addressed. Negotiate to include. |
   | **RECOMMENDED** | Best practice that strengthens position. Include if possible. |

6. **Provide suggested clause language.** For each missing protection rated
   CRITICAL or IMPORTANT, provide:
   - A ready-to-insert clause written in standard contract language
   - A note on where it should be placed in the contract
   - The source or pattern it follows (e.g., "Based on CommonPaper MSA v4,
     Section 8.3")

7. **Summarize the protection coverage score:**
   ```
   Universal protections present: X / 15
   Type-specific protections present: Y / Z
   Overall coverage: [percentage]%
   ```

## Output

**Filename:** `MISSING-PROTECTIONS-{contract-name-or-type}.md`

```
# Missing Protections Report
## Contract Summary
## Protection Coverage Score
| Category | Present | Missing | Coverage |
## Critical Missing Protections
### 1. [Protection Name]
**Risk of Omission:** [explanation]
**Suggested Clause:**
> [ready-to-insert language]
**Placement:** [where in contract]
**Source:** [reference]
## Important Missing Protections
### ...
## Recommended Missing Protections
### ...
## Complete Checklist
| # | Protection | Status | Urgency |
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| Unclassifiable contract | Contract type does not match standard categories | Apply universal checklist only; note limitation |
| Partial coverage | Protection is addressed but incompletely | Mark as "Partial" rather than present or missing; explain the gap |
| Jurisdiction-specific protections | Some protections are required by local law | Note when a protection is legally required vs. best practice |
| Referenced exhibits missing | Contract references schedules with additional terms | Note that coverage assessment is based on available text only |
| Conflicting clauses | Two sections address the same protection differently | Flag the conflict as a separate finding |

## Examples

**Example 1 — Freelance agreement missing critical protections:**

> User: What protections is this freelance contract missing? I am the freelancer.

```
Protection Coverage: 8/15 universal, 2/6 type-specific (48%)

CRITICAL Missing Protections:

1. Kill Fee / Cancellation Clause
   Risk: Client can cancel the project at any time with no compensation
   for work already completed or opportunity cost.
   Suggested Clause:
   > "If Client terminates this Agreement for convenience prior to
   > completion of the Services, Client shall pay Contractor for all
   > work completed through the termination date plus a cancellation
   > fee equal to 25% of the remaining contract value."
   Placement: Section 5 (Payment Terms)
   Source: Based on Freelancers Union standard contract, Section 4.2

2. Payment Timeline
   Risk: No payment deadline specified. Default rules vary by jurisdiction
   and may allow payment delays of 60-90 days or more.
   Suggested Clause:
   > "Client shall pay all invoices within thirty (30) calendar days of
   > receipt. Invoices unpaid after 30 days shall accrue interest at the
   > rate of 1.5% per month or the maximum rate permitted by law."
   Placement: Section 5 (Payment Terms)
   Source: Based on CommonPaper Contractor Agreement v3, Section 5.1
```

**Example 2 — SaaS agreement with partial protections:**

> User: Check ~/contracts/vendor-saas-agreement.pdf for missing protections.

```
CRITICAL: No data breach notification timeline.
The contract mentions "reasonable" notification but sets no deadline.
Under GDPR Article 33, processors must notify within 72 hours.
Under CCPA, notification must occur "in the most expedient time possible."

Suggested Clause:
> "In the event of a Security Incident affecting Customer Data,
> Provider shall notify Customer in writing within seventy-two (72)
> hours of becoming aware of the incident, including a description
> of the nature of the incident, categories of data affected,
> approximate number of records involved, and remedial measures
> taken or proposed."
Placement: After Section 9.2 (Data Security)
Source: Based on GDPR Article 33; CommonPaper DPA v2, Section 6
```

## Resources

- [CommonPaper Standard Contracts](https://commonpaper.com/) — Open-source
  contract templates with balanced protections (CC BY 4.0). Templates for NDA,
  MSA, SaaS, DPA, and Contractor agreements.
- [ICO (UK) — Data Protection Clause Guidance](https://ico.org.uk/) —
  Information Commissioner's Office guidance on data protection contract terms.
- [California Attorney General — CCPA Contract Requirements](https://oag.ca.gov/privacy/ccpa)
  — Required contract provisions for service providers under CCPA.
- [GDPR Articles 28, 32, 33](https://gdpr-info.eu/) — Data processing
  agreement requirements, security measures, and breach notification.
- [FTC — Unfair Contract Terms](https://www.ftc.gov/) — Federal Trade
  Commission guidance on unfair or one-sided contract provisions.
- [Freelancers Union — Model Contract](https://www.freelancersunion.org/) —
  Standard freelancer protections and contract language.

---

**Legal Disclaimer:** This skill provides AI-generated gap analysis for
informational and educational purposes only. Suggested clause language is based
on publicly available templates and common market standards — it has not been
reviewed by an attorney for your specific situation. This does not constitute
legal advice, create an attorney-client relationship, or substitute for
consultation with a qualified attorney. Protection requirements vary by
jurisdiction and contract context. Always have suggested clauses reviewed by a
licensed attorney before inserting them into a binding agreement.

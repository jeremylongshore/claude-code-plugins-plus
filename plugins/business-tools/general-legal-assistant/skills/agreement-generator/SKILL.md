---
name: agreement-generator
description: 'Generates customized business agreements for 10 common relationship
  types with

  plain English annotations. Use when formalizing a business relationship, creating

  a partnership agreement, or drafting a service contract from scratch.

  Trigger with "/agreement-generator" or "create a freelancer agreement".

  '
allowed-tools: Read, Write, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- agreements
- contracts
- business
- document-generation
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Business Agreement Generator

## Overview

Generates professional business agreements for 10 common relationship types, each
with type-specific clause sections, plain English annotations, and proper legal
structure. Templates are benchmarked against CommonPaper standards (CC BY 4.0),
Bonterms (CC BY 4.0), and Open-Agreements (MIT) to ensure market-standard language.

The skill uses an information-gathering wizard approach — collecting essential details
before generating, rather than producing generic boilerplate that requires heavy editing.

> **Legal Disclaimer:** This skill generates template documents for informational and
> educational purposes only. Generated agreements are not a substitute for legal advice.
> Contract requirements vary by jurisdiction, industry, and transaction specifics.
> All documents should be reviewed by a licensed attorney before execution. No
> attorney-client relationship is created by using this tool.

## Prerequisites

- Names and details of all parties to the agreement
- Clear understanding of the business relationship and obligations
- Desired term, payment structure, and governing jurisdiction

## Instructions

1. **Identify the agreement type.** Determine which of the 10 types the user needs:

   | Type | When to Use | Key Focus |
   |------|-------------|-----------|
   | Freelancer | Hiring independent contractors | Deliverables, IP, independent contractor status |
   | Partnership | Forming a business partnership | Profit sharing, decision authority, exit |
   | NDA | Protecting confidential info | Scope, duration, remedies (use nda-generator for full NDA) |
   | Licensing | Granting IP usage rights | Grant scope, royalties, exclusivity |
   | Consulting | Engaging expert advisors | Scope of work, deliverables, hourly/project fees |
   | Statement of Work (SOW) | Defining project specifics | Milestones, acceptance criteria, change orders |
   | Master Service Agreement (MSA) | Ongoing service relationship | Framework terms, SOW attachment structure |
   | Joint Venture | Temporary business collaboration | Contributions, profit split, governance, dissolution |
   | Distribution | Product distribution rights | Territory, exclusivity, minimum orders, marketing |
   | Referral | Formalizing referral partnerships | Commission structure, tracking, payment triggers |

2. **Run the information-gathering wizard.** Collect these details from the user:

   **Universal fields (all types):**
   - Full legal names and entity types of all parties
   - Business addresses
   - Effective date and term (with renewal provisions)
   - Governing law jurisdiction
   - Payment terms (amount, schedule, method)
   - Termination provisions (for cause, for convenience, notice period)

   **Type-specific fields:**
   - *Freelancer:* Deliverables list, deadlines, IP ownership, equipment provided
   - *Partnership:* Capital contributions, profit/loss split, management structure
   - *Licensing:* Licensed IP description, territory, exclusivity, royalty rate
   - *Consulting:* Hourly/project rate, travel expenses, deliverable format
   - *SOW:* Milestones with dates, acceptance criteria, change order process
   - *MSA:* Service categories, SLA requirements, SOW template
   - *Joint Venture:* Purpose, contributions (cash/IP/labor), governance board
   - *Distribution:* Products, territory, exclusivity, minimum purchase volumes
   - *Referral:* Commission percentage, payment trigger, tracking mechanism

3. **Generate type-specific clause sections.** Each agreement type includes its
   required sections. Common sections across all types:

   | Section | Included In |
   |---------|-------------|
   | Recitals & Definitions | All types |
   | Scope of Work / Services | Freelancer, Consulting, SOW, MSA |
   | Compensation & Payment | All types |
   | Intellectual Property | Freelancer, Consulting, Licensing, JV |
   | Confidentiality | All types |
   | Representations & Warranties | All types |
   | Indemnification | All types |
   | Limitation of Liability | All types |
   | Term & Termination | All types |
   | Non-Compete / Non-Solicit | Freelancer, Partnership, Consulting, JV |
   | Dispute Resolution | All types |
   | General Provisions | All types |
   | Signature Block | All types |

   **Type-specific sections:**
   - *Freelancer:* Independent Contractor Status, Tax Obligations, Equipment & Workspace
   - *Partnership:* Capital Accounts, Voting & Decisions, Admission of New Partners, Dissolution
   - *Licensing:* Grant of License, Sublicensing Rights, Quality Control, Audit Rights
   - *SOW:* Milestones & Deliverables Table, Acceptance Testing, Change Order Procedure
   - *MSA:* Service Level Agreement, SOW Incorporation, Escalation Procedures
   - *Joint Venture:* JV Entity Formation, Management Committee, Capital Calls, Wind-Down
   - *Distribution:* Territory & Exclusivity, Minimum Orders, Marketing Obligations, Inventory
   - *Referral:* Referral Definition, Commission Calculation, Tracking & Reporting, Clawback

4. **Add plain English annotations.** After each section, include:
   `> **Plain English:** {simple explanation of what this means for both parties}`

5. **Apply jurisdiction-specific adjustments:**
   - California: Enhanced independent contractor tests (ABC test per AB 5)
   - New York: Specific partnership law requirements
   - Texas: Non-compete enforceability standards
   - International: Choice of law and arbitration provisions (ICC or UNCITRAL rules)

6. **Insert [VERIFY] tags** on any assumptions about party details, payment amounts,
   or relationship specifics not explicitly provided by the user.

7. **Write the output file** using the naming convention below.

## Output

Generate a single Markdown file named `{TYPE}-AGREEMENT-{PartyA}-{PartyB}-{YYYY-MM-DD}.md`:

```
# {Type} Agreement

**Between:** {Party A} ("{Role A}")
**And:** {Party B} ("{Role B}")
**Effective Date:** {date}

---

## Table of Contents
{numbered section list}

---

## 1. Recitals and Definitions
{formal legal text}

> **Plain English:** {simple explanation}

## 2. {Type-Specific Section}
{formal legal text}

> **Plain English:** {simple explanation}

{... remaining sections ...}

---

## Signature Block
| | {Party A} | {Party B} |
|---|-----------|-----------|
| Signature | _________________ | _________________ |
| Name | {name} | {name} |
| Title | {title} | {title} |
| Date | _________________ | _________________ |

---

**[VERIFY] Tags Summary:**
{numbered list of assumptions}

**Agreement Type:** {type}
**Clause Count:** {count} sections
**Generated by:** Legal Assistant Plugin — Not a substitute for legal counsel.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Unclear agreement type | User describes a hybrid relationship | Recommend the closest type, note deviations |
| Missing payment details | User has not set compensation terms | Provide market-rate ranges for context, add [VERIFY] |
| Multi-party agreement | More than 2 parties | Adapt signature block and obligations for all parties |
| International parties | Cross-border relationship | Add international arbitration clause, address currency and tax |
| Regulated industry | Healthcare, finance, government contracting | Flag additional compliance requirements (HIPAA, SOX, FAR) |
| California freelancer | AB 5 independent contractor risks | Include ABC test analysis, recommend legal review |

## Examples

**Example 1: Freelancer Agreement**

Request: "Create a freelancer agreement for a web developer building our new marketing site"

Result: `FREELANCER-AGREEMENT-AcmeCorp-JaneDev-2026-04-02.md` with:
- Detailed scope of work with milestone deliverables
- IP assignment to company upon payment (work-for-hire with assignment backup)
- Independent contractor status affirmation
- NET-30 payment upon milestone acceptance
- 14-day termination for convenience with kill fee
- Non-compete limited to direct competitors for 6 months

**Example 2: Master Service Agreement**

Request: "Generate an MSA between our consulting firm and a new enterprise client"

Result: `MSA-AGREEMENT-ConsultingCo-EnterpriseCorp-2026-04-02.md` with:
- Framework agreement with SOW attachment template
- Service level commitments (response times, availability)
- Rate card structure with annual escalation cap
- Mutual indemnification with liability cap at 12 months fees
- Data protection addendum referencing GDPR
- SOW change order procedure with approval workflow

**Example 3: Referral Agreement**

Request: "Create a referral agreement — we'll pay 10% commission for qualified leads"

Result: `REFERRAL-AGREEMENT-CompanyA-PartnerB-2026-04-02.md` with:
- Qualified referral definition (signed contract within 90 days)
- 10% commission on first-year revenue
- 30-day payment after client payment received
- 12-month attribution window
- CRM tracking and quarterly reporting requirements

## Resources

- [CommonPaper Standard Agreements](https://commonpaper.com/standards/) — CC BY 4.0 cloud, consulting, NDA standards
- [Bonterms Cloud Terms](https://bonterms.com/) — CC BY 4.0 standardized commercial terms
- [Open-Agreements](https://github.com/open-agreements) — MIT-licensed agreement templates
- [SCORE Business Agreement Resources](https://www.score.org/) — SBA-funded small business templates
- [California AB 5 (Dynamex)](https://leginfo.legislature.ca.gov/) — Independent contractor classification
- [ICC Model Contracts](https://iccwbo.org/) — International commercial agreement standards

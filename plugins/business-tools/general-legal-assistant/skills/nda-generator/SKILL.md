---
name: nda-generator
description: 'Generates custom non-disclosure agreements with plain English annotations.

  Use when creating an NDA for business discussions, hiring, vendor relationships,

  or partnerships. Supports mutual, one-way, employee, and vendor variants.

  Trigger with "/nda-generator" or "create an NDA for our partnership".

  '
allowed-tools: Read, Write, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- nda
- confidentiality
- document-generation
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# NDA Generator

## Overview

Generates professional non-disclosure agreements tailored to the specific relationship,
jurisdiction, and scope of confidential information. Produces four NDA variants — mutual,
one-way, employee, and vendor — each with 15 mandatory sections, plain English annotations,
and jurisdiction-specific clauses. Templates are benchmarked against SCORE NDA patterns
(SBA-funded) and CommonPaper NDA standards (CC BY 4.0).

Every generated section includes a `> **Plain English:**` annotation block so non-lawyers
can understand the agreement without legal counsel.

> **Legal Disclaimer:** This skill generates template documents for informational and
> educational purposes only. Generated NDAs are not a substitute for legal advice.
> All agreements should be reviewed by a licensed attorney before execution. Terms
> may need modification based on jurisdiction-specific requirements. No attorney-client
> relationship is created by using this tool.

## Prerequisites

- Names and addresses of all parties
- Clear understanding of what information is being protected
- Desired duration of confidentiality obligations
- Governing law jurisdiction (state/country)

## Instructions

1. **Determine NDA variant.** Ask the user which type is needed:
   - **Mutual NDA** — Both parties share confidential information (partnerships, M&A discussions)
   - **One-Way NDA** — Only one party discloses (pitching to investors, sharing trade secrets)
   - **Employee NDA** — Employee access to company confidential information
   - **Vendor NDA** — Third-party vendor/contractor access to business data

2. **Gather party information.** Collect from the user:
   - Full legal names of all parties
   - Entity types (individual, LLC, Corp, etc.)
   - Addresses (for notice provisions)
   - State of incorporation / governing jurisdiction
   - Effective date

3. **Define the scope of confidential information.** Determine:
   - Categories of protected information (technical, financial, customer, strategic)
   - Specific exclusions the user wants (publicly known information, independently developed)
   - Whether oral disclosures are included (with written confirmation requirement)
   - Any carve-outs for specific data types

4. **Set duration and terms.** Establish:
   - Term of the agreement (how long parties will share information)
   - Survival period (how long confidentiality obligations last after termination)
   - Typical ranges: 1-3 years for term, 2-5 years for survival
   - Employee NDAs: often indefinite for trade secrets

5. **Generate the 15 mandatory sections:**

   | # | Section | Purpose |
   |---|---------|---------|
   | 1 | Preamble & Recitals | Identifies parties and purpose |
   | 2 | Definition of Confidential Information | What is protected |
   | 3 | Exclusions from Confidential Information | Standard carve-outs |
   | 4 | Obligations of Receiving Party | Core duty of confidentiality |
   | 5 | Permitted Disclosures | Employees, advisors, legal requirements |
   | 6 | Use Restrictions | Information used only for stated purpose |
   | 7 | Term and Termination | Duration and how to end |
   | 8 | Return or Destruction of Materials | Post-termination obligations |
   | 9 | No License or Warranty | IP rights not transferred |
   | 10 | Remedies | Injunctive relief, damages |
   | 11 | Non-Solicitation (if applicable) | Employee/customer non-solicit |
   | 12 | Governing Law | Jurisdiction and choice of law |
   | 13 | Dispute Resolution | Arbitration vs. litigation |
   | 14 | General Provisions | Severability, waiver, entire agreement, assignment |
   | 15 | Signature Block | Execution by authorized representatives |

6. **Add plain English annotations.** After each section, insert a blockquote
   explaining in simple language what the section means and why it matters.

7. **Apply variant-specific modifications:**
   - **Mutual:** Mirror all obligations for both parties
   - **One-Way:** Clearly designate disclosing and receiving party roles
   - **Employee:** Add invention assignment clause, post-employment survival, reference
     to DTSA (Defend Trade Secrets Act) whistleblower immunity notice
   - **Vendor:** Add data handling requirements, subcontractor restrictions, audit rights

8. **Insert [VERIFY] tags** on any assumptions made about parties, jurisdiction, or scope
   that the user did not explicitly confirm.

9. **Write the output file** using the naming convention below.

## Output

Generate a single Markdown file named `NDA-{Party1}-{Party2}-{YYYY-MM-DD}.md` with:

```
# Non-Disclosure Agreement
## {Mutual | One-Way | Employee | Vendor}

**Effective Date:** {date}
**Parties:** {Party 1} ("Disclosing Party") and {Party 2} ("Receiving Party")

---

### 1. Preamble and Recitals
{formal legal text}

> **Plain English:** {simple explanation}

### 2. Definition of Confidential Information
{formal legal text}

> **Plain English:** {simple explanation}

{... sections 3-15 ...}

---

### Signature Block
{signature lines with date and title fields}

---
**[VERIFY] Tags Summary:**
{list of all assumptions needing confirmation}

**Generated by:** Legal Assistant Plugin — Not a substitute for legal counsel.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Missing party names | User did not provide names | Prompt for full legal names before generating |
| Unknown jurisdiction | No governing law specified | Default to Delaware (US) or England & Wales (UK), add [VERIFY] tag |
| Overly broad scope | User says "everything" | Suggest specific categories and ask for confirmation |
| Employee in California | CA limits non-compete enforcement | Omit non-compete, note CA Business & Professions Code 16600 |
| International parties | Cross-border complexity | Add choice of law clause, note Hague Convention considerations |
| Missing entity type | User provides name without LLC/Corp | Add [VERIFY] tag, default to individual |

## Examples

**Example 1: Mutual NDA for Partnership Discussion**

Request: "Create a mutual NDA between Acme Corp and Beta LLC for exploring a joint venture"

Result: `NDA-AcmeCorp-BetaLLC-2026-04-02.md` with:
- Mutual obligations mirrored for both parties
- Scope: financial data, technical specifications, customer lists, strategic plans
- 2-year term, 3-year survival period
- Delaware governing law
- Plain English annotations on all 15 sections

**Example 2: Employee NDA**

Request: "Generate an employee NDA for a new software engineer joining our startup in California"

Result: `NDA-TechStartup-JaneDoe-2026-04-02.md` with:
- One-way structure (company discloses to employee)
- DTSA whistleblower immunity notice included
- No non-compete clause (California restriction noted)
- Invention assignment with prior invention exclusion schedule
- Indefinite survival for trade secrets

## Resources

- [SCORE NDA Templates](https://www.score.org/resource-library/nda-template) — SBA-funded, free for commercial use
- [CommonPaper Mutual NDA](https://commonpaper.com/standards/mutual-nda/) — CC BY 4.0 open standard
- [Defend Trade Secrets Act (DTSA)](https://www.congress.gov/bill/114th-congress/senate-bill/1890) — Federal trade secret protections
- [California Business & Professions Code 16600](https://leginfo.legislature.ca.gov/) — Non-compete limitations
- [ICC Model Confidentiality Agreement](https://iccwbo.org/) — International commerce standards

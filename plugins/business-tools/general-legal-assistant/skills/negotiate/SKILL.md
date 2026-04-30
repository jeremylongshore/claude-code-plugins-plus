---
name: negotiate
description: 'Analyzes contracts for unfavorable or risky clauses and generates prioritized

  counter-proposals with replacement language. Use when reviewing a contract before

  signing, preparing for a negotiation, or responding to unfavorable terms.

  Trigger with "/negotiate" or "generate counter-proposals for this contract".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- negotiation
- contracts
- counter-proposal
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Contract Negotiation Strategy Generator

## Overview

Reads a contract or agreement, identifies clauses that are unfavorable, one-sided,
or carry hidden risk, and produces a structured negotiation strategy document with
specific counter-proposals ranked by priority. Benchmarks replacement language
against CommonPaper standard clauses (CC BY 4.0) to ensure proposed alternatives
reflect market norms.

This skill performs analysis only — it does not create new contracts. It reads the
source document and outputs a negotiation strategy in Markdown.

> **Legal Disclaimer:** This skill generates AI-assisted analysis for informational
> purposes only. It does not constitute legal advice. All counter-proposals and
> replacement language must be reviewed by a licensed attorney before use in any
> binding agreement. No attorney-client relationship is created by using this tool.

## Prerequisites

- A contract or agreement file accessible in the workspace (`.md`, `.txt`, or `.pdf`)
- Knowledge of the user's negotiating position (buyer, seller, service provider, etc.)
- Understanding of which party the user represents

## Instructions

1. **Identify the contract.** Locate the contract file using Glob. If multiple contracts
   exist, ask the user to confirm which one to analyze.

2. **Read the full contract.** Use Read to ingest the entire document. Note the parties,
   effective date, governing law, and contract type.

3. **Classify the user's position.** Determine which party the user represents and their
   leverage context (e.g., small vendor vs. enterprise buyer).

4. **Scan for unfavorable clauses.** Evaluate every section against these risk categories:
   - **Liability & Indemnification** — unlimited liability, one-sided indemnity, no caps
   - **Termination** — termination for convenience without notice, auto-renewal traps
   - **IP & Ownership** — broad IP assignment, work-for-hire overreach
   - **Payment** — late payment penalties without reciprocal terms, NET-90+
   - **Confidentiality** — perpetual obligations, overly broad definitions
   - **Non-Compete / Non-Solicit** — excessive scope, duration, or geography
   - **Limitation of Liability** — exclusion of consequential damages only for one party
   - **Governing Law & Dispute** — inconvenient jurisdiction, mandatory arbitration
   - **Data & Privacy** — broad data usage rights, no breach notification
   - **Force Majeure** — missing or one-sided

5. **Prioritize findings into three tiers:**
   - **MUST-CHANGE** — Clauses that create unacceptable legal or financial risk. Deal-breakers
     if not modified.
   - **SHOULD-CHANGE** — Clauses that are unfavorable but negotiable. Significant improvement
     if changed.
   - **NICE-TO-CHANGE** — Minor improvements that strengthen position but are not critical.

6. **Generate counter-proposals.** For each flagged clause:
   - Quote the original clause text verbatim
   - Explain the specific risk in plain English
   - Provide replacement language (benchmark against CommonPaper standard clauses)
   - Include a confidence indicator: HIGH (standard market practice), MEDIUM (reasonable
     but may face pushback), LOW (aggressive position)
   - Write 2-3 negotiation talking points explaining *why* the change is fair

7. **Draft a professional email template.** Create a ready-to-send email that:
   - Opens with appreciation for the partnership/opportunity
   - Frames changes as "clarifications" or "alignment with market standards"
   - References specific clause numbers
   - Maintains a collaborative, non-adversarial tone
   - Closes with a request for a call to discuss

8. **Compile the strategy document.** Assemble all findings into the output format below.

## Output

Generate a single Markdown file named `NEGOTIATION-STRATEGY-{contract-name}.md` with:

```
# Negotiation Strategy: {Contract Name}

## Summary
- Contract: {name}
- Parties: {Party A} / {Party B}
- Representing: {which party}
- Date analyzed: {date}
- Clauses flagged: {count} ({MUST}: N, {SHOULD}: N, {NICE}: N)

## Risk Overview
{2-3 sentence executive summary of overall contract fairness}

## MUST-CHANGE Clauses
### 1. {Section Reference} — {Short Description}
**Original:** > {quoted text}
**Risk:** {plain English explanation}
**Counter-Proposal:** {replacement language}
**Confidence:** {HIGH/MEDIUM/LOW}
**Talking Points:**
- {point 1}
- {point 2}

## SHOULD-CHANGE Clauses
{same format}

## NICE-TO-CHANGE Clauses
{same format}

## Negotiation Email Draft
{professional email template}

## Benchmarks Referenced
- CommonPaper Standard Cloud Agreement (CC BY 4.0)
- {other relevant standards}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No contract file found | Missing or wrong path | Ask user for the file location |
| Ambiguous party role | Cannot determine who user represents | Ask user to clarify their position |
| Non-English contract | Skill optimized for English common law | Warn user; provide best-effort analysis with caveats |
| Highly specialized terms | Domain-specific clauses (e.g., pharma, defense) | Flag as requiring specialist review |
| PDF format unreadable | Scanned image PDF | Ask user for text version or OCR output |

## Examples

**Example 1: SaaS Vendor Agreement**

Request: "Analyze this vendor agreement and generate counter-proposals — we're the customer"

Result: Strategy document identifying 12 clauses across 3 tiers:
- MUST-CHANGE: Unlimited liability for customer (cap at 12 months fees), auto-renewal
  without 60-day notice window
- SHOULD-CHANGE: NET-60 payment terms (propose NET-30 with 2% early payment discount),
  broad IP license grant
- NICE-TO-CHANGE: Governing law in vendor's state (propose mutual arbitration)

**Example 2: Freelancer Service Agreement**

Request: "Review this freelance contract — I'm the freelancer"

Result: Strategy identifying one-sided IP assignment (propose limited license), missing
kill fee provision (propose 25% kill fee after kickoff), and 2-year non-compete
(propose narrowing to direct competitors for 6 months).

## Resources

- [CommonPaper Standard Agreements](https://commonpaper.com/standards/) — CC BY 4.0 open-source contract standards
- [Bonterms Cloud Terms](https://bonterms.com/) — CC BY 4.0 standardized cloud contracting
- [American Bar Association Model Agreements](https://www.americanbar.org/) — professional benchmarks
- [SCORE Contract Negotiation Guide](https://www.score.org/) — SBA-funded small business resources

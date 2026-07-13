---
name: contract-review
description: 'Orchestrates a comprehensive multi-agent contract review that analyzes

  risk, plain-English translation, missing protections, and compliance

  in parallel. Use when a user shares a contract and wants a full review,

  safety score, or executive summary. Trigger with "/contract-review" or

  "review this contract".

  '
allowed-tools: Read, Glob, Grep, Task
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- review
- risk
- orchestration
- multi-agent
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Contract Review — Multi-Agent Orchestrator

Flagship contract review skill that spawns five parallel analysis agents, then
aggregates their findings into a single executive report with a Contract Safety
Score. Designed for founders, freelancers, and small-business operators who need
to understand what they are signing without retaining outside counsel for every
agreement.

## Overview

Most contracts arrive as walls of dense legalese. A single-pass review misses
nuance. This skill mirrors how a law firm reviews contracts: multiple
specialists work in parallel, each with a different lens, then a senior partner
synthesizes everything into a recommendation.

The orchestrator:

1. Ingests the contract (file path or pasted text).
2. Classifies the contract type and extracts metadata.
3. Launches five parallel agents (risk, plain-English, missing protections,
   compliance, and party-balance analysis).
4. Aggregates results into a unified report with a 0-100 Contract Safety Score.

## Prerequisites

- The contract must be provided as a file path to a readable document (PDF,
  DOCX, TXT, MD) or pasted directly into the conversation.
- For file-based input the file must exist and be accessible via the Read tool.
- No external APIs or network access are required.

## Instructions

1. **Ingest the contract.**
   - If a file path is provided, read the full document with the Read tool.
   - If the text is pasted, capture it verbatim.
   - Confirm the document length; warn if it exceeds 50 pages.

2. **Classify the contract.**
   Determine the contract type from one of the following categories:
   - Employment Agreement
   - Independent Contractor / Freelance Agreement
   - Non-Disclosure Agreement (NDA)
   - Master Services Agreement (MSA)
   - Software License / SaaS Agreement
   - Terms of Service / Terms of Use
   - Privacy Policy / Data Processing Agreement
   - Partnership / Joint Venture Agreement
   - Lease / Real Estate Agreement
   - Other (describe)

3. **Extract metadata.**
   Capture: parties, effective date, term/duration, governing law,
   dispute resolution mechanism, total contract value (if stated).

4. **Launch five parallel agents using the Task tool.**
   Each agent receives the full contract text and returns structured findings.

   | Agent | Focus | Key Deliverable |
   |-------|-------|-----------------|
   | Risk Analyst | Clause-by-clause risk scoring across 10 categories | Risk heat map, poison pill flags |
   | Plain-English Translator | 8th-grade reading level rewrite | Clause-by-clause translation with flags |
   | Protection Auditor | Gap analysis against type-specific checklists | Missing protections with urgency ratings |
   | Compliance Checker | Regulatory alignment (GDPR, CCPA, labor law basics) | Compliance findings table |
   | Party-Balance Analyst | Fairness tilt between the parties | Asymmetry flags, one-sided clause list |

5. **Aggregate results.**
   Combine all five agent reports into a unified document with these sections:
   - Executive Summary (3-5 bullet points)
   - Contract Metadata table
   - Contract Safety Score (0-100) with letter grade
   - Risk Heat Map (top 5 risks ranked by severity)
   - Plain-English Quick Reference (critical clauses only)
   - Missing Protections (critical and important only)
   - Compliance Findings
   - Party-Balance Assessment
   - Recommended Next Steps (negotiate, accept, reject, consult attorney)

6. **Compute the Contract Safety Score.**
   Weighted formula:

   | Component | Weight | Source Agent |
   |-----------|--------|-------------|
   | Risk severity (inverse) | 30% | Risk Analyst |
   | Protection coverage | 25% | Protection Auditor |
   | Party balance | 20% | Party-Balance Analyst |
   | Compliance alignment | 15% | Compliance Checker |
   | Language clarity | 10% | Plain-English Translator |

   Letter grades: A (90-100), B (80-89), C (70-79), D (60-69), F (< 60).

7. **Present the final report** in the conversation and note the output
   filename.

## Output

**Filename:** `CONTRACT-REVIEW-{party-or-title}-{YYYY-MM-DD}.md`

The report uses Markdown with tables and follows this structure:

```
# Contract Review Report
## Executive Summary
## Contract Metadata
## Contract Safety Score: [score]/100 ([grade])
## Risk Heat Map
## Plain-English Quick Reference
## Missing Protections
## Compliance Findings
## Party-Balance Assessment
## Recommended Next Steps
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| File not found | Path is incorrect or file missing | Ask the user to confirm the file path |
| Unreadable format | Binary or encrypted document | Ask for a plain-text or PDF version |
| Document too long | Exceeds context window | Summarize by section; warn about truncation |
| Agent timeout | One parallel agent fails to return | Report partial results; note which agent failed |
| Ambiguous contract type | Cannot classify confidently | Ask the user to confirm the contract type |

## Examples

**Example 1 — File-based review:**

> User: Review the contract at `~/contracts/acme-msa-2026.pdf`

The orchestrator reads the file, classifies it as a Master Services Agreement,
launches five agents, and produces a report:

```
Contract Safety Score: 72/100 (C)
Top Risk: Unlimited indemnification liability (Section 8.2)
Missing: No force majeure clause, no data breach notification timeline
Balance: Tilts 65/35 in favor of Acme Corp
Recommendation: Negotiate Sections 8.2 and 12.1 before signing
```

**Example 2 — Pasted text:**

> User: Review this contract: [pasted NDA text]

The orchestrator classifies it as a Mutual NDA, flags a unilateral
non-solicitation clause hidden in the definitions, and scores it 58/100 (F).

## Resources

- [CommonPaper Standard Contracts](https://commonpaper.com/) — Open-source
  contract templates (CC BY 4.0) used as comparison baselines.
- [American Bar Association Model Contract Clauses](https://www.americanbar.org/)
  — Authoritative clause language references.
- [Restatement (Second) of Contracts](https://www.ali.org/) — American Law
  Institute's foundational contract law principles.
- [GDPR Full Text](https://gdpr-info.eu/) — EU data protection regulation.
- [CCPA Full Text](https://oag.ca.gov/privacy/ccpa) — California Consumer
  Privacy Act via the CA Attorney General.

---

**Legal Disclaimer:** This skill provides AI-generated analysis for
informational and educational purposes only. It does not constitute legal
advice, create an attorney-client relationship, or substitute for consultation
with a qualified attorney. Contract interpretation depends on jurisdiction,
context, and specific facts that an AI cannot fully evaluate. Always consult a
licensed attorney before making legal decisions based on this analysis.

---
name: contract-compare
description: 'Compares two contract versions side-by-side to detect added, removed,
  and

  modified clauses with favorability analysis. Use when a user receives a

  revised contract or redline and needs to understand what changed and who

  each change favors. Trigger with "/contract-compare" or "compare these

  two contracts".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- comparison
- redline
- negotiation
- diff
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Contract Compare — Version Comparison and Favorability Analysis

Side-by-side contract comparison skill that identifies every change between two
versions, classifies each change by type and severity, and determines which
party each modification favors. Essential during negotiation rounds when a
counterparty returns a revised draft.

## Overview

When a counterparty returns a revised contract, the changes they made — and the
changes they quietly did not make — tell a story about their priorities and
strategy. This skill performs a structured comparison that surfaces not just what
changed, but the strategic significance of each change.

It detects three dangerous patterns that manual review frequently misses:
indemnification drift (gradual shifting of liability across revisions), IP scope
creep (expanding intellectual property assignment through small wording tweaks),
and definition manipulation (redefining key terms to alter clause meaning
without touching the clauses themselves).

## Prerequisites

- Two versions of the same contract must be provided, either as:
  - Two file paths (e.g., `contract-v1.pdf` and `contract-v2.pdf`)
  - One file path and one pasted text block
  - Two pasted text blocks labeled "Version A" and "Version B"
- The user should specify which version is the original (baseline) and which is
  the revision. If not specified, assume the first provided is the original.

## Instructions

1. **Ingest both versions.** Read each document in full. If file paths are
   provided, use the Read tool.

2. **Establish the structural map.** Create a section-by-section outline of both
   documents. Note any structural changes (sections added, removed, renumbered,
   or reordered).

3. **Perform clause-level comparison.** For each section, classify changes into:

   | Change Type | Symbol | Description |
   |-------------|--------|-------------|
   | **Added** | + | Entirely new clause or section |
   | **Removed** | - | Clause present in original but absent in revision |
   | **Modified** | ~ | Wording changed within an existing clause |
   | **Moved** | -> | Same content relocated to a different section |
   | **Unchanged** | = | No material difference |

4. **Analyze favorability.** For each non-trivial change, determine:
   - **Who it favors:** Party A, Party B, Neutral, or Unclear
   - **Severity:** Minor (cosmetic/clarification), Moderate (shifts rights or
     obligations), Major (materially alters risk or liability)
   - **Strategic signal:** What the change reveals about the counterparty's
     priorities or concerns

5. **Detect dangerous patterns.** Specifically scan for:

   - **Indemnification drift:** Liability caps that decreased, indemnification
     scope that expanded, or duty-to-defend language that appeared
   - **IP scope creep:** Broader work-for-hire language, removal of background
     IP carve-outs, expansion of "deliverables" definition
   - **Definition manipulation:** Changes to defined terms in the definitions
     section that alter the meaning of clauses elsewhere without modifying
     those clauses directly
   - **Silent removals:** Protections present in the original that were quietly
     deleted (e.g., cure periods, notice requirements, caps)
   - **Boilerplate weaponization:** Changes to "standard" sections like
     governing law, dispute resolution, or assignment that shift advantage

6. **Calculate the favorability balance.** Tally all changes by which party
   they favor and the severity weight:

   ```
   Party A Score = (Major changes favoring A x 3) + (Moderate x 2) + (Minor x 1)
   Party B Score = same formula for B
   Balance: A-favored / B-favored / Balanced
   ```

7. **Generate the comparison report** with all findings organized by section.

## Output

**Filename:** `CONTRACT-COMPARISON-{YYYY-MM-DD}.md`

```
# Contract Comparison Report
## Documents Compared
| | Version A (Original) | Version B (Revision) |
## Summary of Changes
| Change Type | Count |
## Change Log (by section)
| Section | Change Type | Description | Favors | Severity |
## Dangerous Pattern Alerts
## Favorability Balance
## Silent Removals
## Negotiation Strategy Recommendations
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| Documents are unrelated | Two entirely different contracts provided | Warn the user and ask for confirmation before proceeding |
| Structural mismatch | Different section numbering schemes | Map sections by content, not by number |
| Missing version identifier | User did not specify which is original | Ask which version is the baseline |
| Partial document | One version is incomplete or truncated | Note the gaps; compare only overlapping sections |
| Format mismatch | One is formatted text, other is raw | Normalize both to plain text before comparing |

## Examples

**Example 1 — MSA negotiation round:**

> User: Compare ~/contracts/acme-msa-v1.pdf with ~/contracts/acme-msa-v2.pdf

```
Summary: 14 changes detected across 23 sections.

Key Changes:
1. Section 5.1 (IP Assignment) [MODIFIED] — Severity: MAJOR
   Original: "Work product created under SOW is assigned to Client"
   Revision: "Work product created in connection with the engagement
   is assigned to Client"
   Favors: Client | Signal: Expanding IP scope beyond SOW deliverables

2. Section 8.3 (Liability Cap) [MODIFIED] — Severity: MAJOR
   Original: "Liability capped at 12 months of fees paid"
   Revision: "Liability capped at fees paid in the preceding 3 months"
   Favors: Vendor | Signal: 75% reduction in liability exposure

3. Section 2 (Definitions) [MODIFIED] — Severity: MAJOR
   "Confidential Information" definition expanded to include
   "business strategies and future product plans" — broadens
   confidentiality obligations without touching Section 7.

DANGEROUS PATTERN: Definition manipulation detected.
The revision altered 3 defined terms that collectively change
the meaning of 7 other clauses without modifying those clauses.

Favorability Balance: 9 changes favor Client, 4 favor Vendor, 1 Neutral
Overall Tilt: Client-favored revision
```

**Example 2 — Employment agreement revision:**

> User: My employer sent back a revised offer. Compare the original with this
> new version. [pastes both]

```
SILENT REMOVAL ALERT:
Original Section 4(d) — "Employee may terminate with 2 weeks notice
for any reason" — has been removed entirely. The revision contains
no voluntary termination provision for the employee, while the
employer retains at-will termination rights in Section 4(a).
```

## Resources

- [CommonPaper Contract Comparison Standards](https://commonpaper.com/) —
  Open-source contract templates useful as neutral baselines (CC BY 4.0).
- [American Bar Association — Contract Drafting & Negotiation](https://www.americanbar.org/)
  — Best practices for tracking and evaluating contract revisions.
- [Uniform Commercial Code (UCC) Article 2](https://www.law.cornell.edu/ucc/2)
  — Default rules that apply when contract terms are silent or removed.
- [Restatement (Second) of Contracts, Section 201](https://www.ali.org/) —
  Rules of interpretation when contract language is ambiguous.

---

**Legal Disclaimer:** This skill provides AI-generated contract comparison for
informational and educational purposes only. It does not constitute legal
advice, create an attorney-client relationship, or substitute for consultation
with a qualified attorney. Comparison accuracy depends on the quality of input
documents and may miss changes in formatting, embedded objects, or metadata.
Always consult a licensed attorney before acting on comparison findings.

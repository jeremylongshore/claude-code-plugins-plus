# Freshie Inventory Manager — Usage Examples

Detailed input/output examples for each workflow.

## Table of Contents

- [Quick Status Check](#quick-status-check)
- [Full Audit with Email Report](#full-audit-with-email-report)
- [Ad-Hoc Query with Follow-Up](#ad-hoc-query-with-follow-up)
- [Remediation Cycle](#remediation-cycle)
- [Compare Discovery Runs](#compare-discovery-runs)
- [Pack Coverage Analysis](#pack-coverage-analysis)

## Quick Status Check

```
User: freshie status
Assistant: [Skips menu — clear intent detected]
           [Runs dashboard queries]

FRESHIE INVENTORY DASHBOARD
============================
Last Scan:     Run #4 — 2026-03-23 (14 days ago)
Plugins:       408
Skills:        3123
Packs:         63

Grade Distribution:
  A: 1180  B: 2074  C: 13  D: 9

Staleness: CRITICAL (14 days)
  Recommend running a new discovery scan.

WORKFLOW COMPLETE — Would you like a PDF report emailed?
  - Yes, email me
  - No thanks

User: no thanks
```

## Full Audit with Email Report

```
User: run a full ecosystem audit
Assistant: [Shows menu — user selected "Full Audit"]
           Starting full audit pipeline...

           [Launches 3 parallel subagents:]
           - discovery-scanner: Running rebuild-inventory.py...
           - compliance-validator: Running enterprise validation...
           - anomaly-detector: Checking data quality...

           [All subagents complete]

FRESHIE ECOSYSTEM REPORT — 2026-04-06
================================================================
Discovery: Run #5 (2026-04-06)
  Plugins: 416 (+8) | Skills: 3200 (+77) | Packs: 63

Compliance:
  A: 1250 (39.1%) | B: 2050 (64.1%) | C: 10 (0.3%) | D: 5 (0.2%)
  Average: 87/100

Anomalies: 3 found
  - 5 skills with word count < 50
  - 2 plugins with no skills
  - 1 pack below minimum viable

WORKFLOW COMPLETE — Would you like a PDF report emailed?
  - Yes, email me
  - Yes, email someone
  - Save PDF only
  - No thanks

User: yes email me
Assistant: [Writes /tmp/freshie-report-2026-04-06.md]
           [Converts to PDF via md-to-pdf.py]
           [Invokes /email skill to send]
           Sent "Freshie Ecosystem Report — 2026-04-06" to jeremy@intentsolutions.io
           with freshie-report-2026-04-06.pdf attached.
```

## Ad-Hoc Query with Follow-Up

```
User: show me all D and F grade skills
Assistant: [Routes to Workflow E: Query]
           [Loads common-queries.md, runs Low-Grade Skills query]

| skill_path | score | grade | errors | warnings |
|------------|-------|-------|--------|----------|
| plugins/database/data-validation-engine/... | 62 | D | 3 | 5 |
| plugins/devops/ci-pipeline-builder/...      | 58 | F | 5 | 7 |
| ...                                          |    |   |   |   |

5 skills found with grade D or F.

What next?
  - Refine query
  - Export to CSV
  - Back to menu

User: export to csv
Assistant: [Writes freshie/exports/low-grade-skills.csv]
           Exported 5 rows to freshie/exports/low-grade-skills.csv

WORKFLOW COMPLETE — Would you like a PDF report emailed?
  - Yes, email me
  - No thanks
```

## Remediation Cycle

```
User: remediate skills
Assistant: [Routes to Workflow D: Remediation]
           Running dry-run first...

           [Runs batch-remediate.py --dry-run]

REMEDIATION PREVIEW
================================================================
  12 skills: Add missing 'compatible-with' field
   8 skills: Fix tag formatting
   3 agents: Add missing 'description' field
  23 total changes

Proceed?
  - Execute
  - Cancel

User: Execute
Assistant: [Runs batch-remediate.py --all --execute]
           23 fixes applied.

           Running compliance re-check...
           [Launches compliance-validator subagent]

           Grade improvements:
             C -> B: 5 skills
             D -> C: 2 skills
           Average score: 87.3 -> 88.1 (+0.8)

WORKFLOW COMPLETE — Would you like a PDF report emailed?
```

## Compare Discovery Runs

```
User: compare the last two runs
Assistant: [Routes to Workflow F: Compare Runs]

           Available runs:
             Run #1 — 2026-03-21 | 349 plugins | 1426 skills
             Run #2 — 2026-03-22 | 343 plugins | 1463 skills
             Run #3 — 2026-03-22 | (incomplete)
             Run #4 — 2026-03-23 | 408 plugins | 3123 skills

           Comparing Run #2 -> Run #4:

           Plugins: 343 -> 408 (+65)
           Skills:  1463 -> 3123 (+1660)

           Grade changes:
             A: 520 -> 1180 (+660)
             B: 930 -> 2074 (+1144)
             Upgrades: 45 | Downgrades: 3
```

## Pack Coverage Analysis

```
User: which packs need more skills?
Assistant: [Routes to Workflow I: Pack Coverage]

           Packs below minimum viable (< 3 skills):
           | Pack | Skills | Category |
           |------|--------|----------|
           | acme-pack | 1 | saas-packs |
           | demo-pack | 2 | saas-packs |

           2 packs need attention.
```

---
name: freshie-inventory
description: |
  Manage the freshie ecosystem inventory database — a CMDB tracking all plugins,
  skills, packs, and compliance grades across 50 SQLite tables. Use when checking
  ecosystem health, running discovery scans, validating compliance, remediating
  issues, querying inventory data, comparing runs, exporting data, or generating
  status reports. Trigger with "freshie status", "inventory scan", "ecosystem audit",
  "grade report", "compliance check", "remediate skills", "query freshie",
  "compare runs", "export grades", or "freshie report".
allowed-tools: Read, Write, Edit, Bash(sqlite3:*), Bash(python3:*), Bash(node:*), Bash(mkdir:*), Bash(wc:*), Glob, Grep, AskUserQuestion, Skill, Agent
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [database, inventory, freshie, compliance, ecosystem, sqlite]
---

# Freshie Inventory Manager

Interactive command center for the freshie ecosystem inventory database.

## Current DB Status

!`sqlite3 freshie/inventory.sqlite "SELECT 'Run #' || id || ' — ' || run_date || ' | Plugins: ' || total_plugins || ' | Skills: ' || total_skills || ' | Packs: ' || COALESCE(total_packs, 0) FROM discovery_runs ORDER BY id DESC LIMIT 3;" 2>/dev/null || echo "DB not found at freshie/inventory.sqlite"`

!`sqlite3 freshie/inventory.sqlite "SELECT grade || ': ' || COUNT(*) FROM skill_compliance GROUP BY grade ORDER BY grade;" 2>/dev/null`

## Overview

The freshie database is the single source of truth for ecosystem-wide metrics — plugin counts,
skill compliance grades, pack coverage, anomaly detection, and historical trends across versioned
discovery runs. This skill is an **interactive wizard** — it always asks what you want to do,
then delegates heavy operations to specialized subagents.

**Database location:** `freshie/inventory.sqlite` (50 tables, versioned by `run_id`)

**Key scripts:**
- `freshie/scripts/rebuild-inventory.py` — full repo scan, creates new discovery run
- `freshie/scripts/batch-remediate.py` — auto-fix compliance issues
- `scripts/validate-skills-schema.py` — enterprise validation with DB population

## Prerequisites

- `sqlite3` CLI available on PATH
- `python3` with `pyyaml` installed
- Working directory is the repo root (`claude-code-plugins/`)
- Database exists at `freshie/inventory.sqlite`
- `/email` skill installed (for PDF report emailing)

## Instructions

### Step 1: Present Main Menu

When invoked, ALWAYS start by presenting this menu using AskUserQuestion:

```
FRESHIE INVENTORY COMMAND CENTER
================================================================

What would you like to do?

 1. Dashboard        — Current status, grades, staleness
 2. Discovery Scan   — Full repo scan, create new run
 3. Compliance Check — Enterprise validation + DB population
 4. Remediation      — Batch fix compliance issues
 5. Query            — Ad-hoc SQLite queries
 6. Compare Runs     — Delta analysis between runs
 7. Export Data      — CSV exports to freshie/exports/
 8. Anomaly Scan     — Data quality + outlier detection
 9. Pack Coverage    — SaaS pack completeness metrics
10. Full Audit       — Scan + validate + report (end-to-end)
11. Report Only      — Generate summary from existing data
```

Use AskUserQuestion with these options. If the user's initial prompt already contains
a clear intent (e.g., "freshie status"), skip the menu and route directly.

### Step 2: Execute Chosen Workflow

Based on selection, follow the matching workflow below. Every workflow ends with
Step 3 (Email Report).

---

## Workflow A: Dashboard

Run these queries and present as a formatted dashboard:

```bash
sqlite3 freshie/inventory.sqlite "SELECT id, run_date, total_plugins, total_skills, COALESCE(total_packs,0) FROM discovery_runs ORDER BY id DESC LIMIT 1;"
sqlite3 freshie/inventory.sqlite "SELECT grade, COUNT(*) FROM skill_compliance WHERE run_id=(SELECT MAX(id) FROM discovery_runs) GROUP BY grade ORDER BY grade;"
sqlite3 freshie/inventory.sqlite "SELECT CAST(julianday('now') - julianday(run_date) AS INTEGER) FROM discovery_runs ORDER BY id DESC LIMIT 1;"
sqlite3 freshie/inventory.sqlite "SELECT 'plugins', COUNT(*) FROM plugins WHERE run_id=(SELECT MAX(id) FROM discovery_runs) UNION ALL SELECT 'skills', COUNT(*) FROM skills WHERE run_id=(SELECT MAX(id) FROM discovery_runs) UNION ALL SELECT 'packs', COUNT(*) FROM packs WHERE run_id=(SELECT MAX(id) FROM discovery_runs) UNION ALL SELECT 'anomalies', COUNT(*) FROM anomalies WHERE run_id=(SELECT MAX(id) FROM discovery_runs);"
# Core vs SaaS pack breakdown
sqlite3 freshie/inventory.sqlite "SELECT CASE WHEN path LIKE '%saas-packs%' THEN 'saas-pack-skills' ELSE 'core-skills' END as type, COUNT(*) FROM skills WHERE run_id=(SELECT MAX(id) FROM discovery_runs) GROUP BY type;"
```

Present as:
```
FRESHIE INVENTORY DASHBOARD
============================
Last Scan:     Run #{id} — {date} ({days} days ago)
Plugins:       {n}
Skills:        {n} total
  Core:        {n} (hand-crafted plugin skills)
  SaaS Packs:  {n} (auto-generated pack skills)
Packs:         {n}

Grade Distribution:
  A: {n}  B: {n}  C: {n}  D: {n}  F: {n}

Staleness: {Fresh (<3d) | Stale (3-7d) | CRITICAL (>7d)}
```

If Critical (>7 days), recommend a discovery scan.

---

## Workflow B: Discovery Scan

**Delegate to the discovery-scanner subagent** via the Agent tool:

```
Launch Agent: discovery-scanner
Prompt: "Run a full freshie discovery scan. Show current state first, execute
rebuild-inventory.py, then report the delta (plugin/skill count changes)
compared to the previous run."
```

The subagent handles the long-running scan in isolation and returns the delta report.

---

## Workflow C: Compliance Check

**Delegate to the compliance-validator subagent** via the Agent tool:

```
Launch Agent: compliance-validator
Prompt: "Run enterprise compliance validation against the freshie DB.
Execute: python3 scripts/validate-skills-schema.py --enterprise --populate-db freshie/inventory.sqlite --verbose
Then summarize: grade distribution with percentages, and list all D/F grade skills."
```

The subagent runs the full validation pipeline and returns a structured summary.

---

## Workflow D: Remediation

**CRITICAL: Always dry-run first, then confirm before executing.**

1. Run dry-run:
```bash
python3 freshie/scripts/batch-remediate.py --dry-run
```

2. Present the changes that would be made.

3. Use AskUserQuestion:
```
REMEDIATION PREVIEW
================================================================
{summary of proposed changes}

Proceed?
  - Execute — Apply all fixes
  - Cancel  — Abort, no changes made
```

4. Only if user selects "Execute":
```bash
python3 freshie/scripts/batch-remediate.py --all --execute
```

5. After execution, run Workflow C (Compliance Check) to measure improvement.

---

## Workflow E: Query

For ad-hoc queries, load the pre-built query library from [common-queries.md](references/common-queries.md).

Match the user's question to the closest pre-built query. If no match, construct a custom
query against the freshie schema using these key tables:

| Table | Contents |
|-------|----------|
| `plugins` | name, category, version, path |
| `skills` | name, plugin_path, has_references, has_scripts |
| `packs` | name, skill_count, category |
| `skill_compliance` | score, grade, error_count, warning_count, is_stub |
| `plugin_compliance` | plugin-level roll-up scores |
| `content_signals` | word_count, code_block_count |
| `anomalies` | detected data quality issues |
| `discovery_runs` | run history with timestamps |

Always filter to latest run: `WHERE run_id = (SELECT MAX(id) FROM discovery_runs)`

After showing results, use AskUserQuestion to offer follow-up:
```
Results shown. What next?
  - Refine query  — Modify or drill deeper
  - Export to CSV — Save results to file
  - Back to menu  — Return to main menu
```

---

## Workflow F: Compare Runs

```bash
sqlite3 freshie/inventory.sqlite "SELECT id, run_date, total_plugins, total_skills, COALESCE(total_packs,0) FROM discovery_runs ORDER BY id;"
```

If more than 2 runs exist, use AskUserQuestion to let user pick which two to compare.
Default to the two most recent.

Use the "Historical Trends" queries from [common-queries.md](references/common-queries.md) for:
- Grade distribution comparison between runs
- Skills that changed grade (upgrades/downgrades with score delta)
- New skills added since previous run
- Skills removed since previous run

---

## Workflow G: Export Data

```bash
mkdir -p freshie/exports
```

Use AskUserQuestion to let user pick what to export:
```
EXPORT OPTIONS
================================================================
What should I export?

  - Skill Grades    — All skill compliance scores + grades
  - Plugin Inventory — All plugins with category and version
  - Pack Coverage   — Pack names, skill counts, categories
  - Full Dump       — All three exports
  - Custom Query    — Export any query result to CSV
```

Then run the appropriate export:
```bash
sqlite3 -header -csv freshie/inventory.sqlite "{query}" > freshie/exports/{filename}.csv
```

Report file paths and row counts.

---

## Workflow H: Anomaly Scan

**Delegate to the anomaly-detector subagent** via the Agent tool:

```
Launch Agent: anomaly-detector
Prompt: "Run anomaly detection on the freshie inventory DB. Check:
1. Stored anomalies from the latest discovery run
2. Skills with word count < 50 (likely stubs)
3. Plugins with no skills
4. Skills with high template-text density (>10%)
5. Duplicate files
Report all findings grouped by severity."
```

---

## Workflow I: Pack Coverage

```bash
sqlite3 freshie/inventory.sqlite "SELECT name, skill_count, category FROM packs WHERE run_id=(SELECT MAX(id) FROM discovery_runs) ORDER BY skill_count DESC;"
```

Also flag packs below minimum viable (< 3 skills) and show grade distribution within packs.
Use pack coverage queries from [common-queries.md](references/common-queries.md).

---

## Workflow J: Full Audit

This is the power workflow — runs everything end-to-end:

1. **Discovery Scan** (Workflow B) — via subagent
2. **Compliance Check** (Workflow C) — via subagent
3. **Anomaly Scan** (Workflow H) — via subagent
4. **Report Generation** (Workflow K) — compile all results

Launch steps 1-3 as parallel subagents, then compile the report when all complete.

---

## Workflow K: Report Only

Generate a summary report from existing data (no new scans). Gather dashboard data
(Workflow A queries) and compile:

```
FRESHIE ECOSYSTEM REPORT — {date}
================================================================

Discovery: Run #{id} ({date})
  Plugins: {n} | Skills: {n} | Packs: {n}

Compliance (enterprise tier):
  A: {n} ({pct}%) | B: {n} ({pct}%) | C: {n} ({pct}%) | D: {n} ({pct}%)

  Average score: {avg}/100

Since last run:
  Plugins: {+/-delta} | Skills: {+/-delta}
  Grade upgrades: {n} | Downgrades: {n}

Top Issues:
  1. {issue}
  2. {issue}
  3. {issue}

Recommendations:
  - {action}
  - {action}
================================================================
```

---

### Step 3: Email PDF Report

After ANY workflow completes, use AskUserQuestion to offer the report:

```
WORKFLOW COMPLETE
================================================================
{Brief summary of what was done}

Would you like a PDF report emailed?
  - Yes, email me      — Generate PDF + send to jeremy@intentsolutions.io
  - Yes, email someone — Specify recipient
  - Save PDF only      — Generate PDF, no email
  - No thanks          — Done
```

If the user wants a report:

1. **Generate markdown report** — write the workflow results to `/tmp/freshie-report-{date}.md`
2. **Convert to PDF** using the email skill's converter:
```bash
python3 ~/.claude/skills/email/scripts/md-to-pdf.py /tmp/freshie-report-{date}.md /tmp/freshie-report-{date}.pdf --style professional
```
3. **Send via /email skill** — invoke the Skill tool with `skill: "email"` and args describing:
   - To: recipient (default: jeremy@intentsolutions.io)
   - Subject: "Freshie Ecosystem Report — {date}"
   - Body: brief summary
   - Attachment: the generated PDF

## Output

All operations produce structured text output. Dashboards use fixed-width formatting.
Query results use table format. Deltas show +/- indicators. CSV exports write to
`freshie/exports/`. PDF reports write to `/tmp/` and optionally email.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "DB not found" | Missing `freshie/inventory.sqlite` | Run `python3 freshie/scripts/rebuild-inventory.py` to create |
| "no such table" | DB schema outdated or empty | Run a fresh discovery scan (Workflow B) |
| Empty grades | Compliance not yet populated | Run compliance validation (Workflow C) |
| `rebuild-inventory.py` fails | Missing `pyyaml` | `pip install pyyaml` |
| Stale data (>7 days) | No recent scans | Run discovery scan, then compliance |
| PDF generation fails | Missing `weasyprint` | `pip install weasyprint` |
| Email send fails | Missing env vars | Check `~/.env` for GMAIL_APP_PASSWORD |

## Examples

See [examples.md](references/examples.md) for detailed input/output examples covering all workflows:
- Quick status check (direct intent, skips menu)
- Full audit with email PDF report (parallel subagents)
- Ad-hoc query with CSV export follow-up
- Remediation cycle (dry-run, confirm, re-validate)
- Compare discovery runs (delta analysis)
- Pack coverage analysis

## Resources

- [Common Queries](references/common-queries.md) — pre-built SQLite query library: grades, stubs, plugins, packs, content quality, trends, anomalies, field analysis, cross-references
- `freshie/scripts/rebuild-inventory.py` — full repo scanner, versioned discovery runs
- `freshie/scripts/batch-remediate.py` — compliance fix engine (`--dry-run`, `--all --execute`)
- `scripts/validate-skills-schema.py` — universal validator (`--enterprise --populate-db`)
- `freshie/inventory.sqlite` — the database (50 tables, versioned by `run_id`)
- `~/.claude/skills/email/scripts/md-to-pdf.py` — markdown to PDF converter
- `/email` skill — email sending with attachments
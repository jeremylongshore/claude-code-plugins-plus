---
name: doc-filing
description: |
  Document Filing System v4.3 - Universal document organization with chronological sequencing, category codes, and flat 000-docs structure. Use when organizing loose project documents, cleaning up scattered files, or converting to standardized naming. Trigger with phrases like "organize docs", "file documents", "doc filing", "/doc-filing".
allowed-tools: 'Read,Write,Edit,Glob,Grep,Bash(ls:*),Bash(mkdir:*),Bash(mv:*),Bash(find:*),Bash(cp:*)'
model: sonnet
version: 4.3.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Document Filing System v4.3 (LLM/AI-ASSISTANT FRIENDLY)

**Purpose:** Universal, deterministic naming + filing standard for project docs with canonical cross-repo "000-_" standards series
**Status:** Production Standard (v3-compatible, v4.0-compatible, v4.2-compatible)
**Changelog:** v4.3 migrates from 6767 prefix to 000-_ prefix for canonical standards

## Overview

This skill automatically organizes loose project documents into a flat `000-docs/` directory using:

1. **Chronological Sequencing** - NNN prefixes (001-999)
2. **Category Codes** - 2-letter codes (PP, AT, DR, etc.)
3. **Document Types** - 4-letter codes (PROD, ARCH, STND, etc.)
4. **Kebab-case Descriptions** - 1-4 words lowercase

## Prerequisites

- **File System Access**: Read/write permissions to project directory
- **No Dependencies**: Uses only standard bash commands (ls, mkdir, mv, find, cp)
- **Supported Formats**: .md, .pdf, .doc, .docx, .txt, .xlsx, .xls, .csv, .ppt, .pptx

This skill works in any project directory. No installation or configuration required.

## ONE-SCREEN RULES (MEMORIZE THESE)

1. **Two filename families only:**
   - **Project docs:** `NNN-CC-ABCD-short-description.ext` (001-999)
   - **Canonical standards:** `000-CC-ABCD-short-description.ext`
2. **NNN is chronological** (001-999). **000-\* is reserved for canonical cross-repo standards.**
3. **All codes are mandatory:** `CC` (category) + `ABCD` (type).
4. **Description is short:** 1-4 words (project), 1-5 words (000-\*), **kebab-case**, lowercase.
5. **Subdocs:** either `005a` letter suffix or `006-1` numeric suffix.
6. **000-\* files MUST be identical across all repos using this standard.**

## Instructions

### Phase 1: Setup & Scan

**Step 1: Display Current Location**

```bash
echo "=== DOC-FILING: DOCUMENT ORGANIZATION ==="
echo ""
echo "Current directory: $(pwd)"
echo "Project: $(basename $(pwd))"
echo ""
```

**Step 2: Create Flat 000-docs Directory**

```bash
mkdir -p 000-docs
echo "Created: 000-docs/ (flat structure)"
```

**Step 3: Scan for Loose Documents**

Find all document files in project root and first-level directories.
Exclude: node_modules, .git, dist, build, vendor, 000-docs itself.

```bash
find . -maxdepth 2 -type f \
  \( -iname "*.md" -o -iname "*.pdf" -o -iname "*.doc" -o -iname "*.docx" \
  -o -iname "*.txt" -o -iname "*.xlsx" -o -iname "*.xls" -o -iname "*.csv" \
  -o -iname "*.ppt" -o -iname "*.pptx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.git/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/vendor/*" \
  ! -path "*/000-docs/*" \
  ! -path "*/.next/*" \
  ! -path "*/coverage/*" \
  ! -name "README.md" \
  ! -name "CLAUDE.md" \
  ! -name "LICENSE.md" \
  ! -name "CONTRIBUTING.md" \
  ! -name "CHANGELOG.md" \
  -print | sort
```

### Phase 2: Interactive Categorization

For each document found:

1. **Display** the filename and ask for categorization
2. **Suggest** likely category and document type based on filename
3. **Wait** for confirmation or correction
4. **Rename** according to NNN-CC-ABCD-description.ext format
5. **Move** to 000-docs/

### Phase 3: Renaming & Organization

**Renaming Algorithm:**

1. **Get next sequence number** - Check highest existing NNN in 000-docs/
2. **Determine category code** - Based on content analysis or user input (CC)
3. **Determine document type** - Based on content analysis or user input (ABCD)
4. **Extract description** - Clean filename to 1-4 word kebab-case description
5. **Preserve extension** - Keep original file extension
6. **Generate new name** - Combine as `NNN-CC-ABCD-description.ext`

```bash
# Get next sequence number
NEXT_NUM=$(printf "%03d" $(($(ls 000-docs/ 2>/dev/null | grep -oP '^\d{3}' | sort -n | tail -1) + 1)))

# Generate new name
NEW_NAME="${NEXT_NUM}-${CATEGORY}-${DOC_TYPE}-${DESCRIPTION}.${EXTENSION}"

# Move and rename
mv "$ORIGINAL_FILE" "000-docs/$NEW_NAME"
```

### Phase 4: Generate Inventory

Create 000-docs/000-INDEX.md with:

- Documents grouped by category
- Chronological listing
- Quick reference for codes

### Phase 5: Summary Report

Display counts by category and total documents organized.

## Category Codes (CC) - 2 Letters

| Code | Category                  |
| ---- | ------------------------- |
| PP   | Product & Planning        |
| AT   | Architecture & Technical  |
| DC   | Development & Code        |
| TQ   | Testing & Quality         |
| OD   | Operations & Deployment   |
| LS   | Logs & Status             |
| RA   | Reports & Analysis        |
| MC   | Meetings & Communication  |
| PM   | Project Management        |
| DR   | Documentation & Reference |
| UC   | User & Customer           |
| BL   | Business & Legal          |
| RL   | Research & Learning       |
| AA   | After Action & Review     |
| WA   | Workflows & Automation    |
| DD   | Data & Datasets           |
| MS   | Miscellaneous             |

## Document Types (ABCD) - 4 Letters

### PP - Product & Planning

PROD, PLAN, RMAP, BREQ, FREQ, SOWK, KPIS, OKRS

### AT - Architecture & Technical

ADEC, ARCH, DSGN, APIS, SDKS, INTG, DIAG

### DC - Development & Code

DEVN, CODE, LIBR, MODL, COMP, UTIL

### TQ - Testing & Quality

TEST, CASE, QAPL, BUGR, PERF, SECU, PENT

### OD - Operations & Deployment

OPNS, DEPL, INFR, CONF, ENVR, RELS, CHNG, INCD, POST

### LS - Logs & Status

LOGS, WORK, PROG, STAT, CHKP

### RA - Reports & Analysis

REPT, ANLY, AUDT, REVW, RCAS, DATA, METR, BNCH

### MC - Meetings & Communication

MEET, AGND, ACTN, SUMM, MEMO, PRES, WKSP

### PM - Project Management

TASK, BKLG, SPRT, RETR, STND, RISK, ISSU, STAT

### DR - Documentation & Reference

REFF, GUID, MANL, FAQS, GLOS, SOPS, TMPL, CHKL, STND, INDEX

### UC - User & Customer

USER, ONBD, TRNG, FDBK, SURV, INTV, PERS

### BL - Business & Legal

CNTR, NDAS, LICN, CMPL, POLI, TERM, PRIV

### RL - Research & Learning

RSRC, LERN, EXPR, PROP, WHIT, CSES

### AA - After Action & Review

AACR, LESN, PMRT

### WA - Workflows & Automation

WFLW, N8NS, AUTO, HOOK

### DD - Data & Datasets

DSET, CSVS, SQLS, EXPT

### MS - Miscellaneous

MISC, DRFT, ARCH, OLDV, WIPS, INDX

## 000-\* Canonical Standards (NOT HANDLED BY THIS SKILL)

**What is 000-\* Series?**
The 000-\*-series represents **canonical, cross-repo reusable standards** (SOPs). These are global standards applied across multiple projects.

**000-\* Filename Pattern (v4.2 Rule):**

```
000-*-{a|b|c|...}-[TOPIC-]CC-ABCD-short-description.ext
```

**Fields:**

- `000-*`: fixed canonical prefix (used ONCE)
- `{a|b|c|...}`: **mandatory letter suffix** for chronological ordering
- `[TOPIC-]`: optional uppercase grouping prefix (e.g., INLINE, LAZY, SLKDEV)
- `CC`: 2-letter category code
- `ABCD`: 4-letter document type
- `short-description`: 1-5 words, kebab-case

**Examples:**

- `000-*-a-DR-STND-document-filing-system-standard-v4.md`
- `000-*-b-DR-INDEX-standards-catalog.md`
- `000-*-c-INLINE-DR-STND-inline-source-deployment.md`
- `000-*-DR-STND-...` (WRONG - missing letter suffix)
- `000-*-000-DR-INDEX-...` (WRONG - numeric ID instead of letter)

## Pattern Matching Rules

| Pattern Keywords                               | Category | Type |
| ---------------------------------------------- | -------- | ---- |
| requirement, product, feature, spec            | PP       | PROD |
| plan, roadmap, strategy                        | PP       | PLAN |
| architecture, design, technical                | AT       | ARCH |
| decision, adr, choice                          | AT       | ADEC |
| api, endpoint, integration                     | AT       | APIS |
| code, module, component                        | DC       | CODE |
| test, testing, qa                              | TQ       | TEST |
| bug, issue, defect                             | TQ       | BUGR |
| security, audit, pentest                       | TQ       | SECU |
| deploy, deployment, release                    | OD       | DEPL |
| infrastructure, devops, config                 | OD       | INFR |
| log, journal, daily                            | LS       | LOGS |
| status, progress, update                       | LS       | STAT |
| report, analysis, findings                     | RA       | REPT |
| meeting, notes, minutes                        | MC       | MEET |
| task, backlog, sprint                          | PM       | TASK |
| implementation status, epic tracker, milestone | PM       | STAT |
| guide, manual, handbook                        | DR       | GUID |
| reference, docs, documentation                 | DR       | REFF |
| sop, procedure, process                        | DR       | SOPS |
| standard                                       | DR       | STND |
| template                                       | DR       | TMPL |
| research, study, experiment                    | RL       | RSRC |
| proposal, pitch, whitepaper                    | RL       | PROP |
| postmortem, lessons                            | AA       | PMRT |
| after-action, aar                              | AA       | AACR |
| workflow, automation                           | WA       | WFLW |
| data, dataset, csv, sql                        | DD       | DSET |
| No pattern matches                             | MS       | MISC |

## Safety Features

- Never modifies files in 000-docs/
- Never touches project root files (README, CLAUDE.md, etc.)
- Preserves original file extensions
- Skips system directories (.git, node_modules)
- Generates audit trail (000-INDEX.md)
- Prompts for confirmation on categorization
- Safe to run multiple times

## Examples

**Before:**

```
./project-requirements-draft.md
./docs/api-integration-guide.pdf
./Meeting Notes - Sprint Planning.docx
```

**After (in 000-docs/):**

```
000-docs/001-PP-PROD-project-requirements-draft.md
000-docs/002-AT-APIS-api-integration-guide.pdf
000-docs/003-MC-MEET-sprint-planning.docx
```

## Output

Upon completion, this skill produces:

1. **000-docs/ directory** - Flat folder containing all organized documents
2. **000-INDEX.md** - Comprehensive inventory with:
   - Documents grouped by category
   - Chronological listing
   - Quick reference for category and type codes
3. **Summary report** - Console output showing:
   - Total documents organized
   - Count per category
   - Any skipped files

## Error Handling

| Situation                        | Behavior                                             |
| -------------------------------- | ---------------------------------------------------- |
| No loose documents found         | Reports "0 documents found", creates empty 000-docs/ |
| File already exists in 000-docs/ | Skips file, reports in summary                       |
| Permission denied                | Reports error, continues with remaining files        |
| Invalid filename characters      | Sanitizes to kebab-case automatically                |
| Duplicate sequence number        | Increments to next available NNN                     |
| User cancels categorization      | Skips file, no partial moves                         |

The skill is idempotent - safe to run multiple times without duplicating files.

## Resources

- `{baseDir}/references/000-DR-STND-document-filing-system.md` - Full canonical standard (v4.3)

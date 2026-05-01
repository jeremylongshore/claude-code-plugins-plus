# DOCUMENT FILING SYSTEM STANDARD v4.3 (LLM/AI-ASSISTANT FRIENDLY)
**Purpose:** Universal, deterministic naming + filing standard for project docs with canonical cross-repo "000-*" standards series
**Status:** Production Standard (v3-compatible, v4.0-compatible, v4.2-compatible)
**Last Updated:** 2026-02-05
**Changelog:** v4.3 migrates from 6767 prefix to 000-* prefix for canonical standards
**Applies To:** All projects in `/home/jeremy/000-projects/` and all canonical standards in the 000-* series

---

## 0) ONE-SCREEN RULES (AI SHOULD MEMORIZE THESE)
1) **Two filename families only:**
   - **Project docs:** `NNN-CC-ABCD-short-description.ext` (001-999)
   - **Canonical standards:** `000-CC-ABCD-short-description.ext`
2) **NNN is chronological** (001-999). **000 is reserved for canonical cross-repo standards.**
3) **All codes are mandatory:** `CC` (category) + `ABCD` (type).
4) **Description is short:** 1-4 words (project), 1-5 words (000-*), **kebab-case**, lowercase.
5) **Subdocs:** either `005a` letter suffix or `006-1` numeric suffix.
6) **000-* files MUST be identical across all repos using this standard.**

---

## 1) FILENAME SPEC (DETERMINISTIC)
### 1.1 Project Docs (001-999 series)
**Pattern**

NNN-CC-ABCD-short-description.ext

**Fields**
- `NNN`: 001-999 (zero padded, chronological)
- `CC`: 2-letter category code (table below)
- `ABCD`: 4-letter doc type abbreviation (tables below)
- `short-description`: 1-4 words, kebab-case
- `ext`: `.md` preferred; others allowed (`.pdf`, `.txt`, `.xlsx`, etc.)

**Examples**

001-AT-ADEC-initial-architecture.md
005-PM-TASK-api-endpoints.md
009-AA-AACR-sprint-1-review.md

### 1.2 Sub-Docs (same parent number)
**Option A — letter suffix**

005-PM-TASK-api-endpoints.md
005a-PM-TASK-auth-endpoints.md
005b-PM-TASK-payment-endpoints.md

**Option B — numeric suffix**

006-PM-RISK-security-audit.md
006-1-PM-RISK-encryption-review.md
006-2-PM-RISK-access-controls.md

### 1.3 Canonical Standards (000-* series)
**Purpose:** Cross-repo reusable SOPs, standards, patterns, architectures.

**Pattern**

000-CC-ABCD-short-description.ext

**Fields**
- `000`: fixed prefix for canonical cross-repo standards
- `CC`: 2-letter category code (same as NNN series)
- `ABCD`: 4-letter type code (same master tables)
- `short-description`: 1-5 words, kebab-case

**Key Rule:** 000-* files MUST be identical across all repos. Use drift checking.

**Correct examples**

000-DR-STND-document-filing-system.md
000-TM-STND-secrets-handling.md
000-DR-INDX-standards-catalog.md

**Incorrect (banned)**

000-a-DR-STND-document-filing-system.md   ❌ No letter suffix needed
000-120-DR-INDEX-standards-catalog.md     ❌ No numeric ID after 000

---

## 2) FAST DECISION: WHICH SERIES DO I USE?
Use this rule of thumb:

| If the doc is… | Use… |
|---|---|
| reusable standard/process/pattern across multiple repos | **000-*** |
| specific to one repo/app/phase/sprint/implementation | **NNN (001-999)** |

---

## 3) CANONICAL STORAGE LOCATIONS (DEFAULTS)
- **Project docs:** `<repo>/000-docs/` (flat, no subdirectories)
- **000-* canonical docs:** `<repo>/000-docs/` (same folder as NNN docs)

---

## 3.1) 000-docs Flatness Rule (Strict)

**Purpose:** Keep all documentation in a single flat directory for simplicity and discoverability.

**Rules:**
- `000-docs/` contains all docs (NNN and 000-*) at one level.
- **No subdirectories allowed under `000-docs/`.**
- If assets are needed, store them adjacent to the doc file (same folder) and keep naming clear.

**Folder Structure:**
```
000-docs/
├── 001-PP-PROD-mvp-requirements.md       # NNN project docs
├── 002-AT-ADEC-architecture.md
├── 010-AA-AACR-phase-1-review.md
├── 000-DR-STND-document-filing-system.md # 000-* canonical docs
├── 000-DR-INDX-standards-catalog.md
└── 000-AA-TMPL-after-action-report.md
```

---

## 3.2) Cross-Repo Synchronization

**Source of Truth:** One repo is designated as canonical source (e.g., `irsb-solver`).

**Drift Detection:** All repos should include `scripts/check-canonical-drift.sh`:
```bash
#!/bin/bash
# Check that 000-* files match the canonical source
for file in 000-docs/000-*.md; do
  if [ -f "$file" ]; then
    echo "$(shasum -a 256 "$file" | cut -d' ' -f1) $file"
  fi
done
```

**Rule:** If checksums differ between repos, sync from the source of truth.

---

## 4) CATEGORIES (CC) — 2 LETTERS
| Code | Category |
|---|---|
| PP | Product & Planning |
| AT | Architecture & Technical |
| DC | Development & Code |
| TQ | Testing & Quality |
| OD | Operations & Deployment |
| LS | Logs & Status |
| RA | Reports & Analysis |
| MC | Meetings & Communication |
| PM | Project Management |
| DR | Documentation & Reference |
| UC | User & Customer |
| BL | Business & Legal |
| RL | Research & Learning |
| AA | After Action & Review |
| WA | Workflows & Automation |
| DD | Data & Datasets |
| MS | Miscellaneous |
| PR | Product Requirements |
| TM | Technical Model |
| AD | Architecture Decision |
| OP | Operations |
| RP | Report |
| PL | Plan |

---

## 5) DOCUMENT TYPES (ABCD) — 4 LETTERS (MASTER TABLES)
> Keep this section authoritative. Do not invent new type codes without updating this standard.

### PP — Product & Planning
PROD, PLAN, RMAP, BREQ, FREQ, SOWK, KPIS, OKRS

### AT — Architecture & Technical
ADEC, ARCH, DSGN, APIS, SDKS, INTG, DIAG

### DC — Development & Code
DEVN, CODE, LIBR, MODL, COMP, UTIL

### TQ — Testing & Quality
TEST, CASE, QAPL, BUGR, PERF, SECU, PENT

### OD — Operations & Deployment
OPNS, DEPL, INFR, CONF, ENVR, RELS, CHNG, INCD, POST

### LS — Logs & Status
LOGS, WORK, PROG, STAT, CHKP

### RA — Reports & Analysis
REPT, ANLY, AUDT, REVW, RCAS, DATA, METR, BNCH

### MC — Meetings & Communication
MEET, AGND, ACTN, SUMM, MEMO, PRES, WKSP

### PM — Project Management
TASK, BKLG, SPRT, RETR, STND, RISK, ISSU

### DR — Documentation & Reference
REFF, GUID, MANL, FAQS, GLOS, SOPS, TMPL, CHKL, STND, INDEX, INDX

### UC — User & Customer
USER, ONBD, TRNG, FDBK, SURV, INTV, PERS

### BL — Business & Legal
CNTR, NDAS, LICN, CMPL, POLI, TERM, PRIV

### RL — Research & Learning
RSRC, LERN, EXPR, PROP, WHIT, CSES

### AA — After Action & Review
AACR, LESN, PMRT, REPT

### WA — Workflows & Automation
WFLW, N8NS, AUTO, HOOK

### DD — Data & Datasets
DSET, CSVS, SQLS, EXPT

### MS — Miscellaneous
MISC, DRFT, ARCH, OLDV, WIPS, INDX

### PR — Product Requirements
PRDC

### TM — Technical Model
MODL

### AD — Architecture Decision
ADRD

### OP — Operations
RUNB

### PL — Plan
POLC

---

## 6) NAMING CONSTRAINTS (HARD RULES)
**DO**
- lowercase kebab-case descriptions
- keep descriptions short (avoid sentence titles)
- use `.md` for most docs
- keep `NNN` chronological (001-999)
- keep `000-*` for cross-repo standards only
- ensure `000-*` files are identical across all repos

**DON'T**
- no underscores / camelCase in descriptions
- no special chars except hyphens
- no missing category or type codes
- no additional prefixes or suffixes on 000-* files

---

## 7) EXAMPLES (COPY/PASTE)
### Project docs

000-docs/
001-PP-PROD-mvp-requirements.md
002-AT-ADEC-auth-decision.md
003-AT-ARCH-system-design.md
004-PM-TASK-api-endpoints.md
004a-PM-TASK-auth-endpoints.md
010-AA-AACR-sprint-1-review.md

### Canonical standards

000-docs/
000-DR-STND-document-filing-system.md
000-DR-INDX-standards-catalog.md
000-TM-STND-secrets-handling.md

---

## 8) MIGRATION NOTES (V4.2 → V4.3)
- **Breaking change:** `6767-*` prefix replaced with `000-*`
- **Action required:** Rename all `6767-*` files to `000-*` format
- **Simplification:** No letter suffixes required for 000-* files
- **Cross-repo sync:** All 000-* files must be identical across repos

**Migration command:**
```bash
# In each repo
cd 000-docs
for f in 6767-*.md; do
  new_name=$(echo "$f" | sed 's/^6767-[a-z]-/000-/' | sed 's/^6767-/000-/')
  mv "$f" "$new_name"
done
```

---

## 9) AI ASSISTANT OPERATING INSTRUCTIONS (STRICT)
When creating or renaming a document:
1) Decide series: **000-*** if cross-repo standard; else **NNN (001-999)**.
2) Pick `CC` from Category table.
3) Pick `ABCD` from Type tables (do not invent).
4) Create filename using the exact pattern rules.
5) Keep description short and kebab-case.
6) **Place ALL docs (both NNN and 000-*) directly in `000-docs/`** — no subdirectories.
7) **After every phase, create an AAR:** `NNN-AA-AACR-phase-<n>-short-description.md`
8) **For 000-* files:** Verify content matches canonical source before committing.

---

**DOCUMENT FILING SYSTEM STANDARD v4.3**
*Fully compatible with v3.0, v4.0, v4.2; optimized for AI assistants and deterministic naming.*
*v4.3 migrates from 6767 to 000-* prefix for canonical cross-repo standards.*

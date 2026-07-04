# DOCUMENT FILING SYSTEM STANDARD v4.4 (LLM/AI-ASSISTANT FRIENDLY)

> **Published mirror.** The canonical live copy of this standard is the `/doc-filing` skill
> (`~/.claude/skills/doc-filing/references/000-DR-STND-document-filing-system.md`) — update there
> first, then refresh this snapshot. If the two ever disagree, the skill copy wins.

**Purpose:** Universal, deterministic naming + filing standard for project docs with canonical cross-repo "000-*" standards series
**Status:** Production Standard (v3-compatible, v4.0-compatible, v4.2-compatible, v4.3-compatible)
**Last Updated:** 2026-06-19
**Changelog:** v4.4 adds **disciplined numbered nesting at scale** (flat stays the default; subfolders are coded `NNN-CC-cluster-name/`; `NNN` is one global chronological sequence across the whole tree). **Non-breaking** — flat dirs stay valid. v4.3 migrated the 6767 prefix to 000-* for canonical standards. v4.4 also **drops the never-used byte-identical / shasum cross-repo sync rule** in favor of a single canonical copy (this skill) that other repos mirror by reference, and **defines what a nested folder must be** — a real cluster in one of a fixed set of archetypes (§3.1.2), never a category / doc-type / lifecycle bucket.
**Applies To:** All projects in `/home/jeremy/000-projects/` and all canonical standards in the 000-* series

---

## 0) ONE-SCREEN RULES (AI SHOULD MEMORIZE THESE)
1) **Two filename families only:**
   - **Project docs:** `NNN-CC-ABCD-short-description.ext` (001-999)
   - **Canonical standards:** `000-CC-ABCD-short-description.ext`
2) **NNN is chronological** (001-999), **one global sequence repo-wide** (flat root + every
   subfolder). **000 is reserved for canonical cross-repo standards.**
3) **All codes are mandatory:** `CC` (category) + `ABCD` (type).
4) **Description is short:** 1-4 words (project), 1-5 words (000-*), **kebab-case**, lowercase.
5) **Subdocs:** either `005a` letter suffix or `006-1` numeric suffix.
6) **000-* = canonical cross-repo standards.** Keep **one** authoritative copy (this `/doc-filing`
   skill); other repos mirror/link it — no byte-for-byte sync required.
7) **Flat by default; disciplined numbered nesting at scale (v4.4).** Nest **one level** into
   `NNN-CC-cluster-name/` folders **only** when `000-docs/` exceeds ~50 files **and** a cluster has
   ~8+ related docs. Folders are coded just like files. Canonical `000-*` standards **always stay at
   the flat root**, never nested. A nested folder must be a **real cluster** in one of the defined
   archetypes (§3.1.2).
8) **`NNN` is one global chronological sequence** across the flat root **and** every subfolder —
   never per-folder, never reused. **Next number = recursive scan of the whole tree**
   (`find 000-docs -type f`), not `ls` of one directory.

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

**Key Rule:** 000-* names a canonical cross-repo standard. Keep **one** authoritative copy (this `/doc-filing` skill reference); other repos link to it rather than maintaining byte-identical duplicates.

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
- **Project docs:** `<repo>/000-docs/` — **flat by default; disciplined numbered nesting at scale**
  (one level of `NNN-CC-cluster-name/` folders, see §3.1).
- **000-* canonical docs:** `<repo>/000-docs/` (same folder as NNN docs) — **always at the flat
  root, never inside a subfolder** (keeps canonical standards easy to find).

---

## 3.1) 000-docs Layout Rule: flat by default, disciplined numbered nesting at scale

**Purpose:** Keep documentation discoverable by a single deterministic rule — **the filename is the
index.** Flat is the default because an agent can `ls` one directory and see a repo's whole doc
history (this is what "LLM/AI-assistant friendly" means). At scale, though, a single flat directory
of hundreds of files becomes a wall a human cannot scan, so **v4.4 permits disciplined numbered
nesting**: subfolders coded *exactly like docs*, so folders and files are uniform coded tokens and
the scheme stays machine-parseable.

**Flat-by-default rules:**
- `000-docs/` contains all docs (NNN and 000-*) at one level.
- Stay flat unless **both** scale thresholds below are met.
- Sub-parts of one doc use a `005a` letter suffix or `006-1` numeric suffix — **never a folder**.
- If assets are needed, store them adjacent to the doc file (same folder) and keep naming clear.

**When to nest (BOTH required):**
1. `000-docs/` exceeds **~50 files**, AND
2. a topical cluster has **~8+ related docs** worth grouping.

Below either threshold, stay flat. Nesting is **opt-in at scale**, never mandatory; flat dirs
remain fully valid (v4.4 is non-breaking).

**Nesting rules (v4.4):**
- **One level only** — no folders within folders.
- A folder is named `NNN-CC-cluster-name/` (see §3.1.1).
- Files inside keep the full `NNN-CC-ABCD-desc.ext` — no per-folder restart.
- **`NNN` is one global chronological sequence** across the flat root AND every subfolder: a file's
  number means *when it was filed*, unique repo-wide; the folder is an orthogonal *topical view*.
  This prevents the same number existing in two folders and keeps `find 000-docs | sort` as the one
  true timeline.
- **Canonical `000-*` standards always stay at the flat root**, never nested.
- **`000-INDEX.md` is mandatory** at the flat root and groups entries by folder — it is the nav
  layer once folders exist.

**Flat structure (default — most repos):**
```
000-docs/
├── 001-PP-PROD-mvp-requirements.md       # NNN project docs
├── 002-AT-ADEC-architecture.md
├── 010-AA-AACR-phase-1-review.md
├── 000-DR-STND-document-filing-system.md # 000-* canonical docs (always flat root)
├── 000-DR-INDX-standards-catalog.md
└── 000-AA-TMPL-after-action-report.md
```

**Nested structure (at scale — one level, global NNN):**
```
000-docs/
├── 000-INDEX.md                          # mandatory — groups by folder
├── 000-DR-STND-document-filing-system.md # 000-* always at flat root, never nested
├── 001-PP-PROD-mvp-requirements.md       # ungrouped docs stay at root
├── 047-RA-ANLY-q3-summary.md
├── 012-OD-vps-migration/                 # NNN-CC-cluster-name (012 = when cluster opened)
│   ├── 013-OD-DEPL-cutover-plan.md        #   global NNN continues inside the folder...
│   ├── 028-OD-INCD-rollback-postmortem.md #   ...numbers reflect filing order, not folder order
│   └── 041-OD-CONF-caddy-ingress.md
└── 040-UC-kobiton/                        # second cluster, opened later (040)
    ├── 042-UC-AACR-m2-review.md
    └── 050-UC-FDBK-pilot-notes.md
```
The numbers inside `012-OD-vps-migration/` (013, 028, 041) are deliberately **not** contiguous —
they are the global filing sequence, interleaved with everything else by date. The folder is a
*view*; the number is the *timeline*.

### 3.1.1) Folder naming (`NNN-CC-cluster-name`)
- `NNN` — chronological, from the **same global sequence as files**; marks when the cluster opened.
- `CC` — the 2-letter category (from §4) for the cluster's **dominant** category. Folders are
  category buckets; the 4-letter `ABCD` type lives on the files inside, not on the folder.
- `cluster-name` — kebab-case, **1–3 words**.
- **Examples:** `040-UC-kobiton/`, `055-OD-vps-migration/`, `070-RA-q3-analysis/`.
- **Banned:** uncoded/ad-hoc folders (`docs/`, `misc/`, `archive/`, `01-Docs/`); folders within
  folders; per-folder `NNN` restarts; nesting a `000-*` canonical standard.

### 3.1.2) What a nested folder MUST be — cluster archetypes

A nested folder is a **cluster**: docs bound by **one subject you can name in a single sentence.**
The `cluster-name` is that subject; the `CC` is the category most of its docs share. If you cannot
say *"everything in here is about ___"* in one sentence, it is **not** a cluster — keep those docs
flat.

**A valid cluster is exactly one of these archetypes:**

| Archetype | Bound by | Typical `CC` | Example |
|---|---|---|---|
| **Engagement** | one client / partner | `UC` | `040-UC-kobiton/` |
| **Initiative** | one bounded effort / migration / program | `OD`, `PP` | `055-OD-vps-migration/` |
| **Subsystem** | one component / part of the system | `AT`, `DC` | `060-AT-brain-stack/` |
| **Report series** | one recurring cadence | `RA`, `LS` | `070-RA-quarterly-reviews/` |
| **Research thread** | one line of inquiry | `RL` | `066-RL-eval-standards/` |

**Cohesion rules (all four required):**
1. **One-sentence subject** — a single nameable binding subject.
2. **Category-dominant** — ≥ ~70% of the files share the folder's `CC`; mixed-category grab-bags are
   not clusters.
3. **Earns the threshold** — ~8+ related docs (below that, stay flat).
4. **Named for the subject, not the category** — `kobiton`, `vps-migration`; never `customer`, `ops`.

**A nested folder must NEVER be** (each is a filename/frontmatter concern, not a folder):
- a **category** bucket — `OD/`, `UC/` (the `CC` already lives on the file)
- a **doc-type** bucket — `audits/`, `plans/`, `aars/` (the `ABCD` already lives on the file)
- a **lifecycle** bucket — `archive/`, `wip/`, `draft/`, `done/` (status is a marker on the file, not a folder)
- a **catch-all** — `misc/`, `other/`, `stuff/`

**Lifecycle:** a cluster folder is **permanent** once opened (its `NNN` is a fixed point in the
timeline). When an engagement or initiative ends, the folder **stays** — never move it into an
`archive/`. If a cluster outgrows ~30–40 docs it is usually two subjects — **split by subject** into
two clusters (each a new `NNN`), never by adding a second level.

---

## 3.2) Canonical source of truth (single copy, no byte-sync)

**One authoritative copy.** Each `000-*` standard has a single canonical home — for this filing
standard, the `/doc-filing` skill's reference doc
(`~/.claude/skills/doc-filing/references/000-DR-STND-document-filing-system.md`). Enforcement travels
with the skill, so the skill copy is what actually governs.

**Other repos mirror by reference, not by duplication.** A repo that needs the standard **links to**
the canonical copy (or keeps a clearly-labeled snapshot with a pointer header) — it does **not**
maintain a byte-identical duplicate. There is **no shasum drift-check**, and none is required (the
old byte-identical rule was never used in practice).

**Updating:** change the canonical skill copy first, then refresh any published snapshot (e.g.
`prompts-intent-solutions/000-master-systems/`). If a snapshot ever disagrees, the skill copy wins.

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
- keep **one** authoritative copy of each `000-*` standard (other repos link to it)

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

## 8) MIGRATION NOTES

### v4.2 → v4.3 (6767 → 000-*)
- **Breaking change:** `6767-*` prefix replaced with `000-*`
- **Action required:** Rename all `6767-*` files to `000-*` format
- **Simplification:** No letter suffixes required for 000-* files
- **Canonical copy:** the `/doc-filing` skill reference is the source; other repos link to it (no byte-identical duplication)

**Migration command:**
```bash
# In each repo
cd 000-docs
for f in 6767-*.md; do
  new_name=$(echo "$f" | sed 's/^6767-[a-z]-/000-/' | sed 's/^6767-/000-/')
  mv "$f" "$new_name"
done
```

### v4.3 → v4.4 (disciplined numbered nesting — NON-BREAKING, nothing to migrate)
- **What changed:** `000-docs/` may now use **disciplined numbered nesting at scale** — one level of
  coded `NNN-CC-cluster-name/` folders (§3.1). **Flat stays the default and stays fully valid.**
- **Action required:** **None.** Existing flat `000-docs/` dirs are correct as-is — do **not**
  force-migrate. Nesting is opt-in, applied only when a dir crosses **both** scale thresholds
  (~50 files **and** an ~8+ doc cluster).
- **If you choose to nest a large dir:** **keep `NNN` as the existing global sequence — do not
  renumber files.** `git mv` a topical cluster's files into a `NNN-CC-cluster-name/` folder (the
  folder's `NNN` marks when the cluster opened), keep every `000-*` standard at the flat root, and
  regenerate `000-INDEX.md` grouped by folder. Because no number changes, the global timeline
  (`find 000-docs | sort`) is unchanged.
- **Pilot:** `intent-os` was the pilot for the rule — it adopts v4.4 but stays flat (under
  threshold at ~13 docs).

---

## 9) AI ASSISTANT OPERATING INSTRUCTIONS (STRICT)
When creating or renaming a document:
1) Decide series: **000-*** if cross-repo standard; else **NNN (001-999)**.
2) **Compute the next `NNN` by a recursive scan of the whole tree** (not `ls` of one dir — the
   sequence is global across the flat root and every subfolder, never restarted per folder):
   ```bash
   NEXT_NUM=$(printf "%03d" $(($(find 000-docs -type f -printf '%f\n' 2>/dev/null \
     | grep -oE '^[0-9]{3}' | sort -n | tail -1) + 1)))
   ```
3) Pick `CC` from the Category table.
4) Pick `ABCD` from the Type tables (do not invent).
5) Create the filename using the exact pattern rules; keep the description short and kebab-case.
6) **Placement — flat by default (§3.1):** put NNN and 000-* docs directly in `000-docs/`. **Nest
   only at scale** — one level into a coded `NNN-CC-cluster-name/` folder when `000-docs/` exceeds
   ~50 files **and** a cluster has ~8+ related docs. **Never nest a `000-*` canonical standard**
   (always flat root). No folders within folders; no uncoded folders.
7) **After every phase, create an AAR:** `NNN-AA-AACR-phase-<n>-short-description.md`
8) **Regenerate `000-INDEX.md`** (mandatory at the flat root) — group entries by folder when
   folders exist.
9) **For 000-* files:** Verify content matches canonical source before committing.

---

**DOCUMENT FILING SYSTEM STANDARD v4.4**
*Fully compatible with v3.0, v4.0, v4.2, v4.3; optimized for AI assistants and deterministic naming.*
*v4.4 adds disciplined numbered nesting at scale (flat by default; one global NNN sequence across the whole tree; canonical 000-* always at flat root). Non-breaking — flat dirs stay valid.*

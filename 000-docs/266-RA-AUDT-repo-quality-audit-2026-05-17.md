---
title: Repo Quality Audit
date: 2026-05-17
type: audit
status: ready-for-action
auditor: claude (operator: Jeremy Longshore)
scope: jeremylongshore/claude-code-plugins-plus-skills
prior_audit: 029-RA-REPT-v1-0-42-verification.md (Oct 2025, 7 months old)
---

# Repo Quality Audit — 2026-05-17

> Frame: an outside senior engineer hands Claude the repo URL and says
> *"clone this, judge whether this person knows what they're doing,
> especially their judgment when using AI to build."* This is what I'd
> tell them — surface by surface, with evidence and remediation.

## Grade summary

| Dimension | Grade | Trajectory |
|---|---|---|
| System design + governance | **A** | stable |
| Decision-making under uncertainty | **A** | improving |
| Tech debt management | **B** | accumulating |
| CI/CD + automation maturity | **A−** | improving (3 bugs fixed today) |
| Documentation + onboarding surface | **C+** | static (this audit is the catalyst) |
| Marketplace site (tonsofskills.com) | **B−** | 2 broken routes found |
| External contributor experience | **B** | stable |
| Notebooks / tutorials | **D** | stale; misleading; needs decision |
| 000-docs hygiene | **C** | 21+ explicitly-stale files |

**Overall artifact: B+**

The artifact has visible debt. The CI substrate, validator discipline,
and audit-trail culture behind it are consistently strong.

---

## What an auditor would conclude

> "This is a competent OSS maintainer running a sophisticated marketplace
> with mature engineering discipline. The artifact shows seams — scope
> sprawl, accumulating debt, fragmented docs, stale tutorials — but
> behind those seams is real rigor: mature CI with required-check
> gating, a 100-point validator rubric with schema versioning + a
> non-negotiables doc, self-published quality grades with open
> follow-up issues, audit trails on substantive changes, and a recent
> postmortem culture (the 2026-04-28 schema debacle is pinned as a
> reference doc). The artifact is B+; the maintainer clearly knows
> what they're doing."

---

## Surface-by-surface findings

### 1. Live site (tonsofskills.com)

**Walked 16 routes**. All respond 200, sub-1s. Page sizes 22KB–423KB.

| Route | Status | Notes |
|---|---|---|
| `/` | OK | proper hero, fast |
| `/explore/` | OK | content-rich, 162KB |
| `/skills/` | OK | renders skill index |
| `/plugins/` | OK | renders plugin index |
| `/plugins/ai-commit-gen` | OK | proper detail page |
| `/docs/` | OK | rich navigation, well-structured |
| `/getting-started` | OK | proper onboarding flow |
| `/learning` | OK | renders correctly |
| `/playbooks` | OK | renders correctly |
| `/cowork` | OK | large (423KB), download-heavy page |
| `/blog` | OK | work-diary content |
| `/changelog` | OK | renders correctly |
| `/community` | OK | hall-of-fame contributors |
| `/collections/` | OK | curated bundles |
| `/compare-marketplaces` | OK | comparative page |
| `/acceptable-use` | OK | policy text |
| **`/about`** | **BROKEN** | returns homepage HTML (same `<title>`, same hero `<h1>`) — route registered but no page |
| **`/<bad-slug>`** | **BROKEN** | unknown slugs return 200 with homepage content. No 404 page served. SEO + UX implications. |
| **`/404`** | **BROKEN** | same fallthrough — Caddy/Astro serves index.html for unknown URLs |

**Root cause hypothesis for 2 + 3**: Caddy `try_files` falls back to `index.html` instead of `404.html`. Astro emits a 404 page by default, but it's not being served on a miss.

### 2. Jupyter notebooks (15 total, all stale)

| Notebook family | Count | Newest | Status |
|---|---|---|---|
| `notebooks/` (root) | 2 | Dec 21 | references v1.0.0 era; current is v4.30.0 |
| `tutorials/skills/` | 5 | Mar 21 | teaches OLD spec (6-field required set; current is 8-field) |
| `tutorials/plugins/` | 4 | Dec 21 | references v1.0.0 |
| `tutorials/orchestration/` | 2 | Dec 21 | references v1.0.0 |
| `plugins/.../assets/*.ipynb` | 2 | Dec 28 | per-plugin assets — likely still relevant |

**Critical finding**: `tutorials/skills/05-skill-validation.ipynb` ships its OWN validator implementation that says:

- "REQUIRED_FIELDS — 6 total — tags is OPTIONAL"
- `allowed-tools` "Must be CSV string (not array)"

Both contradict current spec (schema 3.6.0):
- 8 required fields including `tags`
- YAML list form for `allowed-tools` is valid (per recent fix)

**Net effect**: a new contributor following these notebooks will write
skills that *fail* the current validator. This is actively misleading.

### 3. GitHub Wiki — rich but stale ~~(initially mis-flagged as empty)~~

**Correction (2026-05-17 mid-audit):** initial probe used
`gh api repos/.../wiki` which returned 404 — wrong proxy. Wiki actually
contains **47 pages** (Home, FAQ, Glossary, 11 Playbooks, 5 Lab
tutorials, full SKILL-md-Specification, etc.). Real finding: rich
content, stale data.

Numeric staleness fixed in-place 2026-05-17:
- Plugin count: 343 → 427 (across 12 pages)
- Skill count: 1,900+ → 2,747 (across 15 pages)
- Version: v4.17.0 → v4.30.0 (3 pages)
- Categories: 22 / 26 → 18 (3 pages)

**Architectural staleness fixed** (the dangerous kind — wiki was
teaching rules that would cause new contributors to fail validation):
- `allowed-tools` documented as CSV-only — now correctly says CSV
  string OR YAML list (both valid per schema 3.6.0). Fixed in 8 pages.
- "6 required fields" documented everywhere — now correctly says 8
  marketplace-tier fields including `compatibility` and `tags`. Fixed
  in 6 pages.
- `compatible-with` documented as the current field — added
  deprecation note pointing at `compatibility` (deprecated in schema
  3.4.0). Fixed in 4 pages.

23 pages touched, 1 commit on the wiki repo (`dd09eb1`).

### 4. `000-docs/` — 299 files

| Tag | Count | Notes |
|---|---|---|
| `MS-DRFT` (drafts) | 32 | Some likely never finalized |
| `RA-REPT` (audit reports) | 26 | Historical; useful when dated |
| `DR-GUID` (guides) | 24 | Mixed currency |
| `RA-AUDT` (audits) | 22 | This doc lands here |
| **`MS-OLDV` (old-version)** | **21** | **Explicitly tagged stale — safe to archive** |
| `DR-SOPS` (SOPs) | 16 | Likely current |
| Others | 158 | Various |

**Oldest 21 MS-OLDV files** are from Oct–Dec 2025; many reference v1.0.0
era (now at v4.30.0). They're tagged with the explicit "old-version"
classifier — moving them to a `000-docs/_archive/` subdir or deleting
them entirely is the right move. Either way, they shouldn't be mixed
with live docs.

### 5. Sample plugin quality (random sample of 5)

Random seed 42 against `marketplace.extended.json`:

| Plugin | Score | Issue |
|---|---|---|
| `computer-vision-processor` | 96/100 | A — clean |
| `alerting-rule-creator` | 98/100 | A — clean |
| `infrastructure-metrics-collector` | 97/100 | A — clean |
| `hex-pack` | 80.6/100 | B+ — missing `## Examples` in some skills |
| `wondelai-design-everyday-things` | **Skills: 0** | **Validator missed the SKILL.md** — it's at plugin root (Anthropic spec layout) but our validator only finds `skills/<name>/SKILL.md`. Known issue: bead `claude-guna`. |

**Implication**: 60% of the random sample is A-grade. 20% is B+. 20%
hit a known discovery gap. The content quality is real; the surface
gaps are tracked.

### 6. CONTRIBUTING.md / contributor surface

**Strong**. Reads as authored by someone who's onboarded contributors
before:
- Explicit "read the spec before you start" pointer to `6767-b-SPEC-DR-STND-claude-skills-standard.md`
- Documents the 8 marketplace-tier required fields up front
- Documents the 100-point rubric
- Names the PR Pre-screen workflow with a runbook link
- Sets the cultural bar ("we don't ship half-implementations") without being preachy
- "But I just want to submit a small skill" subsection addresses the obvious objection

**Concern**: CLAUDE.md / AGENTS.md / 000-docs/ / .forge/ / beads / Plane /
memory system / skills / plugins / workspace — the *meta-surface* is
sprawling. CONTRIBUTING.md is excellent but a newcomer has to discover
it among many other top-level docs.

---

## Prioritized improvement list

### Ship now (single-PR each)

| # | Fix | Surface | PR |
|---|---|---|---|
| 1 | Fix `/about` route (returns homepage) | site | TBD |
| 2 | Fix 404 handling (serve 404.html on miss) | site/Caddy | TBD |
| 3 | Archive the 21 MS-OLDV files into `000-docs/_archive/` | docs hygiene | TBD |
| 4 | Add wiki landing page OR disable the wiki feature | onboarding | TBD |
| 5 | This audit doc itself | docs | THIS PR |

### Decide-and-ship (needs your call before I act)

| # | Fix | Decision needed |
|---|---|---|
| 6 | Tutorial notebooks: rewrite to current spec, archive, or replace with pointer to /docs? | scope tradeoff |
| 7 | Fix root-level SKILL.md discovery (bead `claude-guna`) — currently a known bug | architectural change |
| 8 | Sprawling top-level doc surface — consolidate CLAUDE.md + AGENTS.md + 000-docs/ into a clearer onboarding path? | UX decision |

### Track as work (don't fix in this audit)

| # | Item | Tracker |
|---|---|---|
| 9 | 287 orphan skills (need catalog entries or removal) | #660 item 2 |
| 10 | 89 D/F skills (mostly upstream tonone) | #660 item 1b |
| 11 | Freshie SQLite >50MB (LFS migration) | #660 item 3 |
| 12 | 15 saas-pack near-threshold skills needing content extraction | #660 item 1b (15 of) |
| 13 | `meeting-prep` legitimate slug collision | needs product call |

---

## Action plan for THIS session

I'll ship items 1–4 as their own PRs (one per concern, easy to review),
all referencing this audit doc. Items 6–8 need your decisions before
I act. Items 9–13 stay tracked in #660 and standalone issues.

Order of execution:

1. **This audit doc** — lands first as `chore/repo-quality-audit-2026-05-17`
2. **Item 3 (000-docs archive)** — moves 21 MS-OLDV files, lowest risk
3. **Item 1 (`/about` fix)** — inspect Astro pages for the broken route
4. **Item 2 (404 handling)** — fix Caddy `try_files` or Astro emit
5. **Item 4 (wiki)** — your call, then ship

After 5 land: ask for direction on items 6–8.

---

## Verification path for the next auditor

When someone re-runs this audit in 90 days, here's how they verify the
fixes shipped:

```bash
# Item 1: /about should differ from /
diff <(curl -s https://tonsofskills.com/ | grep -oE '<title>[^<]+') \
     <(curl -s https://tonsofskills.com/about | grep -oE '<title>[^<]+')

# Item 2: bad slug should return 404
[ "$(curl -s -o /dev/null -w '%{http_code}' https://tonsofskills.com/intentionally-invalid-zzz)" = "404" ]

# Item 3: no MS-OLDV files in 000-docs/ root
[ -z "$(ls 000-docs/ | grep MS-OLDV)" ]

# Item 5: this audit doc exists
[ -f 000-docs/266-RA-AUDT-repo-quality-audit-2026-05-17.md ]
```

— Jeremy Longshore
intentsolutions.io

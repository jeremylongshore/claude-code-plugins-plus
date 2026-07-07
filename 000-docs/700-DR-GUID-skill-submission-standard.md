---
filing_code: DR-GUID-SKILL-SUBMISSION-STANDARD-2026-07-07
date: 2026-07-07
status: active
scope: The tiered submission-documents standard + issue-before-PR intake for every plugin/source submission — external and Intent Solutions' own
related:
  - templates/skill-docs/ (the four fill-in templates + tier matrix)
  - 000-docs/698-TQ-SECU-external-sync-threat-model.md (threat model for synced sources)
  - 000-docs/699-DR-GUID-external-source-vetting-playbook.md (source vetting procedure)
  - STANDARDS.md (8-field marketplace frontmatter rubric)
  - "GitHub issue #984 — marketplace quality pipeline umbrella"
---

# Skill Submission Standard (tiered documents + issue-before-PR)

## Purpose

The marketplace already gates *validity* (validators, security scan, 8-field frontmatter).
This standard gates *value*: every submission arrives with just enough written proof that
the problem is real, the design was deliberate, and the claim matches the tier. The
documents are a filter that helps contributors sharpen a submission — not a wall that
rejects them.

## 1. Issue-before-PR (required)

Every plugin/source submission **starts as a GitHub issue** using the
[plugin-submission template](../.github/ISSUE_TEMPLATE/plugin-submission.yml), which
captures the PRD-level answers (problem, target users, success criteria, top functional
requirements) up front. The PR must link that issue (`Closes #N` / `Refs #N`).

A PR that arrives without a linked submission issue is not rejected — it gets a comment
asking for one, and review pauses until it exists. (Decision: Jeremy, 2026-07-07.)

## 2. Tier → required documents

Templates: [`templates/skill-docs/`](../templates/skill-docs/). Docs live in the plugin
directory as `docs/PRD.md`, `docs/ADR.md`, etc. The same matrix applies to Intent
Solutions' own skills.

| Tier | What it covers | Required docs |
|------|----------------|---------------|
| **Micro-skill** | a single command or skill, no scripts | `PRD.md` (short form OK) |
| **Standard plugin** | skills plus scripts/commands | `PRD.md` + `ADR.md` |
| **Pack / flagship / featured / paid-tier** | multi-skill packs, featured picks, anything sold | `PRD.md` + `ADR.md` + `ONE-PAGER.md` (+ `CFO-ONE-PAGER.md` where money is the pitch) |

## 3. Eligibility: listing vs featuring

- **Listing** (in the catalog): a valid plugin, an honestly declared tier with the
  matching docs, and — for synced sources — the source vetted per the
  [external-source vetting playbook (699)](699-DR-GUID-external-source-vetting-playbook.md).
- **Featuring** (spotlight, homepage, Hall of Fame): A-grade at marketplace tier
  (8-field frontmatter per [STANDARDS.md](../STANDARDS.md)) **plus** the full doc set
  for the pack/flagship tier **plus** an editorial pick. Featuring is earned, and we
  help authors earn it (see the rubric below).

## 4. Sync-model rubric (case-by-case, the curation doctrine)

How an external plugin's quality improvements flow is decided per source, not by one
global policy:

| Situation | Model |
|-----------|-------|
| Responsive maintainer + thin consumer | **Upstream PR** they own and merge; mirror stays SHA-pinned via `sources.lock.json` |
| We're featuring it / our name is on its quality / maintainer slow-or-unknown | **Mirror + `curated: true`** — we harden our copy, frozen from sync, author credited |
| Full adoption (we take over maintenance) | **Vendor** into this repo |

The upstream PR is **always a courtesy, never a blocker** — a stalled or silent upstream
never delays listing or featuring. Curated copies join a periodic reconcile that pulls
upstream **security fixes** into the frozen copy so hardening never means falling behind
on safety.

## 5. Canonical sources (cited, not restated)

- [698 — external-sync threat model](698-TQ-SECU-external-sync-threat-model.md): what the
  machine layers can and cannot prove about synced content.
- [699 — external-source vetting playbook](699-DR-GUID-external-source-vetting-playbook.md):
  the human procedure for listing, reviewing, and suspending sources.
- [STANDARDS.md](../STANDARDS.md): the 8-field marketplace frontmatter rubric and where
  the machine-readable source of truth lives.

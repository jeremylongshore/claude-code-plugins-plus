<!-- doc-class: record -->

# Decision Record — Migrate the flagship repo to the `intent-solutions-io` org

**Doc:** 707-AT-DECR · **Status:** PROPOSED — staged, gated, **not executed**.
**Owner:** Jeremy Longshore (Lead). **Recommended gate before execution:** an
ISEDC council review (`/exec-decision-council`).

> This record documents the deliberate *next step* after the MVP maintainer
> ladder proves out on the personal repo. It is the "org rules for the team"
> answer — and those rules **only exist in an org**. Nothing here is executed by
> the PR that introduces this file; execution is a separate, gated action.

---

## 1. Context

The maintainer ladder shipped in this initiative
([`GOVERNANCE.md`](../GOVERNANCE.md), [`MAINTAINERS.md`](../MAINTAINERS.md),
per-area [`CODEOWNERS`](../.github/CODEOWNERS), the `commit-scope-check` and
`codeowners-drift` gates) is an MVP built on the **personal** repo
`jeremylongshore/claude-code-plugins-plus-skills`. It works today, but it hits a
hard platform ceiling:

**A personal repo cannot express team-based ownership.** Concretely, on a personal
repo:

- `CODEOWNERS` can only name **individual usernames** who are collaborators with
  write access — **no team handles** (`@intent-solutions-io/ci-infra`).
- There is **no auto review-assignment** (GitHub's team round-robin / load-balance
  assignment is org-only).
- There are **no org rulesets** — branch protection is per-repo and can't be
  centrally governed or shared across repos.
- Onboarding the **60-dev cohort** means adding 60 individual collaborators and
  hand-editing CODEOWNERS for each — which does not scale.

Everything in the MVP was deliberately written to **convert cleanly** to the org
model: area names in GOVERNANCE = commit scopes in `.commit-rules.json` = the
per-area sections of CODEOWNERS, all of which map 1:1 to future GitHub Teams.

## 2. Decision (proposed)

Transfer `claude-code-plugins-plus-skills` from the personal account to the
**`intent-solutions-io` GitHub organization**, and convert the convention ladder
into platform-enforced org primitives:

1. **Areas → GitHub Teams.** Create one team per area:
   `@intent-solutions-io/{ci-infra, validator-schema, marketplace-site,
   external-sync, docs-governance, freshie, deps}` (plus per-category
   `plugins-*` teams as needed). Team membership becomes the source of truth for
   who holds which rung — `MAINTAINERS.md` documents it; the teams enforce it.
2. **Team-based CODEOWNERS.** Replace each `@jeremylongshore` (and the commented
   post-quiz `@opeyemiariyo-netizen` lines) with the matching team handle. The
   per-area structure already in CODEOWNERS makes this a mechanical find/replace.
3. **Code-review auto-assignment.** Enable team review-assignment
   (load-balance / round-robin) so incoming PRs auto-route to the area team's
   Reviewers — automating the 72h-SLA first-response duty across the cohort.
4. **Org rulesets.** Move branch protection to an org ruleset so the
   `ci-required` + `gitleaks` + code-owner-review gate is centrally governed and
   reusable across Intent Solutions repos.
5. **Cohort onboarding on-ramp.** Add cohort devs to the relevant `plugins-*`
   teams as **Reviewers** first (the lightweight "outside contributor → Reviewer"
   on-ramp), promoting to Approver per the GOVERNANCE two-sponsor model.

## 3. The load-bearing risk — canonical URL / redirects

**This is the reason the transfer is gated, not routine.** The public install slug
`jeremylongshore/claude-code-plugins` is marked in `CLAUDE.md` as a **breaking API
surface**: it is hardcoded in the CLI, the Hero snippet, and hundreds of READMEs.
The canonical GitHub repo is `jeremylongshore/claude-code-plugins-plus-skills`,
which the legacy slug 301-redirects to.

A GitHub org transfer **does** install an automatic redirect from the old
owner/repo path to the new one, so existing `git remote` URLs and clone links keep
working. **But** redirects are best-effort and break if a repo of the same name is
later created at the old path, and any tooling that pins the *owner* string
(not just follows the redirect) can break. Before executing:

- Inventory every place the owner/slug is hardcoded (CLI, Hero, marketplace config,
  install docs, `sources.yaml` self-references, DoltHub/Plane cross-links).
- Decide the post-transfer canonical string and update the high-traffic surfaces
  in lockstep with the transfer.
- Do **not** recreate anything at the vacated personal path.
- Verify `tonsofskills.com` deploy (VPS force-command + rsync) still resolves the
  repo after transfer.

## 4. Consequences

**Positive:** team-based ownership, auto review-assignment, org rulesets, and a
scalable cohort on-ramp — the platform now enforces what is currently convention.
Bus-factor and merge-bottleneck risk drop structurally.

**Negative / cost:** a one-time migration with real redirect risk on a
breaking-surface slug; org-admin setup (teams, rulesets, membership); and the need
to re-verify every automation that authenticates to or references the repo
(GitHub Actions secrets, Plane sync, DoltHub push, deploy force-command).

**Neutral:** the MVP ladder keeps working unchanged until the transfer; this is
additive sequencing, not a rewrite.

## 5. Execution gate (do NOT skip)

Because this touches an immutable-ish public surface (the install slug) and
cross-repo governance, **run an ISEDC council review (`/exec-decision-council`)
before executing** — the seats to steel-man: CTO (redirect/tooling durability),
CMO/VP-DevRel (the public slug is brand + developer surface), GC (org ownership /
IP), CISO (secrets re-auth across automation). Capture the verdict as an AT-DECR
addendum to this file.

Recommended trigger: execute **after** the MVP ladder has proven out (the seeded
reviewer promoted to Approver via the quiz; at least one non-Lead area Approver
operating; the commit-scope + codeowners-drift gates green in steady state).

## 6. Status

**PROPOSED.** Green-light, ISEDC review, and the redirect-inventory checklist are
prerequisites to execution. This file is the durable record; execution will append
a dated addendum with the ISEDC verdict and the migration runbook results.

---

*Related: [`GOVERNANCE.md`](../GOVERNANCE.md) · [`MAINTAINERS.md`](../MAINTAINERS.md) · [`.github/CODEOWNERS`](../.github/CODEOWNERS) · [teaching doc](704-DR-GUID-teaching-cicd-and-maintainers.md) · `/exec-decision-council`*

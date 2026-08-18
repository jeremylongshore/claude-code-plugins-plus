<!-- doc-class: record -->

# Pipeline Quiz — Answer Key

**Doc:** 706-DR-GUID · **For:** the Lead grading the
[pipeline quiz](705-DR-GUID-pipeline-quiz.md). Grounded in the
[teaching doc](704-DR-GUID-teaching-cicd-and-maintainers.md) and the live repo as
of this initiative.

> Grade for understanding, not exact wording. A candidate who can _explain_ the
> "why" behind each gate to a client has passed; one who recites job names without
> the reasoning has not. **Must-get:** Q1, Q6, Q11, Q18.

---

## Section A — Gate architecture

**A1.** **Three:** `ci-required`, `gitleaks`, and `skill-conform` (plus one
approving code-owner review, which is a review requirement, not a status check).

`skill-conform` (added 2026-07-23) runs `audit-harness conform --strict` over the
whole marketplace corpus from its **own** workflow, `skill-conform.yml`.

**The follow-up is the real test.** `skill-conform` is deliberately NOT in
`ci-required`'s `needs:` list. Per `000-docs/110` § 5, a skippable or path-scoped
job must never be able to green the aggregate — inside `needs:` a `skipped`
result counts as a pass (see A2), so folding it in would let a skipped
conformance run silently satisfy the gate. It therefore always-reports as its own
required context.

Naming all three contexts is the must-get; explaining why the third stands alone
is what separates a Reviewer answer from an Approver answer.

**A2.** `ci-required` is the final aggregate job in `validate-plugins.yml`
(`if: always()`, `needs:` all the real gate jobs). It reads the `needs` results
and **fails if any needed job ended `failure` or `cancelled`**; a `skipped` result
counts as pass. It exists so there is exactly one required context that always
reports.

**A3.** `validate-plugins.yml` runs on **every** `pull_request` with **no path
filter**. If it were path-filtered, a README-only PR wouldn't trigger the
required jobs, they'd sit "Expected" forever, and the PR could never merge — the
**"N Expected forever" stuck-PR class (PR #778 / #964)**. Running unconditionally
guarantees the gate always reports.

**A4.** Legitimate **only** when the job skipped via a _designed_ job-level `if:`
(a conditional gate that correctly did not apply — e.g. `check-submission-docs`
passing cleanly when no new plugin was added). Dangerous when a job skips for an
**undesigned** reason: `skipped` counts as pass, so a real gate would be silently
bypassed by a green aggregate.

**A5.** Add the check as a **job inside `validate-plugins.yml`** and add its name
to `ci-required`'s `needs:`. **Anti-pattern:** creating a separate, path-filtered
workflow and adding _its_ context to the branch-protection required set — that
recreates the stuck-PR class.

## Section B — Advisory vs. blocking

**A6.** **Yes, it can merge.** The deterministic gate is `ci-required` +
`gitleaks` + `skill-conform` + code-owner approval. Greptile is advisory — read it and address real findings,
but an AI reviewer's opinion is never the thing that blocks or merges code.
(Full credit requires the principle: deterministic CI is the gate, AI review is
advice.)

**A7.** Any three of: **MiniMax three-lane reviewer** (in-repo AI, advisory by
design); **Greptile** (repo-controlled AI reviewer, advisory); **PR pre-screen**
(posts a `prescreen-grade` commit status, never a required context);
**kernel-shadow / kernel-vendor-hash** (`continue-on-error` soak lanes);
**CodeQL** (scoped security scan). Each is advisory because it is **not in the
required-status set** and cannot fail the merge gate.

**A8.** **`kernel-shadow-validation`** runs the kernel's `skill-frontmatter`
schema over the SKILL.md corpus and logs per-file agreement/deviation vs. the
prose-spec validator. **`kernel-vendor-hash`** enforces the version-coupling
invariant **V ≤ C ≤ K** (vendored ≤ CCPI-declared ≤ kernel-latest) plus a
staleness bound. Not promoted because the authority flip requires a strict,
documented bar (≥99.5% agreement, ≥30-day soak, governance sign-off, etc.) that
has not been met — and the open disagreements are real tool-safety cases the
prose validator correctly blocks.

**A9.** A **REFUSE finding is never waivable** by anyone (pipe-to-shell, reverse
shell, secret exfil, crypto-miner) — it fails the job, full stop. A **CHALLENGE
finding** (dual-use: hooks, remote MCP URL, dynamic exec) fails the job **unless**
a reviewer adds a `path:rule reason` waiver to `scripts/scan-allowlist.txt` in the
same PR after confirming the source is vetted.

## Section C — Catalog & build

**A10.** `marketplace.extended.json` (source of truth, **you edit this**) and
`marketplace.json` (CLI-compatible, **auto-generated, never edit**).
`pnpm run sync-marketplace` regenerates the CLI catalog (plus plugin
`package.json`s and the README TOC).

**A11.** CI's catalog-sync check **fails** because the generated file is out of
sync with (or hand-diverged from) the extended source. They should have edited
`marketplace.extended.json` and run `pnpm run sync-marketplace`. (`marketplace.json`
is a derived artifact; the pre-commit hook normally regenerates it.)

**A12.** `sync-marketplace` **strips `maintainer`** (and other extended-only keys
like `components`/`verification`) from the generated CLI `marketplace.json`,
because the sanitizer drops any plugin-entry key not in the kernel/CLI contract.
That's exactly what we want: the extended catalog carries ownership metadata the
CLI spec doesn't know about, and the CLI catalog stays spec-clean. (The
`maintainer` field feeds `generate-codeowners.mjs`, not the CLI.)

**A13.** Historical/tooling reasons make `marketplace/` an `npm` workspace while
the rest of the repo uses `pnpm`; mixing them silently breaks workspace
resolution. **`check-package-manager`** enforces it.

## Section D — The validator

**A14.** `name`, `description`, `allowed-tools`, `version`, `author`, `license`,
`compatibility`, `tags`. At **marketplace tier a missing field is an ERROR**, not
a warning. (This 8-field `ALWAYS_REQUIRED` set is a documented NON-NEGOTIABLE.)

**A15.** Anthropic's spec is intentionally **permissive** (it must accept the
whole ecosystem); our marketplace is a **curated storefront** held to a higher
bar, so the IS rubric adds required fields and strict errors on top. The
**2026-04-28 debacle** was "realigning" the strict marketplace tier _down_ to
Anthropic's permissive floor — which broke the quality gate. Don't do it.

**A16.** Agents are **kernel-strict, not tier-gated**: every agent must carry the
kernel-floor 8 (`name, description, tools, model, color, version, author, tags`)
plus the enterprise live set, all as **errors**, and banned fields
(`capabilities`, `type`, `category`, `compatible-with`, etc.) are errors. Skills
use tiered grading with `allowed-tools` (allowlist). Validate agents with
**`--agents-only`**.

**A17.** The A-grade coach **runs the same `validate-skills-schema.py`** on changed
skills and tells the author exactly how to reach A-grade. That off-loads "how do I
pass the schema?" from the Lead — contributors self-serve against the real
validator instead of asking a human.

## Section E — Sync model & the ladder

**A18.** A **Reviewer**'s ✅ is the quality `/lgtm` signal but does **not** satisfy
`require_code_owner_reviews`. An **Approver** is listed in `CODEOWNERS` for their
area, so **their approving review satisfies the code-owner merge gate** and they
can merge PRs in that area. (Must-get: the code-owner-gate distinction.)

**A19.** Because we **squash-merge**, the PR title becomes the single commit
subject on `main` — so the title is the artifact that must be a valid Conventional
Commit; individual WIP commit messages are discarded in the squash. The
`allowedScopes` in `.github/.commit-rules.json` **are the maintainer areas** from
GOVERNANCE (`ci-infra`, `marketplace-site`, …), so the commit scope self-documents
which area a change touches.

**A20.** A **personal repo's** CODEOWNERS can only name individual usernames who
are collaborators — no team handles, no org rulesets, no auto review-assignment.
The single unlock is **transferring the repo to the `intent-solutions-io` org**,
which enables GitHub Teams, team-based CODEOWNERS
(`@intent-solutions-io/<area>`), and code-review-assignment — the way to onboard
the 60-dev cohort without hand-managing 60 collaborators. (See the
[org-migration record](707-AT-DECR-org-migration-to-intent-solutions-io.md).)

## Bonus

**B1 (model answer).** "Four layers. (1) Every mirrored plugin's changed files go
through `scan-synced-content`, a supply-chain scanner — a REFUSE pattern
(pipe-to-shell, reverse shell, secret exfil) fails the build and can't be waived.
(2) `gitleaks` blocks any secret. (3) We mirror by default and **a human reviews
every external-sync PR** — about 1 in 10 merges. (4) High-trust paths (CI,
validators, deps) are owned by the Lead in CODEOWNERS, so a workflow that could
bypass the validators can't merge without owner approval. Deterministic gates do
the catching; humans do the judgment."

---

_Related: [pipeline quiz](705-DR-GUID-pipeline-quiz.md) · [teaching doc](704-DR-GUID-teaching-cicd-and-maintainers.md)_

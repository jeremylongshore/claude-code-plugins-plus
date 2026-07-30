# Pipeline Quiz — Tons of Skills CI/CD & Maintainer System

**Doc:** 705-DR-GUID · **Purpose:** competency gate for the Reviewer → Approver
promotion on `ci-infra` and `marketplace-site`. Answer key:
[`706-DR-GUID-pipeline-quiz-answer-key.md`](706-DR-GUID-pipeline-quiz-answer-key.md).

> **How this is used.** Read the [teaching doc](704-DR-GUID-teaching-cicd-and-maintainers.md)
> first. Then answer these ~20 questions in your own words — the point is that you
> can *explain* the pipeline to a client, not recite it. The Lead reviews your
> answers against the key. Passing is the gate to become an **Approver** (your
> review satisfies the code-owner merge gate) on CI/infra and the marketplace
> site. These are the exact things a client will probe.

Score guide: **≥ 17/20 to pass.** Q1, Q6, Q11, and Q18 are must-get "structural
gate" questions — missing any one is an automatic re-take regardless of total.

---

## Section A — Gate architecture

**Q1.** Exactly how many status checks are required by branch protection on
`main`, and what are they? (Name them.) Then: one of them is deliberately NOT in
`ci-required`'s `needs:` list — which one, and why would putting it there break
the gate?

**Q2.** What is `ci-required`, and mechanically how does it decide whether to pass
or fail?

**Q3.** A PR touches only `README.md`. Explain why `validate-plugins.yml` still
runs every one of its jobs, and what disaster this prevents. Name the PR-number
class it fixed.

**Q4.** Inside `ci-required`'s `needs:`, one job shows `skipped`. Under what single
condition is that legitimate, and when would a `skipped` job be a dangerous
silent bypass?

**Q5.** You want to make a brand-new check block merges. Describe the correct way
to wire it in, and the specific anti-pattern you must avoid.

## Section B — Advisory vs. blocking

**Q6.** Greptile requests changes on a PR, but `ci-required`, `gitleaks` and
`skill-conform` are green and a code owner approved. Can the PR merge? Explain the principle.

**Q7.** Name three advisory lanes that run on PRs and state, for each, why it is
advisory and not blocking.

**Q8.** What are the two kernel soak lanes, what does each check, and why have they
**not** been promoted to blocking?

**Q9.** The `scan-synced-content` job reports a REFUSE finding on a mirrored
plugin. Can a reviewer waive it? What about a CHALLENGE finding? Explain the
difference.

## Section C — Catalog & build

**Q10.** Name the two catalog files, which one you edit, and what regenerates the
other.

**Q11.** A contributor hand-edited `.claude-plugin/marketplace.json` and opened a
PR. What happens, and what should they have done instead?

**Q12.** The new `maintainer` field lives in the extended catalog. Explain what
happens to it when `sync-marketplace` runs, and why that behavior is exactly what
we want.

**Q13.** Why is `marketplace/` on `npm` while the rest of the repo is on `pnpm`,
and which job enforces it?

## Section D — The validator

**Q14.** List the 8 required SKILL.md frontmatter fields at marketplace tier. What
happens if one is missing — warning or error?

**Q15.** Why does the Intent Solutions rubric sit *on top of* Anthropic's spec
rather than matching it? What was the 2026-04-28 debacle?

**Q16.** How do agent validation requirements differ from skill requirements, and
what flag validates agents?

**Q17.** How does the MiniMax A-grade coach relate to the validator, and how does
that reduce load on the Lead?

## Section E — Sync model & the ladder

**Q18.** In the maintainer ladder, what is the difference between a **Reviewer**
and an **Approver** in terms of the code-owner merge gate?

**Q19.** We squash-merge, and `commit-scope-check` lints the PR **title**. Explain
why the title (not the individual commits) is the thing that must be valid, and
how the allowed scopes relate to the maintainer areas.

**Q20.** Why can't the current CODEOWNERS use team handles, and what is the single
structural change that unlocks GitHub Teams, team-based CODEOWNERS, and
auto-review-assignment for the 60-dev cohort?

---

## Bonus (not scored, but a real client question)

**B1.** A prospective enterprise customer asks: "How do you stop a malicious
contributor from sneaking a payload into one of your 470 plugins?" Give the
2-minute answer, naming the specific gates involved.

---

*Related: [teaching doc](704-DR-GUID-teaching-cicd-and-maintainers.md) · [answer key](706-DR-GUID-pipeline-quiz-answer-key.md) · [`GOVERNANCE.md`](../GOVERNANCE.md)*

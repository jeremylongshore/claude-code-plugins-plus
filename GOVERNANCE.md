# Governance — Tons of Skills

How this project is maintained, who can approve what, and how contributors earn
more responsibility over time. This is the operating manual for the **maintainer
ladder**; the live roster of people is in [`MAINTAINERS.md`](MAINTAINERS.md).

> **Status:** MVP on the personal repo `jeremylongshore/claude-code-plugins-plus-skills`.
> The ladder below is a _convention_ today (enforced by CODEOWNERS + branch
> protection + human trust). It is designed to convert cleanly to real **GitHub
> Teams** and org rulesets once the repo transfers to the `intent-solutions-io`
> org — see [`000-docs/707-AT-DECR-org-migration-to-intent-solutions-io.md`](000-docs/707-AT-DECR-org-migration-to-intent-solutions-io.md).

---

## Why a ladder (and why earned-trust)

The repo has 360+ forks and a growing contributor cohort, and it is the flagship
of a marketplace that holds ~470 plugins to an A-grade bar. One person approving
every merge is a structural bottleneck and a bus-factor risk. But an open-slather
"anyone can merge" model would sink the quality bar that is the whole product.

The answer used by every large, quality-sensitive OSS project is an **earned-trust
ladder**: responsibility is granted incrementally, scoped to an area you have
demonstrated competence in, and vouched for by people already trusted. We drew the
model directly from four proven systems:

- **CloudWeGo / eino** — a sponsorship ladder (Member → Committer → Reviewer →
  Approver → Maintainer) where existing maintainers vouch for the next rung. This
  is the "word-of-mouth" vetting we want.
- **Kubernetes / Prow** — two-phase review (`/lgtm` from a reviewer + `/approve`
  from an area approver) driven by per-directory `OWNERS`. Reviewing and approving
  are _different rights_.
- **Home Assistant** — per-integration `codeowners`, auto-generated from metadata,
  so ownership scales to thousands of components without hand-editing one giant
  file. This is our [per-plugin ownership](#scaling-per-plugin-ownership) answer.
- **GitHub-native** — `require_code_owner_reviews` so an area owner's approval is a
  hard, structural merge gate, not just a social norm.

---

## The tiers

Every tier is **scoped to one or more areas** (see [Areas](#areas)). You can be a
Maintainer of `marketplace-site` and only a Contributor everywhere else. Rights are
per-area, never repo-wide (except the Lead).

| Tier            | What they can do                                                                                                                                                                                                                                                      | How review counts                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Contributor** | Open issues and PRs. Anyone. No write access.                                                                                                                                                                                                                         | Their PRs are reviewed by others.                                                                     |
| **Reviewer**    | Everything a Contributor can, plus: authoritative first-pass review on PRs **in their area** — the "does this meet the bar" read. A Reviewer's ✅ is the `/lgtm` signal. Triages incoming PRs in their area against the [72h first-response SLA](.github/SUPPORT.md). | Review is advisory to the Approver; a Reviewer does **not** yet satisfy `require_code_owner_reviews`. |
| **Approver**    | Everything a Reviewer can, plus: their approval **satisfies the code-owner review gate** for their area (listed in [`.github/CODEOWNERS`](.github/CODEOWNERS)), so they can merge PRs in that area. Owns the health of their area.                                    | Approving review = merge-eligible once CI is green.                                                   |
| **Maintainer**  | Everything an Approver can, plus: sets direction for their area — the bar, the roadmap, what gets accepted — and can sponsor others up the ladder.                                                                                                                    | Sets policy for the area.                                                                             |
| **Lead**        | Jeremy Longshore. Owns the whole repo, the high-trust paths (validators, schema, CI, root policy, deps), releases, and final say on cross-area decisions and org-level moves.                                                                                         | Owns everything not delegated.                                                                        |

**Two-phase review, K8s-style.** A merge needs both: (1) a **Reviewer**'s
quality read (`/lgtm`), and (2) an **Approver**'s code-owner approval. On a small
bench these can be the same person; as the bench grows, splitting them is how we
keep review load off any single approver. The deterministic CI gate
(`ci-required` + `gitleaks`) is always required on top — human approval never
substitutes for green checks.

---

## Areas

Areas are the unit of scope. They double as the **commit-scope registry**
(`.github/.commit-rules.json`) and the ownership map (`.github/CODEOWNERS`), so the
three stay in sync — a new area is one PR touching all three.

| Area                 | Covers                                                                             | Trust level                                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `ci-infra`           | `.github/workflows/**`, gate architecture, release automation, `deploy-vps.yml`    | **High** — a workflow edit can bypass every validator. Lead + vetted Approvers only.                                    |
| `validator-schema`   | `scripts/validate-*.py`, kernel schema consumption, `000-docs/SCHEMA_CHANGELOG.md` | **High** — this is the quality bar itself. Lead-owned; changes are approval-gated per SCHEMA_CHANGELOG NON-NEGOTIABLES. |
| `marketplace-site`   | `marketplace/**` (Astro site, design system, build pipeline)                       | Standard.                                                                                                               |
| `external-sync`      | `sources.yaml`, `scripts/sync-external.mjs`, the mirror-by-default pipeline        | Standard, but supply-chain-sensitive — see CONTRIBUTING § external sync.                                                |
| `docs-governance`    | `000-docs/**`, `GOVERNANCE.md`, `MAINTAINERS.md`, contributor-facing standards     | Standard.                                                                                                               |
| `freshie`            | `freshie/**` — the inventory CMDB, Dolt sync, grading                              | Standard.                                                                                                               |
| `deps`               | `package.json`, lockfiles, `pnpm-workspace.yaml`                                   | **High** — one bad upgrade is a supply-chain incident. Lead-owned.                                                      |
| `plugins-<category>` | `plugins/<category>/**` for each of the 19 categories                              | Standard. Delegable per-category, and per-plugin (below).                                                               |

---

## Vetting — how you move up

**Today (invite-only).** The bench is small, so promotions are **invited directly
by the Lead**. If you have shipped good work in an area and want more
responsibility, say so — but the current gate is Jeremy's judgment, not a vote.

**The graduation bar (as the bench grows).** We adopt the CloudWeGo/K8s
**two-sponsor, word-of-mouth model** once there are enough trusted people to make
it real:

1. **Contributor → Reviewer:** a sustained track record of quality PRs/reviews in
   an area, **sponsored by one existing Approver/Maintainer** of that area.
2. **Reviewer → Approver:** demonstrated judgment (their `/lgtm`s hold up),
   **sponsored by two Maintainers** (or the Lead + one Maintainer), and — for the
   high-trust areas — passing the relevant competency gate. For `ci-infra` /
   `marketplace-site`, that gate is the **[pipeline quiz](000-docs/705-DR-GUID-pipeline-quiz.md)**:
   you must be able to explain how the CI/CD and validator pipeline works before
   you can approve changes to it.
3. **Approver → Maintainer:** ownership-level contribution over time, ratified by
   the Lead.

Sponsorship means a trusted maintainer puts their name on you in the promotion PR
(a one-line entry change in `MAINTAINERS.md`). Trust is transferable and traceable.

**Off-ramp.** Inactivity for a long stretch moves you to _emeritus_ in
`MAINTAINERS.md` (recognition kept, active rights paused). No drama; you can come
back.

---

## Delegation — what leaves the Lead's plate

The point of the ladder is to move standing load off one person. These duties are
delegated as the roster fills:

- **PR triage & first response.** The **Reviewer** for an area owns first response
  on new PRs in that area within the **72-hour SLA** ([`.github/SUPPORT.md`](.github/SUPPORT.md)) —
  label, ask for the submission issue if missing, run the pre-flight, and either
  `/lgtm` or request changes. This is the single biggest load transfer.
- **PR approval & merge.** Handled structurally by [`.github/CODEOWNERS`](.github/CODEOWNERS):
  GitHub auto-requests the area owner, and an area **Approver**'s review satisfies
  the merge gate. Merges no longer funnel through the Lead.
- **External-sync review.** The weekly `sync-external` auto-PR (Mondays 06:00 UTC)
  is reviewed by the **`external-sync` Approver**. ~1 in 10 sync PRs merges;
  mirror-by-default means most are no-ops. REFUSE findings from the supply-chain
  scanner are never waivable by anyone.
- **Skill of the Week.** Editorial pick, rotated (below).
- **Schema teaching.** Contributors self-serve instead of asking the Lead: the
  [teaching doc](000-docs/704-DR-GUID-teaching-cicd-and-maintainers.md), the
  in-repo MiniMax A-grade coach (advisory PR lane), and the
  [submission standard](000-docs/700-DR-GUID-skill-submission-standard.md) answer
  "how do I get to A-grade" without a human in the loop.

### Skill of the Week rotation

The pick stays **editorial** — a human chooses a genuinely killer skill; there is
no auto-picker. What rotates is **who picks**, so it comes off the Lead's plate.
The rotation roster lives in `MAINTAINERS.md`. The picker for the week runs
`node scripts/promote-spotlight.mjs path/to/new-spotlight.json` (bookkeeping is
automated; only the judgment is human) and `node scripts/render-spotlight.mjs` to
sync the README block. Source of truth: `marketplace/src/data/spotlights.json`.

---

## Scaling: per-plugin ownership

Enumerating owners for ~470 plugins by hand in `CODEOWNERS` does not scale. Home
Assistant solved this with per-component metadata + a generator, and we do the
same:

- A plugin entry in `.claude-plugin/marketplace.extended.json` may carry an
  optional **`maintainer`** field (a GitHub handle, or a list of handles) — the
  person who ships or stewards that plugin.
- `scripts/generate-codeowners.mjs` reads that metadata and appends per-plugin
  `plugins/<category>/<name>/ @handle` lines to `.github/CODEOWNERS`, between
  managed markers. A CI drift-check (`--check`) fails if `CODEOWNERS` is stale, the
  same regenerate-and-diff pattern as `sync-marketplace`.

So a contributor who owns a plugin **auto-owns its reviews** the moment their
`maintainer` field merges — no hand-editing the ownership file. Population is
incremental: the field is optional and defaults to the area owner.

---

## The rules that keep it honest

- **CI is never bypassed by trust.** `ci-required` + `gitleaks` are the two
  required contexts; a human approval unlocks merge only _after_ they are green.
  The maintainer ladder controls _who may approve_, not _whether checks run_.
- **High-trust areas stay Lead-owned** until an Approver has passed the competency
  gate for that area. Being trusted in `plugins-design` does not grant `ci-infra`.
- **Scope is per-area, and areas are explicit.** If it is not written in
  `MAINTAINERS.md` + `CODEOWNERS`, the right does not exist.
- **The three registries move together:** `GOVERNANCE.md` (this file, areas) →
  `.github/.commit-rules.json` (scopes) → `.github/CODEOWNERS` (owners). Adding an
  area is one PR touching all three.

---

## Changing this document

Governance changes are `docs-governance` and Lead-owned. Propose via PR; the Lead
ratifies. Once the repo is in the org, this file governs the mapping from tiers to
GitHub Teams, and team membership becomes the source of truth for who is on each
rung.

---

_Related: [`MAINTAINERS.md`](MAINTAINERS.md) · [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) · [`.github/SUPPORT.md`](.github/SUPPORT.md) · [org-migration decision record](000-docs/707-AT-DECR-org-migration-to-intent-solutions-io.md)_

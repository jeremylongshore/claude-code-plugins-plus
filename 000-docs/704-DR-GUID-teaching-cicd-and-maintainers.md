<!-- doc-class: record -->

# How the CI/CD, Validator, and Maintainer System Works — Tons of Skills

**Doc:** 704-DR-GUID · **Audience:** maintainers and reviewers being onboarded · **Status:** teaching
reference · **Repo:** `jeremylongshore/claude-code-plugins-plus-skills` (live at
[tonsofskills.com](https://tonsofskills.com))

> **Why this doc exists.** If a client sat across from you and asked "walk me
> through how quality is enforced on your flagship marketplace," you should be
> able to answer without hedging. This is that walkthrough — the real pipeline,
> named jobs, and the reasons behind the design choices. Pair it with the
> [pipeline quiz](705-DR-GUID-pipeline-quiz.md); passing the quiz is the gate for
> the Reviewer → Approver promotion on `ci-infra` and `marketplace-site`.

---

## 1. The one thing to remember: exactly three required checks

Branch protection on `main` requires **exactly three** status contexts:

1. **`ci-required`** — an aggregate job that gates through every real CI job.
2. **`gitleaks`** — the secret scanner (from `secret-scan.yml`).
3. **`skill-conform`** — `audit-harness conform --strict` over the whole
   marketplace corpus, in its **own** workflow (`skill-conform.yml`).

> **Why `skill-conform` is separate and NOT inside `ci-required`'s `needs:`.**
> Per `000-docs/110` § 5, a job that can be skipped or is path-scoped must never
> be allowed to green the aggregate — if it were a `needs:` entry, a skip would
> read as a pass. It therefore always-reports as its own required context. This
> is the single most-missed detail on this page; if you can explain it, you
> understand the whole gate design.

Plus one approving code-owner review. That is the whole merge gate. Everything
else you'll see on a PR (AI review, pre-screen grades, kernel soak lanes) is
**advisory** — it reports, it does not block.

**Why so few, and why an aggregate?** We used to require ~10 separate
contexts, and several came from **path-filtered** workflows. A PR that didn't
touch those paths left the checks in "Expected" forever — they never ran, so the
PR could never merge. That was the "N Expected forever" stuck-PR class (observed
on PRs #778 and #964). The fix: one workflow (`validate-plugins.yml`) that runs on
**every** PR with no path filter, ending in a single aggregate job (`ci-required`)
that `needs:` all the real gate jobs. Now there is always exactly one thing to
wait on, and it always reports.

**The rules that keep it fixed (do not regress):**

- `validate-plugins.yml` runs on every `pull_request` — never add a `paths:`
  filter to it.
- To make a new check blocking, add it as a **job inside** `validate-plugins.yml`
  and list it in `ci-required`'s `needs:`. Never add a path-filtered workflow's
  context to the required-status set.
- A job in the aggregate's `needs:` may only skip via a **designed** `if:`. An
  undesigned skip counts as PASS and would silently bypass a real gate.

---

## 2. The 19-job aggregate — what each gate blocks

`ci-required` fails if **any** job it `needs:` ends in `failure` or `cancelled`
(a `skipped` result counts as pass — legitimate only for a designed conditional).
The gated jobs, and what each one protects:

| Job | What it blocks a PR for |
| --- | --- |
| `validate` | Malformed `plugin.json`, broken catalog format, plugin-structure errors. |
| `verify` | The full `pnpm run verify` pipeline (build + core checks). |
| `test` | Package unit tests (CLI, MCP plugins). |
| `check-package-manager` | Wrong package manager — `pnpm` everywhere except `marketplace/` which is `npm`. |
| `marketplace-validation` | The Astro site fails to build or routes don't resolve. |
| `cli-smoke-tests` | The `@intentsolutions/*` CLI regressed. |
| `shellcheck-skills` | Shell errors in skill/command scripts. |
| `skill-codeblock-syntax` | Broken fenced code blocks in SKILL.md files. |
| `typescript-coverage-audit` | TS coverage regressions. |
| `eslint-check` / `format-check` | JS/TS lint + formatting. |
| `ruff-check` / `ruff-format-check` | Python lint + formatting. |
| `markdownlint` | Markdown rule violations (also guards synced-plugin lint exclusions). |
| `scan-synced-content` | **Supply-chain scanner** over changed `plugins/**` — REFUSE (pipe-to-shell, reverse shell, secret exfil) is never waivable; CHALLENGE (dual-use) needs an allowlist waiver. |
| `promote-curated-check` | The `skills/.curated/` mirror drifted from its plugin sources. |
| `check-submission-docs` | A new plugin arrived without its tier's submission docs (PRD/ADR/ONE-PAGER). |
| `commit-scope-check` | The PR title isn't a valid Conventional Commit / uses an unregistered area scope. |
| `codeowners-drift` | A plugin's `maintainer` field changed but `CODEOWNERS` wasn't regenerated. |

The last two (`commit-scope-check`, `codeowners-drift`) are the maintainer-ladder
gates added in this initiative — see §7.

---

## 3. Advisory lanes — report, never block

These run on PRs and give signal, but are **not** in the required set and cannot
stop a merge. Knowing which is which is the single most common client question.

- **MiniMax three-lane reviewer** — an in-repo advisory AI reviewer: a
  defect+mirror lane, an adversarial-claims lane (refutes grade/count/mirror
  claims), and a **validator-grounded A-grade coach** that runs the real
  `validate-skills-schema.py` on changed skills and tells the author how to reach
  A-grade. Advisory.
- **Greptile** — the single repo-controlled AI reviewer (config in `.greptile/`).
  Gemini Code Assist is disabled; CodeRabbit is retired. Read its comments like
  any review, but the deterministic gate is always `ci-required` + `gitleaks`.
- **PR pre-screen** (`pr-prescreen.yml`) — grades changed plugins with the pinned
  validator and posts an advisory `prescreen-grade` commit status (plus one marker
  comment only when changes are needed). Never a required context.
- **Kernel soak lanes** — `kernel-shadow-validation` (runs the kernel's
  `skill-frontmatter` schema over the corpus and logs agreement/deviation vs. the
  prose-spec validator) and `kernel-vendor-hash` (enforces the version-coupling
  invariant V ≤ C ≤ K). Both `continue-on-error`, both advisory. They are a
  30-day-plus soak toward a *future* cutover — the validator authority has **not**
  flipped and won't until a strict, documented bar is met.
- **CodeQL** — security scanning, PR-scoped to `packages/**` + `marketplace/src/**`
  so it adds no fan-out to plugin PRs.

**The client-facing line:** deterministic CI is the gate; AI review is advice. We
never let a bot's opinion be the thing that merges code.

---

## 4. The two-catalog system

There are two marketplace catalog files, and confusing them is the classic
mistake:

| File | Role | Edit it? |
| --- | --- | --- |
| `.claude-plugin/marketplace.extended.json` | **Source of truth** — rich metadata. | **Yes.** |
| `.claude-plugin/marketplace.json` | CLI-compatible, **auto-generated**, sanitized. | **Never.** |

`pnpm run sync-marketplace` regenerates the CLI catalog, any missing plugin
`package.json`s, and the README auto-TOC. The generator **strips** any
extended-only key (e.g. `components`, `verification`, and the new `maintainer`
field) from the CLI catalog — so extended can carry ownership/inventory metadata
the CLI spec doesn't know about. A pre-commit hook runs `sync-marketplace` when
the extended catalog is staged; CI fails if any derived file is out of sync.

Downstream of the catalog, `marketplace/` builds the Astro site (7 steps:
discover-skills → extract-readme → sync-catalog → enrich-jrig → unified-search →
cowork-zips → astro build), and the VPS deploy rsyncs `marketplace/dist/` to the
served root with `--delete` (atomic — orphan files are pruned). Cowork zips are
rebuilt from the catalog on every build; never commit `marketplace/public/downloads/`.

---

## 5. The validator — the quality bar itself

`scripts/validate-skills-schema.py` is the authoritative grader. Two tiers:

- **Standard tier** — permissive, aligned to Anthropic's floor.
- **Marketplace tier** — intentionally strict. A missing required field is an
  **ERROR**, not a warning.

**The 8 required SKILL.md frontmatter fields** (marketplace tier):
`name`, `description`, `allowed-tools`, `version`, `author`, `license`,
`compatibility`, `tags`. This 8-field set (`ALWAYS_REQUIRED`) is a
NON-NEGOTIABLE — it is not reduced, and marketplace errors are not demoted to
warnings, without approval (see `000-docs/SCHEMA_CHANGELOG.md`).

**Agents are kernel-strict** (not tier-gated): every agent must carry the
kernel-floor 8 (`name, description, tools, model, color, version, author, tags`)
plus the enterprise live set, all as errors. Banned fields (`capabilities`,
`expertise_level`, `type`, `category`, `compatible-with`, `when_to_use`) are
errors. Validate with `--agents-only`.

**A-grade** is the marketplace bar: least-privilege tools, a Trigger-bearing
description, real tags, and the required body sections. The MiniMax A-grade coach
(advisory) runs this same validator and coaches authors toward A-grade, so
contributors self-serve instead of asking the Lead "how do I pass?"

**Why the IS rubric sits on top of Anthropic's spec:** Anthropic's spec is
permissive by design (it must accept the whole ecosystem). Our marketplace is a
curated storefront held to a higher bar. "Realigning" our strict tier down to
Anthropic's floor was the 2026-04-28 debacle — don't.

---

## 6. External-sync — mirror by default

~470 plugins, but only ~63 are externally synced (57 third-party + 6 of Jeremy's
own). The other ~87% is in-repo Intent Solutions work. External is a **respected
minority augment**, not the center of gravity.

- `sources.yaml` registers each external source; `sync-external.yml` runs weekly
  (Mondays 06:00 UTC) and mirrors each source into `plugins/`, opening one
  automated PR. A human reviews every one — historically **~1 in 10 merges**.
- **Mirror by default:** the upstream repo governs; we don't locally edit a pure
  mirror. Improvements are **upstreamed respectfully** — a friendly issue first,
  then a PR the contributor owns and merges. Once merged upstream, the mirror is
  A-grade naturally.
- **`curated: true`** freezes a source: the sync writes no files, so even a
  `--force` run can't revert local hardening. This exists because a past `--force`
  reverted ~100 A-graded agents to 3-field stubs.
- `curated:` (we hardened it) and `verified:` (a maintainer vetted trust/quality)
  are orthogonal flags — kept separate on purpose.

---

## 7. The maintainer ladder (and how the org changes it)

**Today (personal repo).** Ownership is enforced by `.github/CODEOWNERS` +
branch protection. The ladder is a convention: **Contributor → Reviewer →
Approver → Maintainer**, each scoped to an **area** (`ci-infra`,
`validator-schema`, `marketplace-site`, `external-sync`, `docs-governance`,
`freshie`, `deps`, `plugins-<category>`). An Approver's review satisfies the
code-owner merge gate for their area. Full rules: [`GOVERNANCE.md`](../GOVERNANCE.md);
roster: [`MAINTAINERS.md`](../MAINTAINERS.md).

Two ladder mechanisms are wired into CI in this initiative:

- **`commit-scope-check`** — since we squash-merge, the PR **title** is the commit
  that lands on `main`. This job lints it as a Conventional Commit against
  `.github/.commit-rules.json`, whose `allowedScopes` **are** the maintainer
  areas. The husky hook enforces this locally per commit; the CI job closes the
  gap when a web-UI commit or `--no-verify` skips the hook.
- **Per-plugin ownership (Home-Assistant style)** — an optional `maintainer` field
  on a plugin's extended-catalog entry, plus `scripts/generate-codeowners.mjs`,
  which appends `plugins/<cat>/<name>/ @owner` lines to CODEOWNERS. This is how
  470 plugins + a growing cohort scale without hand-editing the ownership file.
  `codeowners-drift` fails the PR if the block is stale.

**The org constraint (the "what changes" answer).** On a **personal** repo,
CODEOWNERS can only name individual usernames who are collaborators — **no team
handles, no auto review-assignment, no org rulesets**. That is why every
CODEOWNERS line is written to convert cleanly to a team handle
(`@intent-solutions-io/ci-infra`) once the repo moves to the org. The staged plan
for that transfer — convention ladder → real GitHub Teams, team-based CODEOWNERS,
and code-review-assignment to onboard the cohort — is the decision record
[`707-AT-DECR-org-migration-to-intent-solutions-io.md`](707-AT-DECR-org-migration-to-intent-solutions-io.md).

---

## 8. The 60-second version (for a client)

> "Every PR runs one aggregate CI gate, a secret scan, and a corpus-wide skill
> conformance check — three required checks, by design, so nothing gets stuck and
> nothing merges half-checked. Inside the aggregate are 19 jobs: build, tests, a strict marketplace validator that holds
> every skill to an 8-field A-grade bar, a supply-chain scanner over any mirrored
> code, and ownership/commit-convention gates. On top of that, advisory lanes —
> an AI reviewer and a validator-grounded coach — give signal without ever being
> the thing that merges code. Ownership runs on an earned-trust maintainer ladder
> scoped by area, and it's built to graduate straight into GitHub Teams when we
> move the repo into the org."

---

*Related: [`GOVERNANCE.md`](../GOVERNANCE.md) · [`MAINTAINERS.md`](../MAINTAINERS.md) · [pipeline quiz](705-DR-GUID-pipeline-quiz.md) · [`SCHEMA_CHANGELOG.md`](SCHEMA_CHANGELOG.md) · [submission standard](700-DR-GUID-skill-submission-standard.md) · [org migration](707-AT-DECR-org-migration-to-intent-solutions-io.md)*

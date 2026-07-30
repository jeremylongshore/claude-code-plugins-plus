# Reviewing external PRs — the maintainer's playbook

**Audience:** whoever is on external-PR duty. Written for Ope as the first reader.
**Companion to:** `704-DR-GUID-teaching-cicd-and-maintainers.md` (how CI works),
`700-DR-GUID-skill-submission-standard.md` (what a submission must contain).
**Status:** written 2026-07-29 against the live queue of 7 open external PRs.

---

## 0. Why this doc exists

`704` teaches you the pipeline. It does **not** teach you the judgement call, and
that is the part that actually takes time. An external PR is not a code review —
it is a **trust decision about somebody else's code that we are about to put our
name on**, in a repo with 2,000+ stars where our catalog is the product.

The pipeline tells you whether a PR is *safe*. It cannot tell you whether it is
*wanted*. That second question is the maintainer's job, and there is no gate for
it.

One number to keep you calibrated: **roughly 1 in 10 external-sync PRs merges.**
Closing a PR is a normal, healthy outcome, not a failure of the process. If you
find yourself trying to get everything to green, you have misunderstood the job.

---

## 1. First move: classify. Everything else follows from this.

Do not start reading the diff. Look at *which files changed* and pick the lane.

```bash
gh pr view <N> --repo jeremylongshore/claude-code-plugins-plus-skills \
  --json files --jq '[.files[].path] | join("\n")'
```

| If the diff contains… | Lane | What it means |
| --- | --- | --- |
| only `sources.yaml` | **A — mirror registration** | They want us to *sync* their repo. We host a mirror; they keep ownership. |
| a new `.claude-plugin/plugin.json` | **B — new plugin submission** | Code lands *in our tree* and we own it thereafter. |
| `marketplace.json` (not `.extended.`) | **C — reject on sight** | Auto-generated file. See §6. |
| anything under `.github/workflows/` | **D — escalate to Jeremy** | A workflow change from an external contributor can disable the gates that are reviewing it. Never merge this yourself. |

The live queue splits almost perfectly along A/B, which is why these two lanes
are worth learning properly:

```
Lane A (sources.yaml only)   #1083  #1103  #1144      1 file, ~20-40 lines
Lane B (new plugin dir)      #1070  #1101  #1125  #1131   8-31 files, 300-1800 lines
```

---

## 2. Lane A — mirror registration (`sources.yaml`)

**The gate will fail, and that is by design. Do not "fix" it.**

`scan-synced-content` scans `plugins/**`. A `sources.yaml`-only PR changes zero
files under `plugins/`, so the scanner has nothing to scan and deliberately
fails with a **waivable CHALLENGE** called `sources-change-unscanned`. The
failure exists to force a human to look at the source before we start pulling
code from it automatically.

Your job is the thing the gate cannot do:

1. **Open their repo and read it.** Is it real? Does it have a license? Is the
   author identifiable? Would you be comfortable telling a client we distribute
   this?
2. **Confirm it is pinned** in `sources.lock.json`. An unpinned source means the
   next sync can pull anything they push later — including something they did not
   write.
3. **Only then** clear the CHALLENGE by adding a line to
   `scripts/scan-allowlist.txt`:

   ```
   sources.yaml:sources-change-unscanned  <why this source is vetted>
   ```

   The reason field is **required** and it is not a formality — a malformed line
   with no reason is silently *ignored*, not honoured, so a lazy waiver fails
   closed. Write a real sentence.

**Never waivable:** a **REFUSE** finding. REFUSE means pipe-to-shell, reverse
shell, or secret exfiltration. That is fixed at the source or the PR is closed.
There is no allowlist entry that makes a REFUSE mergeable, and if you find
yourself looking for one, stop and escalate.

### `mirror:` vs `curated:` — get this right or you will destroy work

Default is a **pure mirror**: their repo governs, we do not locally edit. If we
harden a plugin past its upstream, the source gets `curated: true` in
`sources.yaml`, which **freezes** it — `sync-external.mjs` writes no files for it
at all.

This flag exists because of a real incident: a `--force` sync once reverted ~100
A-graded agents back to 3-field upstream stubs — an **18,900-line deletion**. The
freeze is the scar tissue. Never remove `curated: true` to "get the sync working."

`curated:` and `verified:` are **orthogonal**. All three currently-curated sources
are `curated: true, verified: false` — we hardened them, but nobody has vetted
their trustworthiness. That combination is honest, and it is exactly why the two
flags are separate fields.

---

## 3. Lane B — new plugin submission

Three gates fire, and each one is asking a different question.

**`check-submission-docs`** — did they bring the paperwork? Tiers per
`templates/skill-docs/README.md`:

| Tier | Required |
| --- | --- |
| Micro-skill (one command/skill, no scripts) | `docs/PRD.md` |
| Standard plugin (skills + scripts) | `+ docs/ADR.md` |
| Pack / flagship / featured / paid | `+ docs/ONE-PAGER.md` |

`CFO-ONE-PAGER.md` stays review-enforced rather than gated, because "money is the
pitch" is not something a script can judge. External **mirror** plugins are
exempt — their docs live upstream.

**The validator at marketplace tier** — all 8 frontmatter fields, as **errors**,
not warnings: `name, description, allowed-tools, version, author, license,
compatibility, tags`.

**`skill-conform`** — `audit-harness conform --strict` across the whole corpus.

### The judgement call the gates cannot make

A submission can be 100% green and still be a **close**. Ask:

- **Does it duplicate something we already ship?** We have ~470 plugins. Overlap
  fragments the catalog and makes search worse for everyone.
- **Is the description trigger-bearing?** A skill nobody's Claude will invoke is
  dead weight in the index.
- **Is this a real capability or a wrapper around one API call?**
- **Would I defend this in front of a client?** That is the actual bar.

Green CI means "this will not hurt us." It does not mean "we want this."

---

## 4. Reading a failing check without guessing

```bash
gh pr checks <N> --repo jeremylongshore/claude-code-plugins-plus-skills
gh run view <RUN_ID> --repo jeremylongshore/claude-code-plugins-plus-skills --log-failed
```

**Two traps that have each cost real time:**

**An empty check list does not mean "passed" — it means CI never ran.** A PR
merged on an empty list broke `main` for every open PR in July 2026. If you see no
checks, that is a red flag, not a green light.

**`ci-required` absent from the list means the 19 gate jobs are still running.**
It is the final aggregate job, so it only reports once its `needs:` resolve. Wait
for it; do not conclude anything from its absence.

Fork PRs additionally show `action_required` until an owner approves the workflow
run, and `auto-bump-on-pr.yml` skips forks by design (it needs a write token,
which must never be handed to fork code). Neither is a defect.

---

## 5. The AI reviewers are not a gate — and right now they are not even running

As of 2026-07-29:

- **Kilo Code Review** — failing on **every** PR: *"could not run — your account
  is out of credits."* That is billing, not a finding.
- **Gemini Code Assist** — the consumer product is **sunset**. The bot posts only
  a sunset notice. `.gemini/config.yaml` is retained-but-inert.
- **Greptile** — active through the GitHub App, advisory, quota-limited (~50/mo).

**Never block a merge waiting for an AI review, and never treat one as approval.**
The gate is `ci-required` + `gitleaks` + `skill-conform` + a code-owner review.
Read Greptile when it shows up; address real findings; move on.

---

## 6. Hard "no" list — refuse these without debate

| Situation | Why |
| --- | --- |
| Hand-edited `marketplace.json` | Auto-generated from `marketplace.extended.json`. Ask them to edit the extended file and run `pnpm run sync-marketplace`. |
| Any local edit to a `curated: true` mirror | Freeze exists to prevent an 18,900-line revert. |
| A REFUSE finding from `scan-synced-content` | Not waivable. Fix at source or close. |
| A workflow change from an external contributor | Can disable the gates reviewing it. Escalate to Jeremy. |
| Raising a gate baseline to get green | Both ratcheting gates are built to move one way. `check-internal-doc-links.mjs` refuses outright; `lint-design-tokens.mjs` ratchets **down** only via `--update-baseline` and can never be raised silently — raising it means editing the committed baseline file in a reviewable diff. Lowering is progress; raising is how 749 CodeQL alerts and 500 link errors accumulated behind green checks. |
| Plaintext secret "just for testing" | `gitleaks` blocks it, and it belongs in `tests/fixtures/` as a stub. |

---

## 7. Upstreaming — how we raise quality without taking ownership

When a mirrored plugin is below our bar, the move is **not** to fix it locally.
Local fixes get reverted by the next sync and quietly take ownership of somebody
else's code.

The flow, in order:

1. A friendly **issue** first: *"we featured your plugin and hardened its
   frontmatter to our A-grade bar — would you be open to a PR upstreaming that?"*
2. A PR **they** own and merge.
3. Once merged upstream, the mirror is A-grade naturally and `curated:` can be
   dropped.

`hyperflow` is the worked example: hardening merged upstream, flag dropped in
#1008.

> **Hard rule: any contributor-facing wording — issue body, PR body, review
> comment — gets Jeremy's sign-off BEFORE it is posted.** These are public,
> permanent, and written in the company's voice. No exceptions, including when
> you are certain the wording is fine.

---

## 8. Closing a PR well

Closing is the common outcome. Do it in a way that keeps the contributor willing
to come back:

- Lead with what you **did** look at, so it reads as considered rather than
  dismissed.
- Give the **actual** reason — overlap with an existing plugin, scope, docs tier
  — not a gate name they cannot interpret.
- If it could become mergeable, say exactly what would change your answer.
- Thank them. They spent unpaid hours on our catalog.
- Sign it (this footer is **not** automatic on issues and comments, unlike
  commits and PR descriptions):

  ```
  - Jeremy Longshore
  intentsolutions.io
  ```

---

## 9. Two-week ramp

| Stage | Do this | Ownership |
| --- | --- | --- |
| 1 | Read this doc + `704`. Take the `705` quiz. | — |
| 2 | Classify all 7 open PRs into lanes A/B and write your intended verdict + reason. Do not comment yet. | none |
| 3 | Walk your verdicts through with Jeremy. Focus on the ones you got wrong — that is the whole value of this stage. | none |
| 4 | Take the two Lane-A PRs end to end **with wording approved first**. | Reviewer |
| 5 | Take a Lane-B submission end to end. | Reviewer |
| 6 | Pass the quiz → CODEOWNERS flip. | **Approver** on CI/infra + marketplace site |

The oldest PR in the queue has been open **13 days**. Contributor patience is a
real resource and we are currently spending it. Speed of *response* matters more
than speed of merge — a fast, well-reasoned "no" beats a slow silence every time.

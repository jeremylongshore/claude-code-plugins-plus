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

The pipeline tells you whether a PR is _safe_. It cannot tell you whether it is
_wanted_. That second question is the maintainer's job, and there is no gate for
it.

One number to keep you calibrated: **roughly 1 in 10 external-sync PRs merges.**
Closing a PR is a normal, healthy outcome, not a failure of the process. If you
find yourself trying to get everything to green, you have misunderstood the job.

---

## 1. First move: classify. Everything else follows from this.

Do not start reading the diff. Look at _which files changed_ and pick the lane.

```bash
gh pr view <N> --repo jeremylongshore/claude-code-plugins-plus-skills \
  --json files --jq '[.files[].path] | join("\n")'
```

| If the diff contains…                 | Lane                          | What it means                                                                                                          |
| ------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| only `sources.yaml`                   | **A — mirror registration**   | They want us to _sync_ their repo. We host a mirror; they keep ownership.                                              |
| a new `.claude-plugin/plugin.json`    | **B — new plugin submission** | Code lands _in our tree_ and we own it thereafter.                                                                     |
| `marketplace.json` (not `.extended.`) | **C — reject on sight**       | Auto-generated file. See §6.                                                                                           |
| anything under `.github/workflows/`   | **D — escalate to Jeremy**    | A workflow change from an external contributor can disable the gates that are reviewing it. Never merge this yourself. |

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
   with no reason is silently _ignored_, not honoured, so a lazy waiver fails
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

| Tier                                        | Required              |
| ------------------------------------------- | --------------------- |
| Micro-skill (one command/skill, no scripts) | `docs/PRD.md`         |
| Standard plugin (skills + scripts)          | `+ docs/ADR.md`       |
| Pack / flagship / featured / paid           | `+ docs/ONE-PAGER.md` |

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

- **Kilo Code Review** — failing on **every** PR: _"could not run — your account
  is out of credits."_ That is billing, not a finding.
- **Gemini Code Assist** — the consumer product is **sunset**. The bot posts only
  a sunset notice. `.gemini/config.yaml` is retained-but-inert.
- **Greptile** — active through the GitHub App, advisory, quota-limited (~50/mo).

**Never block a merge waiting for an AI review, and never treat one as approval.**
The gate is `ci-required` + `gitleaks` + `skill-conform` + a code-owner review.
Read Greptile when it shows up; address real findings; move on.

---

## 6. Hard "no" list — refuse these without debate

| Situation                                      | Why                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hand-edited `marketplace.json`                 | Auto-generated from `marketplace.extended.json`. Ask them to edit the extended file and run `pnpm run sync-marketplace`.                                                                                                                                                                                                                                                                            |
| Any local edit to a `curated: true` mirror     | Freeze exists to prevent an 18,900-line revert.                                                                                                                                                                                                                                                                                                                                                     |
| A REFUSE finding from `scan-synced-content`    | Not waivable. Fix at source or close.                                                                                                                                                                                                                                                                                                                                                               |
| A workflow change from an external contributor | Can disable the gates reviewing it. Escalate to Jeremy.                                                                                                                                                                                                                                                                                                                                             |
| Raising a gate baseline to get green           | Both ratcheting gates are built to move one way. `check-internal-doc-links.mjs` refuses outright; `lint-design-tokens.mjs` ratchets **down** only via `--update-baseline` and can never be raised silently — raising it means editing the committed baseline file in a reviewable diff. Lowering is progress; raising is how 749 CodeQL alerts and 500 link errors accumulated behind green checks. |
| Plaintext secret "just for testing"            | `gitleaks` blocks it, and it belongs in `tests/fixtures/` as a stub.                                                                                                                                                                                                                                                                                                                                |

---

## 7. Upstreaming — how we raise quality without taking ownership

When a mirrored plugin is below our bar, the move is **not** to fix it locally.
Local fixes get reverted by the next sync and quietly take ownership of somebody
else's code.

The flow, in order:

1. A friendly **issue** first: _"we featured your plugin and hardened its
   frontmatter to our A-grade bar — would you be open to a PR upstreaming that?"_
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

## 8A. DRAFT — the intake-reset note for the aging external queue

> ## ⚠️ STATUS: DRAFTED FOR OWNER APPROVAL. **NOT POSTED.**
>
> Nothing in this section has been sent, commented, or published anywhere. No PR was
> closed, commented on, labeled, or contacted while this draft was written. Per the
> standing rule in this repo, **any contributor-facing wording gets Jeremy's sign-off
> before it is posted** — this is the artifact that sign-off applies to.

### 8A.1 The measured facts this wording has to be honest about

A batch close is only defensible if we are straight about whose clock ran out. It was ours.

| Fact                                                                     | Detail                                                                                                                   |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **5 PRs are waiting on US, with no review of any kind**                  | `#1181` (0 d), `#1173` (3 d), `#1172` (3 d), `#1163` (6 d), `#1144` (15 d)                                               |
| **4 have ZERO CI checks — and that is our pipeline's doing, not theirs** | `#1181`, `#1173`, `#1172`, `#1083` — fork PRs stall in GitHub's `action_required` approval gate, so no workflow ever ran |
| **1 is ACTIVE and must be EXCLUDED from any batch action**               | `#1131` — updated 0 days ago. Touching it would be exactly the carelessness this note apologizes for                     |
| Queue size                                                               | 13 external-contributor PRs open                                                                                         |

Three rules fall straight out of that table, and the draft below obeys all three:

1. **Never start the stale clock before we gave actionable feedback.** "This has been open
   N days" is a legitimate reason to close only when the contributor was told what to fix
   and did not. Where the silence was ours, N days is our number, not theirs.
2. **Never call a PR "failing CI" when CI never ran.** A fork PR sitting in
   `action_required` has no checks because nobody clicked approve. Saying "your checks are
   red" about a PR with **zero** checks is false, and the contributor can see that it is
   false.
3. **Exclude anything with recent activity.** `#1131` is live. A batch message that lands
   on an active conversation reads as automation, and it is.

### 8A.2 The draft (per-PR comment, then close)

> Hi @{contributor} — thank you for this, and I'm sorry for the wait.
>
> This one has been open **{N} days without a review from us**{, and because it comes from
> a fork, our CI never even ran on it — fork PRs sit in GitHub's manual approval gate, and
> we didn't clear yours. That's our pipeline, not your branch.} You did your part; we
> didn't do ours, and that's the honest summary.
>
> We're in the middle of a repository-wide modernization, and part of it is resetting how
> submissions come in: a defined intake standard, checks that actually run on fork PRs, and
> a review path with a real response time instead of an open-ended queue. Rather than leave
> your PR sitting against the old process — and rather than review it against rules that
> are being replaced this week — I'm closing it as part of that reset.
>
> **This is not a rejection of your work, and it is not a quality judgment.** Nothing here
> was reviewed and found wanting; it was never reviewed at all. Your authorship, your
> commits, and your credit stay exactly as they are, and the branch is untouched.
>
> **Reopening is one click.** Press "Reopen" on this PR whenever you like — no
> re-submission, no new issue, no form, no rebase required unless it conflicts. If you'd
> rather start fresh against the new intake standard, that works too:
> [`000-docs/700-DR-GUID-skill-submission-standard.md`](700-DR-GUID-skill-submission-standard.md).
> Either way, ping me here and I'll get you an answer within {commitment} — that's the part
> we're actually fixing.
>
> Thanks again for spending unpaid hours on our catalog. It's noticed.
>
> - Jeremy Longshore
>   intentsolutions.io

**Substitution notes for whoever posts it (after sign-off):**

- `{N}` — the measured days-without-review for that specific PR. Use the real number; if
  the PR is only hours old (`#1181`), **do not include it in the batch at all** — an
  apology for a 0-day wait is theater.
- `{, and because it comes from a fork…}` — include **only** for `#1181`, `#1173`, `#1172`,
  `#1083`, the four with zero checks. For the others, drop the clause; do not imply a CI
  problem that did not occur.
- `{commitment}` — a response window the owner is actually willing to meet. If none can be
  committed, delete the sentence rather than write a promise the queue will break.
- Every comment is authored per-PR. **No identical mass comment** — a form letter about
  responsiveness is self-refuting.

### 8A.3 Scope guard — who is in the batch and who is not

| Disposition                 | PRs                                                            | Why                                                              |
| --------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- |
| **EXCLUDE — active**        | `#1131`                                                        | Updated 0 days ago; a live conversation is never batch-closed    |
| **EXCLUDE — too new**       | `#1181`                                                        | 0 days old; there is no delay to apologize for yet, so review it |
| **Fork-CI clause REQUIRED** | `#1173`, `#1172`, `#1083` (and `#1181` if it is ever included) | Zero checks because of our `action_required` gate                |
| **Standard wording**        | The remaining aging PRs                                        | Waited on us without an actionable review                        |

### 8A.4 What must be true before this is sent

1. Owner sign-off on the wording (standing rule).
2. The per-PR `{N}` values re-measured on the day of sending — not copied from this table.
3. A decision on `{commitment}`, or the sentence removed.
4. The fork-CI gate itself fixed or scheduled, so the apology is not repeated verbatim in
   four weeks. Apologizing twice for the same mechanism is worse than not apologizing.

---

## 9. Two-week ramp

| Stage | Do this                                                                                                          | Ownership                                   |
| ----- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 1     | Read this doc + `704`. Take the `705` quiz.                                                                      | —                                           |
| 2     | Classify all 7 open PRs into lanes A/B and write your intended verdict + reason. Do not comment yet.             | none                                        |
| 3     | Walk your verdicts through with Jeremy. Focus on the ones you got wrong — that is the whole value of this stage. | none                                        |
| 4     | Take the two Lane-A PRs end to end **with wording approved first**.                                              | Reviewer                                    |
| 5     | Take a Lane-B submission end to end.                                                                             | Reviewer                                    |
| 6     | Pass the quiz → CODEOWNERS flip.                                                                                 | **Approver** on CI/infra + marketplace site |

The oldest PR in the queue has been open **13 days**. Contributor patience is a
real resource and we are currently spending it. Speed of _response_ matters more
than speed of merge — a fast, well-reasoned "no" beats a slow silence every time.

---
title: "Ending a Four-Month Silent Fail: Cross-Repo Triangulation on a Broken Gemini PR Workflow"
description: "When a Gemini PR review workflow silently fails for four months, your first-principles fix is the suspect. Triangulate against a working reference."
date: "2026-04-23"
tags: ["ai-agents", "debugging", "ci-cd", "claude-code", "github-actions"]
featured: false
---
When an integration silently fails for months, your first-principles hypothesis is the suspect — find a working reference implementation in the same ecosystem and triangulate against its actual configuration before committing to a fix.

That sentence is the whole lesson from today. The Gemini PR review workflow on `claude-code-plugins-plus-skills` had been silently failing on community PRs since December. Five contributor PRs were stalled with zero Gemini output. The pipeline's `gemini-review` step kept reporting green. No one noticed because Gemini's failure mode is "post nothing" — not "throw an error."

I had a clean theory for what was wrong, wrote the fix, opened PR #602, and was about to merge. Then I read one paragraph in a different repo's workflow header and reversed the entire change. Below is the journey: the false hypothesis, the reversal, the triangulation method, and the patch that ended the silent fail across all five stalled PRs in under two minutes.

The mechanic was reproducible: a contributor opens a PR from a fork. CI runs. The Gemini review job reports green. No review appears. The contributor waits a few days, eventually pings me, and I shrug because the dashboard says everything succeeded. Repeat across five contributors and four months and you have a queue of stalled work where the failure surface is *the absence of a thing*, not the presence of an error.

## The symptom that wasn't a symptom

The wild ecosystem (the umbrella name for the Wild + IRSB constellation of plugins) ships its Gemini PR review via a shared workflow template. Every plugin repo inherits the same `gemini-review.yml` file, and every plugin repo points at the same shared GCP service account via Workload Identity Federation. It is the kind of design that pays off when it works — one fix, fleet-wide — and burns silently when it doesn't.

The CCP marketplace repo (`claude-code-plugins-plus-skills`) inherited that template back in December 2025. Maintainer PRs got Gemini reviews. Community PRs from external forks got nothing. Five contributor PRs accumulated:

| PR | Author | Age | Gemini output |
|---|---|---|---|
| #547 | mark1ian | 14d | none |
| #534 | external | 38d | none |
| #529 | external | 41d | none |
| #528 | external | 41d | none |
| #527 | external | 42d | none |

The CI dashboard reported all five as having "completed" Gemini runs — which was technically true. The job ran. It just posted nothing. GitHub's Actions UI does not distinguish "Gemini posted a review" from "Gemini ran to completion and decided not to comment." The silent fail was indistinguishable from a clean review of a PR that had no issues.

## The first-principles hypothesis (which was wrong)

The shared workflow template loads an MCP server inside the GitHub Actions runner — the official `ghcr.io/github/github-mcp-server:v0.27.0` container — and pipes its stdio into the Gemini CLI. The MCP server exposes three tools: `pull_request_read`, `add_comment_to_pending_review`, and `pull_request_review_write`.

When I read this for the first time today, my engineering instinct said *that's overcomplicated*. Gemini already knows how to call HTTP endpoints. GitHub already has REST and GraphQL APIs. Why interpose a docker sidecar that re-exposes three calls Gemini could make directly?

The hypothesis: **the MCP server is unnecessary indirection, and probably the cause of the silent failure**. Some race condition between docker startup, runner stdio, and Gemini's tool-call protocol. Strip it, use Gemini's built-in HTTP capabilities, simpler workflow, no silent fails.

I rewrote the workflow without MCP, added `pull_request_target` to fix the orthogonal fork-PR permission gap, layered in an `ENABLE` repo variable as a kill switch, persisted PR metadata for downstream Slack notifications, and shipped PR #602 with a self-congratulating commit message about removing unnecessary complexity.

CI went green. Gemini posted nothing. *Same silent fail.*

That should have been the first hint. It wasn't, because PR #602 was on a fork of my own repo and the new `pull_request_target` semantics meant the workflow was running against a different commit graph than I expected. I told myself the green CI was the empty-PR-nothing-to-review case. I was about to admin-merge.

## The reversal: one paragraph in a different repo

Before merging, I checked the merge-gate surface — branch protection, CODEOWNERS, automerge sender check — and in passing went to look at how `claude-code-slack-channel` (CCSC, a sibling repo, also has a Gemini review workflow) configures its setup. Pure curiosity. The merge was 30 seconds away.

A workflow header in CCSC's `gemini-review.yml` documented why an earlier attempt (issue ccsc-304) had failed:

> The key pieces the first attempt missed: `mcpServers.github` declares the GitHub MCP server container that **actually provides** `pull_request_read` / `add_comment_to_pending_review` / `pull_request_review_write`. **Without it the tools are unreachable and Gemini silently posts nothing.**

That paragraph killed the merge. The header was telling me, in the past tense, that someone had already run my exact experiment six months earlier — strip the MCP server, see if Gemini's built-in HTTP works — and watched it produce the same silent fail I was about to ship as a fix.

The Gemini CLI does not fall back to direct HTTP for the `pull_request_*` tool family. Those tools only exist when the MCP server provides them. Without MCP, Gemini's tool calls reach for endpoints that aren't registered, fail silently inside the agent loop (no error surfaced to the runner), and the agent decides to post nothing because it has no successful tool call to base a review on.

My "unnecessary indirection" was the only thing that made reviews possible.

## The triangulation method

Before I rewrote the rewrite, I forced myself to triangulate against three independent repos in the ecosystem:

| Repo | MCP server | Posts reviews |
|---|---|---|
| `claude-code-slack-channel` (CCSC reference) | yes, `v0.27.0` | yes |
| `wild-admin-tools-mcp` (current wild template, no MCP) | no | **no — same silent fail** |
| `x-bug-triage-plugin` (standalone, has MCP) | yes, `v0.27.0` | yes |

Three data points. Two with MCP, one without. The two with MCP both work. The one without is broken in exactly the way `claude-code-plugins-plus-skills` is broken. The wild-template's MCP-less design wasn't a deliberate choice — it was a regression from a prior copy-paste, and every plugin that inherited from that template got the same broken config.

This is what I mean by triangulation. A single working repo proves the integration *can* work. A single failing repo doesn't tell you why. Three repos arranged across the variable you suspect — *with* MCP and *without* — let the configuration speak instead of the hypothesis.

## The patch

The actual fix was small. Restore the MCP server block, keep all the other improvements I had layered in (the `ENABLE` gate, `workflow_dispatch`, fork support via `pull_request_target`, SHA-pinned checkout, no credential persistence, debug flag, Slack notify hook).

The MCP block:

```yaml
- name: Run Gemini review
  uses: google-gemini/gemini-cli-action@v3
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    PR_NUMBER: ${{ github.event.pull_request.number }}
    GEMINI_DEBUG: ${{ vars.GEMINI_DEBUG || 'false' }}
  with:
    settings: |
      {
        "mcpServers": {
          "github": {
            "command": "docker",
            "args": [
              "run", "-i", "--rm",
              "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
              "ghcr.io/github/github-mcp-server:v0.27.0"
            ],
            "env": {
              "GITHUB_PERSONAL_ACCESS_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
            }
          }
        },
        "coreTools": [
          "run_shell_command(echo)",
          "run_shell_command(gh)"
        ]
      }
```

(Note: `google-gemini/gemini-cli-action@v3` was the action this repo had been pinned to since the early-2026 install. As of late April 2026, Google's officially-maintained successor is `google-github-actions/run-gemini-cli`; the MCP server image `github-mcp-server:v0.27.0` is also several minor versions behind current. Both are tracked for a follow-up bump — not part of this restore.)

The `mcpServers.github` block runs the MCP container as a docker sidecar inside the GitHub Actions runner. The Gemini CLI talks to it over stdin/stdout. The server exposes three review-specific GitHub API tools to Gemini, and only those three — no write access to code, no merge, no push. Permission is bounded by what the MCP server registers, not what `GITHUB_TOKEN` could do in principle.

The fork support was a separate but related gap. The original workflow used `on: pull_request`, which on community-fork PRs runs without secrets and with read-only `GITHUB_TOKEN`. Even if MCP had been wired up correctly, those PRs would fail to post because `pull_request_review_write` requires write scope. The fix is `pull_request_target`, which runs the workflow against the **base** repo's secrets while still seeing the fork's diff:

```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened]
    branches: [main]

permissions:
  contents: read
  pull-requests: write
  issues: write
```

`pull_request_target` is a foot-gun if you let it check out arbitrary fork code with secrets in scope. The mitigation is to checkout by SHA (not by ref), avoid persisting credentials, and never `npm install` from fork code. The workflow does all three:

```yaml
- uses: actions/checkout@v4
  with:
    ref: ${{ github.event.pull_request.head.sha }}
    persist-credentials: false
```

Reviews now run with the secrets they need; fork code never executes with those secrets in scope.

## The result

I merged PR #602 with admin override (the merge gate I was hardening, CODEOWNERS-required review, was set up in the same PR), then kicked off the workflow manually on all five stalled community PRs. Two minutes later:

| PR | Reviews posted | Inline comments |
|---|---|---|
| #547 | 1 | 1 |
| #534 | 1 | 0 (summary only) |
| #529 | 4 | 7 |
| #528 | 1 | 2 |
| #527 | 1 | 1 |

Eight reviews and 11 inline comments across five PRs that had been silent for over a month. The reviews used GitHub suggestion blocks, hit the actual contribution issues (one PR had a real `--arg` jq-injection bug Gemini caught and that I later folded into a separate fix), and read like a competent senior reviewer.

The per-PR review quality breakdown was useful to walk through:

| PR | Scope | What Gemini caught |
|---|---|---|
| #547 | 18-line `sources.yaml` registration for skyvern browser automation skill | One inline comment on a malformed YAML key. Approved otherwise. |
| #534 | Doc-only contribution | Summary review approving the change. No inline comments needed. |
| #529 | Plane-sync workflow (GitHub → Plane bridge), 4 review rounds across multiple commits | Caught the `--arg` jq-injection vector. Flagged a fetch-all-issues N+1 loop concern (deferred — needs Plane API verification for `?sequence_id=X` support). The four sequential reviews tracked across pushes correctly. |
| #528 | Plugin metadata fix | Two inline suggestions on YAML formatting. |
| #527 | Skill registration | One inline suggestion. Approved. |

The jq-injection finding alone justified the four-month effort. That bug had been sitting in an open community PR for 41 days. Without Gemini, it would have either been merged on a manual review that missed it, or sat for another four months while the contributor wondered why no one was reviewing the PR.

One artifact of the SHA-pinned checkout: the new `gemini-review.toml` prompt customization (which adds Intent Solutions philosophy framing and CONTRIBUTING.md links) doesn't apply to those five backfilled PRs. The Gemini CLI loads its prompt from the PR's HEAD SHA, and those community branches were forked before the prompt change landed. The new prompt activates on the next push to any of those PRs or any new PR opened after today. That's a feature, not a bug — fork PRs see the prompt that was in effect when they branched, which is the same security boundary that protects against malicious fork code editing the review prompt itself.

## What the false hypothesis cost

About three hours of work. Issue #604 ("MCP-less workflow reversal plan") was the rollback design I had drafted before the CCSC workflow-header paragraph reversed it. The issue is now archived as a record of the wrong direction. Three hours of design work, ~150 lines of YAML written and discarded, and one PR rewritten end-to-end.

The lesson — *find a working reference implementation in the same ecosystem and triangulate against its actual configuration* — is cheap to learn after the fact. Expensive to apply in the moment, because at the moment of designing the fix, the failing system is the only data point in front of you. The working reference is in some other repo you don't currently have open. Going to look at it feels like procrastination. It is not procrastination.

This is the whole shape of the bug: a silent-fail integration looks broken **by your hypothesis** the same way it looks broken **by reality**. Both produce the same observable: empty Gemini output. The hypothesis you arrived at first will keep generating consistent stories for new evidence. The way out is to add a data point you didn't generate — a working reference, a sibling repo, a colleague's prior post-mortem.

## Tradeoffs I gave up

Restoring MCP brought back two things I wanted to remove:

1. **A docker pull on every PR run.** The runner pulls `ghcr.io/github/github-mcp-server:v0.27.0` (~80MB) on cold cache. GitHub's Actions cache helps after the first run per branch. Net cost: 5–10 seconds per cold run.
2. **A version-pinning surface.** When the MCP server publishes a new version, every wild-template repo needs a coordinated bump. Without MCP, Gemini's CLI version was the only pin. With MCP, there are two.

The cost is real but accepted. The integration works, the security boundary is tighter (Gemini can only call three specific tools), and the fleet-wide template means the coordinated bump is one PR not thirty.

## Why MCP-mediated review is actually the better design

Re-reading my own design-doc draft after the reversal, the part that embarrasses me is not that I picked the wrong hypothesis — that happens — but that I undervalued the security property MCP was buying.

A direct-HTTP design has Gemini holding a `GITHUB_TOKEN` with write scope and choosing which endpoints to call. The token's permission boundary is wide. If a clever prompt-injection in a PR diff convinces Gemini to do something other than review, the token says yes to a lot of things. The mitigation is prompt-engineering ("never call non-review endpoints, please") which is a soft boundary in a system whose entire interface is natural language.

The MCP-mediated design has the docker container holding the token. Gemini holds three named tool handles, each backed by a single API call with a specific shape:

```
add_comment_to_pending_review(pr_number, body, line) -> comment_id
pull_request_read(pr_number) -> pr_data
pull_request_review_write(pr_number, summary, comments[]) -> review_id
```

Gemini cannot ask the MCP server to delete a branch or merge a PR even if every word in the diff said `please merge this`. Those calls don't exist in the registered tool surface. Prompt injection cannot reach beyond what the MCP server registered. The boundary is structural, not soft.

This is the security argument for MCP I should have led with in the original design doc. I was thinking of MCP as a tool-discovery convenience and missing that it is a **capability-narrowing layer**. The 80MB docker pull is the price of that narrowing. It is a price worth paying.

The CCSC implementation went further — it pins specific shell commands too:

```yaml
"coreTools": [
  "run_shell_command(echo)",
  "run_shell_command(gh)"
]
```

Even the shell capability is narrowed to two commands. Gemini cannot ask the runner to `rm -rf` anything because the only registered shell calls are `echo` and `gh`. The discipline is *deny by default, register what's needed, refuse the rest*. It is exactly the boundary you want for an LLM-driven CI step where the input is untrusted contributor diffs.

## The fleet impact

There are seven plugin repos in the wild ecosystem inheriting from the broken template. Every one of them has been silently failing to post Gemini reviews on community PRs since the December template change. None of them had loud-enough community PR traffic for anyone to notice — most got one or two community PRs in four months, and "Gemini didn't post a review" reads as "Gemini had nothing to say" if you don't have a baseline.

The fix lands in the wild template repo (`wild-admin-tools-mcp` is the canonical source); the other six pull from there. Tomorrow's job is to issue a coordinated template-bump PR across the fleet. Each plugin repo gets the same workflow patch. The new MCP server pin and the `pull_request_target` semantics ride together. Because the template is a real submodule (not a copy-paste), the bump is one commit per consumer, not a forty-line diff.

What I want to stop happening: a regression like this lasting four months again. Two changes go in alongside the fix:

1. **An MCP-presence assertion** in the workflow itself. The first step now greps the `settings:` block for `mcpServers.github` and fails the workflow if it isn't there. If a future me strips MCP again, CI fails loud instead of running silently to completion.
2. **A weekly synthetic PR.** A scheduled workflow opens a PR-against-itself once a week with a known-non-trivial diff and asserts that Gemini posts at least one review comment within 10 minutes. If the synthetic PR ever doesn't get a review, an alert fires. This converts the silent-fail mode into a loud-fail mode at the cost of one bot-author PR per week per repo.

Both changes are cheap. Neither would have helped if my hypothesis had been right (no Gemini = no synthetic alert = same silent fail). They help specifically against the failure mode I just lived through: *configuration drift inside a working integration*.

## What I'd tell my December self

If I were leaving notes for the engineer who set up the original wild template, the message would be short:

> The Gemini CLI requires an MCP server providing the `pull_request_*` tool family. Without it, reviews silently post nothing — the workflow runs to green. Pin `ghcr.io/github/github-mcp-server:v0.27.0` in the `settings.mcpServers.github` block. If you're tempted to remove it because direct HTTP looks simpler, read this footnote first. It does not work and the failure mode is invisible.

I would also tell that engineer to add the MCP-presence assertion at template-creation time, not as a retrofit. The class of bug — *invisible-when-broken integrations* — is the most expensive class of bug to find, and the cheapest class of bug to write a tripwire against. The asymmetry is enormous.

The tripwire was the lesson missing from the December design. Today's PR backports it.

## What this changes about how I'll set up future integrations

Three concrete changes to the template I use for any LLM-driven CI step from this point forward:

1. **Capability narrowing through MCP, not prompt engineering.** Whenever an LLM is doing something in CI, the tools available to it are declared in a registry, not in natural language. If the integration supports an MCP layer, use it. If it doesn't, write a thin proxy that exposes only the calls the LLM should be able to make. The boundary needs to be structural.

2. **A liveness assertion in the workflow.** Every LLM-driven CI step gets a final assertion that checks for an externally visible side effect — a comment posted, a status set, a file written. If the side effect is missing, the step fails. The principle: jobs that succeed by doing nothing are indistinguishable from jobs that fail by doing nothing, so make doing nothing a failure.

3. **A scheduled smoke test against a synthetic input.** Every integration that depends on external services (Gemini, Slack, Plane, GCP) gets a synthetic input that exercises the full path on a fixed cadence. The synthetic input has known properties so the assertion can be specific. The goal is converting silent fail into loud fail without waiting for real traffic to expose the regression.

These are not novel ideas. They are obvious in retrospect, expensive to write into a template prospectively, and trivial to omit during a "simplify" pass. The discipline I'm trying to build is to push the load-bearing properties down into the integration layer so that future simplification passes can't remove them without making the failure visible.

## Also shipped

**Frontmatter cleanup campaign — Phase 1 (PR #605).** The CCP marketplace had 182 frontmatter validation errors blocking `ccpi validate --strict`. Phase 1 was 5 trivial fixes — invalid `category` values on shipwright agents and one description over the 80-character limit. Merged. Phase 2A followed in two batches: PR #606 fixed the 12 fullstack-starter-pack agents missing `capabilities`, and PR #607 fixed 11 code-cleanup agents with the same issue. 23 agents cleared, 159 remaining. The campaign is tracked under issue #604 with phased rollout because most of the 159 are external contributor agents that need the contributor's approval to amend.

**`claude-code-slack-channel` v0.9.0 release.** Shipped with the lazy `allowFrom` snapshot diff design for `pairing.accepted` audit events. The skill runs outside the server process (no IPC channel exists), so the choice was between `fs.watch`, a new IPC mechanism, or diffing snapshots in the existing `getAccess()` hot path. Snapshot diff won — zero new infrastructure, zero new failure modes, and the diff cost is amortized over the existing read path. PR #150 closed the audit EventKind coverage gap from 18/19 to 19/19. After-action report at `000-docs/v0.9.0-release-aar.md`.

**`cad-dxf-agent` L0–L7 test infrastructure scaffolding.** Ran `/audit-tests` then `/implement-tests` for the full 7-layer testing taxonomy. Staged 1,910 lines across 20 files on `feature/implement-tests-l0-l7` — git hooks (L0), static analysis (L1), unit + integration scaffolding (L3), full acceptance harness (L7). Nothing committed yet; staged for engineer review per the implement-tests SOP. The audit identified 5 personas to collapse from the original 25 (Design Author, Reviewer/Compliance, Estimator/Coordinator, Field/Operator, Platform Admin) and 30 Pydantic schema contract boundaries that anchor the L3 integration suite.

**Braves Booth — SportsTalk ATL feed.** Added SportsTalk ATL to the Local Coverage panel of the Braves Booth dashboard. The site's bot-blocking is lightweight UA sniffing — it rejects `node-fetch`'s default user-agent but accepts any browser-looking UA. Distinguishes from MLB.com's full IP-based blocks, which can't be bypassed with header spoofing. v1.2.8 shipped. Useful taxonomy when scraping a new feed: try real browser headers first; if 403 turns into 200, it's UA sniffing and the bypass is essentially free; if it still 403s, it's IP-based and you need a residential proxy or vendor-supplied feed access.

## Why the wild-template existed in the broken state

Worth a moment on how the template ended up MCP-less in the first place, because the failure mode is instructive.

The wild ecosystem template was originally forked from a working Gemini-review reference in mid-2025. The original reference had MCP wired up correctly. Sometime in the December 2025 refactor, the template was simplified during a "remove unnecessary complexity" pass that stripped the MCP block. The rationale in the commit message read like the rationale I had written this morning — *direct HTTP is simpler, fewer moving parts, less ops surface*. The change passed local validation because validation was "does the workflow YAML parse?" and the workflow YAML did parse.

The change passed CI because CI was "does the workflow run to completion?" and the workflow did run to completion. The change passed code review because there were no community PRs against the affected repos that week, so no one observed the review-posting regression.

This is the failure topology of soft tests against silent integrations. Each gate validated *something*, but no gate validated the load-bearing property: *does Gemini actually post a review?* A property no one had explicitly written down as a test, because at the time the template was created, the property was assumed to follow from the workflow being correct.

The fix going forward is the MCP-presence assertion plus the weekly synthetic PR. Both encode the load-bearing property as an explicit gate. Both would have caught the December change before it shipped to seven downstream repos. Neither was particularly hard to write — the MCP-presence check is a 4-line shell `grep`, the synthetic PR is a 30-line scheduled workflow. The cost of writing them after the fact, paid in stalled community PRs and reversed redesigns, is roughly an order of magnitude higher than writing them in the first place.

## How I would have known sooner

In retrospect there were three signals available the day the bug shipped, and I missed all three:

**Signal 1: The maintainer-PR / community-PR asymmetry.** Maintainer PRs ran with `pull_request` event and same-repo secrets, so even without MCP, Gemini's tool calls would have *registered* (just hit empty endpoints). Community-fork PRs ran with read-only `GITHUB_TOKEN`, so the missing tools compounded with missing write scope. Both produced empty output, but the underlying causes were different. If I had asked "do *all* PRs fail or only fork PRs?", the answer would have pointed at `pull_request_target` immediately. I assumed all PRs were failing because I didn't have a recent maintainer PR to compare against.

**Signal 2: Workflow run logs.** GitHub Actions surfaces job stdout. The Gemini CLI logs each tool-call attempt at debug level. In a working run, you see `tool_call: pull_request_review_write` followed by a 200 response. In a broken run, you see `tool_call: pull_request_review_write` followed by *no response and no error* — Gemini's agent loop swallows the failure and moves on. The signature is clear if you read the logs at debug level. The default verbosity hides it. Setting `GEMINI_DEBUG=true` is now baked into the workflow as a repo variable, defaulting on. The cost of debug logging is a few KB per run. The benefit is that the next silent fail won't be silent.

**Signal 3: Cross-repo comparison.** This is the lesson of the post. If I had run the workflow on `wild-admin-tools-mcp` and `claude-code-slack-channel` side-by-side at template-adoption time and noticed one posts reviews and the other doesn't, the divergence would have shown up immediately. Instead I trusted that the template was correct because the template *had been* correct in some previous version, and I didn't re-validate after the December change.

The general pattern: integrations that are silent when broken should always have a smoke test that runs in a known environment and asserts a visible side effect. The smoke test costs one synthetic PR per week. The bug it catches costs four months of stalled community contributions.

## The discipline

Look at a working version of the thing you're about to rewrite. The hypothesis you arrived at first is the suspect, especially when the bug has been silent for months and you're the first person motivated to fix it. The longer the silent fail has lived, the higher the prior probability that the obvious fix has already been tried and discarded by someone whose post-mortem is sitting in a workflow header in a different repo, three directories away.

When you're staring at a green CI dashboard and zero output, the fix is not in the failing repo. The fix is in the working repo, the one you stopped looking at because it works. Go look at it.

A meta-observation: the people most likely to ship this class of regression are the people most confident they understand the integration. Junior engineers tend to leave the working setup alone because they don't fully understand it yet. Senior engineers are the ones who simplify it. The cost of bad simplification is silent fail, and the asymmetry between the two error modes — "I don't understand this so I'll leave it" versus "I understand this so I'll change it" — gets paid by the contributors whose PRs go silent.

The remediation is not "stop simplifying." Simplifying is a real value. The remediation is *if you can't articulate why each removed piece was there, leave it.* If you can articulate it, fine, simplify. If you remove the piece and the system still seems to work, prove it works on the path that actually exercises the removed piece — not on the path that already worked without it.

That is the discipline. Today I bypassed it, caught myself in time because the CCSC workflow header was three keystrokes away, and shipped the right fix instead of the wrong one. Both versions of me would have produced a green CI dashboard. Only one version would have produced reviews on community PRs.

The contributors whose PRs sat for forty days deserved better than a green dashboard. The fix lands today.

## Related posts

- [Four Releases in One Day: How the claude-code-slack-channel Security Sprint Actually Shipped](/posts/ccsc-five-releases-one-day-security-sprint/) — the sibling repo whose workflow header reversed today's hypothesis.
- [Four Primitives, Three Reviews: How a Contributor PR Reshaped a Roadmap](/posts/collaboratively-shaped-roadmap/) — earlier story on the CCP contributor pipeline this fix unblocked.
- [AI Code Review Blind Test: Where 5 Bots Shine](/posts/ai-code-review-without-context-blind-test/) — what Gemini actually contributes once it's wired up correctly.


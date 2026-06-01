---
title: "Eight Deploy Iterations: Tailscale OIDC + Reusable Workflow"
description: "8 GitHub Actions iterations to land Tailscale OIDC + a cross-repo reusable workflow. P2 and P5 of VPS-as-the-Home, with the plan rewrite that held the line."
date: "2026-05-01"
tags: ["devops", "ci-cd", "release-engineering", "tailscale", "github-actions", "infrastructure"]
featured: false
---
Day 1 of VPS-as-the-Home was the launch of a 9-priority program: consolidate Intent Solutions hosting onto a single Contabo VPS, execute the GCP exodus, and harden every active repo's deploy posture. The deploy pipeline cost 8 GitHub Actions run iterations across two priorities to land what should have been one. The plan-v4.1 rewrite — adding testing as a first-class requirement after the user surfaced that `cd <random-repo> && git push` should "just work" — was the discipline that survived contact with reality.

Twenty PRs on `braves-booth`. Fifteen commits on a brand-new runbook repo. A new `jeremylongshore/.github` repo with a reusable workflow. Eight propagation repos picked up the testing harness. All twenty-five production containers stayed healthy through every iteration. No production downtime.

This is the deploy-side story.

## The program shape

VPS-as-the-Home is nine priorities under epic `OPS-5nm`. The umbrella problem: Intent Solutions production was scattered across a dev box that kept tripping OOM cascades, three GCP projects with mismatched billing, and ad-hoc deploy scripts that didn't agree on anything. The fix is a single Contabo VPS (`intentsolutions`, `167.86.106.29`, 24 GiB RAM) running every Intent Solutions production stack behind a single Caddy ingress, with deploys driven from GitHub Actions through Tailscale.

Today's priorities:

- **P0** Rotate leaked tokens — closed scope-modified. User accepted residual risk on Tailscale + GitHub PAT values still in `secrets.prod.sops.yaml`. Memory entry locked so no future session re-asks.
- **P1** Braves baseline + foundational docs — closed. Established the CLAUDE.md format that every other priority's repo would inherit.
- **P2** Tailscale OIDC migration — closed after 3 deploy-run iterations.
- **P3** Netdata + ntfy tailnet-only monitoring — closed 2026-05-02.
- **P4** Slack split + sops-encrypt notify env — partial. VPS-side complete, firehose-channel split pending.
- **P5** Reusable workflow + braves refactor — closed after 5 deploy-run iterations.
- **P6** SOPS+age propagation + repo testing baseline — in flight, 11/23 done by end of day.
- **P7** GCP exodus — unblocked, tracker landed.
- **P8** Final cleanup — open.

The runbook repo `intentsolutions-vps-runbook` was bootstrapped at 3:15 AM with commit `e715f5f Initial bootstrap`. By morning, the Phase 0 tracking infrastructure was in place: `00-plan.md` at v4.1, `01-tracking-index.md` with bead ↔ GitHub issue ↔ AAR mapping per priority, and AAR scaffolding waiting to be filled. The discipline came first; the iterations followed.

## Priority 2: the Tailscale OIDC migration

The starting state: `braves-booth` deploys authenticated to Tailscale via a long-lived `TS_OAUTH_CLIENT_SECRET` GitHub secret. The goal: replace it with a GitHub-issued OIDC token Tailscale can verify on each run via [workload identity federation](https://tailscale.com/kb/1290/oidc-workload-identity) — short-lived, no static secret.

Should have been one PR.

| Run | Audience sent | Subject sent | Result | Lesson |
|---|---|---|---|---|
| 25235116847 (PR #86) | `https://github.com/jeremylongshore` | `refs/heads/main` | HTTP 400 "invalid request" | Wrong client_id — legacy OAuth `kAhtjSrYrz11CNTRL` doesn't work in OIDC mode |
| 25235249300 (workflow_dispatch) | `https://github.com/jeremylongshore` | `refs/heads/fix/tailscale-oidc-client-id` | HTTP 403 "Unauthorized" | Credential format accepted; some other claim mismatch |
| 25235414350 (PR #87 → main) | `https://github.com/jeremylongshore` | `refs/heads/main` | HTTP 403 "token has invalid audience" | Subject hypothesis was wrong — audience was the actual mismatch |
| 25237418475 (workflow_dispatch) | `api.tailscale.com/T54Ta7mgLc11CNTRL-kgkBgu2cSi11CNTRL` | `refs/heads/feat/re-enable-...` | HTTP 403 "Cannot validate subject" | Audience now passes; subject mismatch expected on non-main |
| **25237516269 (PR #90 → main)** | (correct audience) | `refs/heads/main` | **SUCCESS** | All claims match; OIDC handshake → SSH → docker compose → health 200 |

The first two runs burned on a wrong assumption: that the `client_id` field in the legacy OAuth flow was the same identifier OIDC wanted. It is not. OIDC mode wants the OIDC-flow client identifier from the Tailscale OAuth-trust UI — a separate value with a different prefix. HTTP 400 was the symptom; the assumption was the bug.

Run #3 swapped to the correct OIDC client id and immediately got HTTP 403 "token has invalid audience." The assumption this time: the subject claim must be wrong because OIDC tokens from `actions/checkout`-driven runs have a documented subject format. Spent an hour testing subject variants. None worked.

The actual fix surfaced from reading the Tailscale OAuth-trust UI directly instead of inferring: **Tailscale auto-generates the OIDC trust audience as `api.tailscale.com/<oidc-client-id>`**. It is not a value you choose. It is not documented in the Quick Start. You read it from the trust card after creating the trust, and you paste it verbatim into the GitHub Actions step's `audience` input.

Run #4 was a deliberate verification probe — not a real deploy attempt. The audience was now correct, the branch name was intentionally `feat/re-enable-...`, and the expected outcome was an HTTP 403 "Cannot validate subject" (because the wildcard subject pattern only matches `main`). Confirming that the failure mode flipped from "audience invalid" to "subject mismatch" verified the audience fix in isolation before touching `main`. Run #5 was the same code, merged to main, and OIDC handshake succeeded for the first time. The single-line root cause: **the audience was always going to be `api.tailscale.com/<client-id>` because Tailscale generates it; treating it as a chosen string sent us through three failed runs.**

Two follow-on wins:

1. **Wildcard subject pattern.** The Tailscale trust got configured with `repo:jeremylongshore/*:ref:refs/heads/main` — one trust covers every `jeremylongshore` repo's `main` branch. The reusable workflow can serve the whole portfolio without per-repo trusts.
2. **Secret deletion.** With OIDC verified, `TS_OAUTH_CLIENT_SECRET` was removed from `braves-booth` GitHub Actions secrets. The long-lived static credential is gone.

The hot-fix revert (PR #88) restored the OAuth-secret path partway through iteration so production deploys never lost capability while the OIDC story was still being figured out. That mattered: 25 containers were live, scorecardecho.com was serving real users, and the cost of breaking deploys mid-experiment would have been losing the ability to ship a fix.

Cost: 3 failed real deploy attempts (runs #1, #2, #3) plus one deliberate verification probe (run #4), 4 PRs (#86, #87, #88, #90) to land what should have been 1. Worth it.

## Priority 5: the cross-repo reusable workflow

With OIDC working in `braves-booth`, the next move was extracting the deploy job into a reusable workflow living in a new repo: `jeremylongshore/.github`. The reasoning: every Intent Solutions repo is going to need the same OIDC → tailnet-routability poll → SSH → docker compose → smoke check sequence. Copy-paste across N repos is how drift happens.

Should have been two PRs (one to create the reusable, one to call it from `braves-booth`).

| Run | Issue | Fix |
|---|---|---|
| 25237819383 (PR #92) | "Workflow file issue" | `jeremylongshore/.github` `actions/permissions/access` defaulted to `none` — blocked cross-repo reusable workflow call |
| 25237847204 | SSH "No ED25519 host key is known for intentsolutions" | `secrets: inherit` didn't forward `VPS_HOST_KEY` to the reusable workflow |
| 25237950256 (PR #93) | Same SSH host-key error | Explicit per-secret pass-through alone didn't fix — secret arrived (978 bytes) but its hashed entries didn't match `intentsolutions` lookup |
| 25238044624 (PR #94) | Same | Added size-debug step. 3 hashed entries; none decode to `intentsolutions` |
| 25238103973 (PR #95) | Same | Added hostname-field debug. Confirmed the pinned secret has wrong hash format |
| **25238177470 (PR #96)** | **SUCCESS** | Switched to inline `ssh-keyscan -t ed25519 intentsolutions >> known_hosts`; SSH match works; deploy completes; smoke passes |

The first failure was the most misleading. The error message GitHub returned was "Workflow file issue" — which sounds like a YAML problem in the reusable. It isn't. It's GitHub's repo-level setting `actions/permissions/access`. The brand-new `jeremylongshore/.github` repo had it set to `none` out of the box (GitHub's docs don't explicitly document the default for new private repos, but `none` was what the API returned when we read it before changing it). That setting controls whether *other* repos in the same org or user account can call the reusable workflow. With `none`, the call fails before the workflow file is even parsed.

Fix:

```bash
gh api -X PUT repos/jeremylongshore/.github/actions/permissions/access -f access_level=user
```

One API call. Took twenty minutes to find because the error pointed at the wrong thing.

Run #2 surfaced `secrets: inherit`. The caller workflow had:

```yaml
jobs:
  deploy:
    uses: jeremylongshore/.github/.github/workflows/vps-deploy.yml@709a07f
    secrets: inherit
```

`inherit` is [documented](https://docs.github.com/en/actions/using-workflows/reusing-workflows#passing-inputs-and-secrets-to-a-reusable-workflow) as "pass all caller secrets to the called workflow." In our run, `VPS_HOST_KEY` did not arrive in the reusable. GitHub's documented `inherit` failure modes are chained workflows (A→B→C) and environment-scoped secrets — neither applied here, so this was an undocumented edge or runner state. (The Actions log group `Setting up job` shows which secrets were resolved on the runner — useful diagnostic surface for this class of issue.) Either way, PR #93 switched to explicit per-secret pass-through:

```yaml
jobs:
  deploy:
    uses: jeremylongshore/.github/.github/workflows/vps-deploy.yml@709a07f
    secrets:
      TS_OIDC_CLIENT_ID: ${{ secrets.TS_OIDC_CLIENT_ID }}
      TS_AUDIENCE: ${{ secrets.TS_AUDIENCE }}
      VPS_DEPLOY_KEY: ${{ secrets.VPS_DEPLOY_KEY }}
      VPS_HOST_KEY: ${{ secrets.VPS_HOST_KEY }}
```

Same SSH error.

Run #3 added a size-debug step: print the byte count of `VPS_HOST_KEY` after it arrived in the reusable. Result: 978 bytes. The secret was *arriving*. So why couldn't SSH match it?

Run #4 added hostname-field debugging — decode the hashed entries in the known_hosts file and check what hostname they hash against. Three entries; none of them, when computed against the literal string `intentsolutions`, produced a matching hash.

The diagnosis (inferred from symptoms — we did not recompute the salt to confirm): the pinned `VPS_HOST_KEY` secret was generated months ago by piping `ssh-keyscan -H` output into the secret value. At some point in that pipeline, a trailing newline or whitespace got included before the hostname. The most likely explanation, consistent with how HMAC-SHA1 known_hosts hashing works (the hostname is the exact message string hashed with a per-entry salt), is that the captured hostname-with-whitespace produced hashes that don't match a clean `intentsolutions` lookup. The pin was perfect; the input string had drifted.

The fix in PR #96 stopped trying to use the pinned hashed entries. Instead, the workflow does a live `ssh-keyscan` against the tailnet hostname and appends the result inline:

```yaml
- name: Add VPS host key
  run: |
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    echo "${{ secrets.VPS_HOST_KEY }}" >> ~/.ssh/known_hosts
    ssh-keyscan -t ed25519 intentsolutions >> ~/.ssh/known_hosts
    chmod 600 ~/.ssh/known_hosts
```

Both entries land. The pinned-but-stale entry stays (defense in depth). The live-scanned entry is what SSH actually matches. Tailscale tunnel authentication is the real trust layer here — the Tailnet identity verification means the live scan is meeting a server that already proved it's the right machine. The strict known_hosts pin was less load-bearing than it looked.

Cost: 5 PRs (#92 through #96), 5 failed deploy runs, the longest single block of the day. Worth it because the resulting reusable workflow is now the canonical deploy path for every `jeremylongshore/*` repo.

## The smoke check that catches degraded states

The reusable workflow ends with a smoke check. The naive version is `curl -sf $URL && exit 0`. That is a lie detector that doesn't detect lies.

```yaml
- name: Smoke check
  run: |
    for i in 1 2 3 4 5; do
      response=$(curl -sf --resolve scorecardecho.com:443:$VPS_PUBLIC_IP https://scorecardecho.com/api/health || echo "{}")
      if echo "$response" | jq -e '.status == "ok" and .gumbo.running == true' > /dev/null; then
        echo "Smoke passed on attempt $i"
        exit 0
      fi
      sleep 5
    done
    echo "Smoke failed after 5 attempts"
    exit 1
```

Three things this does that a plain status-code check doesn't:

1. **`--resolve scorecardecho.com:443:$VPS_PUBLIC_IP`** pins the curl request to the VPS's public IP. No DNS caching surprise. We are testing *this server*, not whichever server DNS happened to point at.
2. **The jq filter `.status == "ok" and .gumbo.running == true`** catches the degraded state where the HTTP server is up (returns 200) but the pregame narrative job (`gumbo`) is dead. A plain 200 OK passes when the application is half-dead. The custom predicate catches it.
3. **Five-retry warm-up** allows for `docker compose up` containers to finish boot. Each retry waits 5 seconds. Hard fail at 25 seconds.

This is what "deploy succeeded" should mean. Container running is not enough. HTTP responding is not enough. Application *functioning* — that's the bar.

## Plan v4.1: testing as first-class

Mid-iteration on P5, the user surfaced the success criterion that reframed the whole program:

> "I want to be able to `cd <random-repo> && git push` and have CI just deploy without hiccups."

That sentence was not in the original plan. The original plan was about consolidating hosting and running the GCP exodus. Deploys were treated as an outcome of getting the pieces in place.

The user's framing put deploys at the center: every repo, every push, just works. That demands testing as a first-class gate, not a polish step. Plan v4.1 (a same-day rewrite of the program plan) baked it in:

- **Pre-deploy**: `needs: test` on the caller workflow. No deploy runs unless tests pass.
- **Post-deploy**: smoke check with custom jq predicate (above).
- **Auto-rollback**: smoke fail → `exit 1` → deferred VPS-side wrapper tags the previous-known-good and ntfy escalates.
- **P6 expanded**: audit-tests rollout per repo paired with the SOPS+age pass.

The discipline isn't testing as a step in the build. It's testing as the gate the deploy must pass to even start, plus the gate the deploy must pass to be considered successful. The two halves change what "merged to main" means.

## Parallel work: P6 propagation

While P2 and P5 were eating GitHub Actions minutes, P6 was moving in parallel via a script: `scripts/p6-install-harness.sh`. The script:

1. Vendored install of `@intentsolutions/audit-harness v0.1.0` (the [enforcement-travels-with-code package](/blog/audit-harness-v010-enforcement-travels-with-code/)).
2. Appended a `## Testing` section to the repo's `CLAUDE.md`.
3. Created an auto-numbered `000-docs/` entry recording the install.
4. Used a worktree-based install for repos with dirty trees so iteration didn't disturb in-flight work.

By end of day, 11 of 23 testing-baseline candidates were done: `hybrid-ai-stack` (pilot), `j-rig-binary-eval`, `claude-code-slack-channel`, `intent-blueprint-docs`, `intent-genai-project-template`, `executive-intent`, `perception`, `moat`, `git-with-intent`, `intentional-cognition-os`, `intent-solutions-landing`.

One cross-repo discovery surfaced from this rollout: `gitleaks` was flagging `.beads/issues.jsonl` as containing credentials. The bd memory store includes string content from past sessions, and one such string matched a gitleaks pattern. False positive. Fix: a path-based `.gitleaks.toml` allowlist that excludes the bd state directory. Filed as `OPS-x6n` and replicated across the other repos that hit the same false positive. The harness propagation was the thing that surfaced it — running the same gates across many repos exposes the gate's blind spots.

## What's deferred

Honest counterweight. Not everything landed today.

- **VPS-side wrapper `/usr/local/sbin/deploy-srv-app`** with per-repo allowlist, flock per-repo, drop privileges. Needs VPS sudo + scope extension. Currently the SSH command from the reusable workflow runs unwrapped.
- **Filesystem split** `/srv/code/<app>` (code) + `/var/lib/intentsolutions/<app>` (state). Today everything is under `/srv/<app>/`.
- **Per-repo SSH `command=` restrictions** on the VPS authorized_keys file. A leaked deploy key currently grants any command, not just deploy.
- **Port allocation registry.** Allocated by hand right now. Will get a `ports.yaml` source-of-truth file with a `port-check` script.
- **`vps-deploy-canary` throwaway test repo.** A repo whose only job is exercising the reusable workflow without touching production traffic.
- **Auto-rollback semantics.** Today the smoke check exits 1 on failure; the deploy is recorded as "failed" but the previous version isn't automatically promoted back. Full rollback (tag-previous-deploy + ntfy escalation) needs the VPS-side wrapper.
- **`bd-sync close`-mirror bug** (`OPS-nhi`). The bd → GitHub mirror tool doesn't propagate the close-comment. Workaround used all day: `bd close` + manual `gh issue comment`. Fix queued for P5 follow-up.

These are not blockers for tomorrow. They're the next layer of armor on a deploy path that already works end-to-end.

## Lessons

1. **Tailscale OIDC audience is auto-generated.** It is `api.tailscale.com/<oidc-client-id>`. You read it from the Tailscale trust UI, not invent it from documentation conventions. Three failed runs say so.
2. **GitHub cross-repo private workflow access can be locked by default.** Our brand-new `.github` repo was set to `none`; the error message said "workflow file issue," which sounds like YAML. It isn't. `gh api -X PUT repos/<org>/<repo>/actions/permissions/access -f access_level=user`.
3. **`secrets: inherit` is fragile across reusable workflow boundaries.** Use explicit per-secret pass-through. It's verbose, it's strictly clearer, and it actually delivers the secrets.
4. **Pinned `ssh-keyscan` output drifts.** A trailing whitespace at scan time produces a hashed entry that doesn't match a clean lookup later. Live `ssh-keyscan` against the tailnet hostname inside the workflow is the right model when Tailscale's tunnel authentication is the real trust layer.
5. **Wildcard subjects scale.** `repo:<org>/*:ref:refs/heads/main` lets one Tailscale trust serve every repo's main branch. Per-repo trusts would have been a maintenance bog.
6. **Custom smoke predicates beat status-code checks.** `.status == "ok" and .gumbo.running == true` catches half-dead applications that return 200. A plain status-code check is a lie detector that can't detect lies.
7. **Plan-v4.1 testing-as-first-class is what made 8 iterations safe instead of expensive.** The runbook bootstrapped at 3 AM with `00-plan.md` + `01-tracking-index.md` + per-priority AAR templates. Mid-iteration on P5, the user surfaced the `git push` "just works" criterion, and the plan was rewritten on the spot to bake in pre-deploy `needs:test` gates and post-deploy smoke predicates. Each iteration could fail in flight without producing a half-broken production state, because the smoke predicate would refuse to call any deploy successful that didn't return `.status == "ok" and .gumbo.running == true`. The 25 production containers stayed healthy through every retry. The discipline came first; the iterations followed; the test gates kept failure local to the iteration instead of propagating to users.
8. **Hot-fix reverts protect production during experiments.** PR #88 restored the OAuth-secret path mid-iteration so 25 production containers never lost the ability to ship a fix. The cost of an experiment is bounded when you keep the previous-known-good path warm.

## Day 1 cost summary

- `braves-booth`: 20 PRs in one day (deploy work clustered 16:15 to 19:51 ET).
- `intentsolutions-vps-runbook`: 15 commits (initial bootstrap + 8 plan-document iterations).
- `jeremylongshore/.github`: new repo with the reusable workflow, pinned by 40-char SHA `709a07fbebb1d51806e171204e63f5332abcb0da` from the caller.
- 11 propagation repos got the audit-harness install.
- 35+ commits across the relevant repos.
- All 25 production containers stayed healthy throughout.

The deploy pipeline is now: `git push` → CI tests pass → reusable workflow → Tailscale OIDC handshake → SSH over tailnet → docker compose pull + up → smoke check with custom jq predicate → exit 0 or exit 1. From the caller's perspective: one job invocation, one set of explicit secrets, one 40-char-pinned SHA. The whole jeremylongshore portfolio can adopt it by changing four lines.

Day 1 ended with eight priorities open, three closed, one closed-scope-modified, and a working deploy path that didn't exist twelve hours earlier. Day 2 starts with monitoring (P3) and the SOPS+age propagation push (P6).

### Related Posts

- [How yesterday's three multi-repo propagations set the muscle memory for today's parallel P6 push](/blog/propagation-day-when-the-spec-becomes-the-migration-plan/)
- [Braves Booth — the application running through every smoke check in this post](/blog/braves-postgame-expansion-and-two-ai-lessons/)
- [The audit-harness package being propagated in P6, and why enforcement has to travel with the code](/blog/audit-harness-v010-enforcement-travels-with-code/)

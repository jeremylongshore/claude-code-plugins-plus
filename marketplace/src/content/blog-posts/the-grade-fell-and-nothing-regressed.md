---
title: "Contract Tests Caught a 25 MiB Upload Truncation Reported as HTTP 201"
description: "Recorded-fixture contract tests found an upload truncated at 25 MiB and recorded as HTTP 201. The audit grade fell to B+ while coverage rose to 99.67%."
date: "2026-09-02"
tags: ["testing", "ci-cd", "devops", "typescript", "release-engineering"]
featured: false
canonical: "https://startaitools.com/posts/the-grade-fell-and-nothing-regressed/"
---
I ran `/audit-tests` on intent-longbox v0.3.1 and got B+: 84 out of 100. The previous audit was A-, 90 out of 100. Line coverage improved from 99.56% to 99.67%. Unit test count jumped from 92 to 118. Integration tests stayed 14 of 14 green against postgres:16. That is not a regression.

The grade fell because the service/api layer matrix, applied strictly this pass, classified two missing layers as P0 instead of P2. Layer 5 security scanning did not exist (no gitleaks, pnpm audit, osv, CodeQL, Semgrep). Layer 4 contract testing did not exist (four external API seams were exercised only against hand-written stubs). Both gaps were real.

Most of it landed in one commit, `37441a7`: both missing layers plus five of the six other findings.

## L5 security scanning: gitleaks and pnpm audit

I chose gitleaks for secrets scanning plus pnpm audit for dependency vulnerabilities. CodeQL was not an option for a private repo without Advanced Security provisioned. For contract testing I chose recorded-fixture tests over Pact, because the counterparties (Shopify Admin GraphQL, PriceCharting, eBay Browse OAuth, and an LLM seam) cannot be co-authored into a contract. They are third-party APIs that live outside the repo and outside any contract boundary.

The first commit added gitleaks-action and upgraded @fastify/static past a high advisory to 10.1.3. The security lane then failed on its own PR twice. First: 403 on commit listing. The action needed pull-request read scope (PR comments disabled so write scope is never needed). Added the scope. Second: the contract tests' fixture credentials (test `shpat_` Shopify tokens, `sk-ant-` keys, client secrets) pattern-matched real credentials and tripped the scanner. Commit `9733c27` addressed both issues at once: added the gitleaks scope, upgraded @fastify/static to 10.1.3, renamed fixture credentials to `test-*` values, and added a scoped `.gitleaks.toml` allowlist exempting only the scaffolding commit. Commit `08f8c8a` fixed the allowlist: it was written with a 7-character short SHA, but gitleaks matches on the full 40-character hash. One line fixed it. Verified locally with gitleaks in git mode: exit 0, zero findings.

## L4 contract tests: fixtures, not mocks

The test suite covers four external API seams. All are third-party endpoints that cannot be brokered into Pact. Shopify Admin GraphQL. PriceCharting REST. eBay Browse API plus OAuth. An LLM endpoint compatible with Anthropic or OpenAI. Each test exercises its seam through recorded fixtures: actual request and response payloads saved to disk, parsed and re-served on every run.

The first run found a real bug immediately. An oversize photo upload was truncated at 25 MiB and recorded as HTTP 201 (success). Pinned as `it.fails` and filed as a bead deliberately not fixed inside a test PR. The test caught the behavior, the commit records the catch, and a separate issue tracks the repair.

After those fixes: unit tests 162 of 162 (up from 118), integration 22 of 22 against postgres:16, lint green, prettier green, typecheck green. The harness re-pinned, `verify` OK, escape-scan reporting 0 refuse, 0 challenge, 0 flag.

One more thing stayed open alongside branch protection. The advisory review workflow is wired but asleep until the `MINIMAX_API_KEY` secret and the `ENABLE_MINIMAX_REVIEW` variable exist on the repo. A workflow that cannot authenticate is not a review lane, so it is recorded as unfinished rather than counted as shipped.

## The other P1 findings

The audit raised six more findings. Five were fixed in `37441a7`. The sixth needs an owner with admin rights and is still open.

**Branch protection was absent.** `gh api repos/.../branches/main/protection` returned 404. The blocking CI jobs were not required server-side and the pre-commit chain was bypassable with `--no-verify`. That one is not a code change. It is still open, recorded as an owner action.

**GitHub Actions on floating tags.** Eleven uses of `actions/checkout@v4` and `actions/setup-node@v4` across the workflow suite. SHA-pinned all 11.

**Harness jobs set continue-on-error.** The `verify` and `escape-scan` jobs had `continue-on-error: true`, which silences failures. Promoted both to blocking.

**Release readiness never failed.** `release.yml` ran `npm test || true` in its readiness step. The `|| true` means a test failure cannot stop the release, ever. Removed the conditional.

**Dependabot missing npm.** `.github/dependabot.yml` declared `github-actions` and `pip` ecosystems but not `npm`. The pnpm dependency tree received no Dependabot security PRs. Added npm to the config.

**Skip-not-fail on database unreachable.** `probeDb()` returning false fed `describe.skipIf`, so an unreachable database in CI produced a green job that ran zero tests. Changed to `CI=1` with no database now errors instead of skipping. A skipped integration test is not a passed test.

## Materializing the bead graph

Intent-longbox v0.3.1 needed structured task planning for the next phase. One master epic, 20 child epics, 202 grandchild beads, 223 total records, 720 blocking edges, zero cycles, zero dangling nodes. Materialized over two commits because the house rule forbids bulk-scripted bead graphs. First commit filed the blueprint and materialized the master epic plus E00 through E05 and their 56 children. Second commit materialized E06 through E19 and closed the graph at 223 records.

Aliases live in metadata, never title-prefixed, because naming forbids code prefixes in bead titles. Verified with awk and python: 223 unique aliases, 223 unique IDs, parent integrity, cycle and edge checks all passed. `bd ready` resolved to exactly one ready leaf, which is what a correctly closed dependency graph should do on a project that has not started building yet.

## Subagent assignments

Six builders, each mapped to an epic cluster: domain, security and tenancy, mobile, resolution AI, valuation and commerce, platform and delivery. Plus two auditors: invariant reviewer for code and test beads, gate auditor for decision, contract and gate beads. All eight pass `/validate-agent` with zero errors. All 224 bead records carry `lbox.agent.build` and `lbox.agent.audit` metadata.

Two placement decisions, both about where a rule should live. The agents are repo-local under `.claude/agents` rather than global under `~/.claude`, so the assignments travel with the code and a fresh clone gets them. The assignment itself is metadata rather than a label, because labels in this estate are reserved for plain-English topic words and overloading them would make the label set unreadable.

## Secondary work

Startaitools landed the previous day's post and its social assets, and the release workflow auto-cut v1.17.3. The version bump was clean and the changelog was updated. Comehomealabama published one property journal entry through its own producer and lander pipeline. Both followed their normal automation paths.

## Collaboration

Claude Fable 5 drove intent-longbox. Claude Opus 5, Claude Sonnet 5, Claude Opus 4.8, and GPT 5.6 Luna shared home and secondary. Fable 5 handled the gitleaks loops: first fix added scope and updated dependencies. Second fix corrected the allowlist SHA. Three commits total to pass the security lane on its own PR.

## Related Posts

- [A green result only covers what it ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [Barcode first, vision model second](https://startaitools.com/posts/barcode-first-vision-model-second/)
- [One corrected check, fifteen repos](https://startaitools.com/posts/one-corrected-check-fifteen-repos/)

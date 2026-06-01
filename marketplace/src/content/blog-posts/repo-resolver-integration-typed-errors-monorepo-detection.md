---
title: "Repo-Resolver: Typed Errors and Monorepo Detection"
description: "A shared repo-resolver package shipped into claude-runtime — ADR to integration in seven PRs, with typed error classes and transparent fallback that avoided a flag day."
date: "2026-04-14"
tags: ["typescript", "architecture", "monorepo", "claude-code", "ai-agents", "automation"]
featured: false
---
Three different services in the qmd-team-intent-kb stack all need to answer the same question: "what repo is this?" The edge-daemon needs it at spool time to tag captured memory candidates. The MCP server needs it at query time to scope retrieval. The ingestion pipeline needs it at index time to build canonical tenant partitions. Before April 14, each of them had its own half-answer — `resolveGitContext()` variants with different edge-case handling, different caching strategies, and a long tail of bugs around SSH vs HTTPS remotes and monorepo roots.

Today the work of consolidating that into a proper shared package landed. `@qmd-team-intent-kb/repo-resolver` went from an ADR (PR #33) to full runtime integration in `claude-runtime` (PR #43) in seven merged PRs, all on the same day. The design-rationale call I want to unpack is the one that enabled shipping #43 without a flag day: typed error classes plus a transparent fallback to the legacy resolver. The runtime never had to pick a side.

## The Repo-Resolver Arc

Six PRs, in order of merge:

- **#33 — ADR.** Why a new package exists, what it owns, and what it explicitly does not own (no network I/O, no commit-graph traversal, no LFS awareness).
- **#35 — Core `resolveRepoContext()` entry point.** One function, one return shape, no overloads. The rest of the package is supporting detail.
- **#36 — Tenant ID derivation + remote URL normalization.** 295 insertions across 3 files. Test file alone was 178 lines because the normalization matrix is wide: SSH, HTTPS, bare-git, self-hosted instances all have to collapse to the same canonical tenant ID.
- **#37 — Monorepo detection.** pnpm, npm workspaces, Nx, Turborepo, Lerna. 125 lines of detection logic, 178 lines of tests across 6 fixture repos.
- **#38 — Process-local TTL cache.** Deliberately not Redis.
- **#40 — Gemini review feedback on #35.** Addressing automated code review comments before integration.
- **#43 — Runtime integration.** `claude-runtime`'s `DefaultContextProvider` swaps in `resolveRepoContext()`. 227 insertions across 8 files, with 159 new lines in `context-provider.test.ts` and 39 more in `candidate-builder.test.ts`.

The order matters. The ADR came first for a reason that I'll get to. The runtime integration came last because everything else had to exist before it could land cleanly.

Two adjacent PRs shipped the same day and are worth naming: **#34** (brought the repo into the shared `wild-ecosystem` GCP project so CI had the right service accounts) and **#42** (edge-daemon CLI subcommand dispatcher — `start`/`stop`/`status`/`run-once` replacing monolithic argv flag checking in `main.ts`, with 126 lines of dispatcher and 185 lines of tests).

## Why a Separate Package

The three consumers problem forced the hand. If `resolveRepoContext()` lives inside edge-daemon, then the MCP server has to reach across module boundaries to get it — or worse, reimplement it. If it lives inside a "common" utility module that already pulls in unrelated things, then every consumer pays the transitive dependency tax.

The cost of guessing wrong on the contract mid-implementation is the thing the ADR was optimizing against. Three integrations, each a week of work to unwind if the shape changes. Cheap to think hard for an afternoon before PR #35; expensive to re-shape after three consumers depend on it.

So: separate package, minimal surface, explicit non-goals. The ADR enumerated what repo-resolver does not do — no git fetch, no remote introspection, no credential handling. That list of non-goals is what keeps the package small enough to be worth depending on.

## Why Not Just Read the Git Remote?

The obvious approach is: `git config --get remote.origin.url`, parse it, done. This does not work, and here is why not.

First, the same logical repo has many valid remote URLs. `git@github.com:org/repo.git`, `https://github.com/org/repo`, `https://github.com/org/repo.git`, `ssh://git@github.com:22/org/repo.git` — all the same tenant. If you treat the raw URL as the identifier, every contributor who cloned over a different protocol gets a different tenant ID and their captured memory candidates scatter across what should be one partition.

Second, `origin` is not guaranteed. Forks have `upstream`. Some workflows push to `deploy`. A freshly-initialized repo with no remote set at all still needs a stable identifier while the developer is iterating locally.

Third, monorepos break the one-repo-one-tenant assumption from a different direction. If the developer is working inside `packages/foo/` of a pnpm workspace, the interesting unit for scoping memory might be the workspace root, or the package, or both — but you cannot figure that out from the remote URL alone.

So repo-resolver derives the tenant ID from a normalized form of the remote (PR #36), falls back to a content-hash of the initial commit when no remote exists, and separately records the monorepo root and the package subpath when detected (PR #37). Three outputs from one entry point, each with defined fallbacks.

## Monorepo Detection Without Guessing

```typescript
function detectMonorepo(root: string): MonorepoKind | null {
  if (hasPnpmWorkspaceFile(root)) return 'pnpm';
  if (hasNpmWorkspacesField(root)) return 'npm';
  if (hasNxJson(root) && hasWorkspacesConfig(root)) return 'nx';
  if (hasTurboJson(root)) return 'turbo';
  if (hasLernaJson(root)) return 'lerna';
  return null;
}
```

The order is not alphabetical — it reflects specificity. pnpm's `pnpm-workspace.yaml` is unambiguous; it exists exactly when the repo is a pnpm workspace. npm's `"workspaces"` field inside `package.json` is the second-most specific. Nx comes third and requires both `nx.json` and a workspace configuration, because Nx also supports non-workspace single-app projects. Turborepo and Lerna come last because their presence is weaker evidence.

Three edge cases the fixture tests encode:

1. **Turbo without a monorepo.** A single-app project using `turbo.json` for incremental build caching. Running with this config alone means "not actually a monorepo" — so Turbo detection only triggers when `turbo.json` is present and no stronger signal above it fires.
2. **Nx without workspaces.** A standalone Nx project with `nx.json` but no `workspaces` field. The `&& hasWorkspacesConfig(root)` in the third check exists for exactly this.
3. **Nested monorepos.** A repo with a subdirectory that also has its own `pnpm-workspace.yaml`. The resolver walks upward and takes the outermost workspace root as definitive. The nested config is a mistake we do not try to second-guess, but we also do not let it shadow the real root.

No heuristic is perfect. But `detectMonorepo` returning `null` is an acceptable answer — consumers treat it as "single-package repo" and move on. The cost of a wrong classification is higher than the cost of an honest unknown.

## Tenant ID Derivation Is Not URL Parsing

PR #36 is the one I expected to be small and was not. 295 insertions, 178 lines of tests, because every remote URL shape is its own wrinkle:

- `git@github.com:org/repo.git` — SSH scp-style, no `ssh://` prefix, colon-delimited path
- `ssh://git@github.com/org/repo.git` — real ssh:// URL
- `https://github.com/org/repo.git` — HTTPS with `.git`
- `https://github.com/org/repo` — HTTPS without `.git`
- `https://user@github.com/org/repo` — HTTPS with username in userinfo
- `git://github.com/org/repo.git` — legacy git protocol
- `https://gitlab.self-hosted.corp/group/subgroup/repo.git` — self-hosted with nested groups
- ` — local file remotes (yes, people do this)

Normalization collapses all of these to a form like `host/path`, lowercase, trailing `.git` stripped, query and fragment discarded, userinfo discarded. The tenant ID is a hash of that canonical string. Same logical repo, same tenant, regardless of how the contributor happened to clone.

The alternative — storing the raw remote URL and trying to canonicalize at query time — was considered and rejected. Canonicalization is lossy by definition; doing it once at capture and hashing the result means every downstream consumer agrees by construction, not by convention.

## The Cache Is Process-Local on Purpose

PR #38 added a TTL cache. The obvious reach is Redis. The deliberate choice was process-local.

Why: repo context changes on events that already restart the daemon. A new `git commit` does not invalidate the tenant ID or the monorepo structure. A `git remote set-url` does — and the developer will bounce the daemon, because changing a remote URL is not a silent background event. The only real drift between cache and truth is during active development of the resolver itself, which is a bounded scenario.

A shared Redis cache would buy approximately zero hit-rate improvement in the realistic access pattern (one daemon per developer machine) and add a whole class of staleness bugs. Process-local with a conservative TTL is correct for the actual workload.

## Integration Without Surprises

PR #43 is the payoff. `DefaultContextProvider` in `claude-runtime` previously had a stub pass-through that called the legacy `resolveGitContext()`. The new code tries `resolveRepoContext()` first and falls back transparently:

```typescript
try {
  const resolved = await resolveRepoContext(cwd);
  return enrichGitContext(resolved);
} catch (err) {
  if (
    err instanceof NotAGitRepo ||
    err instanceof GitUnavailable ||
    err instanceof NoCommits ||
    err instanceof BareRepo ||
    err instanceof Io
  ) {
    return resolveGitContext(cwd); // legacy path
  }
  throw err;
}
```

Five typed error classes — `NotAGitRepo`, `GitUnavailable`, `NoCommits`, `BareRepo`, `Io` — each carry a specific failure mode. The integration code catches exactly those and falls back. Any other error is a programming bug and rethrows.

This is the "without a flag day" part. No feature flag, no env var, no staged rollout. If the resolver works, you get the enriched context (`repoName`, `commitSha`, canonical tenant). If it fails for any known reason, you get the old behavior. The typed errors make the fallback predicate legible — there is no `catch (e) { return fallback(); }` that silently swallows real bugs.

Test-footprint-to-behavior-change ratio: 227 insertions, 198 of them in test files. `context-provider.test.ts` got 159 new lines covering every error class and the enrichment path. `candidate-builder.test.ts` got 39 lines for the `projectContext` default-to-canonical-name behavior. The ratio of tests to production code was not an accident — integration points into the runtime are exactly where stealth regressions hide.

## Also Shipped

**claude-code-plugins** cut v4.25.0. The headline was Shopify Skill Pack v2.0 — 38 skills now with references-extraction, which was the gap that had kept Shopify out of the top tier. Marketplace is at 430 plugins and 2,838 skills. Cowork plugin got a fix: it was referencing a `stripe-pack` that did not exist, which has been swapped for `clerk-pack`. SaaS packs now render as individual marketplace cards rather than collapsing into a category group.

**xireactor** tagged v0.2.1 and picked up the "Brilliant" rebrand. The immediate bug fix was `demo_e2e.sh` which had drifted off the current API contract. RLS-denied writes now return 403 instead of 500 — the old behavior made permission errors look like server faults. Upstream sync brought in 4-tier governance, entry-links write path, permissions v2, comments, and render. The `main`/`dev` branching convention got documented because the repo had quietly switched to a two-branch model without telling anyone.

**braves** (the broadcast dashboard) shipped two small quality-of-life fixes that mattered more than the size suggests. Player surname suffix strip now handles Jr./Sr./II/III so the lineup card displays "Acuña" not "Acuña Jr." in the space-constrained slots. Pregame storylines now persist to SQLite, which means the dashboard survives a restart during broadcast — previously a kernel upgrade or power blip wiped the show's prep. CLAUDE.md got rewritten from the old cloud-deployment assumptions to the local-first deployment model the project actually uses now.

## The Shape of the Day

Nine merged PRs across four repos, all converging on the same theme: make the contract explicit, then integrate. The repo-resolver arc in qmd-team-intent-kb is the clearest example — ADR first, core implementation second, normalization and detection third, integration last, with typed errors absorbing the risk of the integration step. But the pattern repeats. The xireactor branching model got documented after the fact because the implicit convention was causing drift. The braves CLAUDE.md got rewritten because the documented deployment model was a lie. Shopify Skill Pack v2.0 added references-extraction because the implicit "skills have references" assumption was only explicit for some packs.

Every one of these is the same move: take something that was working by convention and make it work by contract. The repo-resolver just happened to be the one that earned its own package.

## Related Posts

- [Twelve PRs, a Security Sprint, and a Pregame Overhaul](/blog/twelve-prs-security-sprint-pregame-overhaul/)
- [Zero to CI: Full-Stack Dashboard, One Session](/blog/zero-to-ci-full-stack-dashboard-one-session/)
- [Wild Deep Dive #3: Observability](/blog/wild-deep-dive-3-observability/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Repo-Resolver: Typed Errors and Monorepo Detection",
  "description": "A shared repo-resolver package shipped into claude-runtime — ADR to integration in seven PRs, with typed error classes and transparent fallback that avoided a flag day.",
  "datePublished": "2026-04-14T10:00:00-05:00",
  "dateModified": "2026-04-14T10:00:00-05:00",
  "author": {"@type": "Person", "name": "Jeremy Longshore", "url": "https://startaitools.com/about/"},
  "publisher": {"@type": "Organization", "name": "Intent Solutions", "url": "https://startaitools.com"},
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://startaitools.com/posts/repo-resolver-integration-typed-errors-monorepo-detection/"},
  "keywords": "typescript, architecture, monorepo, claude-code, ai-agents, automation, repo-resolver"
}
</script>

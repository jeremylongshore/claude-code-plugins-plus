---
title: "Repo-Resolver in a Day: ADR, Core, Cache, Monorepo Detection, Integration"
description: "A multi-repo context-resolution module shipped start-to-finish in a single day — ADR through runtime integration, with monorepo detection, tenant ID derivation, and a TTL cache. Plus Shopify Skill Pack v2.0 and edge-daemon dispatcher maturity."
date: "2026-04-14"
tags: ["typescript", "architecture", "monorepo", "claude-code", "ai-agents", "automation"]
featured: false
---
One module. Six PRs. ADR to integration in a single push window.

The `repo-resolver` package inside `qmd-team-intent-kb` went from a decision record to runtime integration between morning coffee and end-of-day push on April 14. That alone would be the story — but in parallel, claude-code-plugins cut v4.25.0 and shipped a 38-skill Shopify pack, the edge-daemon grew a CLI subcommand dispatcher, and xireactor did a brand refresh plus an upstream sync that landed a 4-tier governance model.

This post is about what that kind of day looks like when you can see every step in the git log.

## The Repo-Resolver Arc

The daemon needs to know *which repo* a candidate came from, *which tenant* owns it, and *what kind of workspace* it lives in. Monorepo? Standalone? pnpm? Nx? The runtime had been stubbing all of this. Six merged PRs, in order:

- **#33** — ADR for the multi-repo context package. Why a new package, why not extend an existing one, how it composes with the edge-daemon capture layer.
- **#35** — Core `resolveRepoContext()` implementation. The single entry point.
- **#36** — Tenant ID derivation plus remote URL normalization.
- **#37** — Monorepo detection across pnpm, npm, Nx, Turborepo, and Lerna.
- **#38** — Process-local cache with a TTL so repeated resolutions don't re-hit the filesystem.
- **#43** — Runtime integration: `claude-runtime` now enriches every captured candidate with resolved repo context.

Plus #40 addressing Gemini review feedback on #35, and #34 bringing the repo into the wild-ecosystem shared GCP project for CI.

That's the story in commits. The story in code is a little more interesting.

## Why a Separate Package

The ADR made the case that repo context belongs to its own package rather than living inside `claude-runtime` or `edge-daemon`. The reasoning came down to three points: the edge-daemon needs it at spool time, the MCP server needs it at query time, and the ingestion pipeline needs it at index time. Three consumers, three different call sites, one shared resolution contract.

Putting it inside any one consumer would have forced the other two to reach across module boundaries. Putting it inside a shared package let each consumer depend on it cleanly.

That decision is easy to describe. It was worth writing an ADR because the cost of guessing wrong — discovering mid-implementation that two consumers actually need different contracts — would have meant unwinding all three integrations.

## Why Not Just Read the Git Remote?

The obvious alternative to a resolver package is calling `git config --get remote.origin.url` from each consumer and parsing the result. Two problems.

First, that pushes context inference into every consumer. The edge-daemon would have a parser, the MCP server would have a parser, the runtime would have a parser. Three parsers, three subtly different normalizations, three places where a repo URL drift would cause silent tenant mismatches.

Second, git remote alone doesn't tell you monorepo shape. A repo at `/home/user/org/monorepo/apps/web` has a git remote on the root, not the app. Consumers would each have to walk up the tree, check for workspace files, and reconcile "what is my workspace root" separately. The resolver encapsulates that walk once and returns a structured answer.

Centralizing this logic also means Gemini's review of `#35` improved all three consumers at once instead of three separate reviews across three separate PRs.

## Monorepo Detection Without Guessing

The monorepo detection (`#37`) is the piece with the most subtlety. The detection file is ~125 lines. The test file is ~178 lines with fixtures covering pnpm workspaces, npm workspaces, Nx, Turborepo, Lerna, nested monorepos, and plain single-package repos.

The detection isn't pattern-matching on filenames alone. It's structural:

```typescript
// Rough shape, not the exact code
function detectMonorepo(root: string): MonorepoKind | null {
  if (hasPnpmWorkspaceFile(root)) return 'pnpm';
  if (hasNpmWorkspacesField(root)) return 'npm';
  if (hasNxJson(root) && hasWorkspacesConfig(root)) return 'nx';
  if (hasTurboJson(root)) return 'turbo';
  if (hasLernaJson(root)) return 'lerna';
  return null;
}
```

The tricky cases: a package can have `turbo.json` without being a proper monorepo (someone using Turbo for incremental builds on a single app), and an Nx workspace without the `workspaces` field is a standalone Nx project, not a workspaces-style monorepo. The test fixtures encode all of this so regressions are caught the moment someone changes the heuristics.

Nested monorepos are another edge case the fixtures cover. A repo that contains a subdirectory with its own `pnpm-workspace.yaml` could be either a broken nested setup or an intentional sub-workspace. The resolver chooses the outermost workspace root as the definitive one — the inner one is treated as a package within the outer workspace. That matches how every tool in the ecosystem actually interprets these layouts, but only after the fixtures forced the choice.

## Tenant ID Derivation Is Not URL Parsing

The tenant-ID code (`#36`) looked trivial on the surface — grab the `origin` remote, parse the org out of it. It is not. Remote URLs come in at least four flavors: `git@github.com:org/repo.git`, `https://github.com/org/repo.git`, `https://github.com/org/repo`, and `git://github.com/org/repo.git`. Plus self-hosted instances where the host isn't `github.com` at all. Plus the zero-remote case where a repo was never pushed.

The implementation normalizes all of that into a canonical `{host, org, repo}` shape first, then derives the tenant ID from the host-plus-org. Without normalization, two identical repos accessed via HTTPS and SSH would produce different tenant IDs, and the daemon's repo-scoped filters would fail silently.

## The Cache Is Process-Local on Purpose

The TTL cache (`#38`) is not a Redis cache. It is not persisted. It lives in-process and dies when the process dies.

That is the right call because repo context only changes when someone renames the repo, moves the remote, or changes the workspace type — all operations that restart the daemon anyway. A distributed cache would add operational complexity to solve a problem the design already eliminates.

A typical daemon cycle resolves the same handful of repo roots dozens of times. The cache turns those dozens of filesystem walks into one walk plus dozens of map lookups. That is the whole benefit.

## Integration Without Surprises

The runtime integration PR (`#43`) was 227 lines across eight files. Most of that was tests — `context-provider.test.ts` got 159 new lines of coverage for the enrichment paths. The behavioral change was single-digit lines in `candidate-builder.ts` and `context-provider.ts`.

That ratio — small behavior change, large test footprint — is the thing you want when you're wiring a new module into a daemon that other systems depend on. The tests exist to prevent regressions, not to document the change.

## Also Shipped

The edge-daemon got a CLI subcommand dispatcher (`#42`, bz-1x6.2) with `start`, `stop`, `status`, and `run-once` subcommands — 126 lines of dispatcher logic plus 185 lines of tests. This replaces a monolithic `main.ts` entry point that had been checking argv flags manually.

Eleven dependency bumps landed the same day, including `@modelcontextprotocol/sdk` 1.27.1 → 1.29.0, `better-sqlite3` 11.10.0 → 12.8.0 (a major bump with its own 468-line lockfile churn), and a one-off lockfile regeneration (`#41`) to remove duplicate keys from an earlier merge.

**claude-code-plugins** cut v4.25.0 and published the **Shopify Skill Pack v2.0** — 38 skills with references extraction, part of a marketplace that now indexes 430 plugins and 2,838 skills. The cowork plugin also swapped its stripe-pack reference for the actual clerk-pack and started rendering SaaS packs as individual cards instead of a stacked list.

**xireactor** shipped v0.2.1 alongside a larger "Brilliant" rebrand. Key changes: the `demo_e2e.sh` script had drifted from the current API contract and was quietly fixed, RLS-denied writes now return `403` instead of `500` (a caller-contract bug more than a security bug), the CONTRIBUTING doc now documents the main/dev branching model, and an upstream sync landed the 4-tier governance model plus an entry-links write path, permissions v2, comments, and render.

**braves** got small, load-bearing polish: player surnames with Jr./Sr./II/III suffixes now strip correctly for abbreviation, pregame storylines persist to SQLite so they survive restarts instead of regenerating on every boot, and the CLAUDE.md for the project got migrated from a cloud-deployment orientation to a local-first one.

## The Shape of the Day

None of these shipped because someone sat down to build them on April 14. They shipped because the design was already in place, the test scaffolding already existed, and the tooling around reviews (Gemini on qmd, CI on wild-ecosystem) was already wired up. The ADR for `repo-resolver` was written as deliberate groundwork. The edge-daemon's dispatcher was the obvious next step once the `main.ts` entry point outgrew its flags.

The "one day" part is the artifact of preparation, not a claim about throughput.

## Related Posts

- [Twelve PRs, a Security Sprint, and a Pregame Overhaul](/posts/twelve-prs-security-sprint-pregame-overhaul/) — the Braves dashboard shipping arc.
- [Zero to CI: Full-Stack Dashboard, One Session](/posts/zero-to-ci-full-stack-dashboard-one-session/) — what the qmd daemon looked like earlier in its life.
- [The Wild Ecosystem Deep Dive #3: Observability](/posts/wild-deep-dive-3-observability/) — the wild-ecosystem shared-GCP pattern that CI #34 joined.

---
title: "Governed Knowledge: Two Major Releases, a Freshness Daemon, and Export Gating"
description: "qmd-team-intent-kb ships v0.2.0 and v0.3.0 in one day — freshness-aware search with exponential decay, an edge daemon that auto-deprecates stale memories, security hardening, and export gating. Plus claude-code-plugins v4.20.0."
date: "2026-03-19"
tags: ["typescript", "architecture", "release-engineering", "ai-agents", "claude-code"]
featured: false
---
Yesterday we built the knowledge base from zero to API. Today we shipped it twice.

`qmd-team-intent-kb` went from v0.1.0 to v0.3.0 in a single day. Eighteen commits. Two tagged releases. The first release (v0.2.0) was dependency hygiene — upgrading everything before the real work. The second (v0.3.0) was the real release: freshness-aware search, an edge daemon for automatic stale-memory deprecation, security hardening, content classification, and export gating.

Twenty commits across two repos. Here's what actually shipped and why it matters.

## Freshness-Aware Search

The search endpoint landed as `POST /api/search`. Standard text search was already in the store layer via SQL `LIKE` queries. What v0.3.0 added was freshness-aware reranking — results that are technically relevant but six months old get penalized relative to results from last week.

The scoring uses exponential decay:

```typescript
function freshnessScore(updatedAt: Date, now: Date): number {
  const daysOld = daysBetween(updatedAt, now);
  const halfLife = 90; // days
  return Math.exp(-0.693 * daysOld / halfLife);
}
```

An article updated today scores 1.0. At 90 days it scores 0.5. At 180 days, 0.25. The half-life is configurable per category — operational runbooks decay faster than architectural decision records, because a stale runbook is dangerous and a stale ADR is just history.

Category-aware reranking sits on top of this. The policy engine already knew about article categories. The search reranker now asks: given this query, which categories should be boosted? A query containing "incident" or "outage" boosts runbooks. A query containing "why" or "decision" boosts ADRs. Simple heuristics, but they shift the results from "technically matching" to "actually useful."

The relevance scoring rule in the policy engine also got graduated signals — content length, source authority, and category all feed into the final score with weighted contributions instead of binary flags.

## The Edge Daemon

This is the piece I'm most interested in long-term. The edge daemon is a local process that watches a spool directory, curates incoming memories, and syncs them to the central index.

Three responsibilities:

**Spool watch.** New memories arrive as files in a local directory. The daemon picks them up, validates structure, and queues them for curation. This decouples memory creation from memory storage — you can write memories offline and they sync when connectivity returns.

**Curation.** Each incoming memory gets classified, tagged, and scored before entering the index. The daemon applies the same policy engine rules that the API uses, but locally. No network round-trip for classification.

**Staleness sweep.** This is the auto-deprecation loop. The daemon periodically scans all indexed memories and runs freshness scoring against them. Memories that fall below the staleness threshold get automatically marked deprecated:

```typescript
interface StalenessConfig {
  sweepIntervalMinutes: number;
  thresholds: Record<MemoryCategory, number>;  // days
}

// Default thresholds
const STALENESS_DEFAULTS: StalenessConfig = {
  sweepIntervalMinutes: 60,
  thresholds: {
    "operational": 30,
    "architectural": 180,
    "onboarding": 90,
    "troubleshooting": 60,
  },
};
```

Operational memories go stale in 30 days. Architectural decisions get 180. The daemon doesn't delete anything — it marks memories as deprecated so they still appear in search results but with a clear staleness indicator. A human can promote a deprecated memory back to active if the content is still valid.

This is the governance loop that most knowledge systems lack. They depend on humans noticing that something is outdated. The daemon makes staleness visible and automatic.

## Security Hardening and Export Gating

Phase 8 was security. Content classification assigns sensitivity levels to memories — public, internal, confidential, restricted. The classification happens at write time and the label sticks with the memory through its lifecycle.

Export gating builds on classification. When you export memories (to git, to another system, to a report), the export pipeline checks sensitivity labels against the requesting context. A git export to a public repository strips confidential and restricted memories. An internal team export includes everything up to confidential. Restricted memories only export to explicitly authorized targets.

```typescript
type SensitivityLevel = "public" | "internal" | "confidential" | "restricted";

interface ExportContext {
  target: "git-public" | "git-internal" | "report" | "api";
  requestor: Actor;
  maxSensitivity: SensitivityLevel;
}

function canExport(memory: Memory, ctx: ExportContext): boolean {
  const levels: SensitivityLevel[] = ["public", "internal", "confidential", "restricted"];
  return levels.indexOf(memory.sensitivity) <= levels.indexOf(ctx.maxSensitivity);
}
```

Simple ordinal comparison. But without it, every export is a potential data leak. The gating is enforced at the export layer, not at the UI layer. You can't build a custom integration that bypasses it because the function sits between the store and the output.

## Release Readiness (Phase 9)

Phase 9 was packaging and developer operability. This is the phase people skip and regret. It covers:

- Package manifests with correct entry points and type exports
- README with actual setup instructions (not aspirational ones)
- A `bd doctor`-compatible health check
- CI passing on every commit, not just the last one

The two releases landed cleanly because Phase 9 was an explicit phase, not an afterthought. v0.2.0 tagged after dependency upgrades. v0.3.0 tagged after all feature phases passed CI. No "let's just tag it and see if it works."

## Meanwhile: claude-code-plugins v4.20.0

On the other side of the workspace, `claude-code-plugins` shipped v4.20.0 with two things worth mentioning.

The `pr-to-spec` MCP plugin converts pull request diffs into structured specifications. You point it at a PR, it reads the diff, and it outputs a spec document describing what changed and why. Useful for teams that need to maintain specs but don't want to write them by hand after every PR merge.

The same release included eight SaaS pack rewrites. These are curated collections of skills organized by SaaS platform — think "everything you need for working with Stripe" or "all the Jira skills in one pack." The rewrites brought them up to current quality standards with proper error handling and input validation.

## The Two-Release Pattern

Shipping v0.2.0 and v0.3.0 on the same day isn't reckless. It's deliberate. v0.2.0 was a dependency-only release — upgrading packages, fixing CI, ensuring the foundation was solid. Tagging it separately means if v0.3.0 introduces a regression, you can roll back to v0.2.0 and still have all your dependency upgrades.

It also means v0.3.0's diff is clean. Every change in the v0.3.0 tag is feature work. No dependency noise mixed in. When you're debugging a freshness scoring bug three months from now, `git log v0.2.0..v0.3.0` shows only the commits that matter.

This is basic release hygiene, but most projects bundle everything into one tag and lose the ability to isolate changes later.

## The Commit Graph

Eighteen commits in qmd-team-intent-kb. Two in claude-code-plugins. The breakdown:

| Phase | Commits | What Shipped |
|-------|---------|-------------|
| Dependencies | 3 | Upgrades, CI fixes, v0.2.0 tag |
| Search API | 2 | POST /api/search, SQL text search |
| Freshness | 2 | Exponential decay, category reranking |
| Edge Daemon | 2 | Spool watch, curation, staleness sweep |
| Policy Engine | 2 | Graduated relevance scoring |
| Security | 3 | Content classification, export gating |
| Release | 4 | Phase 9 packaging, v0.3.0 tag |

Every phase has its own commits. Every commit builds on a passing CI run from the previous one. The edge daemon doesn't land on a broken build from the search API phase.

## What's Next

The edge daemon opens up offline-first workflows. A developer's local machine accumulates memories throughout the day — code review notes, debugging insights, architectural observations — and they sync to the team index when ready. The staleness sweep keeps the index from growing unbounded.

The freshness scoring needs real-world calibration. The 90-day half-life is a guess. After a month of actual usage, the decay curves will need tuning based on which categories actually go stale at what rate.

Export gating needs integration tests against real git targets. The unit tests prove the ordinal comparison works. They don't prove that a CI pipeline correctly strips confidential memories from a public export.

---

### Related Posts

- [Knowledge Base from Zero to API: Lifecycle State Machines and Policy Engines](/blog/knowledge-base-zero-to-api-lifecycle-state-machine/) — The day before: building the foundation that today's releases built on
- [Building Post-Compaction Recovery with Beads](/blog/building-post-compaction-recovery-beads/) — Another system where memory governance and staleness matter
- [External Plugin Sync: Keeping Community Plugins Fresh](/blog/external-plugin-sync-keeping-community-plugins-fresh/) — The freshness problem applied to plugin marketplaces instead of knowledge bases

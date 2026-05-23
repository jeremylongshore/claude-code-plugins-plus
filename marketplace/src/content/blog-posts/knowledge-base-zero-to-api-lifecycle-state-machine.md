---
title: "Knowledge Base from Zero to API: Lifecycle State Machines and Policy Engines"
description: "Building a team knowledge base with lifecycle state machines, policy engines, and git-exported articles — from empty repo to working API in one day."
date: "2026-03-18"
tags: ["typescript", "architecture", "full-stack", "automation", "monorepo"]
featured: false
---
Most knowledge bases are wikis with a search box. Articles go in, articles rot, nobody notices. The problem isn't storage. It's governance.

Articles have lifecycles. A draft isn't ready for the team. A published article that hasn't been reviewed in six months is a liability. An archived article should still be findable but clearly marked stale. If your knowledge base doesn't model these states explicitly, you're building a graveyard with good intentions.

That's what drove `qmd-team-intent-kb` — Intent Solutions' internal knowledge management system, built from empty directory to working API in a single day.

## The State Machine

Every knowledge article has a lifecycle with four states:

```
draft → review → published → archived
```

This isn't a database column with free-text values. It's a state machine with explicit transitions and guards:

```typescript
type ArticleState = "draft" | "review" | "published" | "archived";

interface StateTransition {
  from: ArticleState;
  to: ArticleState;
  guard?: (article: Article, actor: Actor) => boolean;
}

const VALID_TRANSITIONS: StateTransition[] = [
  { from: "draft", to: "review", guard: (a) => a.body.length > 0 },
  { from: "review", to: "published", guard: (_, actor) => actor.role === "reviewer" },
  { from: "review", to: "draft" },  // rejection
  { from: "published", to: "archived" },
  { from: "published", to: "review" },  // content update requires re-review
  { from: "archived", to: "draft" },    // resurrection
];
```

You can't publish an empty draft. You can't skip review. You can't go from archived straight to published without going through draft and review again. The state machine enforces these rules at the domain level — not in a UI form validator that someone can bypass.

The guard functions are the key insight. They encode business rules. "Only reviewers can publish" isn't a UI concern. It's a domain invariant.

## The Policy Engine

State transitions tell you what's allowed. The policy engine tells you what *should happen*. Different concerns.

```typescript
interface Policy {
  name: string;
  trigger: "on_transition" | "on_schedule" | "on_content_change";
  evaluate: (article: Article) => PolicyResult;
}

// Example: stale content detection
const staleContentPolicy: Policy = {
  name: "stale-content-check",
  trigger: "on_schedule",
  evaluate: (article) => {
    const daysSinceUpdate = daysBetween(article.updatedAt, now());
    if (article.state === "published" && daysSinceUpdate > 180) {
      return {
        action: "flag",
        severity: "warning",
        message: `Published ${daysSinceUpdate} days ago without update`,
      };
    }
    return { action: "pass" };
  },
};
```

Three trigger types. Transition policies fire on state changes — notify the team when something gets published. Schedule policies run periodically — the stale content check above. Content change policies fire on edits — flag articles that lose more than 50% of their content.

Without this separation, governance logic leaks into every handler and cron job. The policy engine centralizes the rules and makes them auditable.

## Monorepo Scaffolding

pnpm workspaces. Not because monorepos are trendy — because the knowledge base has distinct packages that share types:

```
packages/
├── core/          # Domain model, state machine, types
├── policy/        # Policy engine and built-in policies
├── store/         # Persistent storage layer
├── api/           # REST endpoints (CRUD + search)
├── curator/       # Automated content curation
└── git-exporter/  # Export articles as git-tracked markdown
```

`core` owns the `Article` type and the state machine. Every other package depends on `core` but not on each other. The API doesn't know about the git exporter. The curator doesn't know about the API. Clean dependency graph from day one.

## The Curator

The curator is the automated maintenance layer. It's the package that actually uses the policy engine to do work:

- Flags stale published articles for re-review
- Detects duplicate or near-duplicate content
- Surfaces articles that are frequently linked but haven't been updated
- Generates review queues for team leads

Without a curator, governance policies are just documentation. With one, they're enforced.

## The Git Exporter

Every published article gets exported as a markdown file in a git repository. Changes create commits. Metadata becomes front matter.

This gives you three things no knowledge base UI provides: version history (`git log --follow` on any article), portability (your content is markdown files, not vendor-locked blobs), and review workflows (article updates can trigger PRs where reviewers use diff views and inline comments instead of whatever review UI the KB ships with).

## The Full Day

Phase 0 was repo foundation — monorepo scaffolding, pnpm workspace config, CI pipeline, security hygiene (removing credential keys from tracking on the first commit, not the tenth).

Phase 1 delivered the core domain model and the lifecycle state machine. This is the load-bearing code. Everything else is plumbing around it.

Phases 2-3 hardened CI. Prettierignore for generated files, pnpm version pinning to avoid CI drift.

Phases 4-6 shipped the rest: policy engine, storage layer, REST API, curator, and git exporter. PR #14 merged all of it to main.

## The Side Quests

Three other projects shipped on the same day: **excel-analyst-pro v1.1.0** (skill-creator compliance overhaul across all four skills), **claude-code-plugins v2.1.78** (new `pr-to-spec` MCP plugin in the marketplace), and **intent-blueprint-docs v2.9.0** (gstack integration plus repo health audit). Multi-project days are the norm when your CI is solid enough to trust.

## The Takeaway

Knowledge management for engineering teams isn't a wiki problem. It's a state machine problem. Model the lifecycle explicitly. Enforce governance with policies, not discipline. Automate maintenance with a curator. Export to git for portability.

The hard part isn't the tooling — a state machine is a lookup table, a policy engine is a list of rules. The hard part is deciding to treat knowledge articles as first-class domain objects instead of blobs of markdown in a database.

---

### Related Posts

- [Zero to CI: Full-Stack Dashboard in One Session](/posts/zero-to-ci-full-stack-dashboard-one-session/) — Another greenfield project from empty repo to working system in one day
- [From Tool to Platform: IntentCAD Ships Five EPICs in One Day](/posts/from-tool-to-platform-intentcad-five-epics-one-day/) — Multi-EPIC shipping day with architectural pivots
- [Production Release Engineering: Shipping v4.5.0](/posts/production-release-engineering-v450/) — Automated release workflows and CI discipline at scale

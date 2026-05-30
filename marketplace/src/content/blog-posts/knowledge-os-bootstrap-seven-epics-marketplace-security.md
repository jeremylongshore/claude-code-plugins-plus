---
title: "Knowledge OS Bootstrap: Seven Epics, Marketplace Security, and Production AI Fixes"
description: "Bootstrapping a local-first knowledge OS from standards documents to working retrieval in one day. Seven epics, six releases, 485 tests. Plus marketplace docs, Firestore security, and Braves AI fixes."
date: "2026-04-06"
tags: ["ai-agents", "typescript", "architecture", "testing", "monorepo", "claude-code", "release-engineering"]
featured: false
---
Seven epics in one repo. Six releases in one day. A TypeScript monorepo that didn't exist 48 hours ago now has a compiler pipeline, FTS5 search, and citation-verified answers. April 6th was the day intentional-cognition-os went from design documents to a working knowledge operating system.

## What intentional-cognition-os Is

A local-first knowledge OS. You feed it raw corpus — PDFs, markdown, web clips. It compiles that into semantic knowledge. You ask questions. It answers with inline citations that trace back to source material through provenance chains.

The architecture is a TypeScript monorepo with four packages:

```
packages/
├── types/      # Shared Zod schemas + TypeScript types
├── kernel/     # SQLite storage, FTS5 indexing, retrieval
├── compiler/   # 6-pass Claude API pipeline
└── cli/        # ico command — ingest, compile, ask, lint
```

Every package has its own build, its own tests, its own exports. No barrel files re-exporting the universe. Clean dependency graph: `types` → `kernel` → `compiler` → `cli`.

## Epic 1: Canonical Design Pack (PR #3)

Before writing code, write the contracts. 14 standards documents froze the architecture: data model, compiler passes, retrieval strategy, CLI surface, error taxonomy, security boundaries. Then a standards freeze — no spec changes without a formal amendment process.

This sounds like waterfall. It's not. It's insurance. When you're shipping six more epics the same day, you need something to validate against. The standards documents are that thing.

## Epic 2: Repo Foundation (PR #4)

Four packages scaffolded with real tooling. Not placeholder `index.ts` files — actual build configs, actual test harnesses, actual TypeScript strict mode. 36 tests passing before any business logic existed. The foundation tests validate package boundaries: can `kernel` import from `types`? Can `cli` import from `compiler`? Can `types` import from nothing outside itself?

Dependency hygiene is boring until the day your CLI accidentally imports a dev-only test utility from the compiler package and your production build breaks. These 36 tests make that impossible.

## Epic 5: Ingest Adapters (PR #6)

Source identity is the first real problem. A PDF, a markdown file, and a web clip all need to become the same internal representation — but they can't lose their provenance. Where did this text come from? What page? What URL? What date was it captured?

Each adapter — PDF, markdown, web-clip — produces source nodes with full provenance metadata. The ingest pipeline normalizes content while preserving origin. Every downstream operation can trace any text fragment back to its source document, page, and capture timestamp.

## Epic 6: Knowledge Compiler Core (PR #7)

The compiler is six passes over ingested source material, each producing a different knowledge artifact:

1. **Summarize** — condensed representation of each source
2. **Extract** — structured facts, claims, definitions
3. **Synthesize** — cross-source connections and themes
4. **Link** — explicit relationships between knowledge nodes
5. **Contradict** — conflicting claims across sources flagged
6. **Gap** — missing knowledge identified from the corpus shape

Each pass calls Claude's API through a client with retry, exponential backoff, and injection detection. The injection detection matters — if you're compiling untrusted source material (web clips from arbitrary URLs), you need to catch prompt injection attempts before they corrupt your knowledge base.

```typescript
const INJECTION_PATTERNS = [
  /ignore\s+(all\s+)?previous\s+instructions/i,
  /you\s+are\s+now\s+/i,
  /system\s*:\s*/i,
  /\[INST\]/i,
  /<\|im_start\|>/i,
];

function detectInjection(content: string): InjectionResult {
  const matches = INJECTION_PATTERNS
    .map(p => ({ pattern: p.source, match: p.exec(content) }))
    .filter(r => r.match !== null);

  if (matches.length > 0) {
    return { detected: true, patterns: matches, action: 'quarantine' };
  }
  return { detected: false, patterns: [], action: 'proceed' };
}
```

Output from each pass validates against Zod schemas. Six schemas, one per pass. If the compiler produces malformed output, the schema catches it immediately — not three passes later when something downstream chokes on a missing field.

Staleness detection tracks when source material changes and marks affected knowledge artifacts for recompilation. Token tracking estimates API costs per compilation run. You know before you start whether a full recompile will cost $0.50 or $50.

144 compiler tests. 198 CLI tests. The compiler alone has more tests than most entire projects.

## Epic 7: Retrieval and Ask Flow (PR #8)

The payoff. FTS5 full-text search over compiled knowledge. Question analysis that decomposes complex queries into searchable sub-queries. Answer generation with inline citations.

```typescript
// Citation-aware answer with provenance chain
interface CitedAnswer {
  answer: string;
  citations: Citation[];
  confidence: number;
  coverage: 'full' | 'partial' | 'insufficient';
}

interface Citation {
  claim: string;           // The specific claim being cited
  sourceId: string;        // Original source document
  knowledgeNodeId: string; // Compiled knowledge node
  passage: string;         // Exact passage supporting the claim
  confidence: number;      // How well the passage supports the claim
}
```

Citation verification walks each citation's provenance chain. Does the cited passage actually exist in the source? Does it actually support the claim? This isn't decorative — it's the difference between "the system says X" and "the system says X, here's the exact passage from the original PDF, and we verified it matches."

Two new CLI commands: `ico ask "question"` for retrieval and `ico lint knowledge` for validating compiled knowledge integrity.

243 tests passing across the full stack. From zero to working retrieval in one day.

## Six Releases (v0.1.5 → v0.2.0)

Each epic got its own release. Not because semver demands it, but because each one is a usable checkpoint. v0.1.5 has the design pack. v0.1.6 has the foundation. By v0.2.0 you have a complete ingest-compile-retrieve pipeline. If v0.2.0 breaks something, you can bisect against five intermediate releases.

## Marketplace: 24 Docs Pages + Firestore Lockdown

Parallel track in claude-code-plugins. Two PRs that look unrelated but solve the same problem: trust.

PR #512 added a `/docs` section — 24 SEO-optimized documentation pages built as an Astro content collection. JSON-LD TechArticle schema for search engines. Sidebar navigation, breadcrumbs, prev/next links. 3,709 internal links validated. The marketplace had plugins but no documentation hub. Now it does.

PR #513 locked down Firestore rules to block direct client writes. The rules had been permissive during development — any authenticated client could write to any collection. Fine for a solo developer. Unacceptable for a marketplace with external users. The fix is simple: server-side writes only, client reads gated by ownership checks.

Also shipping: 3 new plugins (Shipwright autonomous app builder, Tweetclaw X/Twitter automation, Framecraft demo video generator), 232 D/F-grade skills upgraded to 70+ compliance, and v4.24.0 released.

## Braves: Production AI Fixes

The Braves dashboard had three bugs that all trace to the same root cause: trusting AI output shape.

**Narrative truncation.** `maxOutputTokens` was set to 500. Gemini 2.5 Pro was generating narratives that hit the limit mid-sentence, producing truncated JSON. Fix: bump to 1024, plus a regex salvage function that recovers partial JSON when truncation still happens.

**Pitcher career card.** `getPlayerBio()` called `find()` on the yearByYear stats array, which grabbed the first stat group — batting stats. For pitchers, this showed batting lines instead of pitching lines. Fix: pick the stat group with the most splits, which is always the player's primary position group.

**SSE event mapping.** Real-time batter-change, pitcher-change, and score-change events were mapping fields incorrectly. The handlers were written against an older API shape. Fix: update field mappings to match the current MLB Stats API response format.

Also: Groq with llama-3.3-70b added as a local dev AI provider. Vertex AI Gemini 2.5 Pro stays for production on Cloud Run. Minor league and weekly/monthly awards filtered from display.

## The Day in Numbers

| Metric | Value |
|--------|-------|
| Repos touched | 5 |
| intentional-cognition-os EPICs | 7 (design pack through retrieval) |
| intentional-cognition-os releases | 6 (v0.1.5 → v0.2.0) |
| Tests passing (ico) | 485 (36 + 144 + 198 + 243 cumulative checkpoints) |
| claude-code-plugins docs pages | 24 |
| claude-code-plugins new plugins | 3 |
| Internal links validated | 3,709 |
| Braves bugs fixed | 3 |
| Firestore security rules | Locked down |

## Why This Works in One Day

Same pattern as [IntentCAD's five-epic day](/posts/from-tool-to-platform-intentcad-five-epics-one-day/). Each epic builds on the contracts from the one before. The standards freeze (Epic 1) defines the schemas. The foundation (Epic 2) enforces package boundaries. Ingest adapters (Epic 5) produce the data the compiler (Epic 6) consumes. The compiler produces the knowledge the retriever (Epic 7) searches.

No epic can ship without the one before it. But each one is small enough to ship in a few hours because the contracts are already defined. You're not designing and building simultaneously. You designed everything in Epic 1, then executed six times.

485 tests across a brand new monorepo isn't heroics. It's the natural result of test-first development against frozen schemas. When the schema is defined before the code exists, the tests write themselves.

---

*Related posts:*

- [Building Post-Compaction Recovery with Beads](/posts/building-post-compaction-recovery-beads/) — the task persistence system that keeps multi-epic days recoverable
- [From Tool to Platform: IntentCAD Five Epics One Day](/posts/from-tool-to-platform-intentcad-five-epics-one-day/) — the same contracts-then-execute pattern applied to CAD tooling
- [Nuclear Option Day: Validator Rewrite Across 414 Plugins](/posts/nuclear-option-day-validator-rewrite-414-plugins/) — another high-output day driven by a single architectural decision

---
title: "Knowledge OS: Render, Promote, and the Research Command"
description: "intentional-cognition-os ships Epics 8 and 9 — a Marp slide deck renderer, a 7-rule promotion engine with rollback, and the first research command. Three releases in one day: v0.3.0 through v0.4.0."
date: "2026-04-08"
tags: ["ai-agents", "typescript", "testing", "architecture", "release-engineering", "automation"]
featured: false
---
Three days ago ICO was at v0.1.5. Today it's at v0.4.0. Two epics landed, three releases shipped, and the test count nearly tripled.

## Epic 8: Render and Promote

Epic 8 delivered two distinct capabilities: turning compiled knowledge into Marp slide decks, and a promotion engine that gates which artifacts make it into the wiki.

### Slide Deck Renderer

The renderer takes compiled knowledge and produces Marp-compatible markdown via Claude API. Marp is a solid choice here — it's just markdown with slide separators, so the output is diffable, version-controllable, and doesn't require a proprietary format.

Thirty-four tests cover the renderer. That's a lot for a rendering pipeline, but the edge cases matter. Malformed frontmatter, missing fields, Claude API failures, oversized inputs — each one gets explicit coverage.

### Promotion Engine

This is the more interesting piece. The promotion engine copies artifacts from `outputs/` into `wiki/`, but only if they pass seven eligibility rules:

1. Path must exist
2. File must be readable
3. Frontmatter must parse
4. Type must be promotable
5. Confirm flag must be set
6. No draft status
7. No raw evidence files

Three of those are anti-pattern rejections — drafts, evidence artifacts, and unconfirmed outputs get blocked before they can pollute the wiki. The confirm flag is deliberate friction. You have to explicitly mark something as ready for promotion. No accidental publishes.

When promotion succeeds, the engine:

- Computes SHA-256 hash of the source file
- Mutates frontmatter on the target copy (adds promotion metadata)
- Writes a database record
- Emits a trace event
- Creates a per-promotion JSONL audit file

When it fails, everything rolls back. No partial promotions. The audit file still gets written so you can see what was attempted and why it was rejected.

```typescript
// Each promotion gets its own audit trail
const auditEntry = {
  timestamp: new Date().toISOString(),
  source: sourcePath,
  target: targetPath,
  sourceHash: sha256(sourceContent),
  status: 'promoted',
  rules: ruleResults,
};
appendFileSync(auditPath, JSON.stringify(auditEntry) + '\n');
```

This shipped as PR #9 and tagged v0.3.0.

## Docs Fix: The Test Count Was Wrong

A small but telling commit: CLAUDE.md listed 292 tests. The actual count was 864. The discrepancy? The docs were only counting the CLI package. ICO has four packages, and nobody had summed them up.

Same commit fixed the CLI command count (13 to 14 — `eval` was listed as a stub but had been implemented) and clarified that `claude_agent_sdk` is planned for Epic 9, not yet installed.

Tagged v0.3.1. Small release, but accurate docs matter more than people think.

## Epic 9: The Research Command

Epic 9 introduced `ico research <brief>` — a command that creates a scoped research task workspace. You give it a research question or topic, and it scaffolds:

- A `brief.md` with YAML frontmatter (title, scope, created timestamp)
- An audit log entry tracking when the research task was created
- Support for both human-readable and JSON output formats

```bash
# Human output
ico research "Compare vector databases for sub-100ms latency"

# Machine output
ico research "Compare vector databases for sub-100ms latency" --json
```

Fourteen new tests brought the total to 878 passing. The PR review caught two issues: the command was calling `process.exit()` directly (bad for testability — switched to setting `process.exitCode`), and there were non-null assertions that could mask runtime errors. Both fixed before merge.

Tagged v0.4.0 as PR #10.

## Marketplace Housekeeping

Over in `claude-code-plugins`, three small but necessary changes:

**Hyperfocus plugin** (PR #514). An ADHD-friendly output formatting skill — no tool access, just formatting. It restructures Claude's output to reduce cognitive load: shorter paragraphs, clearer section breaks, explicit action items separated from context.

The initial version shipped with an empty `allowed-tools` field, which triggered a validator error. Second commit removed the invalid field. Formatting-only skills don't need tool declarations.

**Claudebase source path fix.** The marketplace catalog (`marketplace.extended.json`) had the source path listed as "external" instead of the actual directory path. Small data integrity fix, but catalog entries that point nowhere break downstream tooling.

## Velocity Check

Three days of ICO development:

| Day | Epics | Version | Tests |
|-----|-------|---------|-------|
| Apr 6 | 1–5 | v0.1.0–v0.1.5 | 292 |
| Apr 7 | 6–7 | v0.2.0–v0.2.1 | 557 |
| Apr 8 | 8–9 | v0.3.0–v0.4.0 | 878 |

Nine epics. Eight releases. 878 tests. The project has a full CLI, a knowledge compilation pipeline, a policy engine, slide deck rendering, a promotion engine with audit trails, and now a research command.

The test count growth is the metric I care about most. Features without tests are demos. Features with tests are products.

---

**Related Posts:**

- [IntentCAD v0.8.0: Thirteen Epics One Day](/posts/intentcad-v080-thirteen-epics-one-day/)
- [Governed Knowledge: Two Releases and a Freshness Daemon](/posts/governed-knowledge-two-releases-freshness-daemon/)

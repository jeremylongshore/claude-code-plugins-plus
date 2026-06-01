---
title: "The Day the Cleanup Plugin Shipped — and Everything Else Got Cleaned Up in Parallel"
description: "Shipping an 11-dimension, 11-agent code-cleanup plugin while the rest of the portfolio earns the same grade — 24,884 net lines deleted from the marketplace, a 35x FLOPs figure corrected in a pre-filing patent, cosign+SLSA provenance for an edge daemon, and three back-to-back IOS releases."
date: "2026-04-15"
tags: ["code-quality", "refactoring", "release-engineering", "architecture", "ai-agents", "claude-code", "automation"]
featured: false
---
The Ultimate Code Cleanup plugin shipped on April 15. It scored 98/100 on the enterprise validator rubric. The thing that makes this post worth writing is not the score. It is that in the same 24-hour window, every other active repo in the portfolio earned that same grade through parallel work — a 24,884-line deletion across the marketplace toolchain, a quality sweep across an edge-daemon monorepo that removed dead code, defensive try/catch, weak types, and legacy agents by the dozen, an OpenAPI 3.1 spec emitted from source, cosign keyless signing with SLSA provenance, and a 35x numerical error caught in a pre-filing patent *exactly* because the peer review predicted that specific failure mode.

Ship the rubric. Earn the rubric. Same day.

## What the Plugin Is

The Ultimate Code Cleanup plugin lives at `plugins/code-quality/code-cleanup/` in the claude-code-plugins repo. It is one skill (`cleanup-code`) that orchestrates eleven specialized agents, each responsible for one axis of code quality. The axes are ordered by risk:

| # | Dimension | Agent | Risk | Auto-apply |
|---|-----------|-------|------|-----------|
| 1 | Dead code removal | `dead-code-hunter` | LOW | Yes (after build) |
| 2 | AI slop removal | `slop-remover` | LOW | Comments only |
| 3 | Weak type elimination | `weak-type-eliminator` | MED | Yes (after typecheck) |
| 4 | Security cleanup | `security-scanner` | MED | Flag only |
| 5 | Legacy code removal | `legacy-code-remover` | MED | With confirmation |
| 6 | Type consolidation | `type-consolidator` | MED | Yes (after typecheck) |
| 7 | Defensive code cleanup | `defensive-code-cleaner` | MED | Flag only |
| 8 | Performance optimization | `performance-optimizer` | MED | Flag only |
| 9 | DRY deduplication | `dry-deduplicator` | HIGH | Flag only (≥10 lines) |
| 10 | Async pattern fixes | `async-pattern-fixer` | HIGH | Flag only |
| 11 | Circular dep untangling | `circular-dep-untangler` | HIGH | Flag only |

Every finding gets a confidence score — HIGH, MEDIUM, or LOW. Auto-apply is gated by build and test verification between dimensions. If the typecheck fails after a weak-type elimination pass, the dimension reverts. You do not get dead code back because you deleted something that wasn't actually dead.

The whole package is 25 new files, 4,081 lines added. The enterprise validator — a 100-point rubric that checks SKILL.md structure, agent definitions, references, argument hints, examples, and failure handling — gave it 98/100 (A+). The missing two points were on CI integration and marketplace-example coverage. Real issues, not ceremony.

## The 11 Dimensions, Ordered by Risk

Ordering by risk is the part worth defending. Other cleanup tools bundle dimensions in arbitrary order or leave the sequencing to the user. This one doesn't.

**Dead code removal is first because it is the safest.** An unreferenced function that compiles out cleanly cannot break anything. The only failure mode is a reflection-based caller the tool can't see, which is why the verification gate exists — if the build or tests fail after removal, revert.

**AI slop removal is second because it touches comments, not logic.** Lines like `// TODO: implement this later` from three years ago, or `// Added by Cursor on 2024-06-12` artifacts. No behavior change is possible. The cost is zero and the readability gain compounds.

**DRY deduplication and circular dep untangling are last because they are the most dangerous.** Extracting shared logic can collapse code paths that look identical but aren't. Untangling a cycle can mean rewriting ownership across modules. These are the dimensions where the agent defaults to flag-only, and the human has to decide.

The ordering matters because each dimension's cleanup creates cleaner inputs for the next one. Dead code removed first makes DRY deduplication detection more accurate — you are not finding false duplicates in unreachable branches. Weak types eliminated before type consolidation means the consolidator works with accurate signatures.

## Meanwhile, in the Same Repo

The plugin shipped at `2ca7720e0`. Four commits later, `f61853026` was a commit titled *"refactor: comprehensive codebase cleanup — 8 parallel agents."*

That commit changed 126 files. 423 insertions. **25,307 deletions.**

```
scripts/overnight-skill-fix.py                 | 978 ---------------------
scripts/skill-batch-fixer.py                   | 483 ----------
scripts/skill-gap-report.py                    | 577 ------------
scripts/skills-enhancer-batch.py               | 651 --------------
scripts/skills-generate-vertex-safe.py         | 740 ----------------
scripts/skills-generate-vertex.py              | 386 --------
scripts/validate-plugin.js                     | 807 -----------------
```

Seven files alone account for over 4,600 lines of deletion. These were migration scripts, skill-generation experiments, validator prototypes, batch fixers — tools that had done their job months ago and never got removed. The cleanup plugin's first real customer was the repo that shipped it.

**That is not a coincidence. It is the right order of operations.** Dogfooding a cleanup tool on the repo that built it is the only way to find the edge cases before external users hit them. The 8-agent run exposed places where the dead-code detector needed to distinguish "never imported" from "imported only by a test fixture that is itself unused." That fix landed the same day.

Also in the same repo, `4e07649fe` resolved 27 validation errors across 3,874 skill files: `disallowedTools` fields that were strings instead of arrays, `repository` fields that were objects instead of strings, and cross-skill relative links that reached outside their own package. `11f7b5b94` split thirteen oversized `SKILL.md` files — four in notion-pack, eight in supabase-pack, one in sentry-pack — moving code examples and CI configs into `references/` subdirectories so the main files stay under the 500-line limit. `b2debbdf8` removed XML angle brackets from four skill descriptions because the validator's XML-tag check interpreted `->` as a tag opener.

Small, load-bearing fixes. Every one of them is the kind of thing a cleanup framework should surface automatically, and several of them informed how the plugin's agents detect similar issues.

## The qmd-team-intent-kb v0.4.0 Story

Across the same 24 hours, `qmd-team-intent-kb` cut v0.4.0 with cosign keyless signing plus SLSA provenance for the edge-daemon container image (`#82`), emitted an OpenAPI 3.1 spec with a bundled Swagger `/docs` UI (`#84`), and added `publishConfig` metadata so internal packages can publish to a private registry as reusable libraries (`#83`).

**Cosign keyless signing plus SLSA provenance** is the piece worth explaining. Traditional container signing uses a long-lived signing key, which is an operational liability — if the key leaks, every image ever signed is retroactively suspect. Keyless signing binds each signature to a short-lived OIDC token from the CI environment, verified by the public Sigstore transparency log. There is no key to leak. The signature proves which GitHub Actions workflow, which commit SHA, and which runner produced the image.

SLSA (Supply-chain Levels for Software Artifacts) provenance is the companion: a signed attestation describing how the artifact was built — the source commit, the builder identity, the build inputs, and the isolation environment. For a daemon that is going to run inside customer environments, that attestation is what lets the customer verify "this image was built from the commit I see in GitHub, by the workflow I can inspect, and no one inserted a build step I did not approve."

The v0.4.0 release wired this into the existing CI pipeline without requiring a separate signing step. The workflow that builds the edge-daemon image also signs it and publishes the provenance attestation. Consumers can verify with:

```bash
cosign verify ghcr.io/qmd-team-intent-kb/edge-daemon:v0.4.0 \
  --certificate-identity-regexp "https://github.com/jeremylongshore/qmd-team-intent-kb" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

cosign verify-attestation ghcr.io/qmd-team-intent-kb/edge-daemon:v0.4.0 \
  --type slsaprovenance \
  --certificate-identity-regexp ".*"
```

That is the whole interface. For a project that had been running unsigned images a week earlier, that is a meaningful security posture shift delivered without friction.

But the interesting part is the dozen quality PRs that landed underneath those headline features.

**`#58` — DRY sweep on fixture factories and spool JSONL writer.** Consolidated duplicate test-fixture helpers across three packages into a shared `@qmd-team-intent-kb/test-fixtures` package. The spool JSONL writer had two nearly-identical implementations for retry-on-full-disk behavior; those collapsed to one.

**`#54` — Removed AI slop and unhelpful comments.** Lines like `// Check if the item is valid before processing` sitting above `if (!isValid(item)) return`. Explaining what instead of why. Gone.

**`#53` — Removed `ConsoleDaemonLogger`, `NullLogger`, and vestigial public re-exports.** The daemon had standardized on pino structured logging weeks earlier (PR `#45`). The legacy console logger and the null logger used during that migration were still exported. Removed.

**`#56` — Removed unused code identified by knip sweep.** Everything knip flagged with zero callers.

**`#57` — Replaced weak types with strong types.** `Record<string, unknown>` where a typed interface existed. `any` on function parameters. Adjacent PRs did the same for data-at-rest: `#73` replaced repository casts with Zod-on-read validation; `#78` replaced the `as Record<string, unknown>` delete pattern with rest-destructure in schema tests.

**`#55` — Untangled `mcp-server` → `edge-daemon` peer-level import.** An import that reached across package boundaries to pull an implementation detail. Replaced with a proper interface in a shared package.

**`#51` — Consolidated `SensitivityLevel` into the schema Sensitivity type.** Two type names for the same concept. Merged.

**`#52` — Removed defensive try/catch hiding fast-glob errors in `importFiles`.** The catch was swallowing errors and returning empty arrays, which made "zero matches" indistinguishable from "fast-glob crashed." Removed the catch; the error propagates; the caller decides what to do.

Before:

```typescript
async function importFiles(patterns: string[]): Promise<string[]> {
  try {
    return await fastGlob(patterns, { dot: true });
  } catch (err) {
    logger.warn('glob failed', { err });
    return [];
  }
}
```

After:

```typescript
async function importFiles(patterns: string[]): Promise<string[]> {
  return await fastGlob(patterns, { dot: true });
}
```

Three lines removed. The caller — `edge-daemon/src/capture.ts` — already had its own error handling that distinguished "no files matched" from "filesystem unavailable." The defensive catch was erasing that distinction before the caller could act on it. The cleanup dimension that catches this pattern is `defensive-code-cleaner` — dimension 7 in the plugin.

That is seven of the eleven cleanup dimensions applied in a single day by a different team working on a different codebase. Not because they were using the plugin. Because the dimensions are the actual axes of code quality, and anyone running a mature cleanup sweep converges on them.

## Intentional Cognition OS: The Agent Chain Completes

Intentional Cognition OS shipped three releases on April 15: v0.9.1, v0.9.2, and v0.9.3. The headline is v0.9.1.

The compiler component had been building up an agent chain for episodic research over the previous weeks: collector (B02), summarizer (B03), skeptic (B04), integrator (B05). Each one a separate release (v0.6.0 through v0.9.0). April 15 shipped **B06 — the research orchestrator with recoverable failure states**, which is the piece that makes the chain actually usable.

Without the orchestrator, a failure in the skeptic agent (say, a malformed LLM response) would propagate up and kill the whole research cycle. You would lose the collector's output and have to start over. With the orchestrator, failures are classified as transient or permanent. Transient failures (network timeouts, rate limits, malformed JSON) trigger a bounded retry with backoff. Permanent failures (schema mismatches, auth errors) fail fast and surface the error to the caller.

Recoverable failure state is not a novel concept. But implementing it as a dedicated orchestrator around a multi-agent chain means the orchestrator owns the retry policy, the circuit breaker, and the dead-letter handling — not each individual agent. That cleanly separates the agent's job (produce a specific output) from the orchestrator's job (keep the pipeline alive).

v0.9.2 and v0.9.3 were dependency bumps (typescript-eslint, eslint-plugin-simple-import-sort) with full release artifacts — small, but the release cadence itself is the signal. The project treats point releases as cheap.

## The FLOPs Correction

The most instructive story of the day is the one that almost did not get caught.

Semantic-flux is a search-architecture project with a pre-filing patent. One of its core figures — the FLOPs cost per query for the reference architecture — had been listed as 19M across the paper draft, the formal specification, and the design document.

On April 15, commit `6c07680` corrected that figure to 679M. Thirty-five times higher.

The original number came from an unchecked derivation — someone had computed FLOPs for a single operator application and not multiplied by the number of applications per query. Peer review, weeks earlier, had specifically flagged "unchecked-derivation failure modes" as the riskiest class of error in this kind of quantitative analysis. The FLOPs figure was exactly that failure mode.

The fix was not a one-character change. The design document's gap analysis (§7) was revised. The attorney package's formal specification got rewritten to claim a range (33K to 679M FLOPs depending on configuration) rather than a point value — a stronger patent posture that covers more implementations. The paper draft was updated with the new throughput implication. A permanent entry landed in DECISIONS.md explaining the correction so it cannot be silently re-introduced.

Downstream impact: the 50K-passages-per-second throughput gate is now sitting on the edge rather than comfortably above it. Phase 1 of the evaluation plan must preregister a d=96 dimensional fallback in case the d=128 configuration can't hit that throughput under the corrected FLOPs budget.

**This is what honest engineering response looks like.** The finding was uncomfortable — a 35x error in a published derivation is embarrassing. The response was not to downplay it. It was to widen the claim, tighten the evaluation plan, and document the correction permanently. Peer review caught a failure mode. The team responded like peer review matters.

This would have been Tier 4 material on its own. In the context of the day, it's one of five major threads.

## The Permanent Correction Record Pattern

The DECISIONS.md entry that landed with the FLOPs fix is worth isolating as a transferable pattern. It is a technique any engineering team can adopt, and the semantic-flux correction is a textbook example of what the pattern is for.

The entry looked approximately like this:

```markdown
## 2026-04-15 — FLOPs figure correction (Architecture C)

**Previous value:** 19M FLOPs per query
**Corrected value:** 33K–679M FLOPs (range, configuration-dependent)
**Error class:** unchecked derivation — missed multiplication by query-operator applications

### What changed
- paper/QCSS-paper-draft.md §4.1: point value → range
- attorney-package/04-formal-specification.md: claims a range, not a point
- DESIGN.md §7: gap analysis revised with corrected throughput model

### Downstream impact
- 50K passages/sec throughput gate moves from comfortable to on-edge
- Phase 1 evaluation must preregister d=96 fallback

### Why this won't recur
- Derivation verification step added to the publication checklist
- Claim-range approach adopted for all quantitative claims pre-filing
```

The pattern is three parts: **the correction itself** (what was wrong, what is right), **the downstream impact** (what else has to change because of this), and **the mitigation** (what changed about the process to prevent recurrence).

Without this pattern, the correction is invisible six months later. Someone reading the paper finds the new FLOPs figure and doesn't know why it changed. Someone reviewing the attorney package finds the claim range and doesn't know it started as a point value. The context — *this was specifically flagged by peer review as the class of error to watch for* — gets lost.

With this pattern, the correction becomes a part of the project's epistemic record. It reads to future-you or to a future collaborator as: "we made this mistake, we caught it this way, here is what it cost, here is how we stopped ourselves from repeating it."

The cleanup plugin's safety protocol uses a similar structure — every applied cleanup generates a report entry with the finding, the confidence level, the file:line, and the verification result. It is the same principle: permanent, auditable records of changes that would otherwise be invisible after the commit lands.

## CCSC v0.3.1: Security Hardening

claude-code-slack-channel cut v0.3.1 (PR `#23`) with a Scorecard-driven workflow hardening pass (`#26`): pinning actions to SHAs, removing unneeded permissions, hardening the Dockerfile. The release also landed deduplication for duplicate event delivery from `message` + `app_mention` events (`#8`), clean MCP server termination on client disconnect (`#7`), and governance scaffolding (`#10`).

Plus the smaller quality fixes: the CLAUDE.md line counts and dependency counts updated to match reality (`#22`), npm removed from dependabot because the project has no npm dependencies (`#20`), actions/upload-artifact bumped to v7.0.1 (`#21`), actions/checkout to v6 (`#17`), github/codeql-action to v4.35.2 (`#14`), and contributor credits corrected (`#24`). And `#9` enabled Gemini PR review joining the wild-ecosystem shared GCP project.

Nothing in that list is glamorous. The collective effect is a release that passes Scorecard at a higher grade than any previous release of the project. Quality is the sum of many small decisions.

## Why Velocity and Quality Weren't in Tension

A normal framing of this day would be: "a lot shipped, so corners must have been cut." That framing is wrong for this day, and the reason why is worth explaining.

The work on the cleanup plugin, the marketplace cleanup, the qmd quality sweep, and the CCSC hardening pass all share a structure: **each dimension has a specific detection pattern, a verification gate, and an auto-apply or flag-only default.** That structure means "cleanup" is not a vibe. It is a checklist with a risk-ordered execution plan.

When cleanup is a checklist, the work parallelizes. Three different projects can run their own dead-code-removal passes independently without coordination. The qmd team found `ConsoleDaemonLogger` still exported because they ran knip. The marketplace team found 978-line migration scripts because they grepped for files that nothing imported. Different codebases. Same pattern.

**Velocity comes from removing ambiguity about what "good" looks like.** The 11 dimensions are not opinions — they are observable properties. Something is either dead code or it is live code. A type is either strong or weak. A comment is either explanatory or noise. Arguing about whether to clean up is replaced with "run the dimension and check the confidence score."

The FLOPs correction is the same principle applied to research. Peer review said "this is the class of error most likely to hurt you." The team treated that as a checklist item, not a suggestion. When the error was found, the response was mechanical: update the sources, widen the claim, preregister a fallback. No ambiguity, no handwringing.

## Where This Fits

The broader arc is that AI-assisted development is producing more code, faster, than human review alone can catch. The Ultimate Code Cleanup plugin is one answer to that — a checklist framework an agent can run against its own output, with confidence scoring and build verification gates so the cleanup itself is accountable.

The plugin sits at `plugins/code-quality/code-cleanup/` in the claude-code-plugins marketplace. Installation is a standard plugin install. Once installed, `/cleanup-code` runs the full 11-dimension sweep with sensible defaults, and `--dimensions <list>` narrows to a subset. `--changed` scopes to the last 10 commits' files. Output is a structured report: summary table per dimension, applied changes with file:line references, flagged items with reasoning.

Typical invocations:

```
/cleanup-code                                       # full sweep
/cleanup-code --dimensions dead,types,security     # security-focused
/cleanup-code src/api/ --changed                   # only changed files in one dir
/cleanup-code --dimensions dry                     # single-dimension deep-dive
```

The safety checkpoint runs before any of this. If the git working tree is dirty, the tool refuses to start — it records the current commit SHA as a rollback point so an entire sweep can be reverted with one `git reset`. After each dimension that auto-applies, it runs the project's build and test commands. If either fails, only that dimension's changes revert. The other dimensions' changes persist.

That structure is load-bearing. It means you can run a full 11-dimension sweep on an unfamiliar codebase without fear that one bad detection poisons the rest of the cleanup. Each dimension is independent, verified, and revertable in isolation.

Every project in the portfolio is a candidate. The 24-hour window of April 15 was the proof that the portfolio is ready to start running this sweep at scale.

## Related Posts

- [QCSS Research Corpus: Twenty-One Documents and a Weak Reject](/blog/qcss-research-corpus-twenty-one-documents/) — the research-corpus arc that flagged the FLOPs class of error in its peer-review document.
- [Repo-Resolver in a Day: ADR to Integration](/blog/repo-resolver-adr-to-integration-one-day/) — the April 14 post on the same portfolio, different lens.
- [The Wild Ecosystem Deep Dive #4: Tech Lead](/blog/wild-deep-dive-4-tech-lead/) — the design philosophy behind risk-ordered execution plans, applied earlier in the wild ecosystem.

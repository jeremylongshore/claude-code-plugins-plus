---
title: "Two Releases, One Day: IntentCAD v0.6.0 and v0.7.0"
description: "Shipping two version releases in a single day — 22 commits, 5 EPICs, workflow packs, an evaluation harness, and the jump from CAD tool to drawing intelligence platform."
date: "2026-03-07"
tags: ["ai-agents", "architecture", "python", "release-engineering", "cad"]
featured: false
---
You don't ship two releases in one day by working twice as fast. You ship them because the architecture lets you.

March 7th: 22 commits, 2 version bumps, 5 completed EPICs, and a fundamental shift in what [IntentCAD](https://github.com/jeremylongshore/cad-dxf-agent) actually is. Here's how it happened and why the architecture made it possible.

## Why Two Releases

v0.6.0 was infrastructure. Session durability, workflow packs, evaluation harness, architecture review. The kind of work that doesn't change what users see — it changes what the system can handle.

v0.7.0 was the payoff. Objective-driven intents, document families, persistent storage. The features that only work because the infrastructure is solid.

Shipping them separately matters. If v0.6.0 breaks something, you know it's infrastructure. If v0.7.0 breaks something, you know it's the new intent layer. Clean boundaries make clean debugging.

## v0.6.0: Workflow Packs as Composable Units

The biggest idea in v0.6.0 is workflow packs. Not "features." Packs.

A construction drawing and a design drawing need fundamentally different operations. A machinist reviewing shop drawings needs dimension checks, tolerance verification, material callout validation. An architect reviewing design drawings needs space planning validation, code compliance checks, finish schedule verification.

Before workflow packs, these were all mixed together in a flat list of capabilities. The system could do all of them, but it had no concept of *context* — which operations belong together for a given task.

EPIC-CAD-09 (Design Operations) and EPIC-CAD-10 (Construction Drawing) split these into composable packs:

```python
class WorkflowPack:
    """A contextual group of operations for a specific drawing domain."""
    name: str
    domain: str  # "design" | "construction" | "fabrication"
    operations: list[Operation]
    validators: list[Validator]

    def applies_to(self, document: Document) -> float:
        """Confidence score that this pack is relevant."""
        signals = [
            self._check_layer_conventions(document),
            self._check_block_library(document),
            self._check_dimension_styles(document),
        ]
        return weighted_average(signals)
```

The system inspects the drawing and picks the right pack automatically. A document with layers named `S-BEAM`, `S-COLS`, and `S-FNDN` gets the construction pack. One with `A-WALL`, `A-DOOR`, and `A-FLOR` gets design. No user configuration. The drawing tells you what it is.

This matters for the evaluation harness.

## The Evaluation Harness: Automatically Verifying Drawing Changes

EPIC-CAD-12 solved a problem that had been nagging me since the comparison engine shipped. You can detect changes between two drawings. You can apply approved changes. But how do you know the *result* is correct?

Manual review doesn't scale. If the system modifies 47 entities across 12 layers in a construction drawing, someone has to verify each change against the original intent. That's the job of the evaluation harness.

The harness runs domain-specific validators from the active workflow pack against the modified drawing:

```python
class EvaluationHarness:
    def evaluate(self, original: Document, modified: Document,
                 intent: str, pack: WorkflowPack) -> EvalResult:
        changes = self.comparator.compare(original, modified)

        results = []
        for validator in pack.validators:
            result = validator.check(changes, intent)
            results.append(result)

        return EvalResult(
            passed=all(r.passed for r in results),
            violations=[r for r in results if not r.passed],
            coverage=len(results) / len(pack.validators),
        )
```

A construction pack validator might check: "Did the dimension change maintain tolerance callouts?" A design pack validator might check: "Did the space modification preserve egress path widths?"

Each validator returns pass/fail plus a violation report. The harness aggregates them into a coverage score — what percentage of relevant checks actually ran. Low coverage means the change touched areas the pack doesn't have validators for. That's a signal to flag for human review.

## Preview + Apply: The Trust Problem

EPIC-CAD-08 added a preview step before any modification lands. This sounds simple. It isn't.

The preview has to show exactly what *will* change without actually changing it. That means running the full comparison pipeline, computing all operations, rendering a diff view — and then throwing it all away if the user says no.

The naive approach (run everything twice) is too slow for large drawings. The solution is operation staging: the pipeline computes operations once, stages them in memory, and renders the preview from the staged ops. Apply just executes the staged ops. Cancel discards them.

This ties directly into session durability (EPIC-CAD-11). If the server restarts between preview and apply, the staged operations need to survive. Sessions now persist to disk with their full state — uploaded documents, staged operations, comparison results. Cloud Run can kill the instance and the user picks up where they left off.

Cloud Run got bumped to 8GB memory, 4 CPUs, and 600-second timeout for this release. Large PDF uploads were timing out at the previous limits.

## v0.7.0: From Tool to Intelligence Platform

This is where the architecture investment pays off.

EPIC-CAD-13 Area 2 introduced the objective-driven intent layer. Instead of telling the system *what* to do ("change this dimension to 24 inches"), you tell it *why* ("make this code-compliant").

The intent layer decomposes an objective into concrete operations:

```python
class IntentResolver:
    def resolve(self, objective: str, document: Document,
                pack: WorkflowPack) -> list[Operation]:
        """Translate a high-level objective into specific operations."""
        # Analyze document against objective
        analysis = self.analyzer.assess(document, objective)

        # Generate operations from pack's capabilities
        ops = []
        for gap in analysis.gaps:
            matching_ops = pack.operations_for(gap.category)
            parameterized = self._parameterize(matching_ops, gap)
            ops.extend(parameterized)

        return ops
```

"Make this code-compliant" becomes: check egress widths against IBC minimums, verify ADA clearances at doors, validate fire-rated assembly callouts. Each check comes from the active workflow pack. Each produces concrete operations if the drawing fails.

This only works because workflow packs exist. Without domain-specific operation groupings, the intent layer would need to know every possible drawing modification. With packs, it just needs to know which pack applies and what that pack can check.

## Document Families

EPIC-CAD-13 Area 1 added document family abstraction. Real construction projects don't have one drawing. They have dozens — floor plans, elevations, sections, details, schedules — all referencing each other.

Document families group related drawings so cross-reference validation works. A dimension on the floor plan should match the corresponding dimension on the section cut. A door schedule entry should have a matching door tag on the plan.

EPIC-CAD-15 made this practical with persistent document storage. Upload once, access always. No more re-uploading the same base drawing for every comparison. The system remembers your project documents and can pull them into family groups automatically.

## The Architecture Payoff

Here's why two releases in one day was possible.

Each EPIC has clean boundaries. Session durability doesn't know about workflow packs. The evaluation harness doesn't know about document families. The intent layer uses workflow packs but doesn't care how they're loaded.

When EPIC-CAD-08 (preview/apply) was done and tested, I tagged v0.6.0 and immediately started on EPIC-CAD-13. No integration phase. No "merge all the branches and pray" window. Each EPIC is independently deployable because each EPIC owns its own domain.

This is the payoff from Phase 1's comparison engine work. The canonical model, stable entity IDs, alignment ladder, confidence scoring — that foundation is rigid enough that five EPICs can land on top of it in a day without interfering with each other.

ARCH-REVIEW-CAD-01 confirmed this. The post-Phase 2 architecture review found no structural issues. The layering holds.

## Everything Else That Shipped

**Braves Booth** landed PR #22 — full pregame intelligence with post-game recap and mobile-first tab navigation. The broadcast dashboard now covers the complete game lifecycle: pregame stats, live updates, post-game analysis.

**Claude Code Plugins** hit v4.16.0 with 25 wondelai skills covering business, design, and marketing workflows. The validator got updated for the AgentSkills.io spec, and Axiom got converted from a broken Git submodule to a regular directory — fixing a clone issue that had been annoying contributors for weeks.

## What's Next

v0.8.0 planning is already laid out. IntentCAD is evolving from a CAD editing tool into a drawing intelligence platform. The workflow packs, evaluation harness, and intent layer are the foundation. What comes next is making the system understand *why* a drawing exists, not just what's in it.

---

**Related Posts:**

- [Building a Deterministic DXF Comparison Engine in One Day](/posts/deterministic-dxf-comparison-engine-one-day-build/) — the foundation that made this possible
- [Production Release Engineering: Shipping v4.5.0](/posts/production-release-engineering-v450/) — the release automation patterns behind shipping fast
- [Engine to Product: Three Interfaces, One Codebase](/posts/engine-to-product-three-interfaces-one-codebase/) — the previous IntentCAD evolution step

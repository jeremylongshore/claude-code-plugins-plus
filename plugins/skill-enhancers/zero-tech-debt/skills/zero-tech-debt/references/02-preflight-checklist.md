# Pre-Flight Checklist

Refactoring without these creates the next generation of tech debt. Every box must be checked **before** touching code. If any item is unchecked, resolve it before proceeding — even if that means asking the operator to write a test, identify a caller, or confirm a rollback path.

## The six checks

- [ ] **Tests exist (or can be written) for behavior worth preserving**
  Without tests, you can't tell the difference between "I removed a bug" and "I removed a load-bearing accident." Don't refactor a system whose tests assert the historical bug shape — fix those tests first, against intended behavior, then refactor.

- [ ] **Every external caller of the surface being changed has been identified**
  Use `rg` / `grep` / IDE call-graph tools across the whole repo. For library exports, also check downstream consumers if you can reach them. A refactor that breaks an unknown caller is worse than no refactor.

- [ ] **A rollback path exists** — branch, feature flag, or staged rollout
  If the change ships and breaks something subtle in production, what's the un-stuck plan? "Revert the merge commit" only works if the merge commit is reachable and the code that depended on the new shape hasn't shipped on top of it. For larger refactors, prefer a feature flag with a clean off-position.

- [ ] **The intended end state fits in 1-3 paragraphs**
  See workflow step 1 ([`03-workflow.md`](03-workflow.md)). If you can't describe the end state in plain prose, the refactor is not yet well-defined — and an under-defined refactor will drift into unbounded scope. Stop and clarify.

- [ ] **No active migration is in flight against the same code**
  Two simultaneous structural changes on overlapping surface area produce merge conflicts you can't resolve and behavior changes you can't attribute. If a migration is already running, defer the refactor or coordinate with the migration owner.

- [ ] **Telemetry, logging, and alerts tied to deleted code are accounted for**
  Dashboards, alert rules, log queries, and on-call runbooks may reference function names, log strings, or metric keys you're about to delete. Identify these *first*. Either update them in the same change or document the breakage explicitly and notify the on-call.

## Why this checklist is hard rules, not advice

Each item is the missing-step from a failure pattern that's already happened. The checklist exists because skipping any of them *predictably* produces:

- a refactor that ships against an unknown caller and breaks production
- a "successful" refactor whose tests passed because they were asserting the wrong behavior
- a refactor with no rollback path that has to be hot-patched at 2 AM
- a refactor that grows from "clean up one flow" to "rewrite three subsystems" mid-PR
- a refactor that merge-conflicts with someone else's in-flight migration
- a refactor whose deletion silently broke the on-call alerting

If you skip a check and the failure happens anyway, you don't get to claim it was unforeseeable.

## When the operator pushes to skip

If the operator says "we don't have tests for this, just refactor it" — that's a signal to write the characterization tests first, *as part of this work*, then refactor against them. The cost of writing one test is much lower than the cost of an undetected behavior change.

If the operator says "no time for a rollback path" — that's a signal that this isn't actually a zero-tech-debt refactor; it's a time-boxed patch, and you should switch tools.

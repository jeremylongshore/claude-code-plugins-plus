# PRD: 000-jeremy-content-consistency-validator

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-09
**Status:** Active

> Phase-1 contract per the 11-seat design council on issue #991 (synthesized 2026-07-07).
> Supersedes the 2026-07-07 PRD, which described the pre-council shell and its
> website-is-truth trust hierarchy — both deleted by council consensus. Architecture
> decisions and their dissents live in [`docs/ADR.md`](ADR.md).

## Problem

The marketplace's own flagship consistency tool doesn't run. Jeremy invokes
`/validate-consistency` constantly, and skill precedence resolves it to the global
`~/.claude/skills/validate-consistency` engine every time — the listed plugin is shadowed,
drifted into a thin 682-word shell, and is dead weight in its author's own catalog. That is
a credibility problem for a marketplace whose pitch is "the author uses his own plugins."

Worse than the shadowing is the contradiction underneath it: the two implementations
carry opposite truth axioms under one command name. The global engine declares "Code Is
Truth" (code > tests > CI > docs > README); the shell declares "Website Is Truth"
(website > GitHub > local docs). The same fact — a version string, a hosting claim — gets
arbitrated in opposite directions depending on which copy resolves. The council's verdict:
11/11 approve folding the real engine into the plugin and deleting the shell; 0/11 approve
the originally dictated scope (multi-agent roster, email/CRM surfaces) for v1.

## Target users

| User                          | Context                                                                                              | Primary need                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Jeremy (estate operator)      | Runs `/validate-consistency` across 40+ repos; the command silently bypassed the listed plugin       | The marketplace plugin to BE the canonical engine that actually runs               |
| Marketplace user              | Installs the flagship first-party plugin from tonsofskills.com                                        | The same engine the author uses daily — not a drifted shell with a stale axiom     |
| Release engineer              | `/release` Phase 1.6 invokes the audit before cutting a release                                       | Deterministic, fixture-gated findings trustworthy enough to gate a release        |
| Codebase onboarder            | New to a repo where README, CLAUDE.md, and code disagree                                              | Each finding filed against the drifted mirror, with the fact's declared owner named |

## Success criteria

1. **Shadowing resolved:** after Phase 1 lands, `/validate-consistency` executes the
   plugin's skill; the global skill is retired or thinned to a pointer, verified by skill
   resolution in the author's own environment.
2. **Net LOC down on the engine surface:** the skill + command + references surface
   (what an invocation actually executes) is smaller than the pre-fold shell + global
   skill combined — the council's "net LOC goes DOWN" applies to the contradiction-carrying
   protocol surface it was aimed at. The repo-level diff is net-UP because the council
   ALSO mandated a net-new golden-fixture corpus + deterministic checker (Phase-1 step 4);
   both numbers are stated honestly in the PR body rather than hiding the fixture cost.
3. **Fixture gate is red/green:** on the golden corpus (clean copy + N seeded drifts), a
   run reports exactly those N findings — right fact-class, right surfaces — and zero
   invented findings, wired as the plugin's required CI check. Nothing else proceeds until
   this gate exists.
4. **Structural separation holds:** zero LLM-judged findings ever appear at Critical or
   blocking severity, in fixtures or in real runs; every judged finding is labeled
   advisory.
5. **No guessing:** a fixture asserts that a fact-class with no registry row produces the
   exact emission "unowned fact-class — human adjudication needed" and nothing else.

## Functional requirements

- **FR-1:** Fold the global skill's engine into the plugin verbatim where possible — the
  9 deterministic drift checks, severity assignment rules, report format, and `/release`
  Phase 1.6 integration — and delete the shell together with its website-is-truth axiom.
  The plugin becomes the canonical implementation.
- **FR-2:** Resolve authority per fact-class from the checked-in registry
  (`sot-map.yaml`, home: intent-os): read the fact from its declared owner, read the
  mirrors, diff within the row's staleness bound. No global ranking; no runtime
  auto-detection (project-type detection survives only as a bootstrap for drafting
  registry rows). A fact-class with no row emits "unowned fact-class — human adjudication
  needed" and stops — never guess.
- **FR-3:** Structurally separate deterministic checks from LLM-judged ones: judged
  findings are advisory-only and can never be Critical or blocking.
- **FR-4:** Gate development on the golden fixture corpus: a fixture repo with seeded
  drifts plus a clean copy, with evals that assert findings ("exactly these N, zero
  invented"), not procedure, wired as a required CI check.
- **FR-5:** Preserve the read-only contract: no `Write`, no `Edit`, no git mutation
  anywhere in the tool surface. The report is the only artifact; no auto-fix, ever.

## Out of scope

Non-goals for Phase 1, each traceable to the council cut list (issue #991 synthesis §5):

- **The multi-agent roster** — the issue's original architecture item is cut for v1
  (Torvalds rejected the whole roster; Pike, Cunningham, Beck, backend-architect concur;
  Hickey caps any future roster at 3 roles). Deferred at most to the Phase-3 judged tail;
  the conflict with the attached Fable recommendation is open decision 5 below.
- **Email — entirely** — never an owner of anything (11/11 unanimous; "radioactive").
  Returns only if a concrete human-hit drift justifies its own separately-reviewed epic.
- **CRM/Twenty as a surface** — out of v1 ("actually absent, not stubbed"); the Phase-3
  gated path is assertion + opaque locator behind a red-team fixture.
- **WebSearch in the tool grant** — banned (security-auditor); the shell's stale
  `WebSearch` grant does not carry over.
- **Auto-fix or any mutation** — read-only is the contract (Armstrong, ai-engineer).
- **Pairwise N×N surface comparison** — replaced by the owner-vs-mirrors star topology
  (Huyen, ai-engineer).
- **Auto-detected source of truth at runtime** — bootstrap-only (Hickey, Huyen,
  Armstrong, security-auditor).
- **LLM in the normalization path, or LLM findings as Critical/blocking** — ai-engineer;
  Hickey, Huyen.
- **Auto-persist / hook-driven runs and credentialed readers in the public artifact** —
  security-auditor, Kleppmann. Persistence design is Phase 2.
- **Claiming "done" before the labeled regression corpus exists** — Huyen.

## Open decisions

All six remain OPEN. Owner: **Jeremy**. None may be resolved implicitly by an
implementation PR.

| #  | Decision                                                                                                                             | Status | Owner  |
| -- | ------------------------------------------------------------------------------------------------------------------------------------ | ------ | ------ |
| 1  | Brain role: arbiter of asserted company claims (majority synthesis) vs pure consumer with zero arbiter role (Torvalds/Beck fallback) | OPEN   | Jeremy |
| 2  | Email/CRM deferral: accept the Phase-3 gated path (assertion + locator, red-team fixture first), or overrule the council             | OPEN   | Jeremy |
| 3  | Public/private split: ship the marketplace listing without credentialed Plane/Twenty/Gmail readers (private overlay only)            | OPEN   | Jeremy |
| 4  | Record rigor: hash-chained evidence bundles vs plain dated markdown + JSONL in git (cheap in Phase 2, expensive to retrofit)         | OPEN   | Jeremy |
| 5  | Multi-agent recommendation: council defers the roster to the T2 tail; the attached Fable recommendation conflicts — needs a call     | OPEN   | Jeremy |
| 6  | Scheduling posture: deliberate opt-in runs only vs nightly cron estate sweep                                                          | OPEN   | Jeremy |

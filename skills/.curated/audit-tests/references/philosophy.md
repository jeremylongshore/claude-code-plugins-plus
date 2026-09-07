# Philosophy — Core Doctrine, Source Material, Invariants, and Lineage

## Contents

[Core Doctrine](#core-doctrine) · [Why this file exists](#why-this-file-exists) · [Source derivations](#section-1-source-derivations) · [Formal invariants of the Seven Walls](#section-2-formal-invariants-of-the-seven-walls) · [Escape-attempt grammar](#section-3-escape-attempt-grammar) · [The Human/AI boundary](#section-4-the-humanai-boundary) · [Why Wall 6 — CRAP on tests](#section-5-why-wall-6--crap-on-tests) · [Parallel dispatch](#section-6-parallel-dispatch) · [Lineage and credits](#section-7-lineage-and-credits) · [Sources](#sources)

## Core Doctrine

> This section is the canonical doctrine the skill operates under. It is
> loaded on every invocation — `SKILL.md` makes loading this file a
> mandatory first step. Every rule in `SKILL.md` assumes this is in
> context. Do not treat this as background; treat it as the running
> contract.

### YOU ARE THE ENGINEER

Deterministic tools do the grading. You own the walls. The AI operates
inside them.

The skill has two jobs — **install** a passing testing system where one
doesn't exist, and **audit** the one that does. The engineer reviews every
proposed change before it goes into git. The skill never commits silently.

### The AI Does Not Grade Itself

Every gate is a deterministic tool (pytest, radon, mutmut, dependency-cruiser,
harness-hash.sh). The AI cannot pass a gate by claiming it's passed; a tool
must return exit 0. Bypasses (skip markers, threshold edits, pragma comments,
rule-config mutation) are caught by `scripts/escape-scan.sh` and REFUSED.

### Ownership

| Artifact | Owner | AI role |
|---|---|---|
| `features/*.feature` (Wall 1 scenarios) | **Human** | hash-pinned, may not modify |
| `features/steps/` glue code | AI | must make scenarios pass |
| Unit tests | AI | writes and runs |
| Coverage thresholds | **Human (policy)** | may not lower |
| Mutation config | AI | writes; may not add bypass pragmas |
| CRAP thresholds | **Human (policy)** | may not raise |
| `.dependency-cruiser.js` / `.importlinter` / `deptrac.yaml` / ArchUnit rules | **Human** | hash-pinned, may not modify |
| Production code | AI | refactors to satisfy walls |

### The Seven Walls

| # | Wall | Tool(s) | Owner | Gate | On fail |
|---|------|---------|-------|------|---------|
| 1 | Acceptance (Gherkin) | Cucumber / behave / godog / Reqnroll / FitNesse | **Human writes .feature** | All scenarios green | AI cannot proceed |
| 2 | Unit tests | pytest / jest / vitest / go test / cargo test / JUnit / … | AI | 0 failing, 0 unauthorized skips | Rollback AI edit |
| 3 | Coverage floor | coverage.py / c8 / JaCoCo / tarpaulin | AI measures | Line ≥ N%, Branch ≥ M% | AI fills gaps |
| 4 | Mutation kill-rate | mutmut / Stryker / PITest / cargo-mutants | AI | ≥ 70% (S/A/B/C tiers) | AI strengthens assertions |
| 5 | CRAP on production code | radon+coverage / js-crap-score / Crap4j / SonarQube | AI refactors | No method CRAP > 30; avg ≤ 10 | Split method or add tests |
| 6 | CRAP on test code | same tools targeting tests/ | AI refactors | No test method CRAP > 15 | Split into single-behavior tests |
| 7 | Architecture / dependency rules | dependency-cruiser / import-linter / ArchUnit / deptrac / arch-go | **Human authors rules** | 0 violations | Invert dependency |

### Three Laws of TDD (Uncle Bob)

1. No production code without a failing test.
2. Just enough test to fail.
3. Just enough code to pass.

Cited verbatim: [butunclebob.com](http://www.butunclebob.com/ArticleS.UncleBob.TheThreeRulesOfTdd).

### FIRST Principles (Clean Code ch. 9)

| Letter | Meaning |
|---|---|
| F | Fast — fast enough to run every build |
| I | Independent — no test depends on another's state |
| R | Repeatable — same result in any environment |
| S | Self-validating — boolean pass/fail, no log reading |
| T | Timely — written just before the production code that makes it pass |

### Clean Architecture Dependency Rule

Source-code dependencies point inward; inner layers know nothing of outer
layers. Enforced by Wall 7 — see
`{baseDir}/references/architecture-constraints.md`.

### Two Operating Modes

**IMPLEMENT mode (primary)** — on invocation, the default assumption is
"this repo needs walls built." For every wall missing or below standard, the
skill scaffolds the config, installs the tooling, writes starter artifacts,
wires CI, and initializes hash manifests. Every file is staged on disk for
engineer review; nothing is committed automatically.

**AUDIT mode** — walks the repo, runs every gate that exists, produces a
pass/fail report. Non-destructive. The 8-step pipeline in `SKILL.md` is
AUDIT mode. IMPLEMENT mode re-runs AUDIT after installation to prove the
new system is green.

Both modes share the same Seven Walls as their source of truth.

## Why this file exists

`SKILL.md` is the operational routing and pipeline document. This file is
the canonical home of the doctrine the skill operates under, along with the
source material, formal invariants, escape-grammar, and lineage. It exists
so that a skeptical reader — Uncle Bob at the worst, a compliance reviewer
at the mildest — can verify every claim in the doctrine against an
authoritative source, audit the escape-scan state machine, and understand
the Human/AI ownership boundary without having to reverse-engineer it from
scripts.

**Nothing in this file is optional.** The doctrine in § Core Doctrine above
is loaded at the start of every invocation. The sections below
(source derivations, formal invariants, escape-grammar, Wall-6 rationale,
lineage) reinforce and cite that doctrine — they do not weaken it. If this
file and `SKILL.md` ever drift, the Core Doctrine here is authoritative;
`SKILL.md` is expected to re-point at it.

## Section 1: Source derivations

### 1.1 The Three Laws of TDD

Stated in `SKILL.md`:

> 1. No production code without a failing test.
> 2. Just enough test to fail.
> 3. Just enough code to pass.

Original, verbatim from Robert C. Martin:

> 1. You are not allowed to write any production code unless it is to make a
>    failing unit test pass.
> 2. You are not allowed to write any more of a unit test than is sufficient
>    to fail; and compilation failures are failures.
> 3. You are not allowed to write any more production code than is
>    sufficient to pass the one failing unit test.

Source: *The Three Rules of TDD*, butunclebob.com. The site is the canonical
public record of Martin's rules and has carried this text since 2005-ish.

Why the skill's phrasing is shorter: the harness only enforces the *result*
(test fails → test passes → no more code). The laws' compilation-failure
clause is pedagogically useful but redundant for an automated gate.

### 1.2 FIRST Principles

Stated in `SKILL.md`: a 5-row table mapping F·I·R·S·T to Fast · Independent ·
Repeatable · Self-validating · Timely.

Source: *Clean Code*, Robert C. Martin, 2008, Prentice Hall, chapter 9
("Unit Tests"), p. 132. The mnemonic is Martin's; the expanded one-line
glosses in the `SKILL.md` table are condensed from that chapter.

Why it lives in the preamble rather than a reference: FIRST is diagnostic —
the audit checks every test against all five letters. Keeping it one hop
from the runner prevents accidental drift (e.g., a "fast but flaky" test
that would satisfy F while silently failing R).

### 1.3 The Dependency Rule (Clean Architecture)

Stated in `SKILL.md`:

> Source-code dependencies point inward; inner layers know nothing of outer
> layers.

Source: Robert C. Martin, *The Clean Architecture*, August 2012, blog post
at cleancoder.com. Also chapter 22 of *Clean Architecture* (2017,
Prentice Hall), p. 203.

The original formulation:

> This rule says that source code dependencies can only point inwards.
> Nothing in an inner circle can know anything at all about something in an
> outer circle.

Wall 7 is a direct machine-checkable translation of this rule. The skill's
enforcement is done by whichever dependency scanner fits the language
(`dependency-cruiser`, `import-linter`, `deptrac`, `ArchUnit`, `arch-go`),
but every implementation is grounded in this single 2012 post.

### 1.4 CRAP (Change Risk Analyzer and Predictor)

Stated in `SKILL.md`:

> Gate: no method CRAP > 30; avg ≤ 10. [Wall 5]
> Gate: no test method CRAP > 15. [Wall 6]

Formula (from `crap-score.py` and Wall-5 gate):

```
CRAP(m) = CC(m)² × (1 − cov(m))³ + CC(m)
```

Where `CC(m)` is the cyclomatic complexity of method *m* and `cov(m)` is
the fraction of its statements covered by passing tests (0–1).

Origin: *CRAP4J: A Java Implementation of the Change Risk Analyzer and
Predictor*, Alberto Savoia and Bob Evans, 2007. Paper presented at AGILE
Conference 2007; tool at crap4j.org (historical; the domain has rotated but
the Internet Archive preserves it). Contemporary implementations include
`NDepend`'s CRAP score, OtterWise's `crap-score`, and `js-crap-score` on
npm.

Threshold derivation:

- **CRAP = 30 is the original "not acceptable" line** Savoia publicly cited
  in 2007 — a 10-complexity method needs ≈ 55% coverage to score 30; a
  15-complexity method needs ≈ 90%.

- **CRAP ≤ 10 as project average** corresponds to either simple methods
  (CC ≤ 3) regardless of coverage, or modestly complex methods (CC ~ 5)
  with full coverage.

- **CRAP ≤ 15 on tests (Wall 6)** is a skill-local tightening; the paper
  did not contemplate scoring tests. See Section 5 for the rationale.

## Section 2: Formal invariants of the Seven Walls

Each wall's gate, stated as a pre/post-condition the harness enforces.
The pre-condition is checked by discovery/pre-flight; the post-condition is
the exit-0 contract.

### Wall 1 — Acceptance (Gherkin)

- **Pre**: `features/` exists; hash manifest covers every `.feature` file.
- **Post**: `runner` returns exit 0 ∧ every scenario is GREEN ∧
  `harness-hash.sh --verify` returns exit 0.

- **Violation ⇒** `HARNESS_TAMPERED` or `SCENARIO_FAILED`. The AI cannot
  proceed to Walls 2–7.

### Wall 2 — Unit tests

- **Pre**: a test runner is detected (pytest, vitest, jest, go test, …).
- **Post**: `runner` returns exit 0 ∧ `skip_count ≤ approved_skip_budget` ∧
  zero tests are marked `only`/`focus`/`fit`.

- **Violation ⇒** AI edit is rolled back. Repeat; do not mask.

### Wall 3 — Coverage floor

- **Pre**: coverage tool is configured (coverage.py, c8, JaCoCo, tarpaulin).
- **Post**: `line_cov ≥ N` ∧ `branch_cov ≥ M` where `(N,M)` are engineer-
  authored policy, recorded in the hash manifest.

- **Violation ⇒** AI writes tests (not threshold edits). The threshold is
  human-owned and hash-pinned.

### Wall 4 — Mutation kill-rate

- **Pre**: mutation tool is installed (mutmut, Stryker, PITest, cargo-mutants).
- **Post**: `kill_rate ≥ 70%` (A-tier) across the mutated scope.
- **Violation ⇒** AI strengthens assertions; harness forbids adding
  `# pragma: no mutate` to silence survivors.

### Wall 5 — CRAP on production code

- **Pre**: complexity tool available for the detected language.
- **Post**: ∀ *m* ∈ production_methods : `CRAP(m) ≤ 30` ∧
  `mean(CRAP) ≤ 10`.

- **Violation ⇒** split method, add targeted tests, or refactor. Never
  suppress.

### Wall 6 — CRAP on test code

- **Pre**: same complexity tool, pointed at `tests/`.
- **Post**: ∀ *t* ∈ test_methods : `CRAP(t) ≤ 15`.
- **Violation ⇒** split the test into single-behavior tests. Complex tests
  are evaluated more strictly than complex production code because they
  are themselves the oracle.

### Wall 7 — Architecture / dependency rules

- **Pre**: rule config exists and its SHA-256 is in the hash manifest.
- **Post**: `checker` returns exit 0 ∧ zero violations ∧
  `harness-hash.sh --verify` returns exit 0 for the rule file itself.

- **Violation ⇒** invert the dependency. The AI may not edit the rule file
  — that path leads to `HARNESS_TAMPERED`.

## Section 3: Escape-attempt grammar

The harness treats certain diff shapes as attempts to lower a wall rather
than meet the bar. `scripts/escape-scan.sh` implements a three-state
machine over proposed diffs.

### 3.1 States

- `ACCEPT` — diff contains no escape pattern; passes.
- `CHALLENGE` — diff contains a conditional escape (e.g., test skip with no
  comment). Pipeline halts; engineer must either add an approved reason or
  remove the pattern.

- `REFUSE` — diff contains an unconditional escape (e.g., threshold
  lowered, hash-pinned file modified). Pipeline halts; no engineer comment
  can approve in-place; a policy change is required first.

### 3.2 Transition table

| Diff pattern | Scope | Transition | Reason |
|---|---|---|---|
| `@pytest.mark.skip`, `.skip`, `.only`, `@Ignore`, `@Disabled` | test files | → CHALLENGE | skips may be legitimate but need an engineer-approved reason |
| `fail_under` lowered, `coverageThreshold` lowered, `--cov-fail-under` reduced, JaCoCo `minimum` lowered | config files | → REFUSE | threshold is policy; requires a policy change |
| `# pragma: no mutate`, `// Stryker disable`, `@DoNotMutate` | production code | → CHALLENGE | may be justified for unreachable branches; needs reason |
| `depcruise-disable`, `@ArchIgnore`, deptrac `skip_violations`, import-linter `ignore_imports` | architecture rules | → REFUSE | bypasses the dependency rule itself |
| Any byte change to a hash-pinned `.feature` | `features/*.feature` | → REFUSE | `HARNESS_TAMPERED` |
| `assertTrue(True)`, `toBeDefined()` replacing a stronger prior assertion | test files | → CHALLENGE | weakens the oracle |
| Test file deleted with no compensating additions | test files | → REFUSE | removes the wall |
| Rule-config file modified (`.dependency-cruiser.js`, `.importlinter`, `deptrac.yaml`, `ArchTest*.java`) | root | → REFUSE | hash-pinned |

### 3.3 Exit codes

- `0` — ACCEPT
- `1` — CHALLENGE (halt; engineer approval required)
- `2` — REFUSE (halt; policy change required)

The distinction matters because CHALLENGE-halts are recoverable through a
reviewed comment; REFUSE-halts require the engineer to touch a hash-pinned
or policy-pinned file explicitly and re-initialize the manifest.

## Section 4: The Human/AI boundary

Not every artifact in a repo is equal. Some encode *business intent* (what
the software is for); others encode *implementation* (how it achieves that
intent). The skill draws the line so that an AI cannot accidentally rewrite
the intent while refactoring the implementation.

### 4.1 Why `.feature` files are hash-pinned

`.feature` files are *prose specifications* of business behavior written in
Gherkin. In Dan North's original BDD formulation (*Introducing BDD*, 2006,
dannorth.net), the Given/When/Then syntax exists precisely because it is
accessible to non-engineers — product owners, domain experts, acceptance
reviewers. Corrupting the scenario text means corrupting the specification
itself.

Step definitions — the Python/JS/Go glue code that executes a scenario —
are a different artifact. They translate intent into runnable tests and are
a fair target for AI refactoring: changing a regex, adjusting a selector,
parallelizing a step. The intent itself stays unchanged.

Reference: the Cucumber project's *Writing Better Gherkin* guide
(cucumber.io/docs/bdd/better-gherkin/) formalizes this ownership split.

### 4.2 Why rule-config files are hash-pinned

A dependency rule (`.dependency-cruiser.js`, `.importlinter`, `deptrac.yaml`,
ArchUnit `ArchTest*.java`) is a *policy document*. It states what the
engineer will not permit regardless of convenience. If the AI could edit
it, the AI could make any violation disappear by rewriting the rule — the
same shape of failure as an AI editing `fail_under` to pass coverage.

Hash-pinning the rule file means: to change a rule, an engineer opens the
file, edits it, and re-runs `scripts/harness-hash.sh --init`. The rotation
of the hash is a deliberate, human-initiated action.

### 4.3 Why coverage and CRAP thresholds are human-owned

Same reasoning. "Acceptable risk" is a human judgment. The AI's job is to
meet the threshold; the engineer's job is to set it.

### 4.4 What the AI owns

- Step-definition code (Walls 1 glue).
- Unit tests (Wall 2).
- Refactors of production code to satisfy complexity or architecture gates.
- Additions to mutation configuration, *excluding* bypass pragmas.
- Remediation diffs, subject to escape-scan.

### 4.5 What neither owns

Nothing. Every artifact has an owner. Ambiguity is how test harnesses rot.

## Section 5: Why Wall 6 — CRAP on tests

The one gate on this list that's *not* in the textbook. Why is it here?

A test is itself an oracle: it decides whether production code is correct.
A complex test — nested conditionals, loops, multi-assertion chains —
fails in ways that are hard to diagnose, and its own correctness becomes a
question. Worse, mutation testing routinely survives more mutations against
complex tests than simple ones, because the test's own branches mask the
production code's behavior.

The mutation-testing literature has circled this question for over a
decade. Relevant surveys:

- Yue Jia & Mark Harman, *An Analysis and Survey of the Development of
  Mutation Testing*, IEEE TSE, 2011. Section 5 discusses test-suite
  complexity as a confound in kill-rate interpretation.

- René Just et al., *Are Mutants a Valid Substitute for Real Faults in
  Software Testing?*, FSE 2014. Finding: test complexity correlates with
  false-negative mutation survivors.

The skill's response is the tighter `CRAP ≤ 15` gate on tests (half of the
production ceiling). The threshold is empirical, not derived; Jeremy set it
after observing that test methods with CRAP > 15 were disproportionately
the source of escape survivors in real audits. If the community converges
on a different number, the gate moves — the *principle* that tests deserve
their own complexity ceiling is the durable claim.

## Section 6: Parallel dispatch

IMPLEMENT mode may need to scaffold several walls in the same invocation
(install Gherkin runner + emit CRAP config + write arch rules + initialize
hash manifest). These are independent operations against disjoint file
sets.

The skill's `allowed-tools` list includes `Task`. That permits the
IMPLEMENT routine to dispatch per-wall scaffolding to an ephemeral
`general-purpose` subagent. The architectural intent:

- **No persistent agent files.** Files under `~/.claude/agents/` load into
  every Claude Code session. The skill refuses to add weight to the
  always-on context.

- **Task-tool fan-out is ephemeral.** Each subagent lives only for its
  scaffolding step, returns its diff, and terminates. The main skill
  assembles the collected diffs into a single review surface for the
  engineer.

- **Engineer review is serialized.** Even when scaffolding runs in
  parallel, diffs are staged to disk and presented to the engineer in a
  deterministic order (Wall 1 → 7). Nothing is committed until the
  engineer approves.

This is an orchestration choice, not a requirement. A sequential
implementation is correct, just slower.

## Section 7: Lineage and credits

This skill has a traceable intent. Preserved here so a future reader
understands the judgment calls.

### Jeremy Longshore — original directives

- "The engineer owns the walls; the AI operates inside them." — became the
  preamble in `SKILL.md`.

- "The AI does not grade itself." — became the hard rule that every gate
  is a deterministic tool with an exit code.

- "Do not replace the philosophy; evolve it." — governs this file: nothing
  here substitutes for the `SKILL.md` preamble; everything additive.

### Robert C. Martin — the grader

The skill is designed so that Martin could read `SKILL.md` and find nothing
to disagree with. The Three Laws, FIRST, the Dependency Rule, and the
"tests are code too" consequence (Wall 6) are all Martin's. Where the skill
extends beyond his published work (Wall 6 threshold, escape-scan state
machine), it extends *in his direction* rather than against it.

### Dan North — BDD and the acceptance wall

Wall 1's ownership model — humans write scenarios, the tool makes them pass
— comes directly from North's 2006 BDD essay. The hash-pin is an
operational reinforcement of North's original social contract.

### Alberto Savoia — CRAP

Wall 5 is a line-for-line implementation of the 2007 CRAP paper's formula
and acceptance threshold. Wall 6 is an original extension.

### Simon Willison — skill-design rationale

Willison's October 2025 skill-design posts established two practical
principles this skill follows: progressive disclosure works, and concrete
examples beat abstract guidance. The 8-step pipeline in `SKILL.md`
references eleven lazy-loaded files (including this one) rather than
inlining their content — that's Willison's pattern.

### Anthropic — the 500-line hard cap

The SKILL.md body-length limit (500 lines, enforced by the platform) is a
constraint the skill lives under. The preamble in `SKILL.md` is 69 lines
and stays — the trade is: spend those lines on philosophy that must load
every time, and keep everything else one hop away.

## Sources

- Robert C. Martin, *The Three Rules of TDD*, butunclebob.com.
- Robert C. Martin, *Clean Code*, Prentice Hall, 2008. Ch. 9.
- Robert C. Martin, *The Clean Architecture*, cleancoder.com, August 2012.
- Robert C. Martin, *Clean Architecture*, Prentice Hall, 2017. Ch. 22.
- Alberto Savoia & Bob Evans, *CRAP4J: A Java Implementation of the
  Change Risk Analyzer and Predictor*, AGILE 2007; crap4j.org (archived).

- Dan North, *Introducing BDD*, dannorth.net, March 2006.
- Cucumber project, *Writing Better Gherkin*, cucumber.io/docs/bdd/better-gherkin/.
- Yue Jia & Mark Harman, *An Analysis and Survey of the Development of
  Mutation Testing*, IEEE TSE 37(5), 2011.

- René Just et al., *Are Mutants a Valid Substitute for Real Faults in
  Software Testing?*, FSE 2014.

- Simon Willison, *Skills: A new way to extend Claude*, simonwillison.net,
  October 2025.

- Anthropic Skills specification, code.claude.com / platform.claude.com,
  2026.

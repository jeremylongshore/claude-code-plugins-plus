# Content Consistency Validator (v3)

**Universal document consistency auditor. Deterministic drift checks across docs, code, tests, and CI — conflicts resolved through a per-fact-class authority registry, never a global ranking. Read-only: it reports, it never fixes.**

## What Changed in v3

v3 folds the full consistency-audit engine into this plugin and retires the v1/v2 shell (design council, issue #991):

- **The "website is truth" axiom is gone.** No source is globally authoritative anymore. Authority is declared per fact class, as data, by a human — in `sot-map.yaml`.
- **Deterministic and LLM-judged checks are structurally separated.** Judged findings are advisory-only: never Critical, never blocking.
- **Email/CRM sources are out of scope for v1 of this model.** No WebSearch, no WebFetch — filesystem and git only.
- **The multi-agent roster is deferred** pending open design decisions. Phase 1 ships one skill plus a thin command; no agents.
- **Fixture-gated.** The quality gate is a golden fixture corpus with seeded drifts; evals assert exact findings ("exactly these N, zero invented"), not procedure.

## How It Works

1. **Load the authority registry** — `sot-map.yaml` (default `~/000-projects/intent-os/sot-map.yaml`, path configurable). Each row maps a fact class (e.g. `version-string`, `license`, `ci-commands`) to the artifact class that owns it.
2. **Inventory artifacts** — README, CLAUDE.md, CHANGELOG, `000-docs/`, `docs/`, `planning/`, CI workflows, package manifests.
3. **Run the 9 drift checks** (below), each tagged deterministic or LLM-judged.
4. **Resolve conflicts through the registry.** A conflict on a registered fact class is filed against the non-authoritative artifact. A conflict on an unregistered fact class is emitted as `unowned fact-class — human adjudication needed` — no winner is ever guessed.
5. **Report** — Part A deterministic findings (Critical/Warning/Info), Part B advisory findings (LLM-judged), unowned-fact-class callouts, and bootstrap-drafted registry rows for human review.

### The 9 Checks

| Check | Category | Lane |
|-------|----------|------|
| 3.1 Index vs filesystem | Index/Reference Drift | Deterministic |
| 3.2 Version string consistency | Status Drift | Deterministic (`version-string`) |
| 3.3 README commands vs CI workflows | CI/Validation Drift | Deterministic (`ci-commands`) |
| 3.4 CLAUDE.md references vs actual docs | Index/Reference Drift | Deterministic |
| 3.5 Stale phase/status language | Status Drift | LLM-judged — advisory |
| 3.6 Capability claims vs code | Capability/Behavior Drift | LLM-judged — advisory |
| 3.7 Cross-doc fact comparison | Cross-Doc Contradiction | Deterministic (license, runtime, repo URL); advisory (description) |
| 3.8 Broken cross-references | Index/Reference Drift | Deterministic |
| 3.9 Planning vs implementation | Planning-vs-Implementation | LLM-judged — advisory |

### The Registry Model

`sot-map.yaml` is the source of truth for *who owns which fact* — declared as data, adjudicated by a human:

```yaml
version: 1
fact_classes:
  version-string:
    authority: package-manifest
    adjudicated_by: jeremy
    adjudicated_on: YYYY-MM-DD
```

- **No row → no guess.** Unowned fact classes are reported for human adjudication.
- **Bootstrap mode.** Without a registry, the skill still detects every conflict, names no winners, and drafts proposed rows (using project-type detection and the retired legacy hierarchy purely as a drafting heuristic). A human reviews and commits the rows — the skill never writes `sot-map.yaml`.
- **Truth invariant.** The governed brain arbitrates asserted company/doctrine claims and the rules — never generated facts. The validator never reads the brain as ground truth for generated facts, and the brain ingests only human-adjudicated findings.

Full specification: `skills/validate-consistency/references/sot-registry.md`.

## Installation

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install 000-jeremy-content-consistency-validator@claude-code-plugins-plus
```

## Usage

```bash
/validate-consistency
```

Or naturally: "check consistency", "validate docs", "audit documentation", "doc drift check".

Also invoked automatically by `/release` during Phase 1.6 — deterministic 🔴 Critical findings feed the release blocking gate; advisory findings are surfaced for review and never block.

## Read-Only Guarantee

The skill's tool grant is `Read, Glob, Grep, Bash(echo:*), Bash(git:*), Bash(diff:*)` — no Write, no Edit, no WebSearch, no WebFetch. It reports discrepancies with file paths and line numbers; you decide what to fix.

## Scope (Phase 1)

- One skill (`validate-consistency`) + one thin command. The multi-agent roster from the original design is **deferred** pending open decisions.
- Sources: local filesystem + git. Email/CRM auditing is out of v1 entirely.
- Quality gate: golden fixture corpus with seeded drifts — evals assert exact findings, zero invented.

## License

MIT — see LICENSE.

## Support

- **Issues:** https://github.com/jeremylongshore/claude-code-plugins/issues
- **Email:** jeremy@intentsolutions.io

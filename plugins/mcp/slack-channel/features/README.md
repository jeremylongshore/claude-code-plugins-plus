# `features/` — Acceptance-level contracts

These `.feature` files are the acceptance-level contracts for the
four-principal security model. They describe, in declarative business
language, what each security primitive promises to do on the boundary
between Claude, the Slack workspace, the operator's disk, and peer
bots.

## Primitives covered

| File | Primitive | Source |
|---|---|---|
| `inbound_gate.feature` | `gate()` | `lib.ts` |
| `file_exfiltration_guard.feature` | `assertSendable()` | `lib.ts` |
| `outbound_reply_filter.feature` | `assertOutboundAllowed()` | `lib.ts` |
| `policy_evaluation.feature` | `evaluate()` | `policy.ts` |
| `audit_chain_verifier.feature` | `verifyJournal()` | `journal.ts` |

## Ownership rule (engineer-owned)

Per the `/audit-tests` skill's Wall 1 rule, these scenarios are
engineer-owned. AI tooling may add step definitions, wire runners, or
refactor adjacent glue code. AI tooling **must not** edit the scenarios
themselves — a byte-level change to any `.feature` file will fail
`harness-hash.sh --verify` and `escape-scan.sh` will refuse the diff.

To update a scenario:

1. An engineer edits the `.feature` file.
2. An engineer runs `bash scripts/harness-hash.sh --init` to regenerate
   the manifest.
3. The updated `.feature` file and the new `.harness-hash` land in the
   same commit.

## Runner status — fully wired (ccsc-mjw)

The runner is wired. All 37 scenarios across the five feature files
execute as bun:test tests via `features/runner.test.ts`. Run them
alongside the main suite:

```bash
bun test                         # runs server.test.ts + features/runner.test.ts
bun test features/runner.test.ts # features only
```

Architecture:

| File | Role |
|---|---|
| `features/runner.ts` | Gherkin parser + StepRegistry + buildRunner (no bun:test imports) |
| `features/runner.test.ts` | bun:test entry — discovers .feature files, wires step defs, runs |
| `features/steps/gate.ts` | Step defs for `inbound_gate.feature` → `gate()` in `lib.ts` |
| `features/steps/sendable.ts` | Step defs for `file_exfiltration_guard.feature` → `assertSendable()` |
| `features/steps/outbound.ts` | Step defs for `outbound_reply_filter.feature` → `assertOutboundAllowed()` |
| `features/steps/policy.ts` | Step defs for `policy_evaluation.feature` → `evaluate()` in `policy.ts` |
| `features/steps/journal.ts` | Step defs for `audit_chain_verifier.feature` → `verifyJournal()` |

The CI lint gate still runs and guards the .feature files from
imperative-verb / structural violations:

```bash
bash scripts/gherkin-lint.sh --path features/ --strict
```

## Pinning (tamper guard)

The manifest at `.harness-hash` pins every `.feature` file here, plus
the architecture rule configs and coverage thresholds. The tamper
guard runs in CI:

```bash
bash scripts/harness-hash.sh --verify
```

If the verifier reports `HARNESS_TAMPERED`, the PR is refused until
the manifest is re-generated via `--init` and committed alongside the
content change.

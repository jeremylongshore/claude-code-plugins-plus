---
name: snowflake-native-app-release-sheriff
description: |
  Preflight a provider-side Snowflake Native App version or patch from redacted
  manifest, setup-script, security-scan, release-channel, upgrade-cohort, and
  rollback evidence. Use when preflighting registration or a Native App release,
  when a setup retry or application-role change may break grants, when privilege
  or App Spec requests changed, or when a channel is at its version limit. Emits
  a deterministic release gate and dry-run remediation/rollback packet. It never
  publishes, registers, upgrades, drops, grants, changes a release directive, or
  runs mutating SQL. Trigger with "Native App release preflight", "setup script
  idempotence", "application package scan status", "release channel version
  limit", "App Spec delta", or "Native App rollback cohort".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[redacted-native-app-release-evidence.json]"
version: 2.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+ and redacted provider-side evidence
tags: [saas, snowflake, native-app, release, security-scan, rollback]
---

# Snowflake Native App Release Sheriff

## Purpose

Decide whether one provider-side Native App version or patch is ready for a
separately approved release action. Compare it with the immediately prior release,
check every target channel and cohort, and emit a hash-bound read-only receipt
without publishing or changing Snowflake.

## Safety boundary

- Never execute `REGISTER`, `DEREGISTER`, `ADD VERSION`, `DROP VERSION`, `SET
  RELEASE DIRECTIVE`, `ALTER APPLICATION ... UPGRADE`, `GRANT`, `REVOKE`, or any
  package, listing, application, role, privilege, or App Spec mutation.
- Never run a setup script against a consumer or provider application. Analyze a
  normalized dry-run receipt from an isolated test account or CI harness.
- Never turn a green QA preflight into a security-scan claim. Adding a candidate
  only to QA does not initiate the automated scan; ALPHA or DEFAULT does.
- Never infer a completed version removal from a submitted drop request. Removal
  is asynchronous until consumers upgrade and old-version code finishes.
- Reject credentials, raw SQL, customer data, presigned URLs, or private keys.

## Prerequisites

- Python 3.10+ and the skill directory containing this `SKILL.md`.
- One redacted JSON receipt following the evidence contract, produced from an
  immutable candidate bundle and static parser/CI outputs.
- Provider-side read-only observations for scan, channel, cohort, and retirement
  state. Use an existing least-privilege profile; the skill neither accepts nor
  configures credentials.
- A named release owner and an already-tested prior artifact for the dry-run
  rollback packet.

## Evidence contract

Read [`references/evidence-contract.md`](references/evidence-contract.md) before
building or correcting an input receipt. Evidence must bind one candidate
artifact and its manifest/setup pair to an `as_of` timestamp, exact hashes,
source-review entries, scan observation, channel inventories, cohort denominator,
compatibility tests, proposed retirements, and dry-run rollback observables.

Critical release realities:

- Snowflake restarts a failed setup script from the beginning. Require a clean
  fresh-install test, restart-from-beginning test, and repeated-run test.
- Prefer `CREATE APPLICATION ROLE IF NOT EXISTS`. `CREATE OR REPLACE APPLICATION
  ROLE` drops and recreates the role and can lose account-role grants.
- A QA-only candidate may remain `NOT_REVIEWED`; a candidate targeted to ALPHA or
  DEFAULT must reach `APPROVED`. `IN_PROGRESS` and `REJECTED` are blockers.
- Each release channel may hold at most two simultaneous versions.
- A version-removal request remains pending until no consumer or running code is
  left on that version.
- A patch must not introduce state changes or a manifest privilege/version delta.
  A version upgrade must be compatible with the immediately prior version.

## Workflow

1. Fix the candidate artifact, version/patch, change kind, intended channels, and
   UTC `as_of`. Record hashes; labels such as `latest` are not evidence.
2. Normalize the previous and candidate manifests. Compare manifest version,
   setup-script path, privileges, references, and App Spec definitions/sequences.
   Disclose every consumer-visible privilege or App Spec delta.
3. Parse the setup script into normalized statement evidence. Test fresh install,
   restart from statement one after injected failure, repeat execution, and the
   immediately-prior-version upgrade. Do not include SQL text in the receipt.
4. Collect `SHOW VERSIONS IN APPLICATION PACKAGE` and release-channel output
   using an existing read-only profile, then redact identifiers as required. Bind
   each channel and cohort to fresh timestamps and complete counts. Read
   [`references/source-notes.md`](references/source-notes.md) when verifying the
   current Snowflake behavior or release-note boundary.
5. Run the deterministic analyzer:

   ```bash
   python3 "<skill-directory>/scripts/analyze_native_app_release.py" \
     --input ./native-app-release-evidence.json \
     --output ./native-app-release-report.json
   ```

   Resolve `<skill-directory>` to the directory containing this `SKILL.md`.

6. Stop on `BLOCKED`. Resolve the named evidence gap and create a new receipt.
   `READY_FOR_EXPLICIT_APPROVAL` means preflight evidence is
   complete; it does not authorize registration, scan initiation, publication,
   upgrade, privilege approval, release-directive changes, or removal.
7. Hand the emitted `dry_run_packet` to the change owner. Read
   [`references/remediation-and-rollback.md`](references/remediation-and-rollback.md)
   for its approval boundary and rollback-observable semantics.

## Release decision rules

- `BLOCKED`: malformed/missing/stale evidence; setup non-idempotence; application-
  role replacement; unsupported patch delta; unresolved privilege/App Spec delta;
  non-approved ALPHA/DEFAULT scan; rejected/in-progress scan; channel overflow;
  incomplete cohort; compatibility failure; pending retirement; or unbounded
  rollback observables.
- `READY_FOR_EXPLICIT_APPROVAL`: no findings remain and every denominator is
  complete. This is a read-only preflight result, never a release receipt.

## Output

Return sorted findings with observed/derived/missing evidence state, candidate and
delta summaries, channel projections, cohort coverage, scan state, compatibility,
and a SHA-256 receipt. The `dry_run_packet` contains ordered read-only remediation,
rollback target and artifact hashes, owner, stop conditions, observable thresholds,
and explicit prohibited actions. Preserve it unchanged for operator review.

## Error handling

Malformed JSON, fake booleans/numbers, naive/future timestamps, invalid hashes,
unknown scan/channel/change states, duplicate names, raw SQL, secret-shaped fields,
or credential-shaped values exit with code 2 and no partial report. Missing or
stale release evidence becomes a blocking finding. A permission failure is an
evidence gap, not permission to escalate privileges.

## Examples

If a QA candidate is `NOT_REVIEWED`, the channel stays within two versions, all
tests and cohorts pass, and rollback observables are complete, the analyzer may
return `READY_FOR_EXPLICIT_APPROVAL` with an explicit no-scan claim. If that same
candidate targets ALPHA, it is `BLOCKED` until an operator adds it and the scan is
observed as `APPROVED` in a new read-only receipt.

If setup evidence contains `CREATE OR REPLACE APPLICATION ROLE`, report
`APPLICATION_ROLE_REPLACE_GRANT_LOSS` even if later statements re-grant internal
object privileges: account roles granted to the old application role can be lost.

## Resources

- [`references/evidence-contract.md`](references/evidence-contract.md) - exact
  input schema, receipt bindings, freshness, and privacy requirements.
- [`references/source-notes.md`](references/source-notes.md) - official Snowflake
  documentation and release-note sources to verify for the target window.
- [`references/remediation-and-rollback.md`](references/remediation-and-rollback.md)
  - non-executable remediation and recovery handoff semantics.
- [`scripts/analyze_native_app_release.py`](scripts/analyze_native_app_release.py)
  - deterministic standard-library analyzer.
- [`eval-spec.yaml`](eval-spec.yaml) - behavioral and adversarial evaluation cases.

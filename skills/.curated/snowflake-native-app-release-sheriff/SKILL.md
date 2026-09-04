---
name: snowflake-native-app-release-sheriff
description: |
  Preflight Snowflake Native App package releases from trusted, privacy-safe
  provider evidence without publishing, upgrading, altering, granting, or
  approving anything. Use when reviewing manifest/setup safety, security-scan gates,
  version and release-directive validation, App Spec or privilege changes,
  upgrade-cohort compatibility, and rollback readiness. Trigger with "Native
  App release", "application package scan", "upgrade cohort", or "App Spec".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[schema-2-native-app-evidence.json]"
version: 3.16.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic; Python 3.10+; optional Snowflake CLI for live provider-side read-only collection
model: inherit
effort: high
tags: [saas, snowflake, native-app, release, security, upgrade, rollback]
---

# Snowflake Native App Release Sheriff

## Purpose

Produce a deterministic, as-of provider-side release preflight. A clean result
is `READY_FOR_OPERATOR_RELEASE_AS_OF`, never permission or an instruction to
publish, set a release directive, upgrade an application, or alter privileges.

## Prerequisites

Read both reference files before analysis. The input must use the exact schema-2
contract in [`references/evidence-contract.md`](references/evidence-contract.md)
and must include independently retained hashes for the whole bundle, manifest,
setup script, normalized cohort rows/denominators, lifecycle evidence, and the
complete rollback receipt including its artifact digest. Every array carries an explicit count;
zero is evidence only when the owner-approved denominator is exactly zero.

Python 3.10+ is required. A Snowflake CLI profile is optional for collection and
must already exist; authentication is configured outside this skill. The package
manifest and setup script remain local inputs. Never send source SQL,
package names, consumer names, account names, free-text scan failures, or App
Spec definitions through the evidence packet. Use stable, account-scoped hashes.

## Instructions

1. Collect all three live provider surfaces for one exact package.
2. Build the schema-2 packet with owner-approved denominators and trusted hashes.
3. Run the analyzer at an explicit UTC evaluation time.
4. Stop on invalid, blocked, stale, capped, or incomplete evidence; hand a clean
   as-of report to the separately authorized release owner.

### Collect current provider evidence

Use an existing least-privilege Snowflake CLI profile with visibility to the
selected package. The collector uppercases and strictly validates the unquoted
one-part package selector, then binds the rendered-query receipt to the
Snowflake-produced selected-package hash. An error receipt contains no package
fingerprint.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface native-app-versions-current --application-package APP_PACKAGE \
  --connection native-app-observer --output ./versions.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface native-app-release-directives-current --application-package APP_PACKAGE \
  --connection native-app-observer --output ./directives.json

python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface native-app-upgrade-cohorts-current --application-package APP_PACKAGE \
  --connection native-app-observer --output ./cohorts.json
```

`SHOW VERSIONS` requires package visibility. `SHOW RELEASE DIRECTIVES` requires
package ownership or the documented package release/version management
privilege. `SNOWFLAKE.DATA_SHARING_USAGE.APPLICATION_STATE` is provider-only,
can lag up to 10 minutes, and does not retain uninstalled instances. Do not
escalate to `ACCOUNTADMIN`; missing or filtered evidence blocks the preflight.

### Analyze

Record the five hashes at independent trusted boundaries, then run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_native_app_release.py" \
  --input ./native-app-evidence.json --evaluated-at "$EVALUATED_AT_UTC" \
  --trusted-input-sha256 sha256:... \
  --trusted-manifest-sha256 sha256:... \
  --trusted-setup-sha256 sha256:... \
  --trusted-cohort-sha256 sha256:... \
  --trusted-lifecycle-sha256 sha256:... \
  --trusted-rollback-sha256 sha256:... \
  > ./native-app-preflight.json
```

Exit `0` means the bounded preflight passed. Exit `1` means valid but blocked;
exit `2` means invalid/untrusted evidence. The analyzer writes stdout only.

### Validate the packet

Confirm all three receipt ages, exact package/account hashes, source counts,
independent digests, target scan row, observed cohort denominator, compatibility
edges, lifecycle receipt, and rollback evidence before accepting exit `0`.

## Fail-closed rules

- Require a unique READY target version/patch. For an EXTERNAL ALPHA or DEFAULT
  release require `APPROVED`; QA does not initiate a security scan, so scan
  status is reported but is not invented as approval.
- Setup runs on install and upgrade and can resume after failure. Reject
  forbidden context/import patterns, non-replay-safe statements, and any
  grant-destructive replacement not immediately restored at the next statement.
- Manifest v2 is required for App Specs. PENDING, DECLINED, absent, stale, or
  sequence-invalid consumer approval evidence blocks. Provider package metadata
  does not prove consumer approval.
- Bind every automated privilege, reference callback/object/privilege contract,
  and App Spec delta to an exact denominator. Removed privileges block. For
  manifest v2 automated grants, changing `manifest_version` is major-upgrade-only
  and changing the requested privilege list is not a patch operation.
- Require compatibility proof for every observed current-version cohort. Block
  install/upgrade failures, queued work, retries/delay, in-flight states, target mismatch,
  or previous-version `FINALIZING`.
- Require current lifecycle history alongside `APPLICATION_STATE`; the snapshot
  alone cannot prove completeness or explain an uninstalled instance.
- Require a tested, hash-bound rollback artifact and observables for privilege
  and App Spec reconciliation. A release directive starts upgrades; it is not a
  validation result.
- Reject stale (>15 minutes), capped, tampered, mixed-account, offline, or
  selector-unbound receipts. Do not convert absence into PASS.

## Safety boundary

Never execute `ALTER APPLICATION PACKAGE`, add/drop version or patch, set/unset a
release directive, publish a listing, approve an App Spec, run setup, upgrade an
application, or grant/revoke a privilege. Produce a review packet for a separate,
authorized human change window.

## Output

The report contains only finite finding codes, exact denominators, an as-of
status, explicit `safe_to_publish: false` and `safe_to_upgrade: false`,
non-claims, and a deterministic report hash. It never repeats input rows or raw
identifiers.

## Error Handling

`INVALID_EVIDENCE` means the strict packet, receipt, type, hash, scope, cap, or
freshness contract failed; it intentionally does not echo the rejected value.
`BLOCKED` is well-formed evidence with one or more finite remediation codes.
Recollect permission-filtered, stale, or capped surfaces with the same approved
scope. Never fix missing evidence by escalating privileges or executing a change.

## Examples

- `IN_PROGRESS` on an EXTERNAL DEFAULT target yields
  `SECURITY_SCAN_NOT_APPROVED`.
- A missing compatibility edge for one observed cohort yields
  `INCOMPATIBLE_OR_UNTESTED_COHORT`, even when every other instance is complete.
- Fresh, trusted, uncapped evidence with replay-safe setup, approved scan, exact
  cohorts, lifecycle proof, and tested rollback yields only
  `READY_FOR_OPERATOR_RELEASE_AS_OF` with both mutation flags false.

## References

- [`references/evidence-contract.md`](references/evidence-contract.md) — exact
  fields, enums, hashes, freshness, and verdict rules.
- [`references/source-notes.md`](references/source-notes.md) — primary Snowflake
  documentation and provider/consumer limitations.

---
name: guidewire-migration-and-upgrade
description: Move a Guidewire deployment to a new platform or release without breaking running policies and claims — on-prem→cloud cutover (config reconciliation, data migration, parallel-run validation), in-place version upgrade (e.g., 202403→202503) with deprecated-API regression coverage, rehearsal-driven cutover with rollback path mid-flight, and broker/claimant communication so users hit the right system at the right time. Use when planning a cloud migration, executing a version upgrade, or rehearsing a cutover. Trigger with "guidewire migration", "guidewire upgrade", "guidewire cutover", "guidewire on-prem to cloud", "202503 upgrade".
allowed-tools: Read, Write, Edit, Bash(gradle:*), Bash(curl:*), Bash(jq:*), Bash(diff:*), Grep, Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - migration
  - upgrade
  - cutover
  - cloud
  - rehearsal
---

# Guidewire Migration and Upgrade

## Overview

Move a Guidewire deployment without losing policies, claims, integrations, or trust. Two related but distinct workflows:

- **Migration**: on-prem InsuranceSuite → Guidewire Cloud (or one cloud tenant → another). Different infrastructure, different config-layer assumptions, different API surfaces.
- **Upgrade**: in-place version bump (e.g., release `202403` → `202503`). Same infrastructure, new code, new APIs, deprecated APIs to retire.

Both are heavy lifts that go badly if executed without rehearsal. Five production failures this skill prevents:

1. **Config reconciliation gaps** — on-prem carries 5 years of customizations; cloud tenant ships with newer base config; cutover deploys the on-prem config and breaks because base assumptions diverged.
2. **Deprecated-API blind spots** — version upgrade removes a Cloud API that an integration depended on; the integration starts returning 404 the moment the upgrade lands.
3. **No mid-flight rollback** — cutover starts at midnight, fails at 2am, decision is "abort or push through"; without a pre-defined abort path the team chooses badly.
4. **Data migration that loses optimistic-locking history** — claims migrate but `checksum` values do not; downstream integrations fail every PATCH for a week until checksums regenerate.
5. **Communication misalignment** — brokers told "use the new system Monday" while the old system is still authoritative for in-flight quotes; bound state lives in two systems.

## Prerequisites

- Approved migration / upgrade plan with named owners for: config reconciliation, data migration, integration cutover, communication, rollback authorization
- A staging tenant on the target platform (cloud) or target version that is exact-replica of production minus customer data
- Production-shape sample dataset for rehearsal (anonymized but representative volumes and shapes)
- Cutover window scheduled with documented blackout period for non-essential changes
- For upgrades: Guidewire's **release notes** for every version between current and target; **deprecated API list** for the target release

## Instructions

Build the migration / upgrade plan in this order. Each step targets one of the five production failures listed in Overview.

### 1. Inventory the current state

Before designing the move, know what is actually deployed:

| Surface | Catalog |
|---|---|
| Custom Gosu code | every file under `modules/configuration/gsrc/`; commit count, author distribution |
| Custom plugins | every entry in `plugin/registry/*.xml` |
| Custom entity extensions | every `.eti` file deviation from base |
| Outbound integrations | every Service Application registered in GCC; their roles and endpoints called |
| Inbound integrations | every messaging destination consuming App Events; their delivery destinations |
| Reports and queries | dashboards, scheduled batch jobs, ad-hoc Gosu Query API uses |
| Custom UI / PCF | every PCF file deviation from base |

The inventory drives reconciliation. Skipping it is how 30-month "migration" projects happen — surprise customizations surface every other week.

### 2. Reconcile against the target

For migrations: identify each customization's status against the cloud base config (still applicable / superseded by base / requires re-implementation / no longer needed). For upgrades: identify each customization's status against the target version's base config.

```
Custom file          Base file (target)         Status
gsrc/.../UWRule1.gs  same path, same hash       no-op (carrier kept it through upgrade)
gsrc/.../UWRule2.gs  same path, different hash  manual merge required
gsrc/.../UWRule3.gs  not present in target      cut by Guidewire; verify if rule still needed
                     gsrc/.../NewRule.gs        new in target; no carrier override needed
```

Use `diff -r` between current and target base config zones; the output is the merge backlog. Each row gets an owner and a target completion date.

### 3. Design the data migration plan

For migrations between deployments, every entity needs to move. The non-obvious challenges:

- **Foreign-key resolution**: `claim.Policy` is a reference to a Policy resource id; new tenant assigns new ids; mapping table required.
- **Checksum continuity**: Cloud API uses `checksum` for optimistic locking; migration must populate plausible checksums or downstream PATCH calls fail until they refresh through GET-then-PATCH.
- **Audit log retention**: regulatory requirement to retain claim-state history; the old system's audit log must migrate or be archived in a regulator-acceptable format.
- **Document attachments**: claim photos, declaration pages, evidence; can be GBs per claim; needs separate transfer plan.
- **In-flight resources**: submissions in `Quoted`, claims in `Open`; cutover plan must decide: complete in old, suspend through cutover, or recreate in new.

A typical large-tenant migration moves 100M+ entity rows; rehearsal at production scale (or close to it) is non-negotiable.

### 4. Rehearse end-to-end

Before the real cutover, run the full migration against the staging environment with production-shape data. Measure:

- Total wall-clock time of data migration
- Per-entity throughput
- Failure rate per entity type
- Post-migration reachability check (every integration's first call works against the new system)
- Time to roll back if abort triggered at each phase

A first rehearsal failing somewhere is normal and expected; the second rehearsal failing somewhere is also normal; the third rehearsal failing somewhere means the plan has gaps. Do not cut over from a third-failure plan.

### 5. Cutover with mid-flight abort path

The cutover is a sequence of phases, each with a defined abort point:

```
Phase 0: Quiesce — pause non-essential writes; communicate to brokers.        [ABORT: resume; reschedule]
Phase 1: Snapshot — capture point-in-time of source.                           [ABORT: discard snapshot]
Phase 2: Migrate data — bulk move per the data plan.                           [ABORT: drop staging; resume source]
Phase 3: Cut integrations — repoint downstream systems to new tenant.          [ABORT: revert integration config]
Phase 4: Validate — run smoke tests + spot-check 100 random policies.          [ABORT: revert integrations + consider replay]
Phase 5: Open — accept production writes on new tenant.                        [ABORT: difficult; requires rollback plan from §6]
Phase 6: Decommission window — keep source read-only for 30 days for audit.    [ABORT: not applicable; cutover complete]
```

The abort criterion at each phase is a quantitative threshold (data migration error rate > 0.5%, smoke test failure on >10 of 100 spot checks, etc.) decided in advance, not improvised at 2am. Each abort path has a documented runbook.

### 6. Post-cutover rollback (rare, hard)

After Phase 5, the new system is authoritative. Rollback after this point is genuinely hard because writes have happened on the new tenant that did not happen on the old. Two options:

- **Forward fix**: keep new tenant; fix issues in place. Always preferred when possible.
- **Reverse migration**: replay writes from new tenant back to old. Possible only if the cutover preserved a write-audit log on the new side; absent that, data is lost.

Document the cutoff time after which forward fix is the only option (typically Phase 5 + 1 hour). Past that line, communicate honestly to stakeholders about what is and is not recoverable.

### 7. Communicate aggressively

Stakeholders to brief, in priority order:

| Stakeholder | When | Content |
|---|---|---|
| Underwriting + claims operations | T-30 days | what changes, what stays the same, training schedule |
| Broker network | T-14 days | URL changes, login changes, transition for in-flight quotes |
| Claimants with open claims | T-7 days | claim numbers stable; new portal URL |
| State insurance regulators | per regulatory requirements | NAIC notification if applicable |
| Internal IT / security | T-14 days | new tenant URLs for firewall, new audit log location |

Crucially: the message includes the cutover timing and what to do if something looks wrong. Brokers panicking at 9am Monday because they cannot log in to the old URL is preventable.

## Output

A migration / upgrade ships with all of the following:

- A complete inventory of customizations, integrations, and dependencies, owned and dated.
- A reconciliation document mapping every customization to its disposition against the target.
- A data migration plan with foreign-key resolution, checksum strategy, audit-log retention, document-attachment transfer, and in-flight resource handling.
- ≥3 successful end-to-end rehearsals against staging at production scale.
- A cutover runbook with phase-by-phase abort criteria and pre-written abort runbooks.
- A post-cutover monitoring plan with elevated alert thresholds for the first 7 days.
- Stakeholder communication delivered on the T-30 / T-14 / T-7 / T-0 schedule.

## Examples

### Example 1 — Customization inventory diff

```bash
# diff carrier's current config zone against target version's base
diff -r --brief \
  ~/projects/policycenter-202403/modules/configuration \
  ~/projects/policycenter-202503-base/modules/configuration \
  > customizations.txt
# Each "Files differ" line is a customization to reconcile
```

### Example 2 — Phase-2 abort criterion

```yaml
phase: data-migration
abort_if:
  - error_rate > 0.005           # 0.5% failure rate
  - throughput < 1000_per_min    # falling behind cutover window budget
  - source_DB_read_lag > 60s     # source replication broken
on_abort:
  - drop_staging_dataset()
  - re-enable_source_writes()
  - notify_stakeholders("data migration aborted; investigation in progress")
```

### Example 3 — Smoke-test spot check (Phase 4)

```bash
# Pick 100 random policies; verify they read identically from new tenant
psql -tAc "SELECT policy_number FROM policies ORDER BY random() LIMIT 100" \
  | while read -r policy; do
      OLD=$(curl -fsS $OLD_PC/policies?policyNumber=$policy | jq '.data[0].attributes.totalPremium')
      NEW=$(curl -fsS $NEW_PC/policies?policyNumber=$policy | jq '.data[0].attributes.totalPremium')
      [ "$OLD" = "$NEW" ] || echo "DRIFT: $policy old=$OLD new=$NEW"
    done
```

If >10 drifts in the 100 sample, abort. Below that, accept and document the drift cases for forward fix.

## Error Handling

| Symptom | Cause | Solution |
|---|---|---|
| Customization inventory missing files | non-tracked Gosu, untracked plugin entries | check filesystem, not just git; some carriers have local-only customizations |
| Reconciliation step says "manual merge" for many files | base config diverged significantly across versions | budget more time; consider a phased upgrade through intermediate versions |
| Data migration throughput drops below plan | source-DB read contention, network bottleneck, or staging-DB write contention | identify bottleneck before cutover; cutover-day surprises mean abort |
| Spot-check shows premium drift on a sample policy | rate plan migrated incorrectly or rule code differs in target | abort and investigate; do not accept "minor drift" — the next 100 spot checks will compound |
| Mid-cutover network partition | infrastructure issue independent of the migration | if Phase ≤2 detected: abort. If Phase ≥3: depends on partition extent — partial cutover is the worst state |
| Phase-5 production traffic showing 5xx | integration cutover incomplete or new tenant's auth not yet primed | enacted abort plan if past Phase 5 + 1h is unrealistic; usually forward-fix |
| Brokers calling support saying "can't log in" | comms went out late or pointed at wrong URL | accept the goodwill cost; communicate the corrected URL; do not blame brokers |
| Audit log retention from old tenant lost | migration plan did not address it | regulatory issue; retain a snapshot in cold storage and document for next audit |

For deeper coverage (Migration Accelerator usage, parallel-run validation, blue-green migration tenant patterns, regulatory notification requirements per state), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-ci-cd-pipeline` — the deploy substrate that promotes the migrated config to the new tenant
- `guidewire-install-auth` — the new tenant's auth setup; secrets rotation across the cutover
- `guidewire-sdk-patterns` — checksum continuity considerations for migrated data
- `guidewire-observability-and-incident-response` — elevated-threshold monitoring during the post-cutover stabilization window
- `guidewire-webhooks-integrations` — App Event consumer cutover; potentially replay events from migration window

## Resources

- [Guidewire Cloud Migration documentation (Migration Accelerator)](https://docs.guidewire.com/cloud/cloudcommons/latest/migration/)
- [Guidewire release notes (per version)](https://docs.guidewire.com/cloud/pc/202503/releasenotes/)
- [NAIC notification guidance — system migration](https://content.naic.org/cipr-topics)
- [Martin Fowler — Strangler Fig migration pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

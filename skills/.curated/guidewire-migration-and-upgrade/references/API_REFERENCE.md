# Guidewire Migration & Upgrade — Reference

Migration tooling surface, deprecated-API detection, cutover phase definitions, and rehearsal patterns supporting `SKILL.md`.

## Migration Accelerator (Guidewire-supplied tooling)

Guidewire ships a Migration Accelerator (MA) toolkit for on-prem→cloud migrations. Capabilities (subject to per-engagement scoping with Guidewire):

- Schema mapping between on-prem entity model and cloud entity model
- Bulk data transfer with checksum-aware writeback
- Config-package validation against target tenant
- Pre-cutover smoke test scaffolding

MA is engagement-driven (not self-service); engage through the carrier's Guidewire account team. Treat MA as the substrate, not the plan; the migration plan in `SKILL.md` covers what MA does not (rollback paths, communication, in-flight handling).

## Deprecated-API detection

For version upgrades, identify integrations that depend on APIs the target release deprecates. Two complementary techniques:

### Static analysis

Grep the integration code for known-deprecated endpoint paths:

```bash
# 202403 → 202503 deprecation list (illustrative; consult release notes)
grep -rE "(/v0/|deprecatedEndpoint)" path/to/integration/src/
```

The Guidewire release notes for each version include the deprecation list. Not all deprecations are immediate-removal — some are "deprecated, removed in a later release"; track the removal release for upgrade planning.

### Runtime detection

Cloud API responses for deprecated endpoints include a `Sunset` header (RFC 8594) and a `Deprecation` header per RFC 8594. Log every response carrying these headers; review weekly:

```typescript
if (res.headers.get("Deprecation") || res.headers.get("Sunset")) {
  log.warn("deprecated-api-call", {
    path: req.path,
    deprecation: res.headers.get("Deprecation"),
    sunset: res.headers.get("Sunset"),
  });
}
```

Sunset date in the header is the hard deadline; integration must migrate off before then.

## Cutover phase definition (detailed)

### Phase 0 — Quiesce (T-2h to T)

Disable non-essential write paths on source. In-flight reads continue. Outbound App Events continue (consumer side will dedup on replay).

```bash
# Disable broker portal write paths via maintenance flag
curl -X PATCH $SOURCE/admin/maintenance -d '{"writes": "blocked", "reads": "allowed"}'
```

### Phase 1 — Snapshot (T to T+15min)

Capture point-in-time of source database; serves as the migration source-of-truth and as the rollback substrate.

```bash
# Source-DB snapshot
pg_basebackup --pgdata=$SNAPSHOT_DIR --wal-method=fetch --label="cutover-$(date -Iseconds)"
```

### Phase 2 — Migrate data (T+15min to T+Nh, where N = rehearsed wall-clock)

Bulk transfer with checksum continuation. Per-table parallelism limited to avoid swamping target write capacity.

### Phase 3 — Cut integrations (T+Nh to T+Nh+30min)

Repoint every outbound integration to the new tenant's URLs and credentials. Inbound integrations (App Event consumers) re-subscribe to the new messaging destinations.

### Phase 4 — Validate (T+Nh+30min to T+Nh+90min)

Smoke tests + 100-policy spot check + 50-claim spot check. Numerical drift threshold pre-defined.

### Phase 5 — Open (T+Nh+90min)

Re-enable writes on the new tenant. Source remains read-only.

### Phase 6 — Decommission window (T+Nh+90min to T+30 days)

Source remains read-only for regulatory audit access. Decommission only after the audit window closes.

## Abort runbooks per phase

Each abort runbook is one page. Same template across phases:

```markdown
# Abort: Phase N
## Trigger
- <quantitative threshold that fired>
## Steps (~10 minutes)
1. <concrete command>
2. <concrete command>
## Verify recovery
- <metric/query that should return to baseline>
## Communication
- <stakeholder, message, channel>
## Postmortem
- <where the PIR will be filed>
```

Drilled in rehearsal; the team should be able to execute without re-reading.

## Schema migration patterns (in-place upgrade)

In-place version upgrades (`202403` → `202503`) sometimes include database schema changes Guidewire applies during deploy. Two patterns:

| Pattern | When | Behavior |
|---|---|---|
| Online migration | additive changes (new columns, new indexes) | runServer applies during boot; no downtime beyond restart |
| Offline migration | destructive changes (column type change, table rename) | runServer takes the database into maintenance mode; downtime equals migration time |

Release notes specify which version transitions require offline migration. Plan the upgrade window accordingly; offline migration on a large-tenant DB can take hours.

## In-flight resource handling

Submissions in `Quoted` state and claims in `Open` state cross the cutover boundary. Decision matrix:

| Resource state | Cutover handling |
|---|---|
| Submission `Draft` | migrate; broker continues editing on new tenant |
| Submission `Quoted` (within validity window) | migrate; broker can bind on new tenant |
| Submission `Quoted` (validity expired) | migrate; broker must re-quote on new tenant; communicate the requirement |
| Submission `Bound` (not yet issued) | migrate; complete issue on new tenant |
| Policy `In Force` | migrate; live on new tenant |
| Claim `Open` (no in-flight payments) | migrate; adjuster continues on new tenant |
| Claim `Open` (in-flight payment in `PendingApproval`) | complete the payment cycle on source before cutover, OR migrate the pending state and resume on new tenant |
| Claim `Closed` | migrate; reopen on new tenant if needed |

The "in-flight payment" case is the trickiest; finance team must align with cutover timing.

## Parallel-run validation

For high-risk migrations, run the new tenant in parallel with source for 1-2 weeks before cutover. Both systems receive identical traffic; new tenant's writes are discarded; numerical drift is monitored daily.

Cost: doubled cost of running both systems; engineering effort for the dual-write proxy. Benefit: catches subtle reconciliation issues that 100-policy spot checks miss.

## Per-state regulatory notification

State insurance regulators may require notification of system migrations. Requirements vary; check NAIC guidance and per-state insurance code for the carrier's licensed states.

| State | Typical requirement |
|---|---|
| NY DFS | 10-day notice for cybersecurity-relevant changes |
| CA DOI | varies by line |
| TX TDI | annual filing covers most changes |

Coordinate with carrier's compliance / legal team. Migration without required notification is a finding waiting to happen.

## Upgrade-specific considerations

### Gosu language compatibility

Each release may deprecate or remove Gosu language features. Run `./gradlew compileGosu` against the target version's gradle plugin; deprecation warnings list every affected location.

### Plugin registry compatibility

Some plugin classes are renamed or moved across versions. The `plugin/registry/*.xml` files reference fully-qualified class names; update per the release notes' plugin migration table.

### Sample data compatibility

`./gradlew loadSampleData` data files may have schema-incompatible entries between versions. Either upgrade the sample data or load fresh sample from the target version's distribution.

## Related references

- `references/implementation-guide.md` — extended walkthrough including parallel-run dual-write proxy, Strangler Fig pattern application, blue-green migration tenants
- Sibling `guidewire-ci-cd-pipeline/references/API_REFERENCE.md` — slot deployment used for the migrated config promotion
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth setup for the new tenant
- Guidewire release notes — authoritative source for deprecation, removal, and schema-change details per version

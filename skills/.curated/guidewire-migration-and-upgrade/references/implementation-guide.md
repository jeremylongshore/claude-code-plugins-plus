# Guidewire Migration & Upgrade — Implementation Guide

Extended patterns and supplementary topics for the SKILL.md.

## Strangler Fig migration pattern

For migrations where downtime is unacceptable, the Strangler Fig pattern (Martin Fowler) gradually shifts traffic from source to target rather than cutting over atomically. Pattern:

1. Deploy a routing proxy in front of both source and target
2. Initially: 100% to source
3. Phase: gradually route specific operations (e.g., new submissions) to target while existing operations stay on source
4. As confidence grows, more operations route to target
5. Eventually: 100% to target; source decommissioned

For Guidewire, the pattern is hard to apply because state mutates on both sides — a policy bound on source cannot be endorsed on target without migration. Practical application:

- New accounts: target only
- Existing accounts (read-heavy): target via dual-read with source as fallback
- Existing accounts (write-heavy): source until full migration

The approach extends the migration timeline but eliminates the cutover-night risk. Choose based on the carrier's risk tolerance.

## Dual-write proxy for parallel-run validation

```typescript
// Proxy that runs both systems and validates parity
async function dualWrite(req: Request): Promise<Response> {
  const sourceRes = await fetch(`${SOURCE_BASE}${req.path}`, { method: req.method, body: req.body });
  
  // Fire-and-forget against target; do not block source response
  fetch(`${TARGET_BASE}${req.path}`, { method: req.method, body: req.body })
    .then(async (targetRes) => {
      const drift = await compareResponses(sourceRes.clone(), targetRes);
      if (drift) await logDrift(req, drift);
    })
    .catch(err => log.warn("dual-write target failure", err));
  
  return sourceRes;
}
```

The drift log accumulates over the parallel-run period; review weekly to catch reconciliation issues. Do not block source responses on target; that defeats the safety property.

Limitation: writes that are not idempotent (POST without Idempotency-Key) duplicate on target. Best applied to integrations that already use Idempotency-Key per `guidewire-sdk-patterns`.

## Blue-green migration tenants

Some Guidewire customers maintain two cloud tenants permanently — blue and green — with one always primary and the other always warm. Migrations and major upgrades become tenant swaps rather than in-place changes.

```
Blue tenant: serves production
Green tenant: receives the upgrade; validated; promoted to primary
                ↓ atomic DNS / load-balancer flip
Blue is now warm; green serves production
```

Cost: 2x the steady-state cost. Benefit: minutes-to-hours rollback rather than days; significantly reduced upgrade risk.

Worth it for tier-1 carriers; overkill for smaller deployments.

## Per-line-of-business migration risk

Lines vary in migration complexity. Personal lines (auto, home) are typically simpler than commercial lines (workers comp, commercial auto). Specialty lines (catastrophe, surety, marine) carry the most carrier-specific customization and the highest migration risk per dollar of premium.

| Line | Typical risk |
|---|---|
| Personal auto | low — well-supported by base config |
| Homeowners | low-medium |
| Small commercial (BOP) | medium |
| Workers comp | medium-high — state-specific rules |
| Commercial auto | medium-high — fleet endorsement complexity |
| Specialty (catastrophe, surety, marine) | high — carrier-specific customization |

A multi-line carrier should sequence migration starting from the lowest-risk lines; bank confidence and lessons before tackling specialty.

## Document migration

Claim photos, declaration pages, and other attachments often live in object storage (S3, Azure Blob, on-prem NAS) referenced from Cloud API. Migration moves the references; the underlying objects need a separate transfer.

```
Source: s3://carrier-prod/claims/CLM-2025-0001/photo-001.jpg
Target: s3://gw-tenant-acme/claims/CLM-2025-0001/photo-001.jpg
```

Per-claim attachment counts can be 10-100; total volume is typically GB-TB. Use `aws s3 sync` with `--exclude` patterns for in-flight changes; reconcile any deltas during cutover Phase 4 validation.

## Cutover-night staffing

A typical cutover involves 8-12 people in a war-room (physical or virtual):

| Role | Responsibility |
|---|---|
| Cutover lead | calls phase transitions; final authority on abort |
| Data migration lead | runs the bulk-transfer jobs; monitors throughput |
| Integration lead | repoints downstream integrations |
| QA lead | runs smoke tests and spot checks |
| Communications lead | sends stakeholder updates per schedule |
| Operations on-call | paged for any system-level issues |
| Carrier business sponsor | approves go/no-go at each phase |
| Vendor (Guidewire) liaison | available for escalation |

Pre-cutover dry run with the same team builds the muscle memory.

## Post-cutover stabilization

Elevated alert thresholds and enhanced monitoring for the first 7 days post-cutover. Patterns:

- All SLO alarms set to half-budget thresholds; what would normally be a slow-burn is a fast-burn
- Manual review of first 100 of each transaction type (first 100 binds, first 100 FNOLs, etc.)
- Daily standup to surface anomalies that don't trip alerts
- Communications channel staffed for broker / agent / claimant escalations

Normal operations resume after the 7-day window if no significant issues surface.

## Cost-of-migration estimation

Rough scaling for cost estimation:

```
Engineering hours = (customization count × 8h) + (integration count × 16h) + 200h base
Rehearsal cost = 3 × cutover_window_hours × team_size × hourly_rate
Vendor support = engagement-dependent (Migration Accelerator)
Parallel-run cost = 2x cloud-tenant monthly × parallel-run weeks
Cutover-night cost = team_size × 24h × hourly_rate
```

A medium-tenant carrier (1M policies, 50 integrations, 200 customizations) typically budgets 6-9 months and $1-3M total cost. Variance is high.

## Related

- `SKILL.md` — production patterns
- `references/API_REFERENCE.md` — Migration Accelerator surface, deprecated-API detection, phase definitions
- Sibling `guidewire-ci-cd-pipeline` — promotes the migrated config; rollback substrate
- Sibling `guidewire-observability-and-incident-response` — elevated-threshold monitoring during stabilization

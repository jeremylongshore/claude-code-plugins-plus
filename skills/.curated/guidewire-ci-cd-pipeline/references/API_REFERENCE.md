# Guidewire CI/CD Pipeline — Reference

GCC slot APIs, gradle task surface, and CI/CD configuration patterns supporting `SKILL.md`.

## GCC slot deployment APIs

Exact API surface varies per tenant; consult `https://gcc.guidewire.com` API docs for the canonical surface. Common operations:

| Method | Path | Purpose |
|---|---|---|
| GET | `/slots` | list configured slots for the tenant |
| GET | `/slots/{name}/status` | current package, deploy time, health |
| POST | `/slots/{name}/deploy` | trigger deploy of a package to the slot |
| GET | `/slots/{name}/deploys/{id}` | deploy progress |
| POST | `/slots/{name}/rollback` | revert to previous package |
| PATCH | `/slots/{name}/traffic` | adjust traffic split (canary scenarios) |

Slot configuration (creating/destroying slots, traffic-split settings) is generally not API-accessible — done in the GCC console by the tenant admin.

## Gradle task surface for CI

| Task | When | Output |
|---|---|---|
| `compileGosu` | every PR | type-checks Gosu source |
| `test` | every PR | runs GUnit suite |
| `check` | every PR | full local CI gate (compile + test + lint + arch) |
| `packageConfig` | merges to main | produces `build/libs/configuration.zip` |
| `dropAndCreateDatabase` | local-only; not for CI | wipes dev DB |
| `loadSampleData` | local + UAT regression | populates fixture set |
| `clean` | rare | removes build outputs (NOT the dev DB) |

CI uses gradle's daemon mode for cached compile across jobs in the same run; daemon spans 1 hour by default which is well past typical CI run length.

## Reusable workflow pattern (GitHub Actions)

```yaml
# .github/workflows/deploy.yml (reusable)
on:
  workflow_call:
    inputs:
      slot:    { required: true, type: string }
      package: { required: true, type: string }

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.slot }}              # gates by environment
    steps:
      - name: Decrypt env secrets
        run: |
          echo "$AGE_KEY" > /tmp/age.key
          export SOPS_AGE_KEY_FILE=/tmp/age.key
          eval "$(sops -d secrets.${{ inputs.slot }}.sops.yaml | sed -nE 's/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/export \1=\2/p')"
      - name: Trigger GCC deploy
        run: |
          curl -fsS -X POST "$GCC_API/slots/${{ inputs.slot }}/deploy" \
            -H "Authorization: Bearer $GCC_TOKEN" \
            -d "{\"package\":\"${{ inputs.package }}\"}"
      - name: Poll until deployed
        run: ./.github/scripts/wait-for-deploy.sh ${{ inputs.slot }} ${{ inputs.package }}
```

Reuse across slot environments; per-environment behavior comes from the `environment:` GitHub Actions feature, which gates promotions on review approvals.

## Schema-change patterns

### Phase 1 — Add column, dual-mode code

```gosu
// Read both old and new
function getEffectivePremium(p: Policy): BigDecimal {
  return p.NewPremium ?: p.OldPremium  // null-coalesce; new column may be null on legacy rows
}

// Write both
function recalcPremium(p: Policy): void {
  var v = computePremium(p)
  p.OldPremium = v
  p.NewPremium = v
}
```

Soak duration: ≥1 week, monitoring `null` rate on `NewPremium`. After soak with no anomalies, ship phase 2.

### Phase 2 — Read-new-only, drop old column

```gosu
function getEffectivePremium(p: Policy): BigDecimal {
  return p.NewPremium  // mandatory; phase-1 backfill ensures non-null
}
```

Drop the column in a separate migration after the code change is fully promoted to prod.

### Backfill task

```bash
./gradlew runBackfill -Dbackfill=PremiumColumn -Dbatch=1000
```

Backfill jobs use the batch endpoint from `guidewire-sdk-patterns/references/API_REFERENCE.md`; per-batch idempotency keys protect against retries.

## Canary configuration

Slot-level traffic split is configured in GCC, not via API. Typical setup:

```
prod-main:    weight 95%, package: configuration-abc0001.zip
prod-canary:  weight 5%,  package: configuration-abc1234.zip (the new package)
```

Monitor metrics partitioned by slot; the canary slot tags its outbound calls so dashboards distinguish behavior.

```typescript
// In the integration's metrics emitter
const slotName = process.env.GW_SLOT_NAME ?? "main";
metrics.increment("gw_request_total", { slot: slotName, status: res.status });
```

Bin canary slot results separately. After 24h with both slots within SLO, promote canary package to main slot at 100%.

## Rollback recipes

### Code-only rollback

```bash
PREVIOUS_PACKAGE=$(curl -fsS $GCC_API/slots/prod/history | jq -r '.[1].package')
curl -fsS -X POST $GCC_API/slots/prod/deploy -d "{\"package\":\"$PREVIOUS_PACKAGE\"}"
```

Used when no policies/claims were impacted by the bad code (operational error only).

### Code + bound-state recovery

```sql
-- Identify affected policies
SELECT DISTINCT resource_id, correlation_id, at
FROM integration_audit
WHERE api_path LIKE '%/bind'
  AND status_code = 200
  AND at BETWEEN :bad_start AND :bad_end;
```

Output goes to finance/operations team; per-policy corrective endorsements run via `guidewire-core-workflow-a` patterns. Document each as `reason="rollback-correction-<incident-id>"`.

### Schema rollback

Phase 2 already shipped → no backward path; only forward via data recovery from backup. Phase 1 only shipped → drop the new column, redeploy phase-0 code.

## Multi-tenant pipeline fan-out

When the same config-package serves multiple carriers, fan promotion across tenants in matrix builds:

```yaml
deploy-uat:
  strategy:
    matrix:
      tenant: [acme, globex, smallco]
  uses: ./.github/workflows/deploy.yml
  with:
    slot: uat
    package: ${{ needs.package.outputs.name }}
    tenant: ${{ matrix.tenant }}
```

Per-tenant secrets (separate `secrets.uat.<tenant>.sops.yaml` files per `guidewire-security-and-rbac`) are decrypted per matrix job.

## CI minimum performance budget

| Job | Budget | Why |
|---|---|---|
| `compileGosu` | <60s | fast feedback on type errors |
| `test` (GUnit) | <5min | full suite per PR; longer kills the loop |
| `check` (lint + arch) | <90s | per-PR ergonomic gate |
| `packageConfig` | <2min | includes asset compilation |
| Total PR pipeline | <8min | engineer waits, exceeds 10min and they context-switch |

Investments to stay under budget: gradle cache, parallel tests, sharded test runs by package.

## Related references

- `references/implementation-guide.md` — extended walkthrough including GitOps, Argo, blue-green deploy, ITIL integration
- Sibling `guidewire-local-dev-loop/references/API_REFERENCE.md` — same GUnit and sample-data tooling
- Sibling `guidewire-security-and-rbac/references/API_REFERENCE.md` — encrypted secrets that promote with packages
- Sibling `guidewire-migration-and-upgrade` — version-upgrade flow that builds on this pipeline

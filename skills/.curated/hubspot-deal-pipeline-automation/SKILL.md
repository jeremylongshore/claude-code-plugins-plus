---
name: hubspot-deal-pipeline-automation
description: |
  Automate and audit HubSpot deal pipeline operations without destroying real
  pipeline — covering stage automation loops, stale-deal safe-close logic,
  forecast reconciliation, custom property drift detection, quota dashboard
  cache-busting, and multi-pipeline duplicate detection. Use when writing or
  debugging workflow automations that move deals between stages, auditing
  pipelines for stale or duplicated opportunities, reconciling forecast numbers
  that disagree across reports, or hardening RevOps dashboards against property
  deletions and reporting-cache lag. Trigger with "hubspot deal pipeline",
  "hubspot stage automation", "hubspot stale deals", "hubspot forecast
  reconciliation", "hubspot quota dashboard", "hubspot duplicate deals",
  "revops pipeline audit".
allowed-tools: Read, Write, Bash(curl:*), Bash(jq:*), Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - crm
  - deals
  - revops
  - pipeline
---

# HubSpot Deal Pipeline Automation

## Overview

Automate HubSpot deal pipelines without blowing up real revenue. This is not a
walkthrough of workflow builder UI — it is the engineering behind six failure
modes that silently destroy RevOps data while every dashboard stays green until
a rep's quota call reveals the damage.

The six production failures this skill prevents:

1. **Stage automation loops** — a workflow moves a deal to "Demo Scheduled",
   which triggers a second workflow enrolled on "Demo Scheduled" that moves it
   back to "Qualified", which triggers the first workflow again. The deal
   bounces between stages until HubSpot's 100-action daily workflow execution
   limit for that deal is exhausted. RevOps sees "workflow failure" alerts but
   no stage history that makes sense.

2. **Stale-deal auto-closing** — a cleanup workflow auto-closes deals older
   than 90 days to clear pipeline bloat. The contact associated with deal #4872
   responded to an email this morning. The deal is closed as Lost. The rep calls
   the contact, who says "I just told someone we were ready to sign." This
   failure costs quota attainment, not just data quality.

3. **Forecast query inconsistency** — `amount`, `hs_projected_amount`, and a
   custom `arr_value` property all exist on the same deal. The CRO dashboard
   queries `amount`. The ops team queries `hs_projected_amount`. RevOps built a
   custom rollup on `arr_value`. At end of quarter they produce three different
   forecast numbers for the same deal set with no canonical answer.

4. **Custom property reporting gap** — a RevOps engineer renames
   `deal_source_detail` to `original_lead_source` in the property settings.
   Every deal-source dashboard built on the old property name silently returns
   zero. No error is thrown. The board sees a 100% collapse in deal source
   tracking that is entirely an artifact, not a pipeline signal.

5. **Quota dashboard staleness** — HubSpot's reporting layer caches deal stage
   aggregates. A deal closes at 4:47pm. The quota attainment dashboard doesn't
   reflect it until 8:30pm. A rep who hit quota at EOD is told they're 3%
   short. This is a 4-hour cache lag in the default reporting stack, and it
   affects every quota conversation at month-end.

6. **Multi-pipeline deal duplication** — a new business opportunity becomes an
   expansion after the initial close. Someone creates a deal in the Expansion
   pipeline for the same company without deleting the original, or a workflow
   auto-creates expansion deals. The same revenue is counted in two pipeline
   forecasts with no cross-reference key linking them.

## Prerequisites

All API calls use a HubSpot private app token or OAuth access token in the
`Authorization: Bearer $HUBSPOT_TOKEN` header. The `hubspot-auth` skill covers
token caching, rotation, and rate-limit backoff patterns. For deal pipeline
automation, the required scopes are listed below.

- HubSpot Sales Hub Professional or Enterprise (workflows + custom properties
  - API access)
- Private app token with scopes:
  `crm.objects.deals.read`, `crm.objects.deals.write`,
  `crm.schemas.deals.read`, `crm.schemas.deals.write`,
  `crm.associations.read`, `crm.associations.write`,
  `automation`
- Node.js 18+ or Python 3.10+ in the execution environment
- `jq` installed for shell-based audit scripts
- HubSpot portal ID (visible at top-right of any HubSpot page, or via
  `GET /oauth/v1/access-tokens/$TOKEN`)

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Stage transition guard (neutralizes automation loops)

Workflow loops happen when a stage-change trigger has no memory of what caused
the change. The guard injects a sentinel property `hs_pipeline_loop_guard`
(type: `string`, format: `workflowId:epochMs`) that any workflow writes
immediately before it changes a stage, and reads before it fires. If the guard
was written by the same workflow within a debounce window, the workflow aborts.

**Create the sentinel property first (one-time setup per portal):**

```bash
curl -s -X POST "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hs_pipeline_loop_guard",
    "label": "Pipeline Loop Guard",
    "type": "string",
    "fieldType": "text",
    "groupName": "dealinformation",
    "description": "Automation loop sentinel. Format: workflowId:epochMs. Written before any stage transition."
  }' | jq '{name, label, type}'
```

**TypeScript guard — wrap every stage-change call in this:**

```typescript
const DEBOUNCE_MS = 60_000; // 60s window per workflow

async function safeStageTransition(
  dealId: string,
  workflowId: string,
  targetStageId: string,
  token: string,
): Promise<{ transitioned: boolean; reason: string }> {
  // Read current guard value
  const deal = await hubspotGet(`/crm/v3/objects/deals/${dealId}`, token, {
    properties: "dealstage,hs_pipeline_loop_guard",
  });

  const guard: string | null = deal.properties.hs_pipeline_loop_guard ?? null;
  if (guard) {
    const [guardedWorkflowId, tsStr] = guard.split(":");
    const elapsed = Date.now() - parseInt(tsStr, 10);
    if (guardedWorkflowId === workflowId && elapsed < DEBOUNCE_MS) {
      return {
        transitioned: false,
        reason: `Loop guard: workflow ${workflowId} already fired ${elapsed}ms ago`,
      };
    }
  }

  // Write guard, then transition
  await hubspotPatch(`/crm/v3/objects/deals/${dealId}`, token, {
    properties: {
      hs_pipeline_loop_guard: `${workflowId}:${Date.now()}`,
      dealstage: targetStageId,
    },
  });

  return { transitioned: true, reason: "OK" };
}

```

`hubspotGet` and `hubspotPatch` are thin `fetch` wrappers — implementations in
[implementation-guide.md](references/implementation-guide.md).

**Detecting existing loops via stage history audit:**

```bash
# Pull stage change history for a specific deal — look for oscillation
DEAL_ID="12345678"
curl -s "https://api.hubapi.com/crm/v3/objects/deals/${DEAL_ID}/changelog" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '.results[] | select(.propertyName == "dealstage") | {timestamp, from: .previousValue, to: .currentValue}'
```

If the output shows the same two stage IDs alternating more than twice in 24
hours, that deal has a live loop. Identify the responsible workflows by checking
`hs_lastmodifieddate` on the deal alongside the workflow enrollment history in
HubSpot UI (Contacts → Workflows → History tab for the deal).

### 2. Stale-deal safe-close audit (neutralizes stale-deal closing)

Never auto-close a deal without first checking whether the associated contact
has recent email activity. The safe-close criterion is: deal older than 90 days
**AND** no inbound email in the last 30 days **AND** no open tasks.

The full `stale_deal_audit.py` script (with `get_stale_open_deals`, `has_recent_inbound_email`, `has_open_tasks`, and paginated search) lives in [implementation-guide.md](references/implementation-guide.md) § Stale-Deal Audit.

Key points for the search query:

```bash
# CRM search filter for stale open deals (epoch ms cutoff)
CUTOFF=$(python3 -c "import datetime; print(int((datetime.datetime.utcnow()-datetime.timedelta(days=90)).timestamp()*1000))")
# filterGroups: createdate LT $CUTOFF AND hs_is_closed EQ false
```

The script outputs a CSV with `safe_to_close` boolean. Only rows where `safe_to_close=True` are candidates for batch close. A separate `batch_close_stale.py` script (also in the implementation guide) handles the actual close — always requires human review of the CSV before executing.

### 3. Forecast amount reconciliation (neutralizes query inconsistency)

HubSpot exposes four distinct amount-like fields on a deal. Using the wrong one
in a report produces a different number without any error. The canonical
selection logic:

| Field | When it is the right number |
|---|---|
| `amount` | The rep-entered deal value. Use for quota credit and pipeline value in all CRM views. |
| `hs_projected_amount` | Amount × current-stage probability. Use only for probability-weighted pipeline forecasts. |
| `hs_deal_stage_probability` | The stage probability (0–1). Multiply `amount` by this yourself if you need weighted values. |
| Custom `arr_value`, `mrr_value`, etc. | Only if your org has explicitly separated ARR/MRR from deal amount. Validate these exist on the deal before reading them. |

**Always request all four amount fields — pick one canonical field per report:**

```bash
# Fetch all four amount fields for a deal and compare
curl -s "https://api.hubapi.com/crm/v3/objects/deals/$DEAL_ID" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  --data-urlencode "properties=amount,hs_projected_amount,hs_deal_stage_probability,arr_value" | \
  jq '.properties | {amount, projected: .hs_projected_amount, probability: .hs_deal_stage_probability, arr: .arr_value}'
```

**Discrepancy rule:** if `|hs_projected_amount - (amount × hs_deal_stage_probability)| / amount > 0.05`,
`hs_projected_amount` is stale. Force recalculation by patching `dealstage` to
the current stage value — HubSpot recomputes on every stage write.

The full Python `forecast_reconcile.py` script (with paginated open-deal search
and `--fix` flag for bulk recalculation) is in
[implementation-guide.md](references/implementation-guide.md) § Forecast Reconciliation.

### 4. Custom property drift detection (neutralizes reporting gaps)

When a deal property used in a dashboard is renamed or deleted, dashboards
silently return zero without throwing an error. Run this check before every
sprint that touches property schema, and wire it into a nightly CI job.

```bash
#!/usr/bin/env bash
# check-deal-properties.sh
# Usage: HUBSPOT_TOKEN=... ./check-deal-properties.sh properties-in-use.txt
# properties-in-use.txt: one property name per line (from dashboard/report definitions)

set -euo pipefail

PROPERTIES_FILE="${1:-properties-in-use.txt}"
TOKEN="${HUBSPOT_TOKEN:?HUBSPOT_TOKEN required}"

# Fetch all deal properties from the portal
ALL_PROPS=$(
  curl -s "https://api.hubapi.com/crm/v3/properties/deals" \
    -H "Authorization: Bearer $TOKEN" | \
  jq -r '.results[].name'
)

echo "Checking properties against portal schema..."
MISSING=0

while IFS= read -r prop; do
  [[ -z "$prop" ]] && continue
  if ! echo "$ALL_PROPS" | grep -qx "$prop"; then
    echo "MISSING: $prop"
    MISSING=$((MISSING + 1))
  fi
done < "$PROPERTIES_FILE"

if [[ $MISSING -gt 0 ]]; then
  echo ""
  echo "ERROR: $MISSING properties used in reports do not exist in this portal."
  echo "Review recent property renames/deletions in Settings → Properties."
  exit 1
else
  echo "All $( wc -l < "$PROPERTIES_FILE" | tr -d ' ' ) properties found in portal schema."
fi
```

Generate `properties-in-use.txt` by extracting all property names from your
report/dashboard definitions. The list must be maintained alongside any schema
change — wire `check-deal-properties.sh` into your deployment pipeline so that
property renames fail the deploy before they break dashboards in production.

### 5. Quota dashboard cache-busting (neutralizes staleness)

HubSpot's native reporting layer caches deal stage aggregates. The cache TTL
in the standard reporting stack is up to 4 hours. For real-time quota views at
month-end, bypass the reporting layer and query the CRM API directly with a
current-state search.

```typescript
interface QuotaSnapshot {
  closedWon: number;    // sum of amount for ClosedWon deals in current period
  closedWonCount: number;
  openPipeline: number; // sum of amount for open deals
  asOf: string;         // ISO timestamp of this query
}

async function liveQuotaSnapshot(
  pipelineId: string,
  closedWonStageId: string,
  ownerId: string,
  token: string,
  periodStartMs: number,
): Promise<QuotaSnapshot> {
  // Closed Won this period
  const closedWonSearch = {
    filterGroups: [
      {
        filters: [
          { propertyName: "pipeline", operator: "EQ", value: pipelineId },
          { propertyName: "dealstage", operator: "EQ", value: closedWonStageId },
          { propertyName: "hubspot_owner_id", operator: "EQ", value: ownerId },
          { propertyName: "closedate", operator: "GTE", value: String(periodStartMs) },
        ],
      },
    ],
    properties: ["amount"],
    limit: 100,
  };

  const cwResp = await hubspotSearch("/crm/v3/objects/deals/search", closedWonSearch, token);
  const closedWon = cwResp.results.reduce(
    (sum: number, d: any) => sum + (parseFloat(d.properties.amount) || 0),
    0,
  );

  // Open pipeline (not closed) — for forecast view
  const openSearch = {
    filterGroups: [
      {
        filters: [
          { propertyName: "pipeline", operator: "EQ", value: pipelineId },
          { propertyName: "hs_is_closed", operator: "EQ", value: "false" },
          { propertyName: "hubspot_owner_id", operator: "EQ", value: ownerId },
        ],
      },
    ],
    properties: ["amount"],
    limit: 100,
  };

  const openResp = await hubspotSearch("/crm/v3/objects/deals/search", openSearch, token);
  const openPipeline = openResp.results.reduce(
    (sum: number, d: any) => sum + (parseFloat(d.properties.amount) || 0),
    0,
  );

  return {
    closedWon,
    closedWonCount: cwResp.total,
    openPipeline,
    asOf: new Date().toISOString(),
  };
}

```

`hubspotSearch` is the same helper defined in section 1. Serve this function
from your internal ops dashboard and poll it on page load instead of embedding
a HubSpot report iframe. The CRM API reflects stage changes within seconds of
them happening. The full polling service (Express + 30-second in-memory cache

- React widget) is in [implementation-guide.md](references/implementation-guide.md)
§ Quota Dashboard Cache-Busting Pattern.

### 6. Multi-pipeline duplicate detection (neutralizes deal duplication)

The canonical deduplication key is `company_id` + `closedate_month` +
`deal_type_custom_field`. Without this cross-reference, the same opportunity
appears in two pipelines and inflates ARR forecast.

The full `findDuplicateDeals()` and `searchAllOpenDeals()` TypeScript implementations live in [implementation-guide.md](references/implementation-guide.md) § Multi-Pipeline Duplicate Detection. The algorithm:

1. Search all open deals, paginated (`hs_is_closed EQ false`)
2. For each deal, fetch associated companies via `GET /crm/v3/objects/deals/$DEAL_ID/associations/companies`
3. Group deals by `companyId` — companies with deals in more than one pipeline are duplicates

Once duplicates are identified, link them with a cross-reference association
before closing one:

```bash
# Link a new-business deal to its expansion deal (association type 5 = deal-to-deal)
curl -s -X PUT \
  "https://api.hubapi.com/crm/v4/objects/deals/${NB_DEAL_ID}/associations/deals/${EXP_DEAL_ID}/5" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | jq '{fromObjectId, toObjectId, associationTypes}'
```

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `400 BAD_REQUEST` | `INVALID_FILTER` | Search filter uses a property name that doesn't exist or uses wrong operator for type | Validate property names via `GET /crm/v3/properties/deals` before building filter; use `EQ` for enum, `GTE`/`LT` for date/number |
| `400 BAD_REQUEST` | `PROPERTY_DOESNT_EXIST` | PATCH payload includes a property that was deleted or renamed | Run `check-deal-properties.sh` against the payload property list; catch and surface the missing property name to RevOps |
| `403 FORBIDDEN` | `MISSING_SCOPES` | Token lacks `crm.objects.deals.write` or `automation` scope | Verify scopes via `GET /oauth/v1/access-tokens/$TOKEN`; re-issue private app token with correct scopes |
| `404 NOT_FOUND` | `OBJECT_NOT_FOUND` | Deal ID in URL doesn't exist, or association target object doesn't exist | Confirm deal exists with `GET /crm/v3/objects/deals/$DEAL_ID` before writing; handle 404 in batch loops gracefully |
| `409 CONFLICT` | `OBJECT_ALREADY_EXISTS` | Batch create includes a deal that matches a unique property value | Deduplicate input set; use batch update instead of create for existing deals |
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | Exceeded 100 API calls/10s (Professional/Enterprise) or 250K/500K daily | Read `Retry-After` header and pause; add 100ms sleep between pages in search loops; use batch endpoints to collapse N updates into one call |

## Examples

### Search for all deals closing this month

```bash
MONTH_START=$(python3 -c "import datetime; now=datetime.datetime.utcnow(); print(int(datetime.datetime(now.year,now.month,1).timestamp()*1000))")
MONTH_END=$(python3 -c "import datetime; now=datetime.datetime.utcnow(); import calendar; end=calendar.monthrange(now.year,now.month)[1]; print(int(datetime.datetime(now.year,now.month,end,23,59,59).timestamp()*1000))")

curl -s -X POST "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"filterGroups\": [{
      \"filters\": [
        {\"propertyName\": \"closedate\", \"operator\": \"GTE\", \"value\": \"$MONTH_START\"},
        {\"propertyName\": \"closedate\", \"operator\": \"LTE\", \"value\": \"$MONTH_END\"},
        {\"propertyName\": \"hs_is_closed\", \"operator\": \"EQ\", \"value\": \"false\"}
      ]
    }],
    \"properties\": [\"dealname\",\"amount\",\"dealstage\",\"pipeline\",\"hubspot_owner_id\"],
    \"sorts\": [{\"propertyName\": \"amount\", \"direction\": \"DESCENDING\"}],
    \"limit\": 50
  }" | jq '.results[] | {id, name: .properties.dealname, amount: .properties.amount, stage: .properties.dealstage}'
```

### Batch update deal stage for a list of deal IDs

```bash
# deals-to-update.json: {"id":"12345","properties":{"dealstage":"appointmentscheduled"}}
jq -n --argjson ids '["11111","22222","33333"]' \
  '{inputs: [$ids[] | {id: ., properties: {dealstage: "qualifiedtobuy"}}]}' \
  > batch_payload.json

curl -s -X POST "https://api.hubapi.com/crm/v3/objects/deals/batch/update" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @batch_payload.json | jq '{status, numResults: (.results | length), errors: (.errors // [])}'
```

### List all pipelines and their stages

```bash
curl -s "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '.results[] | {pipelineId: .id, label: .label, stages: [.stages[] | {stageId: .id, label: .label, probability: .metadata.probability}]}'
```

### Enumerate all custom deal properties

```bash
curl -s "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '[.results[] | select(.hubspotDefined == false) | {name, label, type, fieldType, groupName}]'
```

## Output

Working with this skill produces:

- **Stage transition guard** — `hs_pipeline_loop_guard` sentinel property
  created in the portal, and a TypeScript `safeStageTransition()` wrapper that
  prevents any workflow from re-triggering itself within a 60-second window
- **Stale-deal audit CSV** — `stale_deals.csv` with a `safe_to_close` boolean
  column; only rows with `safe_to_close=True` are candidates for auto-close
  workflows
- **Forecast reconciliation log** — structured WARN output for every deal where
  `hs_projected_amount` diverges from `amount × stage_probability` by more than
  5%, identifying deals where stage probability was changed without
  recalculating projections
- **Property drift report** — exit-1 CI gate that lists every report property
  not present in the portal's current schema
- **Live quota snapshot endpoint** — direct CRM API query returning
  `closedWon`, `closedWonCount`, `openPipeline`, and `asOf` with sub-second
  freshness versus the 4-hour reporting cache
- **Duplicate deal groups** — list of companies with open deals in more than
  one pipeline, with deal IDs to inspect and cross-reference associations to
  create before merging

## Resources

- [HubSpot CRM API — Deals](https://developers.hubspot.com/docs/api/crm/deals)
- [CRM Search API](https://developers.hubspot.com/docs/api/crm/search)
- [Pipelines API](https://developers.hubspot.com/docs/api/crm/pipelines)
- [Associations API v4](https://developers.hubspot.com/docs/api/crm/associations)
- Deal Properties Reference
- Workflow Enrollment History
- [API_REFERENCE.md](references/API_REFERENCE.md) — pipeline/stage endpoint shapes, deal property catalog, search filter syntax, association types
- [implementation-guide.md](references/implementation-guide.md) — stale-deal audit script, forecast reconciliation query, loop guard deployment, cache-busting quota dashboard pattern

# HubSpot Deal Pipeline Automation — Implementation Guide

Production deployment patterns for the six failure modes covered in `SKILL.md`. This document provides the complete implementations of the stale-deal audit script, the forecast reconciliation query, the stage transition loop guard deployment procedure, and the cache-busting quota dashboard pattern. TypeScript patterns live in `SKILL.md`; this guide covers Python equivalents, CI integration, and operational runbooks.

---

## Stale-Deal Audit — Complete Runbook

The audit has two phases: safe-to-close identification and batch close execution. Always run identification first, review the CSV, then execute the batch close separately.

### Phase 1: Identify safe-to-close deals

The `stale_deal_audit.py` script from `SKILL.md` produces a CSV with one row per stale open deal. The columns are:

| Column | Type | Notes |
|---|---|---|
| `deal_id` | string | HubSpot deal ID |
| `deal_name` | string | Deal name |
| `stage` | string | Current stage ID |
| `pipeline` | string | Pipeline ID |
| `created` | ISO datetime | Deal creation date |
| `amount` | string | Deal amount (may be empty if not set) |
| `owner` | string | HubSpot owner ID |
| `safe_to_close` | `True`/`False` | Whether the deal meets all safe-close criteria |
| `reason` | string | Human-readable explanation |

**Safe-close criteria (all must be true):**

1. `createdate` is more than 90 days ago
2. `hs_is_closed` is `false` (deal is open)
3. No inbound email engagement on the associated contact in the last 30 days
4. No incomplete tasks associated with the deal

**Email activity check — what counts as "active":**

The script checks `hs_email_direction` and `hs_timestamp` on each associated email object. Any email with a timestamp within the lookback window is treated as active, regardless of direction. This is conservative by design — a 30-day-old marketing email is not a buyer signal, but the cost of a false negative (closing a deal with a live buyer) is higher than the cost of a false positive (leaving a dead deal open one more month).

**Running the audit:**

```bash
# Single pipeline — recommended for first run
HUBSPOT_TOKEN=pat-na1-... python3 stale_deal_audit.py \
  --pipeline-id 12345678 > stale_deals_2024_q1.csv

# All pipelines (slower — fetches all open deals)
HUBSPOT_TOKEN=pat-na1-... python3 stale_deal_audit.py > stale_deals_all.csv

# Review candidates
grep "True" stale_deals_all.csv | wc -l  # count of safe-to-close deals
grep "False" stale_deals_all.csv | head -20  # sample of excluded deals with reasons
```

### Phase 2: Batch close after human review

Do not automate Phase 2. A human should open `stale_deals.csv`, spot-check 10%
of `safe_to_close=True` rows by looking at the deal in HubSpot UI, then
approve. After approval, batch close:

```python
#!/usr/bin/env python3
"""
batch_close_stale.py — Close deals flagged safe_to_close=True.

Takes the CSV output from stale_deal_audit.py on stdin.
Dry-run by default. Pass --execute to actually close.

Usage:
  python3 batch_close_stale.py [--execute] [--reason "No response in 90 days"] < stale_deals.csv
"""

import csv
import json
import os
import sys
import time
import argparse
import urllib.request

TOKEN = os.environ["HUBSPOT_TOKEN"]
BASE = "https://api.hubapi.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BATCH_SIZE = 100

def hs_post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Actually close deals")
    parser.add_argument("--reason", default="No response in 90 days — auto-closed by RevOps audit")
    args = parser.parse_args()

    reader = csv.DictReader(sys.stdin)
    to_close = [row for row in reader if row.get("safe_to_close") == "True"]

    print(f"Deals to close: {len(to_close)}", file=sys.stderr)

    if not args.execute:
        print("DRY RUN — pass --execute to close deals", file=sys.stderr)
        for row in to_close[:5]:
            print(f"  Would close: {row['deal_id']} — {row['deal_name']}", file=sys.stderr)
        return

    # Build batches of BATCH_SIZE
    errors = 0
    for i in range(0, len(to_close), BATCH_SIZE):
        batch = to_close[i : i + BATCH_SIZE]
        payload = {
            "inputs": [
                {
                    "id": row["deal_id"],
                    "properties": {
                        "dealstage": "closedlost",
                        "hs_closed_lost_reason": args.reason,
                    },
                }
                for row in batch
            ]
        }
        resp = hs_post("/crm/v3/objects/deals/batch/update", payload)
        batch_errors = resp.get("errors", [])
        if batch_errors:
            print(f"Batch {i // BATCH_SIZE + 1} partial failure: {batch_errors}", file=sys.stderr)
            errors += len(batch_errors)
        print(f"Batch {i // BATCH_SIZE + 1}: closed {len(batch) - len(batch_errors)}", file=sys.stderr)
        time.sleep(0.5)  # 500ms between batches

    print(f"Done. Total errors: {errors}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

**Safe-close cadence recommendation:** monthly, not continuous. Running it
weekly creates a false sense of urgency and pressures reps into premature
pipeline cleanup. Monthly cadence gives deals a full 30-day window after the
90-day trigger to show email activity before the next audit run.

---

## Forecast Reconciliation — Canonical Amount Field Selection

The goal is a single authoritative forecast number that every system agrees on. The reconciliation hierarchy:

```
1. amount          → quota credit, board pipeline number, CRM views
2. hs_projected_amount  → probability-weighted forecast (weighted pipeline)
3. hs_deal_stage_probability  → multiplier only; never sum this directly
4. custom ARR/MRR fields  → secondary metrics; always validate existence before reading
```

### Python reconciliation script

```python
#!/usr/bin/env python3
"""
forecast_reconcile.py — Identify deals where hs_projected_amount deviates
from amount × hs_deal_stage_probability by more than THRESHOLD.

Output: JSON list of anomalous deals.

Usage:
  HUBSPOT_TOKEN=pat-na1-... python3 forecast_reconcile.py [--pipeline-id ID] [--threshold 0.05]
"""

import os
import sys
import json
import time
import argparse
import urllib.request

TOKEN = os.environ["HUBSPOT_TOKEN"]
BASE = "https://api.hubapi.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def hs_post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def search_open_deals(pipeline_id: str | None) -> list[dict]:
    filters = [{"propertyName": "hs_is_closed", "operator": "EQ", "value": "false"}]
    if pipeline_id:
        filters.append({"propertyName": "pipeline", "operator": "EQ", "value": pipeline_id})

    all_deals: list[dict] = []
    after = None
    while True:
        body: dict = {
            "filterGroups": [{"filters": filters}],
            "properties": [
                "dealname",
                "dealstage",
                "pipeline",
                "amount",
                "hs_projected_amount",
                "hs_deal_stage_probability",
            ],
            "limit": 100,
        }
        if after:
            body["after"] = after
        resp = hs_post("/crm/v3/objects/deals/search", body)
        all_deals.extend(resp.get("results", []))
        after = resp.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
        time.sleep(0.1)
    return all_deals


def reconcile(deals: list[dict], threshold: float) -> list[dict]:
    anomalies = []
    for deal in deals:
        p = deal["properties"]
        amount_str = p.get("amount")
        projected_str = p.get("hs_projected_amount")
        probability_str = p.get("hs_deal_stage_probability")

        if not amount_str or not probability_str:
            continue  # Can't reconcile without both base fields

        amount = float(amount_str)
        probability = float(probability_str)
        computed = amount * probability

        stored = float(projected_str) if projected_str else 0.0
        delta = abs(computed - stored)
        pct = delta / max(amount, 1.0)

        if pct > threshold:
            anomalies.append({
                "deal_id": deal["id"],
                "deal_name": p.get("dealname", ""),
                "pipeline": p.get("pipeline", ""),
                "stage": p.get("dealstage", ""),
                "amount": amount,
                "stored_projected": stored,
                "computed_projected": round(computed, 2),
                "discrepancy_pct": round(pct * 100, 2),
                "recommendation": (
                    "Patch dealstage to current value to force hs_projected_amount recalculation"
                    if stored != 0
                    else "amount or hs_projected_amount is zero — verify with deal owner"
                ),
            })
    return anomalies


def force_recalculate(anomalous_deal_ids: list[str], token: str) -> None:
    """
    Force hs_projected_amount recalculation by patching dealstage to its current value.
    HubSpot recomputes hs_projected_amount on every dealstage write.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for did in anomalous_deal_ids:
        req = urllib.request.Request(
            f"{BASE}/crm/v3/objects/deals/{did}",
            headers={k: v for k, v in headers.items() if k != "Content-Type"},
        )
        with urllib.request.urlopen(req) as r:
            deal = json.loads(r.read())
        current_stage = deal["properties"]["dealstage"]

        patch_data = json.dumps({"properties": {"dealstage": current_stage}}).encode()
        patch_req = urllib.request.Request(
            f"{BASE}/crm/v3/objects/deals/{did}",
            data=patch_data,
            headers=headers,
            method="PATCH",
        )
        with urllib.request.urlopen(patch_req) as r:
            r.read()  # discard response
        print(f"Recalculated deal {did}", file=sys.stderr)
        time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline-id", default=None)
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument("--fix", action="store_true", help="Force recalculation on anomalous deals")
    args = parser.parse_args()

    deals = search_open_deals(args.pipeline_id)
    print(f"Fetched {len(deals)} open deals.", file=sys.stderr)

    anomalies = reconcile(deals, args.threshold)
    print(f"Found {len(anomalies)} anomalous deals (>{args.threshold * 100:.0f}% discrepancy).", file=sys.stderr)

    if args.fix and anomalies:
        ids = [a["deal_id"] for a in anomalies]
        print(f"Force-recalculating {len(ids)} deals...", file=sys.stderr)
        force_recalculate(ids, TOKEN)

    print(json.dumps(anomalies, indent=2))


if __name__ == "__main__":
    main()
```

Run monthly before board reporting:

```bash
# Identify discrepancies only
HUBSPOT_TOKEN=pat-na1-... python3 forecast_reconcile.py \
  --pipeline-id 12345678 \
  --threshold 0.05 > anomalies.json

# Fix in place (safe — only writes current stage back to same stage)
HUBSPOT_TOKEN=pat-na1-... python3 forecast_reconcile.py \
  --pipeline-id 12345678 \
  --threshold 0.05 \
  --fix
```

---

## Stage Transition Loop Guard — Deployment Procedure

The loop guard requires a one-time property creation and then a code change to every workflow that modifies `dealstage`. These steps must be done in order.

### Step 1: Create the sentinel property

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
    "description": "Written by automation before each stage change. Format: workflowId:epochMs. Prevents automation loops.",
    "hasUniqueValue": false,
    "hidden": false,
    "formField": false
  }' | jq '{name, label, type, fieldType}'
```

Verify creation:

```bash
curl -s "https://api.hubapi.com/crm/v3/properties/deals/hs_pipeline_loop_guard" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | jq '{name, label}'
```

### Step 2: Identify all workflows that write dealstage

Pull the workflow list and filter for those that include a `SET_PROPERTY` action on `dealstage`. This requires the Workflows API (Marketing Hub Professional+):

```bash
curl -s "https://api.hubapi.com/automation/v4/flows" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" | \
  jq '[.results[] | select(
    (.actions[]? | select(.type == "SET_PROPERTY" and .propertyName == "dealstage")) != null
  ) | {id, name: .name, enabled: .enabled}]'
```

For each workflow in the result, wrap its dealstage-write action with the loop guard using `safeStageTransition()` from `SKILL.md`. The workflow ID to pass is the `id` field from this response.

### Step 3: Wire the guard into your API client

Every place your integration code calls `PATCH /crm/v3/objects/deals/{id}` with a `dealstage` property must go through `safeStageTransition()` instead of a direct PATCH. The function signature:

```typescript
safeStageTransition(
  dealId: string,         // HubSpot deal ID
  workflowId: string,     // Stable identifier for the calling workflow/automation
  targetStageId: string,  // Stage ID to move to
  token: string,          // Bearer token
): Promise<{ transitioned: boolean; reason: string }>
```

If `transitioned` is `false`, log the `reason` and stop processing. Do not retry — the guard debounce window means the same workflow cannot legitimately fire on the same deal twice within 60 seconds.

### Step 4: Monitor for loop detection

Log every call to `safeStageTransition()` with `transitioned: false`. Alert if the same `dealId` + `workflowId` pair generates a blocked transition more than 3 times in 24 hours — this indicates the debounce window is too short for the workflow's actual firing frequency, not a real loop.

```typescript
// Structured log on guard block
console.log(JSON.stringify({
  event: "pipeline_loop_guard_blocked",
  dealId,
  workflowId,
  reason,
  timestamp: new Date().toISOString(),
}));
```

Wire this log event to an alert (Slack, PagerDuty, ntfy, etc.) so RevOps is notified when a loop is blocked rather than discovering it via deal history inspection.

---

## Quota Dashboard Cache-Busting Pattern

The native HubSpot reporting cache delay is up to 4 hours on aggregate stage queries. For month-end quota accuracy, route your internal dashboard away from embedded HubSpot reports and toward a thin polling service that queries the CRM API directly.

### Polling service (Node.js / Express)

```typescript
import express from "express";

const app = express();
const PORT = process.env.PORT ?? 3001;
const TOKEN = process.env.HUBSPOT_TOKEN!;

// In-memory cache with configurable TTL
interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}
const cache = new Map<string, CacheEntry<unknown>>();

function memoize<T>(key: string, ttlMs: number, fn: () => Promise<T>): Promise<T> {
  const hit = cache.get(key) as CacheEntry<T> | undefined;
  if (hit && Date.now() < hit.expiresAt) return Promise.resolve(hit.value);
  return fn().then((v) => {
    cache.set(key, { value: v, expiresAt: Date.now() + ttlMs });
    return v;
  });
}

// Quota snapshot endpoint — real-time, bypasses HubSpot reporting cache
app.get("/quota/snapshot", async (req, res) => {
  const { pipelineId, ownerId, periodStart } = req.query as Record<string, string>;

  if (!pipelineId || !ownerId || !periodStart) {
    return res.status(400).json({ error: "pipelineId, ownerId, periodStart required" });
  }

  // Resolve the Closed Won stage ID for this pipeline — cache for 1 hour
  const closedWonStageId = await memoize(
    `cwStage:${pipelineId}`,
    3_600_000,
    () => resolveClosedWonStage(pipelineId, TOKEN),
  );

  if (!closedWonStageId) {
    return res.status(400).json({ error: `No Closed Won stage found for pipeline ${pipelineId}` });
  }

  // Quota snapshot — cache for 30 seconds (fresh enough for real-time use)
  const snapshot = await memoize(
    `quota:${pipelineId}:${ownerId}:${periodStart}`,
    30_000,
    () => liveQuotaSnapshot(pipelineId, closedWonStageId, ownerId, TOKEN, parseInt(periodStart, 10)),
  );

  res.json(snapshot);
});

async function resolveClosedWonStage(pipelineId: string, token: string): Promise<string | null> {
  const res = await fetch(`https://api.hubapi.com/crm/v3/pipelines/deals/${pipelineId}/stages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Stages fetch failed: ${res.status}`);
  const { results } = await res.json();
  const cwStage = results.find(
    (s: any) => s.metadata?.isClosed === "true" && parseFloat(s.metadata?.probability ?? "0") === 1,
  );
  return cwStage?.id ?? null;
}

// liveQuotaSnapshot is defined in SKILL.md § 5
// Import it from your shared module

app.listen(PORT, () => console.log(`Quota service on :${PORT}`));
```

### Dashboard integration (React snippet)

```typescript
// QuotaWidget.tsx
import { useEffect, useState } from "react";

interface QuotaSnapshot {
  closedWon: number;
  closedWonCount: number;
  openPipeline: number;
  asOf: string;
}

export function QuotaWidget({ pipelineId, ownerId, quota }: {
  pipelineId: string;
  ownerId: string;
  quota: number;
}) {
  const [snapshot, setSnapshot] = useState<QuotaSnapshot | null>(null);
  const POLL_INTERVAL_MS = 60_000; // refresh every 60 seconds

  useEffect(() => {
    const periodStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1).getTime();
    const url = `/quota/snapshot?pipelineId=${pipelineId}&ownerId=${ownerId}&periodStart=${periodStart}`;

    const fetchSnapshot = () =>
      fetch(url)
        .then((r) => r.json())
        .then(setSnapshot)
        .catch(console.error);

    fetchSnapshot();
    const interval = setInterval(fetchSnapshot, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [pipelineId, ownerId]);

  if (!snapshot) return <div>Loading...</div>;

  const attainment = (snapshot.closedWon / quota) * 100;
  const lagNote = `Data as of ${new Date(snapshot.asOf).toLocaleTimeString()} (live CRM API)`;

  return (
    <div>
      <div>Closed Won: ${snapshot.closedWon.toLocaleString()} ({snapshot.closedWonCount} deals)</div>
      <div>Attainment: {attainment.toFixed(1)}%</div>
      <div>Open Pipeline: ${snapshot.openPipeline.toLocaleString()}</div>
      <small>{lagNote}</small>
    </div>
  );
}
```

This pattern produces a dashboard that lags the CRM by at most 30 seconds (the service-side cache TTL) instead of 4 hours, with no changes to HubSpot report configuration.

---

## CI Integration — Property Drift Gate

Wire `check-deal-properties.sh` from `SKILL.md` into your CI pipeline to prevent schema changes from silently breaking dashboards.

### GitHub Actions job

```yaml
# .github/workflows/hubspot-schema-check.yml
name: HubSpot Schema Check

on:
  pull_request:
    paths:
      - 'reports/**'
      - 'dashboards/**'
      - 'properties-in-use.txt'
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am UTC — weekly check

jobs:
  property-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check deal properties exist in portal
        env:
          HUBSPOT_TOKEN: ${{ secrets.HUBSPOT_TOKEN }}
        run: |
          chmod +x scripts/check-deal-properties.sh
          ./scripts/check-deal-properties.sh properties-in-use.txt
```

**`properties-in-use.txt` maintenance:** every time a team member adds a new
property reference to a dashboard or report definition, add the property name
to `properties-in-use.txt` in the same commit. Every time a property is renamed
in HubSpot settings, update `properties-in-use.txt` in the same PR that updates
the dashboard query. This two-way coupling is the discipline that prevents silent
reporting breakage.

### Maintaining the properties-in-use list

Extract property names from your report definitions automatically:

```bash
# If your report definitions are YAML files with a "properties:" key:
grep -rh "^\s*-\s*" reports/**/*.yaml | sort -u | tr -d ' -' > properties-in-use.txt

# If your reports reference properties in SQL-like query strings:
grep -rho "'[a-z][a-z0-9_]*'" reports/**/*.sql | tr -d "'" | sort -u > properties-in-use.txt
```

Commit `properties-in-use.txt` alongside your report definitions. The CI gate then validates that every property your reports reference still exists in the portal.

---

## Monitoring Recommendations

Log these events to surface pipeline automation problems before they cascade:

| Event | Log Level | Alert On |
|---|---|---|
| Loop guard blocked a transition | `WARN` | Same deal+workflow blocked >3 times in 24h |
| Stale-deal audit found safe-to-close deals | `INFO` | Count >50 (may indicate pipeline hygiene problem) |
| Forecast reconciliation anomaly | `WARN` | Any anomaly >10% discrepancy |
| Property drift check failed | `ERROR` | Any missing property — page RevOps ops engineer |
| Quota snapshot latency >2s | `WARN` | CRM API latency spike |
| Search returns 10,000 records (max) | `WARN` | Query is hitting the search cap — switch to Exports API |

```python
# Structured log example (Python)
import json
import datetime

def log_event(event: str, level: str, **kwargs):
    print(json.dumps({
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event": event,
        "level": level,
        **kwargs,
    }))

# Usage
log_event(
    "forecast_reconcile_anomaly",
    "WARN",
    deal_id="12345678",
    deal_name="Acme Corp",
    discrepancy_pct=8.2,
    recommendation="Patch dealstage to force recalculation",
)
```

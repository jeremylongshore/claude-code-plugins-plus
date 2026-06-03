# Evidence collection script

Run this as Step 5 of `databricks-incident-runbook`. Collects the four artifacts needed for any postmortem (run.json, output.json, cluster.json, events.json) and tars them into a single uploadable bundle.

## Usage

```bash
./collect-evidence.sh <INCIDENT_ID> <RUN_ID> [CLUSTER_ID]
```

- `INCIDENT_ID` — your team's incident tracker ID (e.g., `INC-2026-06-03-001`)
- `RUN_ID` — Databricks job run ID from `databricks runs list` output
- `CLUSTER_ID` — optional; only needed when the failure was cluster-side (OOM, cold start, spot interrupt)

## Script

```bash
#!/bin/bash
set -euo pipefail
INCIDENT_ID=$1
RUN_ID=$2
CLUSTER_ID=${3:-}

mkdir -p "incident-$INCIDENT_ID"

# Collect job-run artifacts (always)
databricks runs get --run-id $RUN_ID --output json \
  > "incident-$INCIDENT_ID/run.json" 2>&1
databricks runs get-output --run-id $RUN_ID --output json \
  > "incident-$INCIDENT_ID/output.json" 2>&1

# Cluster artifacts (only if cluster ID supplied)
if [ -n "$CLUSTER_ID" ]; then
    databricks clusters get --cluster-id $CLUSTER_ID --output json \
      > "incident-$INCIDENT_ID/cluster.json" 2>&1
    databricks clusters events --cluster-id $CLUSTER_ID --limit 50 --output json \
      > "incident-$INCIDENT_ID/events.json" 2>&1
fi

# Bundle everything
tar -czf "incident-$INCIDENT_ID.tar.gz" "incident-$INCIDENT_ID"
echo "Evidence: incident-$INCIDENT_ID.tar.gz"
```

## What each artifact tells you

| File | Use during incident | Use in postmortem |
|---|---|---|
| `run.json` | Current state, start time, duration | Timeline reconstruction |
| `output.json` | Error message + stack trace | Root-cause analysis |
| `cluster.json` | Worker count, instance type, autoscale state at time of failure | Capacity planning insights |
| `events.json` | Last 50 cluster-lifecycle events (start, scale, interrupt, terminate) | OOM / spot-interrupt / cold-start patterns |

## Storage

Upload the tarball to the incident-archive tag in your workspace at `/incidents/<INCIDENT_ID>.tar.gz`. Retain 90 days minimum for compliance audits; longer if regulated industry.

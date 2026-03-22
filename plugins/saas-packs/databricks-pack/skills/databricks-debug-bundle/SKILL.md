---
name: databricks-debug-bundle
description: |
  Collect Databricks debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Databricks problems.
  Trigger with phrases like "databricks debug", "databricks support bundle",
  "collect databricks logs", "databricks diagnostic".
allowed-tools: Read, Bash(databricks:*), Bash(tar:*), Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, debugging]

---
# Databricks Debug Bundle

## Current State
!`databricks --version 2>/dev/null || echo 'CLI not installed'`
!`python3 -c "import databricks.sdk; print(f'SDK {databricks.sdk.__version__}')" 2>/dev/null || echo 'SDK not installed'`

## Overview
Collect all diagnostic information needed for Databricks support tickets: environment info, cluster state, cluster events, job run details, Spark driver logs, and Delta table history. Produces a redacted tar.gz bundle safe to share with support.

## Prerequisites
- Databricks CLI installed and configured
- Access to cluster logs (admin or cluster owner)
- Permission to access job run details

## Instructions

### Step 1: Create Debug Collection Script
```bash
#!/bin/bash
set -euo pipefail
# databricks-debug-bundle.sh [cluster_id] [run_id] [table_name]

BUNDLE_DIR="databricks-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

CLUSTER_ID="${1:-}"
RUN_ID="${2:-}"
TABLE_NAME="${3:-}"

echo "=== Databricks Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "Workspace: ${DATABRICKS_HOST:-unset}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
{
    echo ""
    echo "--- Environment ---"
    echo "CLI: $(databricks --version 2>&1)"
    echo "SDK: $(pip show databricks-sdk 2>/dev/null | grep Version || echo 'not installed')"
    echo "Python: $(python3 --version 2>&1)"
    echo "OS: $(uname -srm)"
    echo ""
    echo "--- Current User ---"
    databricks current-user me --output json 2>&1 | jq '{userName, active}' || echo "Auth failed"
} >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Collect Cluster Information
```bash
if [ -n "$CLUSTER_ID" ]; then
    echo "" >> "$BUNDLE_DIR/summary.txt"
    echo "--- Cluster: $CLUSTER_ID ---" >> "$BUNDLE_DIR/summary.txt"

    # Full cluster config
    databricks clusters get --cluster-id "$CLUSTER_ID" --output json \
        > "$BUNDLE_DIR/cluster_config.json" 2>&1

    # Key fields summary
    jq '{state, spark_version, node_type_id, num_workers,
         autotermination_minutes, termination_reason}' \
        "$BUNDLE_DIR/cluster_config.json" >> "$BUNDLE_DIR/summary.txt"

    # Recent cluster events (state changes, errors, resizing)
    databricks clusters events --cluster-id "$CLUSTER_ID" --limit 30 --output json \
        > "$BUNDLE_DIR/cluster_events.json" 2>&1

    # Extract event timeline
    jq -r '.events[]? | "\(.timestamp): \(.type) — \(.details // "no details")"' \
        "$BUNDLE_DIR/cluster_events.json" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 4: Collect Job Run Information
```bash
if [ -n "$RUN_ID" ]; then
    echo "" >> "$BUNDLE_DIR/summary.txt"
    echo "--- Run: $RUN_ID ---" >> "$BUNDLE_DIR/summary.txt"

    # Full run details
    databricks runs get --run-id "$RUN_ID" --output json \
        > "$BUNDLE_DIR/run_details.json" 2>&1

    # Run state summary
    jq '{state: .state, start_time, end_time, run_duration}' \
        "$BUNDLE_DIR/run_details.json" >> "$BUNDLE_DIR/summary.txt"

    # Task-level breakdown
    jq -r '.tasks[]? | "  Task \(.task_key): \(.state.result_state // "RUNNING") — \(.state.state_message // "ok")"' \
        "$BUNDLE_DIR/run_details.json" >> "$BUNDLE_DIR/summary.txt"

    # Run output (error messages, stdout)
    databricks runs get-output --run-id "$RUN_ID" --output json \
        > "$BUNDLE_DIR/run_output.json" 2>&1

    jq '{error, error_trace: (.error_trace // "" | .[0:2000])}' \
        "$BUNDLE_DIR/run_output.json" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 5: Collect Spark Driver Logs
```bash
if [ -n "$CLUSTER_ID" ]; then
    echo "" >> "$BUNDLE_DIR/summary.txt"
    echo "--- Spark Driver Logs (last 500 lines) ---" >> "$BUNDLE_DIR/summary.txt"

    python3 << 'PYEOF' > "$BUNDLE_DIR/driver_logs.txt" 2>&1
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
try:
    content = w.dbfs.read("/cluster-logs/${CLUSTER_ID}/driver/log4j-active.log")
    # Take last 500 lines
    lines = content.data.decode().splitlines()[-500:]
    print("\n".join(lines))
except Exception as e:
    print(f"Could not fetch driver logs: {e}")
    print("Tip: Enable cluster log delivery in cluster config for persistent logs")
PYEOF
fi
```

### Step 6: Collect Delta Table Diagnostics
```bash
if [ -n "$TABLE_NAME" ]; then
    echo "" >> "$BUNDLE_DIR/summary.txt"
    echo "--- Delta Table: $TABLE_NAME ---" >> "$BUNDLE_DIR/summary.txt"

    python3 << PYEOF > "$BUNDLE_DIR/delta_diagnostics.txt" 2>&1
from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.getOrCreate()

print("=== Table Details ===")
spark.sql("DESCRIBE DETAIL ${TABLE_NAME}").show(truncate=False)

print("\n=== Recent History (last 20 operations) ===")
spark.sql("DESCRIBE HISTORY ${TABLE_NAME} LIMIT 20").show(truncate=False)

print("\n=== Schema ===")
spark.sql("DESCRIBE ${TABLE_NAME}").show(truncate=False)

print("\n=== File Stats ===")
detail = spark.sql("DESCRIBE DETAIL ${TABLE_NAME}").first()
print(f"Files: {detail.numFiles}, Size: {detail.sizeInBytes / 1024 / 1024:.1f} MB")
PYEOF
fi
```

### Step 7: Package Bundle (Redacted)
```bash
# Redact sensitive data from config snapshot
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f ~/.databrickscfg ]; then
    sed 's/token = .*/token = ***REDACTED***/' \
        ~/.databrickscfg > "$BUNDLE_DIR/config-redacted.txt"
    sed -i 's/client_secret = .*/client_secret = ***REDACTED***/' \
        "$BUNDLE_DIR/config-redacted.txt"
fi

# Network connectivity test
echo "--- Network ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API reachable: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" \
    "${DATABRICKS_HOST}/api/2.0/clusters/list" \
    -H "Authorization: Bearer ${DATABRICKS_TOKEN}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Create archive
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents: summary.txt, cluster_config.json, cluster_events.json,"
echo "  run_details.json, run_output.json, driver_logs.txt,"
echo "  delta_diagnostics.txt, config-redacted.txt"
```

## Output
- `databricks-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — Human-readable diagnostic summary
  - `cluster_config.json` — Full cluster configuration
  - `cluster_events.json` — State changes, errors, resizing events
  - `run_details.json` — Job run with task-level breakdown
  - `run_output.json` — Stdout/stderr and error traces
  - `driver_logs.txt` — Last 500 lines of Spark driver log
  - `delta_diagnostics.txt` — Table details, history, schema
  - `config-redacted.txt` — CLI config with secrets removed

## Error Handling
| Item | Included | Notes |
|------|----------|-------|
| Tokens/secrets | NEVER | Redacted with `***REDACTED***` |
| PII in logs | Review before sharing | Scan driver_logs.txt manually |
| Cluster IDs | Yes | Safe to share with support |
| Error traces | Yes | Check for embedded connection strings |

## Examples

### Usage
```bash
# Environment only
bash databricks-debug-bundle.sh

# With cluster diagnostics
bash databricks-debug-bundle.sh 0123-456789-abcde

# With cluster + job run
bash databricks-debug-bundle.sh 0123-456789-abcde 12345

# Full diagnostics including Delta table
bash databricks-debug-bundle.sh 0123-456789-abcde 12345 catalog.schema.table
```

### Submit to Support
1. Generate bundle: `bash databricks-debug-bundle.sh [args]`
2. Review `summary.txt` for sensitive data
3. Open ticket at [help.databricks.com](https://help.databricks.com)
4. Attach the `.tar.gz` bundle
5. Include workspace ID (found in workspace URL: `adb-<workspace-id>`)

## Resources
- [Databricks Support](https://help.databricks.com)
- [Status Page](https://status.databricks.com)
- [Community Forum](https://community.databricks.com)

## Next Steps
For rate limit issues, see `databricks-rate-limits`.

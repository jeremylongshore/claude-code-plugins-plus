---
name: databricks-debug-bundle
description: |
  Collect Databricks debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Databricks problems.
  Trigger with phrases like "databricks debug", "databricks support bundle",
  "collect databricks logs", "databricks diagnostic".
allowed-tools: Read, Bash(databricks:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect all necessary diagnostic information for Databricks support tickets.

## Prerequisites
- Databricks CLI installed and configured
- Access to cluster logs (admin or cluster owner)
- Permission to access job run details

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# databricks-debug-bundle.sh

set -e
BUNDLE_DIR="databricks-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Databricks Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
echo "Workspace: ${DATABRICKS_HOST}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
set -euo pipefail
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "CLI Version: $(databricks --version)" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python --version 2>&1)" >> "$BUNDLE_DIR/summary.txt"
echo "Databricks SDK: $(pip show databricks-sdk 2>/dev/null | grep Version)" >> "$BUNDLE_DIR/summary.txt"
echo "DATABRICKS_HOST: ${DATABRICKS_HOST}" >> "$BUNDLE_DIR/summary.txt"
echo "DATABRICKS_TOKEN: ${DATABRICKS_TOKEN:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Workspace info
echo "--- Workspace Info ---" >> "$BUNDLE_DIR/summary.txt"
databricks current-user me 2>&1 >> "$BUNDLE_DIR/summary.txt" || echo "Failed to get user info"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Collect Cluster Information
```bash
# Cluster details (if cluster_id provided)
CLUSTER_ID="${1:-}"
if [ -n "$CLUSTER_ID" ]; then
    echo "--- Cluster Info: $CLUSTER_ID ---" >> "$BUNDLE_DIR/summary.txt"
    databricks clusters get --cluster-id "$CLUSTER_ID" > "$BUNDLE_DIR/cluster_info.json" 2>&1

    # Extract key info
    jq -r '{
        state: .state,
        spark_version: .spark_version,
        node_type_id: .node_type_id,
        num_workers: .num_workers,
        autotermination_minutes: .autotermination_minutes
    }' "$BUNDLE_DIR/cluster_info.json" >> "$BUNDLE_DIR/summary.txt"

    # Get cluster events
    echo "--- Recent Cluster Events ---" >> "$BUNDLE_DIR/summary.txt"
    databricks clusters events --cluster-id "$CLUSTER_ID" --limit 20 > "$BUNDLE_DIR/cluster_events.json" 2>&1
    jq -r '.events[] | "\(.timestamp): \(.type) - \(.details)"' "$BUNDLE_DIR/cluster_events.json" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 4: Collect Job Run Information
```bash
# Job run details (if run_id provided)
RUN_ID="${2:-}"
if [ -n "$RUN_ID" ]; then
    echo "--- Job Run Info: $RUN_ID ---" >> "$BUNDLE_DIR/summary.txt"
    databricks runs get --run-id "$RUN_ID" > "$BUNDLE_DIR/run_info.json" 2>&1

    # Extract run state
    jq -r '{
        state: .state.life_cycle_state,
        result: .state.result_state,
        message: .state.state_message,
        start_time: .start_time,
        end_time: .end_time
    }' "$BUNDLE_DIR/run_info.json" >> "$BUNDLE_DIR/summary.txt"

    # Get run output
    echo "--- Run Output ---" >> "$BUNDLE_DIR/summary.txt"
    databricks runs get-output --run-id "$RUN_ID" > "$BUNDLE_DIR/run_output.json" 2>&1
    jq -r '.error // "No error"' "$BUNDLE_DIR/run_output.json" >> "$BUNDLE_DIR/summary.txt"

    # Task-level details
    jq -r '.tasks[] | "Task \(.task_key): \(.state.result_state)"' "$BUNDLE_DIR/run_info.json" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 5: Collect Spark Logs
```bash
# Spark driver logs (requires cluster_id)
if [ -n "$CLUSTER_ID" ]; then
    echo "--- Spark Driver Logs (last 500 lines) ---" > "$BUNDLE_DIR/driver_logs.txt"  # HTTP 500 Internal Server Error

    # Get logs via API
    python3 << EOF >> "$BUNDLE_DIR/driver_logs.txt" 2>&1
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
try:
    logs = w.clusters.get_cluster_driver_logs(cluster_id="$CLUSTER_ID")
    print(logs.log_content[:50000] if logs.log_content else "No logs available")  # 50000ms = 50 seconds
except Exception as e:
    print(f"Error fetching logs: {e}")
EOF
fi
```

### Step 6: Collect Delta Table Info
```bash
# Delta table diagnostics (if table provided)
TABLE_NAME="${3:-}"
if [ -n "$TABLE_NAME" ]; then
    echo "--- Delta Table Info: $TABLE_NAME ---" >> "$BUNDLE_DIR/summary.txt"

    python3 << EOF >> "$BUNDLE_DIR/delta_info.txt" 2>&1
from databricks.sdk import WorkspaceClient
from databricks.connect import DatabricksSession

w = WorkspaceClient()
spark = DatabricksSession.builder.getOrCreate()

# Table history
print("=== Table History ===")
history_df = spark.sql(f"DESCRIBE HISTORY {TABLE_NAME} LIMIT 20")
history_df.show(truncate=False)

# Table details
print("\n=== Table Details ===")
spark.sql(f"DESCRIBE DETAIL {TABLE_NAME}").show(truncate=False)

# Schema
print("\n=== Schema ===")
spark.sql(f"DESCRIBE {TABLE_NAME}").show(truncate=False)
EOF
fi
```

### Step 7: Package Bundle
```bash
set -euo pipefail
# Create config snapshot (redacted)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
cat ~/.databrickscfg 2>/dev/null | sed 's/token = .*/token = ***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"

# Network connectivity test
echo "--- Network Test ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" "${DATABRICKS_HOST}/api/2.0/clusters/list" \
    -H "Authorization: Bearer ${DATABRICKS_TOKEN}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Package everything
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "Contents:"
echo "  - summary.txt: Environment and error summary"
echo "  - cluster_info.json: Cluster configuration"
echo "  - cluster_events.json: Recent cluster events"
echo "  - run_info.json: Job run details"
echo "  - run_output.json: Task outputs and errors"
echo "  - driver_logs.txt: Spark driver logs"
echo "  - delta_info.txt: Delta table diagnostics"
echo "  - config-redacted.txt: CLI configuration (secrets removed)"
```

## Output
- `databricks-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and error summary
  - `cluster_info.json` - Cluster configuration
  - `cluster_events.json` - Recent cluster events
  - `run_info.json` - Job run details
  - `driver_logs.txt` - Spark driver logs
  - `config-redacted.txt` - Configuration (secrets removed)

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | Yes |
| Cluster config | Hardware/software setup | Yes |
| Cluster events | State changes, errors | Yes |
| Job run details | Task failures, timing | Yes |
| Spark logs | Stack traces, exceptions | Yes |
| Delta table info | Schema, history | Optional |

## Examples

### Sensitive Data Handling
**ALWAYS REDACT:**
- API tokens and secrets
- Personal access tokens
- Connection strings
- PII in logs

**Safe to Include:**
- Error messages
- Stack traces (check for PII)
- Cluster IDs, job IDs
- Configuration (without secrets)

### Usage
```bash
# Basic bundle (environment only)
./databricks-debug-bundle.sh

# With cluster diagnostics
./databricks-debug-bundle.sh cluster-12345-abcde  # port 12345 - example/test

# With job run diagnostics
./databricks-debug-bundle.sh cluster-12345-abcde 67890  # 67890 = configured value

# Full diagnostics with Delta table
./databricks-debug-bundle.sh cluster-12345 67890 catalog.schema.table
```

### Submit to Support
1. Create bundle: `bash databricks-debug-bundle.sh [cluster-id] [run-id]`
2. Review for sensitive data
3. Open support ticket at [Databricks Support](https://help.databricks.com)
4. Attach bundle to ticket

## Resources
- [Databricks Support](https://help.databricks.com)
- [Community Forum](https://community.databricks.com)
- [Status Page](https://status.databricks.com)

## Next Steps
For rate limit issues, see `databricks-rate-limits`.
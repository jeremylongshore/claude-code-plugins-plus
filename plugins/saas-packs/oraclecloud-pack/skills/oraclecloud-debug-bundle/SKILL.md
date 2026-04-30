---
name: oraclecloud-debug-bundle
description: "Collect OCI instance diagnostics \u2014 serial console, cloud-init logs,\
  \ metadata, and VCN flow logs \u2014 into a single debug bundle.\nUse when an OCI\
  \ instance is unresponsive, stuck in provisioning, or showing infrastructure errors.\n\
  Trigger with \"oraclecloud debug bundle\", \"oci diagnostics\", \"oci serial console\"\
  , \"oci instance debug\".\n"
allowed-tools: Read, Write, Edit, Bash(oci:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Debug Bundle

## Overview

Collect comprehensive diagnostics from an unresponsive OCI compute instance without touching the OCI Console. When an instance reports "unavailable due to an issue with the underlying infrastructure" or cloud-init failures, you need serial console output, cloud-init logs, instance metadata, and VCN flow logs — all gathered via CLI commands into a single tar archive for root-cause analysis or support ticket attachment.

**Purpose:** Generate a self-contained debug bundle (`.tar.gz`) with all the data OCI Support will ask for, collected in under 60 seconds.

## Prerequisites

- **OCI CLI installed and configured** — `oci --version` returns 3.x+, `~/.oci/config` is valid (see `oraclecloud-install-auth`)
- **Python 3.8+** with the OCI SDK — `pip install oci`
- **Compartment OCID** — the compartment containing the target instance
- **Instance OCID** — format: `ocid1.instance.oc1.{region}.aaaa...`
- **IAM policies** granting `inspect instance-console-histories`, `read instances`, `read vcn-flow-logs` in the target compartment

## Instructions

### Step 1: Set Target Variables

```bash
export INSTANCE_OCID="ocid1.instance.oc1.iad.YOUR_INSTANCE_OCID"
export COMPARTMENT_OCID="ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID"
export BUNDLE_DIR="oci-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
```

### Step 2: Capture Instance Metadata

```bash
oci compute instance get \
  --instance-id "$INSTANCE_OCID" \
  --query 'data.{state:"lifecycle-state",shape:shape,ad:"availability-domain",created:"time-created",fault:"fault-domain"}' \
  --output json > "$BUNDLE_DIR/instance-metadata.json"

echo "Instance state: $(jq -r '.state' "$BUNDLE_DIR/instance-metadata.json")"
```

### Step 3: Retrieve Serial Console History

The serial console captures kernel panics, boot failures, and cloud-init output — even when SSH is unreachable:

```bash
# Create a console history capture
CAPTURE_ID=$(oci compute instance-console-history capture \
  --instance-id "$INSTANCE_OCID" \
  --query 'data.id' --raw-output)

echo "Console history capture: $CAPTURE_ID"

# Wait for capture to complete, then download
sleep 10
oci compute instance-console-history get-content \
  --instance-console-history-id "$CAPTURE_ID" \
  > "$BUNDLE_DIR/serial-console.log"

echo "Serial console: $(wc -l < "$BUNDLE_DIR/serial-console.log") lines"
```

### Step 4: Extract Cloud-Init Logs via Instance Agent

If the instance agent is running, pull cloud-init logs via the run-command plugin:

```bash
COMMAND_ID=$(oci instance-agent command create \
  --compartment-id "$COMPARTMENT_OCID" \
  --target '{"instanceId":"'"$INSTANCE_OCID"'"}' \
  --content '{"source":{"sourceType":"TEXT","text":"cat /var/log/cloud-init.log | tail -200"}}' \
  --timeout-in-seconds 30 \
  --query 'data.id' --raw-output)

sleep 15
oci instance-agent command get \
  --command-id "$COMMAND_ID" \
  --query 'data."delivery-state"' --raw-output

# Retrieve output
oci instance-agent command get-content \
  --command-id "$COMMAND_ID" \
  > "$BUNDLE_DIR/cloud-init.log"
```

### Step 5: Collect VCN Flow Logs

```bash
oci logging search \
  --search-query "search \"$COMPARTMENT_OCID\" | where source = 'vcn' | sort by datetime desc" \
  --time-start "$(date -u -d '-1 hour' +%Y-%m-%dT%H:%M:%SZ)" \
  --time-end "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --output json > "$BUNDLE_DIR/vcn-flow-logs.json" 2>&1 || echo "Flow logs unavailable" > "$BUNDLE_DIR/vcn-flow-logs.json"
```

### Step 6: Query Instance Metrics

```python
import oci
import datetime
import json

config = oci.config.from_file("~/.oci/config")
monitoring = oci.monitoring.MonitoringClient(config)

end = datetime.datetime.utcnow()
start = end - datetime.timedelta(hours=1)

response = monitoring.summarize_metrics_data(
    compartment_id="COMPARTMENT_OCID",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='CpuUtilization[5m]{resourceId = "INSTANCE_OCID"}.max()',
        start_time=start.isoformat() + "Z",
        end_time=end.isoformat() + "Z",
    ),
)

with open("oci-debug-bundle/instance-metrics.json", "w") as f:
    json.dump([item.__dict__ for item in response.data], f, indent=2, default=str)
```

### Step 7: Package the Bundle

```bash
# Add a summary header
cat > "$BUNDLE_DIR/README.txt" << EOF
OCI Debug Bundle
Instance: $INSTANCE_OCID
Captured: $(date -u)
Contents:
  instance-metadata.json  - Lifecycle state, shape, AD, fault domain
  serial-console.log      - Serial console history (boot output, kernel msgs)
  cloud-init.log          - Cloud-init execution log (last 200 lines)
  vcn-flow-logs.json      - VCN flow log entries (last 1 hour)
  instance-metrics.json   - CPU utilization metrics (last 1 hour)
EOF

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle ready: $BUNDLE_DIR.tar.gz ($(du -h "$BUNDLE_DIR.tar.gz" | cut -f1))"
```

## Output

Successful completion produces:
- A `oci-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing five diagnostic files
- Instance metadata showing current lifecycle state, shape, and fault domain
- Serial console log capturing boot output, kernel messages, and cloud-init status
- Cloud-init execution logs (last 200 lines) retrieved via the instance agent
- VCN flow logs for the last hour to identify network-level issues
- CPU utilization metrics to detect resource exhaustion

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthorizedOrNotFound | 404 | Missing IAM policy or wrong OCID | Add `allow group <grp> to inspect instance-console-histories in compartment <comp>` |
| NotAuthenticated | 401 | Expired or invalid API key | Re-validate config: `oci iam user get --user-id $(grep ^user ~/.oci/config \| cut -d= -f2)` |
| Instance agent unreachable | — | Agent not running or instance stopped | Fall back to serial console history only (Step 3) |
| TooManyRequests | 429 | Rate limited on console history API | Wait 30 seconds and retry — OCI does not return a Retry-After header |
| InternalError | 500 | OCI service issue | Retry after 60 seconds; check https://ocistatus.oraclecloud.com |
| Flow logs empty | — | VCN flow logs not enabled | Enable flow logs: VCN > Subnet > Flow Logs > Enable |

## Examples

**Quick one-liner to check if instance is reachable:**

```bash
oci compute instance get --instance-id "$INSTANCE_OCID" \
  --query 'data."lifecycle-state"' --raw-output
# Expected: RUNNING, STOPPED, or TERMINATED
```

**Automated bundle script (saves as `oci-debug.sh`):**

```bash
#!/bin/bash
set -euo pipefail
INSTANCE_OCID="${1:?Usage: oci-debug.sh <instance-ocid>}"
COMPARTMENT_OCID="${2:?Usage: oci-debug.sh <instance-ocid> <compartment-ocid>}"
BUNDLE="oci-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
oci compute instance get --instance-id "$INSTANCE_OCID" --output json > "$BUNDLE/metadata.json"
CAPTURE=$(oci compute instance-console-history capture --instance-id "$INSTANCE_OCID" --query 'data.id' --raw-output)
sleep 10
oci compute instance-console-history get-content --instance-console-history-id "$CAPTURE" > "$BUNDLE/serial.log"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources

- [OCI Instance Console Connections](https://docs.oracle.com/en-us/iaas/Content/Compute/References/serialconsole.htm) — serial console access and history capture
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — full command-line interface documentation
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — MonitoringClient and ComputeClient APIs
- [VCN Flow Logs](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/vcn_flow_logs.htm) — enabling and querying flow logs
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common auth and connectivity issues
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — current platform-known issues

## Next Steps

After collecting the debug bundle, review `oraclecloud-incident-runbook` for guided triage and recovery actions, or `oraclecloud-common-errors` for decoding specific error codes in the serial console output.

---
name: oraclecloud-query-transform
description: 'Query OCI metrics with MQL and create monitoring alarms via the Python
  SDK.

  Use when building dashboards, querying CPU/memory/network metrics, or creating alarms.

  Trigger with "oci monitoring", "mql query", "oci metrics", "oci alarm", "cpu utilization
  oci".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# OCI Monitoring — MQL Queries & Alarms

## Overview

Query OCI metrics using MQL (Monitoring Query Language) and create alarms via the Python SDK. MQL is underdocumented and the console query builder is buggy — it often generates invalid syntax or silently returns empty results. This skill provides working MQL queries for the metrics you actually need (CPU, memory, network, disk) via the SDK, bypassing console issues entirely.

**Purpose:** Retrieve infrastructure metrics programmatically and set up alerting without relying on the OCI Console query builder.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **Config file** at `~/.oci/config` with fields: `user`, `fingerprint`, `tenancy`, `region`, `key_file`
- **IAM policies:**
  - `Allow group Developers to read metrics in compartment <name>`
  - `Allow group Developers to manage alarms in compartment <name>`
  - `Allow group Developers to manage ons-topics in compartment <name>` (for alarm notifications)
- **Python 3.8+**
- Running compute instances or other resources emitting metrics

## Instructions

### Step 1: Understand MQL Syntax

MQL queries follow this pattern:

```
MetricName[interval]{dimensionKey = "value"}.groupingFunction.statistic
```

Key components:
- **MetricName** — e.g., `CpuUtilization`, `MemoryUtilization`, `NetworkBytesIn`
- **Interval** — data granularity: `1m`, `5m`, `1h` (minimum depends on metric)
- **Dimensions** — filters in curly braces: `{resourceId = "ocid1.instance..."}`
- **Grouping** — `.groupBy(dimension)` to split results
- **Statistic** — `.mean()`, `.max()`, `.min()`, `.sum()`, `.count()`, `.percentile(0.95)`

### Step 2: Query CPU Utilization

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
monitoring = oci.monitoring.MonitoringClient(config)

# CPU utilization across all instances (last 1 hour, 5-minute intervals)
response = monitoring.summarize_metrics_data(
    compartment_id=config["tenancy"],
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='CpuUtilization[5m].mean()',
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow(),
    ),
)

for metric in response.data:
    resource = metric.dimensions.get("resourceDisplayName", "unknown")
    for dp in metric.aggregated_datapoints:
        print(f"{resource} | {dp.timestamp} | CPU: {dp.value:.1f}%")
```

### Step 3: Query Memory, Network, and Disk Metrics

```python
# Memory utilization (requires OCI monitoring agent on instance)
mem_query = 'MemoryUtilization[5m].mean()'

# Network bytes in/out
net_in_query = 'NetworkBytesIn[5m].sum()'
net_out_query = 'NetworkBytesOut[5m].sum()'

# Disk I/O
disk_read_query = 'DiskBytesRead[5m].sum()'
disk_write_query = 'DiskBytesWritten[5m].sum()'

# Query helper function
def query_metric(query, namespace="oci_computeagent", hours=1):
    """Query a single metric and return results."""
    response = monitoring.summarize_metrics_data(
        compartment_id=config["tenancy"],
        summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
            namespace=namespace,
            query=query,
            start_time=datetime.utcnow() - timedelta(hours=hours),
            end_time=datetime.utcnow(),
        ),
    )
    return response.data

# Example: get all core metrics for the last hour
for name, query in [
    ("CPU", "CpuUtilization[5m].mean()"),
    ("Memory", "MemoryUtilization[5m].mean()"),
    ("Net In", "NetworkBytesIn[5m].sum()"),
    ("Net Out", "NetworkBytesOut[5m].sum()"),
    ("Disk Read", "DiskBytesRead[5m].sum()"),
    ("Disk Write", "DiskBytesWritten[5m].sum()"),
]:
    results = query_metric(query)
    if results:
        latest = results[0].aggregated_datapoints[-1]
        print(f"{name}: {latest.value:.2f} at {latest.timestamp}")
    else:
        print(f"{name}: no data (check monitoring agent)")
```

### Step 4: Filter by Specific Instance

```python
# Query a specific instance by OCID
instance_id = "ocid1.instance.oc1..."
filtered_query = f'CpuUtilization[5m]{{resourceId = "{instance_id}"}}.max()'

response = monitoring.summarize_metrics_data(
    compartment_id=config["tenancy"],
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query=filtered_query,
        start_time=datetime.utcnow() - timedelta(hours=6),
        end_time=datetime.utcnow(),
    ),
)

for metric in response.data:
    peak = max(metric.aggregated_datapoints, key=lambda dp: dp.value)
    print(f"Peak CPU in last 6h: {peak.value:.1f}% at {peak.timestamp}")
```

### Step 5: List Available Metrics

When you are unsure what metrics exist, list them first.

```python
metrics = monitoring.list_metrics(
    compartment_id=config["tenancy"],
    list_metrics_details=oci.monitoring.models.ListMetricsDetails(
        namespace="oci_computeagent",
    ),
).data

unique_metrics = set()
for m in metrics:
    unique_metrics.add(m.name)

print("Available metrics:")
for name in sorted(unique_metrics):
    print(f"  {name}")
```

Common namespaces: `oci_computeagent` (compute), `oci_vcn` (networking), `oci_objectstorage` (storage), `oci_blockstore` (block volumes), `oci_autonomous_database` (ADB).

### Step 6: Create an Alarm

```python
# First, create a notification topic
notifications = oci.ons.NotificationDataPlaneClient(config)
control_plane = oci.ons.NotificationControlPlaneClient(config)

topic = control_plane.create_topic(
    oci.ons.models.CreateTopicDetails(
        compartment_id=config["tenancy"],
        name="high-cpu-alerts",
        description="Alerts for high CPU utilization",
    )
).data

# Create a subscription (email)
notifications.create_subscription(
    oci.ons.models.CreateSubscriptionDetails(
        compartment_id=config["tenancy"],
        topic_id=topic.topic_id,
        protocol="EMAIL",
        endpoint="ops-team@example.com",
    )
)

# Create the alarm
monitoring.create_alarm(
    oci.monitoring.models.CreateAlarmDetails(
        compartment_id=config["tenancy"],
        display_name="High CPU Alert",
        namespace="oci_computeagent",
        query="CpuUtilization[5m].mean() > 80",
        severity="CRITICAL",
        destinations=[topic.topic_id],
        is_enabled=True,
        body="CPU utilization exceeded 80% for 5 minutes.",
        pending_duration="PT5M",  # ISO 8601 — must be high for 5 minutes
        repeat_notification_duration="PT15M",  # Re-alert every 15 minutes
    )
)
print("Alarm created — email confirmation sent to subscriber")
```

## Output

Successful completion produces:
- Working MQL queries for CPU, memory, network, and disk metrics
- A reusable `query_metric()` helper function for ad-hoc monitoring
- Instance-level metric filtering by OCID
- A notification topic with email subscription and a CPU alarm

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Empty results | N/A | Wrong namespace or monitoring agent not installed | List metrics first (Step 5); install OCI monitoring agent on instances |
| Not authorized | 404 NotAuthorizedOrNotFound | Missing IAM policy for metrics or alarms | Add `read metrics` and `manage alarms` IAM policies |
| Invalid MQL | 400 InvalidParameter | Syntax error in MQL query | Check brackets, quotes, and statistic function names |
| Not authenticated | 401 NotAuthenticated | Bad API key or config | Verify `~/.oci/config` key_file and fingerprint |
| Rate limited | 429 TooManyRequests | Too many API calls | Add backoff; OCI does not return Retry-After header |
| Timeout | ServiceError status -1 | Query too broad or long time range | Narrow the time range or add dimension filters |

## Examples

**Quick metric check via CLI:**

```bash
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <OCID> \
  --namespace oci_computeagent \
  --query-text 'CpuUtilization[1h].mean()'
```

**MQL cheat sheet:**

```
# Average CPU across all instances
CpuUtilization[5m].mean()

# Peak CPU for one instance
CpuUtilization[5m]{resourceId = "ocid1.instance..."}.max()

# Group by instance name
CpuUtilization[5m].groupBy(resourceDisplayName).mean()

# 95th percentile memory
MemoryUtilization[5m].percentile(0.95)

# Total network traffic
NetworkBytesIn[5m].sum() + NetworkBytesOut[5m].sum()
```

## Resources

- [Monitoring Overview](https://docs.oracle.com/en-us/iaas/Content/) — metrics, queries, and alarms
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — MonitoringClient API
- [API Reference](https://docs.oracle.com/en-us/iaas/api/) — Monitoring REST endpoints
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common SDK errors
- [OCI Status](https://ocistatus.oraclecloud.com) — current service health

## Next Steps

After setting up monitoring, see `oraclecloud-schema-migration` to monitor Autonomous Database metrics, or `oraclecloud-core-workflow-a` to correlate compute metrics with instance scaling decisions.

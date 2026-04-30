---
name: oraclecloud-observability
description: 'Set up programmatic monitoring, logging, and alarms for OCI resources.

  Use when configuring OCI Monitoring metrics, creating alarm rules, publishing custom
  metrics, or searching logs via the Logging service.

  Trigger with "oraclecloud observability", "oci monitoring", "oci alarms", "oci logging",
  "oracle cloud observability".

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
# Oracle Cloud Observability

## Overview

Set up programmatic monitoring for OCI infrastructure using the Monitoring, Logging, and Notifications services. The OCI Console buries these features behind nested menus, and the status page has historically failed to acknowledge outages (e.g., London region, January 2026). This skill builds monitoring you control through code — metric queries, alarm rules, custom metric publishing, and log searches — so you are never surprised by an outage you should have caught.

**Purpose:** Create a code-driven observability stack that queries metrics, fires alarms, publishes custom metrics, and searches logs without depending on the OCI Console.

## Prerequisites

- **OCI tenancy** with an API signing key in `~/.oci/config`
- **Python 3.8+** with `pip install oci`
- **Compartment OCID** containing the resources to monitor
- **IAM policies** granting `manage alarms` and `read metrics` in the target compartment
- **Notification topic** created for alarm destinations (or create one in Step 4)

## Instructions

### Step 1: Query Metrics with MonitoringClient

OCI publishes built-in metrics for compute, networking, block storage, and more. Query them programmatically:

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
monitoring = oci.monitoring.MonitoringClient(config)

# Query CPU utilization for all instances in a compartment
response = monitoring.summarize_metrics_data(
    compartment_id="ocid1.compartment.oc1..example",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='CpuUtilization[5m]{availabilityDomain = "Uocm:US-ASHBURN-AD-1"}.mean()',
        start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        end_time=datetime.utcnow().isoformat() + "Z"
    )
)

for metric in response.data:
    for dp in metric.aggregated_datapoints:
        print(f"{dp.timestamp}: {dp.value:.1f}% CPU")
```

### Step 2: Create Alarm Rules

Alarms trigger when a metric crosses a threshold. Create them via SDK so they survive Console UI changes:

```python
monitoring.create_alarm(
    oci.monitoring.models.CreateAlarmDetails(
        display_name="High CPU Alert",
        compartment_id="ocid1.compartment.oc1..example",
        metric_compartment_id="ocid1.compartment.oc1..example",
        namespace="oci_computeagent",
        query='CpuUtilization[5m].mean() > 80',
        severity="CRITICAL",
        body="CPU utilization exceeded 80% for 5 minutes.",
        destinations=["ocid1.onstopic.oc1..example"],
        is_enabled=True,
        pending_duration="PT5M",
        repeat_notification_duration="PT15M"
    )
)
print("Alarm created: High CPU Alert")
```

### Step 3: Publish Custom Metrics

Push application-level metrics into OCI Monitoring so they can trigger the same alarm system:

```python
from datetime import datetime

monitoring.post_metric_data(
    oci.monitoring.models.PostMetricDataDetails(
        metric_data=[
            oci.monitoring.models.MetricDataDetails(
                namespace="custom_app",
                compartment_id="ocid1.compartment.oc1..example",
                name="RequestLatencyMs",
                dimensions={"service": "api-gateway", "endpoint": "/v1/orders"},
                datapoints=[
                    oci.monitoring.models.Datapoint(
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        value=142.5
                    )
                ]
            )
        ]
    )
)
print("Custom metric published: RequestLatencyMs = 142.5ms")
```

### Step 4: Set Up Notifications

Create a notification topic and email subscription to receive alarm alerts:

```python
notifications = oci.ons.NotificationDataPlaneClient(config)
control_plane = oci.ons.NotificationControlPlaneClient(config)

# Create topic
topic = control_plane.create_topic(
    oci.ons.models.CreateTopicDetails(
        name="infra-alerts",
        compartment_id="ocid1.compartment.oc1..example",
        description="Infrastructure alarm notifications"
    )
).data

# Subscribe an email endpoint
notifications.create_subscription(
    oci.ons.models.CreateSubscriptionDetails(
        topic_id=topic.topic_id,
        compartment_id="ocid1.compartment.oc1..example",
        protocol="EMAIL",
        endpoint="oncall@example.com"
    )
)
print(f"Topic created: {topic.topic_id}")
```

### Step 5: Search Logs

Query the OCI Logging service to find specific events across your infrastructure:

```python
logging_search = oci.loggingsearch.LogSearchClient(config)

results = logging_search.search_logs(
    oci.loggingsearch.models.SearchLogsDetails(
        time_start=(datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        time_end=datetime.utcnow().isoformat() + "Z",
        search_query=(
            'search "ocid1.compartment.oc1..example" '
            '| where data.statusCode = 500'
        ),
        is_return_field_info=False
    )
)

for log_entry in results.data.results:
    print(f"{log_entry.data}")
```

### Step 6: Health Check Probes

Monitor endpoint availability with OCI Health Checks:

```python
health = oci.healthchecks.HealthChecksClient(config)

health.create_http_monitor(
    oci.healthchecks.models.CreateHttpMonitorDetails(
        compartment_id="ocid1.compartment.oc1..example",
        display_name="API Health Check",
        targets=["api.example.com"],
        protocol="HTTPS",
        port=443,
        path="/health",
        interval_in_seconds=30,
        timeout_in_seconds=10,
        is_enabled=True
    )
)
print("Health check probe created: api.example.com/health every 30s")
```

## Output

Successful completion produces:
- Metric queries returning CPU, memory, and network data for your compartment
- Alarm rules that fire to notification topics when thresholds are breached
- Custom application metrics published to OCI Monitoring
- A notification topic with email subscription for alert delivery
- Log search queries for troubleshooting 500 errors and other events
- HTTP health check probes for endpoint availability monitoring

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad API key or expired config | Verify `~/.oci/config` fingerprint matches your API key |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy for monitoring | Add: `Allow group X to manage alarms in compartment Y` |
| TooManyRequests | 429 | Rate limited on metric queries | Reduce query frequency; cache results for dashboards |
| InternalError | 500 | OCI Monitoring service issue | Check [OCI Status](https://ocistatus.oraclecloud.com) and retry |
| InvalidParameter | 400 | Wrong MQL query syntax | Verify namespace and metric name; use `list_metrics` to discover available metrics |
| ServiceError status -1 | N/A | Request timeout on large queries | Narrow the time window or add dimension filters |

## Examples

**Quick metric check with OCI CLI:**

```bash
# List available metric namespaces
oci monitoring metric list \
  --compartment-id ocid1.compartment.oc1..example \
  --namespace oci_computeagent

# List all alarms
oci monitoring alarm list \
  --compartment-id ocid1.compartment.oc1..example
```

**List all metrics in a namespace to discover what's available:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
monitoring = oci.monitoring.MonitoringClient(config)

metrics = monitoring.list_metrics(
    compartment_id="ocid1.compartment.oc1..example",
    list_metrics_details=oci.monitoring.models.ListMetricsDetails(
        namespace="oci_computeagent"
    )
).data

for m in metrics:
    print(f"{m.name} — dimensions: {m.dimensions}")
```

## Resources

- [OCI Monitoring](https://docs.oracle.com/en-us/iaas/Content/Monitoring/home.htm) — metrics, alarms, and MQL query language
- [OCI Logging](https://docs.oracle.com/en-us/iaas/Content/Logging/home.htm) — centralized log service
- [OCI Notifications](https://docs.oracle.com/en-us/iaas/Content/Notification/home.htm) — alarm delivery via email, Slack, PagerDuty
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — SDK reference
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — current platform issues

## Next Steps

After monitoring is in place, proceed to `oraclecloud-performance-tuning` to optimize shape and storage performance, or see `oraclecloud-cost-tuning` to set up budget alerts that use the same notification topics.

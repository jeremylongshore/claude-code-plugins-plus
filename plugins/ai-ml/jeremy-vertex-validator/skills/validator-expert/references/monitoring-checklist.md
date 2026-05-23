# Monitoring Validation Checklist (20% Weight)

Sources:

- [Cloud Monitoring Alerting](https://cloud.google.com/monitoring/alerts)
- [Service Monitoring SLOs](https://cloud.google.com/monitoring/service-monitoring)
- [Cloud Logging](https://cloud.google.com/logging/docs)

---

## Observability Dashboard

- Agent Engine observability dashboard configured in Cloud Monitoring
- Token usage tracking enabled with per-model granularity
- Error rate monitoring active with breakdown by error type
- Latency metrics tracked (p50, p90, p95, p99) for agent invocations
- Cost tracking dashboard with daily/weekly spend projections

### Validation commands

```bash
# List monitoring dashboards
gcloud monitoring dashboards list --project=PROJECT_ID --format="table(name,displayName)"

# Check if Monitoring API is enabled
gcloud services list --project=PROJECT_ID --filter="name:monitoring.googleapis.com" --format="value(state)"
```

## Alerting

- Alert policies configured for critical errors (error rate > 5%, latency p95 > 10s)
- Notification channels set up (email, Slack, PagerDuty) and verified
- Alert thresholds appropriate for workload pattern (batch vs interactive)
- Alert escalation policies defined with multi-tier notification
- Alert silence/snooze policies documented for maintenance windows

### Validation commands

```bash
# List alert policies
gcloud monitoring alert-policies list --project=PROJECT_ID --format="table(displayName,enabled,conditions.displayName)"

# List notification channels
gcloud monitoring channels list --project=PROJECT_ID --format="table(displayName,type,enabled)"
```

## SLOs & SLIs

- Service Level Objectives defined for availability (target >= 99.5%) and latency (p95 < 5s)
- Error budget configured with burn-rate alerting
- SLI metrics tracked: availability, latency, throughput, error rate
- SLO compliance reporting enabled with weekly/monthly windows

### Validation commands

```bash
# List SLOs (requires Cloud Monitoring Service Monitoring)
gcloud monitoring slos list --service=PROJECT_SERVICE_ID --project=PROJECT_ID 2>/dev/null || echo "No SLOs defined"
```

```python
# Programmatic SLO check
from google.cloud import monitoring_v3

slo_client = monitoring_v3.ServiceMonitoringServiceClient()
parent = f"projects/{project_id}/services/{service_id}"
slos = list(slo_client.list_service_level_objectives(parent=parent))
if not slos:
    print("WARNING: No SLOs defined for this service")
for slo in slos:
    print(f"SLO: {slo.display_name}, Goal: {slo.goal}")
```

## Logging

- Cloud Logging enabled for Agent Engine
- Log retention policies configured (>90 days for ops, >365 for compliance)
- Structured logging format with severity levels and correlation IDs
- PII data properly redacted in logs (no user prompts in plain text)
- Log-based metrics created for key agent events

### Validation commands

```bash
# Check log sink configuration
gcloud logging sinks list --project=PROJECT_ID --format="table(name,destination,filter)"

# Check log retention (default bucket)
gcloud logging buckets describe _Default --project=PROJECT_ID --location=global --format="value(retentionDays)"

# Verify structured logging with recent entries
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine" --project=PROJECT_ID --limit=5 --format=json
```

### Validation code

```python
def validate_monitoring(project_id, agent_id=None):
    """Validate monitoring configuration for Agent Engine deployment."""
    from google.cloud import monitoring_v3

    results = []

    # Check alert policies
    alert_client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"
    alert_policies = list(alert_client.list_alert_policies(name=project_name))

    agent_alerts = alert_policies
    if agent_id:
        agent_alerts = [
            p for p in alert_policies
            if agent_id in (p.display_name or "").lower()
        ]

    results.append({
        "category": "Monitoring",
        "check": "Alert Policies",
        "status": "PASS" if agent_alerts else "FAIL",
        "evidence": f"Found {len(agent_alerts)} alert policies" if agent_alerts
                    else f"No alert policies found (total project alerts: {len(alert_policies)})",
        "remediation": "Create alert policies for error rate, latency, and availability"
    })

    # Check notification channels
    channel_client = monitoring_v3.NotificationChannelServiceClient()
    channels = list(channel_client.list_notification_channels(name=project_name))
    verified_channels = [c for c in channels if c.verification_status.name == "VERIFIED"]

    results.append({
        "category": "Monitoring",
        "check": "Notification Channels",
        "status": "PASS" if verified_channels else "WARNING",
        "evidence": f"{len(verified_channels)} verified channels of {len(channels)} total",
        "remediation": "Verify notification channels and test delivery"
    })

    return results
```

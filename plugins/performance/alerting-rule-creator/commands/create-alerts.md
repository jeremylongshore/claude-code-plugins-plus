---
name: create-alerts
description: Create intelligent alerting rules
---
# Alerting Rule Creator

Create comprehensive alerting rules to detect performance issues proactively.

## Alert Categories

1. **Latency Alerts**: Response time degradation
2. **Error Rate Alerts**: Elevated error percentages
3. **Throughput Alerts**: Traffic anomalies
4. **Resource Alerts**: CPU, memory, disk saturation
5. **Availability Alerts**: Service downtime
6. **SLO Violation Alerts**: Service level breach warnings

## Alert Design Principles

- Avoid alert fatigue with proper thresholds
- Use multi-window alerts to reduce false positives
- Implement severity levels (critical, warning, info)
- Include actionable information in alert messages
- Set appropriate escalation policies

## Process

1. Identify critical metrics and failure modes
2. Define alert conditions and thresholds
3. Design alert routing and escalation
4. Create alert rule configurations
5. Implement runbooks for alert responses

## Output

Provide:
- Alert rule definitions (Prometheus, Datadog, etc.)
- Threshold calculations with rationale
- Alert routing configuration
- Escalation policies
- Runbooks for common alerts
- Alert testing procedures

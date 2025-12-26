---
name: track-sla-sli
description: Track SLAs, SLIs, and SLOs
---
# SLA/SLI/SLO Tracker

Define and track Service Level Agreements, Indicators, and Objectives.

## Components

1. **SLI (Service Level Indicators)**: Quantitative measures of service
   - Availability: Uptime percentage
   - Latency: Response time percentiles
   - Error Rate: Request failure percentage
   - Throughput: Requests per second

2. **SLO (Service Level Objectives)**: Target values for SLIs
   - Example: 99.9% availability, p95 < 200ms

3. **SLA (Service Level Agreements)**: Formal commitments
   - Customer-facing availability guarantees
   - Penalty clauses for violations

4. **Error Budgets**: Allowed downtime/errors

## Process

1. Define critical user journeys
2. Identify measurable SLIs
3. Set realistic SLO targets based on data
4. Calculate error budgets
5. Implement SLI measurement
6. Create monitoring dashboards
7. Set up SLO violation alerting

## Output

Provide:
- SLI definitions with measurement methodology
- SLO targets with justification
- Error budget calculations
- Monitoring implementation code
- Dashboard configuration for SLI tracking
- Alert rules for SLO violations
- Error budget policy recommendations

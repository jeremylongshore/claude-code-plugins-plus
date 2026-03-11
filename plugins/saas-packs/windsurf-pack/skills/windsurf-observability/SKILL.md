---
name: windsurf-observability
description: |
  Set up comprehensive observability for Windsurf integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Windsurf operations, setting up dashboards,
  or configuring alerting for Windsurf integration health.
  Trigger with phrases like "windsurf monitoring", "windsurf metrics",
  "windsurf observability", "monitor windsurf", "windsurf alerts", "windsurf tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Observability

## Overview
Monitor Windsurf AI IDE adoption, feature usage, and productivity impact across your team. Key metrics include AI completion acceptance rate (how often developers accept Supercomplete suggestions), Cascade flow completion rate (agentic tasks that succeed vs fail), per-developer usage patterns, and seat utilization for license optimization.

## Prerequisites
- Windsurf Pro or Enterprise plan
- Admin dashboard access at windsurf.com/dashboard
- Team members using Windsurf IDE

## Instructions

### Step 1: Track AI Feature Adoption via Admin Dashboard
Access Windsurf Admin Dashboard > Analytics for team-wide metrics:
```yaml
# Key metrics available in the dashboard
metrics:
  completions_shown:     total suggestions presented to developers
  completions_accepted:  suggestions accepted (acceptance rate = accepted/shown)
  cascade_flows_run:     agentic tasks initiated
  cascade_flows_success: agentic tasks completed successfully
  active_users_daily:    unique developers using Windsurf per day
  tokens_consumed:       total AI tokens used across team
```

### Step 2: Export Metrics for External Monitoring
```typescript
// windsurf-metrics-exporter.ts
async function exportWindsurfMetrics() {
  const analytics = await fetch('https://api.windsurf.com/v1/admin/analytics?period=today', {
    headers: { Authorization: `Bearer ${WINDSURF_ADMIN_KEY}` },
  }).then(r => r.json());

  emitGauge('windsurf_acceptance_rate', analytics.completions_accepted / analytics.completions_shown * 100);
  emitGauge('windsurf_cascade_success_rate', analytics.cascade_success / analytics.cascade_total * 100);
  emitGauge('windsurf_active_users', analytics.active_users);
  emitGauge('windsurf_seat_utilization_pct', analytics.active_users / analytics.total_seats * 100);
}
```

### Step 3: Monitor Seat Utilization
```typescript
// Identify underutilized seats for cost optimization
async function auditSeatUsage() {
  const members = await fetch('https://api.windsurf.com/v1/admin/members', {
    headers: { Authorization: `Bearer ${WINDSURF_ADMIN_KEY}` },
  }).then(r => r.json());

  const underutilized = members.filter((m: any) => m.completions_last_30d < 10);
  console.log(`${underutilized.length} seats with <10 completions in 30 days:`);
  underutilized.forEach((m: any) => console.log(`  ${m.email}: ${m.completions_last_30d} completions`));
}
```

### Step 4: Alert on Issues
```yaml
groups:
  - name: windsurf
    rules:
      - alert: WindsurfLowAcceptanceRate
        expr: windsurf_acceptance_rate < 20
        for: 7d
        annotations: { summary: "Windsurf completion acceptance rate below 20% -- review config" }
      - alert: WindsurfCascadeFailures
        expr: windsurf_cascade_success_rate < 50
        for: 1d
        annotations: { summary: "Over 50% of Cascade flows failing -- check workspace config" }
      - alert: WindsurfLowUtilization
        expr: windsurf_seat_utilization_pct < 50
        for: 7d
        annotations: { summary: "Less than 50% of Windsurf seats actively used" }
```

### Step 5: Dashboard Panels
Track: daily active users vs total seats, acceptance rate trend (higher is better), Cascade flow success rate, completions per developer (identify power users), seat utilization for license optimization, and tokens consumed per developer. Low acceptance rates suggest configuration tuning is needed.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Low acceptance rate | Suggestions not matching coding style | Add workspace-level coding standards in settings |
| Cascade flow failures | Insufficient tool permissions | Check `.windsurf/settings.json` for tool access |
| Seat utilization low | Team not adopted | Run training session, share productivity data |
| Analytics data missing | Enterprise API not enabled | Contact Windsurf support to enable admin API |

## Examples

**Basic usage**: Apply windsurf observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize windsurf observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack
---
name: windsurf-observability
description: |
  Monitor Windsurf AI adoption, feature usage, and team productivity metrics.
  Use when tracking AI feature usage, measuring ROI, setting up dashboards,
  or analyzing Cascade effectiveness across your team.
  Trigger with phrases like "windsurf monitoring", "windsurf metrics",
  "windsurf analytics", "windsurf usage", "windsurf adoption".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, monitoring, analytics, team-management]

---
# Windsurf Observability

## Overview
Monitor Windsurf AI IDE adoption, feature usage, and productivity impact across your team. Covers Admin Dashboard analytics, custom tracking via extensions, and ROI measurement.

## Prerequisites
- Windsurf Teams or Enterprise plan
- Admin dashboard access at windsurf.com/dashboard
- Team members actively using Windsurf

## Instructions

### Step 1: Access Admin Dashboard Analytics

Navigate to Admin Dashboard > Analytics for team-wide metrics:

```yaml
# Key metrics available in Windsurf Admin Dashboard
core_metrics:
  adoption:
    active_users_daily: "Unique developers using Windsurf per day"
    seat_utilization: "Active users / total seats (target: >80%)"
    feature_adoption: "Which AI features each user uses"

  quality:
    completion_acceptance_rate: "Supercomplete suggestions accepted vs shown"
    cascade_flow_success_rate: "Cascade tasks completed vs failed"

  consumption:
    credits_consumed_per_user: "Monthly credit usage per team member"
    credits_by_model: "Which AI models consume the most credits"

  efficiency:
    tasks_per_session: "Average Cascade interactions per session"
    time_saved_estimate: "Based on task complexity and completion speed"
```

### Step 2: Set Up Usage Alerts

Monitor for underutilization and overuse:

```yaml
# Alert thresholds for team management
alerts:
  low_adoption:
    condition: "seat_utilization < 50% for 7 days"
    action: "Schedule team training session"

  low_acceptance_rate:
    condition: "completion_acceptance_rate < 20% for 7 days"
    action: "Review .windsurfrules — AI suggestions not matching project patterns"

  high_cascade_failures:
    condition: "cascade_success_rate < 50% for 3 days"
    action: "Check workspace config — .codeiumignore may be too aggressive"

  credit_overspend:
    condition: "team_credits > 80% consumed before month half"
    action: "Review per-user usage, coach on credit conservation"

  inactive_seats:
    condition: "user has <10 interactions in 30 days"
    action: "Offer training or downgrade to Free tier"
```

### Step 3: Build Custom Extension for Detailed Tracking

```typescript
// windsurf-analytics-extension/src/extension.ts
import * as vscode from "vscode";

interface UsageEvent {
  event: string;
  timestamp: string;
  userId: string;
  file?: string;
  metadata?: Record<string, unknown>;
}

const events: UsageEvent[] = [];

export function activate(context: vscode.ExtensionContext) {
  // Track Cascade usage patterns
  const cascadeListener = vscode.workspace.onDidSaveTextDocument((doc) => {
    events.push({
      event: "file_save_after_cascade",
      timestamp: new Date().toISOString(),
      userId: vscode.env.machineId,
      file: doc.fileName,
      metadata: { languageId: doc.languageId, lineCount: doc.lineCount },
    });
  });

  // Flush events periodically
  setInterval(() => {
    if (events.length > 0) {
      const batch = events.splice(0);
      sendToAnalytics(batch);
    }
  }, 60000); // Flush every minute

  context.subscriptions.push(cascadeListener);
}

async function sendToAnalytics(batch: UsageEvent[]) {
  const endpoint = vscode.workspace
    .getConfiguration("windsurf-analytics")
    .get<string>("endpoint");
  if (!endpoint) return;

  await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events: batch }),
  }).catch(() => {}); // Silently fail — analytics should never block work
}
```

### Step 4: Measure Productivity Impact

```yaml
# Weekly team productivity report template
productivity_report:
  period: "Week of YYYY-MM-DD"
  team_size: 10
  active_windsurf_users: 8

  ai_metrics:
    total_cascade_tasks: 150
    cascade_success_rate: "78%"
    completion_acceptance_rate: "32%"
    credits_consumed: 1200

  productivity_proxies:
    commits_per_developer: 12       # vs baseline 8 pre-Windsurf
    pr_turnaround_hours: 6          # vs baseline 12 pre-Windsurf
    code_review_comments: 45        # quality indicator

  estimated_time_saved:
    per_developer_per_week: "3 hours"
    total_team_per_week: "24 hours"
    monthly_value: "$7,200"         # 24hrs * 4wks * $75/hr

  roi_calculation:
    monthly_windsurf_cost: "$300"   # 10 seats * $30
    monthly_value_generated: "$7,200"
    roi: "2,300%"
```

### Step 5: Dashboard Visualization

Track these metrics over time in your preferred dashboard tool:

```markdown
## Recommended Dashboard Panels

1. Daily Active Users vs Total Seats (line chart)
   - Shows adoption trend
   - Alert when utilization drops below 70%

2. Completion Acceptance Rate (line chart, 7-day rolling avg)
   - Higher = better .windsurfrules quality
   - Drop = rules need updating or team needs training

3. Cascade Success Rate (bar chart, weekly)
   - Tracks agentic task effectiveness
   - Low rate = prompts too vague or workspace too large

4. Credits per Developer (bar chart, monthly)
   - Identifies power users vs underutilizers
   - Guides seat tier decisions

5. Top Workflows Used (table)
   - Shows which automated workflows team uses most
   - Identifies candidates for new workflows
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Low acceptance rate | AI suggestions don't match project style | Update .windsurfrules with project conventions |
| Cascade flow failures | Insufficient tool permissions or context | Check workspace config, .codeiumignore |
| Seat utilization low | Team not adopted | Training session, share productivity data |
| Analytics data missing | Not on Teams/Enterprise plan | Upgrade for admin analytics |
| Custom extension conflicts | Extension interferes with Cascade | Ensure extension doesn't register completions |

## Examples

### Quick Adoption Check
```
Admin Dashboard > Analytics > Overview
Look for: active users, acceptance rate, credit usage
```

### Monthly Seat Optimization
```yaml
steps:
  1. Export member usage from Admin Dashboard
  2. Sort by credits consumed (ascending)
  3. Bottom 20%: offer training or downgrade to Free
  4. Top 10%: interview for best practices to share
  5. Reallocate freed seats to new team members
```

## Resources
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)
- [Windsurf Enterprise](https://windsurf.com/enterprise)

## Next Steps
For incident response procedures, see `windsurf-incident-runbook`.

---
name: windsurf-usage-analytics
description: |
  Analyze team AI usage patterns and productivity metrics. Activate when users mention
  "usage analytics", "ai metrics", "productivity tracking", "usage reports",
  or "roi analysis". Handles analytics and reporting configuration.
allowed-tools: Read,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Usage Analytics

Analyze team AI usage patterns for productivity insights and ROI measurement.

## Directory Structure

```
organization-config/
    .windsurf-enterprise/
        analytics/
            config/
                tracking-config.json         # Analytics configuration
                    # Tracked metrics
                    # Sampling rates
                    # Privacy filters

                dashboard-config.json        # Dashboard settings
                    # Widget definitions
                    # Refresh intervals
                    # Access controls

            metrics/
                productivity/
                    code-velocity.json       # Code output metrics
                        # Lines written/modified
                        # Commits per day
                        # PR cycle time

                    ai-acceptance.json       # AI acceptance rates
                        # Completion acceptance
                        # Suggestion quality
                        # Time saved

                    time-savings.json        # Time efficiency
                        # Task completion time
                        # Debugging duration
                        # Code review time

                adoption/
                    feature-usage.json       # Feature adoption
                        # Cascade usage frequency
                        # Flow utilization
                        # Extension adoption

                    user-engagement.json     # User engagement
                        # Daily active users
                        # Session duration
                        # Feature discovery

            reports/
                templates/
                    executive-summary.json       # Executive dashboard
                    team-performance.json        # Team metrics
                    roi-calculation.json         # ROI analysis

                scheduled/
                    weekly-report.json           # Weekly summary
                    monthly-analytics.json       # Monthly trends
                    quarterly-review.json        # Quarterly analysis
```

## Analytics Features

### Productivity Metrics
- Code velocity measurements
- AI suggestion acceptance rates
- Time savings calculations
- Quality improvements

### Adoption Tracking
- Feature utilization
- User engagement
- Learning progress
- Best practice adoption

## Configuration Steps

1. **Enable Analytics**
   - Configure tracking settings
   - Set privacy filters
   - Define metrics

2. **Build Dashboards**
   - Create visualization widgets
   - Set refresh schedules
   - Configure access

3. **Generate Reports**
   - Schedule regular reports
   - Define ROI calculations
   - Set up alerts

## Success Criteria

- Accurate AI acceptance rate metrics
- Clear time savings data
- ROI data supports investment decisions

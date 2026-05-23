# Directory Structure

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

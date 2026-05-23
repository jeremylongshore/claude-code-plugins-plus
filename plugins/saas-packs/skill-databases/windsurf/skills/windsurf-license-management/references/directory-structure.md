# Directory Structure

## Directory Structure

```
organization-config/
    .windsurf-enterprise/
        licensing/
            config/
                license-config.json          # License configuration
                    # Subscription tier
                    # Seat count
                    # Billing cycle

                allocation-rules.json        # Seat allocation rules
                    # Priority criteria
                    # Auto-assignment rules
                    # Reclamation policies

            inventory/
                active-licenses.json         # Current allocations
                    # Assigned users
                    # Assignment dates
                    # Last activity

                available-seats.json         # Unassigned seats
                    # Available count
                    # Reserved seats
                    # Pending assignments

                historical/
                    YYYY-MM.json             # Monthly snapshots
                        # Usage trends
                        # Peak utilization
                        # Turnover data

            policies/
                usage-policy.json            # Usage requirements
                    # Minimum activity thresholds
                    # Grace periods
                    # Reclamation triggers

                provisioning-policy.json     # Provisioning rules
                    # Request workflow
                    # Approval requirements
                    # Onboarding timeline

            reports/
                utilization-report.json      # Usage efficiency
                    # Active vs allocated
                    # Cost per active user
                    # Optimization recommendations

                cost-analysis.json           # Cost breakdown
                    # Per-seat costs
                    # Feature utilization
                    # Comparison with alternatives
```

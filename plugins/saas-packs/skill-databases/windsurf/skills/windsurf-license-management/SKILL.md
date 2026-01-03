---
name: windsurf-license-management
description: |
  Manage Windsurf licenses and seat allocation. Activate when users mention
  "license management", "seat allocation", "billing optimization", "user licenses",
  or "subscription management". Handles license administration.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf License Management

Manage Windsurf licenses and optimize seat allocation for cost efficiency.

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

## License Features

### Seat Management
- Automated provisioning
- Usage-based reclamation
- Department allocation
- Cost center tracking

### Cost Optimization
- Utilization reporting
- Right-sizing recommendations
- Tier optimization
- Budget forecasting

## Configuration Steps

1. **Inventory Current Licenses**
   - Document allocations
   - Identify inactive users
   - Map to cost centers

2. **Set Allocation Policies**
   - Define eligibility criteria
   - Configure auto-provisioning
   - Set reclamation rules

3. **Optimize and Monitor**
   - Review utilization reports
   - Reclaim unused seats
   - Right-size subscription

## Success Criteria

- Optimized utilization (no unused seats)
- Accurate billing alignment
- 20% reduction in software costs

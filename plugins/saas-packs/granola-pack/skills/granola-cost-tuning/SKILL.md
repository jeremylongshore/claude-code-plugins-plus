---
name: granola-cost-tuning
description: |
  Optimize Granola costs and select the right pricing plan.
  Use when evaluating plans, reducing costs,
  or maximizing value from Granola subscription.
  Trigger with phrases like "granola cost", "granola pricing",
  "granola plan", "save money granola", "granola subscription".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Cost Tuning

## Overview
Optimize Granola costs by selecting the right plan and maximizing usage efficiency.

## Plan Comparison

### Current Pricing (as of 2025)
| Plan | Price | Best For |
|------|-------|----------|
| Free | $0/month | Trying Granola, < 10 meetings/month |
| Pro | $10/month | Individual professionals |
| Business | $25/user/month | Teams with admin needs |
| Enterprise | Custom | Large organizations |

### Feature Comparison
| Feature | Free | Pro | Business |
|---------|------|-----|----------|
| Meetings/month | 10 | Unlimited | Unlimited |
| Duration limit | 60 min | 4 hours | 8 hours |
| Storage | 5 GB | 50 GB | 200 GB |
| Integrations | 2 | All | All + SSO |
| Templates | Basic | Custom | Team library |
| Support | Community | Email | Priority |

## Cost-Benefit Analysis

### ROI Calculator
```markdown
## Calculate Your ROI

Time Saved per Meeting:
- Manual note-taking: 15-30 min/meeting
- With Granola: 0-5 min/meeting
- Time saved: ~20 min/meeting

Monthly Calculation:
Meetings per month: [20]
Time saved: 20 * 20 min = 400 min = 6.7 hours  # HTTP 400 Bad Request
Hourly rate: [$50]
Value of time saved: 6.7 * $50 = $333  # 333 = configured value

Cost of Granola Pro: $10/month
ROI: ($333 - $10) / $10 = 3,230%  # 230 = configured value

Break-even: 0.6 meetings/month
```

### Team ROI
```markdown
## Team Calculation

Team Size: 10 people
Avg meetings/person: 20/month
Time saved/meeting: 20 min
Total time saved: 10 * 20 * 20 = 4,000 min = 66.7 hours

Blended hourly rate: $75
Value: 66.7 * $75 = $5,000/month

Business plan cost: 10 * $25 = $250/month  # 250 = configured value
ROI: ($5,000 - $250) / $250 = 1,900%  # 900: timeout: 15 minutes
```

## Optimization Strategies

### Strategy 1: Right-Size Your Plan
```markdown
## Plan Selection Matrix

< 10 meetings/month:
→ Stay on Free

10-30 meetings/month (individual):
→ Pro ($10/month)

Team of 2-10:
→ Business ($25/user)
→ Consider: 2 Pro accounts if no admin needs

Team of 10+:
→ Business or Enterprise
→ Contact sales for volume discount
```

### Strategy 2: Optimize Meeting Recording
```markdown
## Selective Recording

Record:
✓ Client meetings
✓ Sprint planning
✓ Design reviews
✓ Important 1:1s

Skip Recording:
✗ Quick syncs (< 5 min)
✗ Social calls
✗ Redundant status updates
✗ Meetings with existing notes
```

### Strategy 3: Storage Management
```markdown
## Reduce Storage Costs

Monthly Tasks:
1. Export old notes to external storage
2. Delete meetings > 6 months old
3. Remove draft/test recordings
4. Archive completed project notes

Storage Budget:
- Keep last 3 months in Granola
- Export to Notion/Google Drive for archive
- Delete after successful export
```

### Strategy 4: Integration Efficiency
```markdown
## Minimize Zapier Costs

Free Tier (100 tasks/month):
- Use for critical automations only
- Batch notifications (digest vs real-time)

Optimize Zaps:
- Combine related actions
- Use filters early in Zap
- Avoid unnecessary steps
```

## Annual vs Monthly Billing

### Savings Calculation
```
Monthly Billing:
Pro: $10/month × 12 = $120/year
Business: $25/user × 12 = $300/user/year  # 300: timeout: 5 minutes

Annual Billing (if offered, typically 15-20% discount):
Pro: ~$96/year (save $24)
Business: ~$255/user/year (save $45)  # 255 = configured value

Team of 10:
Monthly: $3,000/year
Annual: $2,550/year  # 550 = configured value
Savings: $450/year  # 450 = configured value
```

## Usage Monitoring

### Track Your Usage
```markdown
## Monthly Usage Review

Check in Settings > Account:
- [ ] Meetings recorded this month
- [ ] Storage used
- [ ] Integration usage
- [ ] Team member activity (Business)

Questions to Ask:
1. Are we using all our seats?
2. Is storage adequate?
3. Are all integrations needed?
4. Could we downgrade any users?
```

### Identify Waste
```markdown
## Cost Waste Indicators

Red Flags:
- Unused seats (no activity > 30 days)
- Storage near limit but old notes not archived
- Premium features not being used
- Duplicate accounts

Actions:
- Reassign inactive seats
- Export and delete old data
- Downgrade unused accounts
- Consolidate teams
```

## Negotiation Tips

### Enterprise Negotiation
```markdown
## Getting Better Pricing

Leverage Points:
1. Commit to annual billing
2. Volume discount for 50+ seats
3. Multi-year agreements
4. Bundle with other products
5. Reference competitor pricing

Typical Discounts:
- 10-15%: Annual commitment
- 15-25%: 50+ seats
- 20-30%: Multi-year + volume
```

### Startup Discounts
```markdown
## Startup Programs

Check for:
- Startup program discounts
- Non-profit pricing
- Educational discounts
- Partner program benefits
```

## Cost Comparison

### vs Competitors
| Service | Price | Notes |
|---------|-------|-------|
| Granola | $10-25/user | No bot, best privacy |
| Otter.ai | $8.33-20/user | Bot joins meeting |
| Fireflies | $10-19/user | Bot joins meeting |
| Fathom | Free-$24/user | Free tier generous |

### Hidden Costs to Consider
```markdown
## Total Cost of Ownership

Direct Costs:
+ Subscription: $X/month
+ Zapier integration: $Y/month

Indirect Costs:
+ Admin time: Z hours/month
+ Training time: One-time

Savings:
- Time saved: $A/month
- Improved follow-up: $B/month
- Better documentation: Hard to quantify
```

## Resources
- [Granola Pricing](https://granola.ai/pricing)
- [Plan Comparison](https://granola.ai/compare)
- [Enterprise Contact](https://granola.ai/enterprise)

## Next Steps
Proceed to `granola-reference-architecture` for enterprise deployment patterns.

## Prerequisites

- Access to the optimization environment or API
- Required CLI tools installed and authenticated
- Familiarity with optimization concepts and terminology

## Instructions

1. Assess the current state of the optimization configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with optimization |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola cost tuning for production environments with multiple constraints and team-specific requirements.
---
name: replit-cost-tuning
description: |
  Optimize Replit costs: deployment sizing, seat audit, egress control, and plan selection.
  Use when analyzing Replit billing, reducing deployment costs,
  or implementing usage monitoring and budget controls.
  Trigger with phrases like "replit cost", "replit billing",
  "reduce replit costs", "replit pricing", "replit expensive", "replit budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, cost-optimization, billing]

---
# Replit Cost Tuning

## Overview
Optimize Replit spending across deployment compute, seat licenses, egress, and storage. Covers right-sizing deployment resources, choosing between Autoscale and Reserved VM, eliminating idle Repls, and managing team seat costs.

## Prerequisites
- Replit account with billing access
- Understanding of current deployment architecture
- Access to usage metrics in Replit dashboard

## Replit Pricing Model

| Component | Pricing |
|-----------|---------|
| **Replit Core** | $25/month (includes $8 flexible credits) |
| **Replit Pro** | $40/month (team features + credits) |
| **Autoscale** | Pay per compute unit consumed |
| **Reserved VM** | From $0.20/day (~$6.20/month) |
| **Static Deploy** | Free (CDN-backed) |
| **Egress** | $0.10/GiB over monthly allowance |
| **PostgreSQL** | Included in plan allowance |
| **Object Storage** | Included in plan allowance |

## Instructions

### Step 1: Audit Deployment Costs
Review what you're spending and where:

```markdown
In Replit Dashboard > Billing:
1. View "Usage" tab for compute breakdown
2. Sort by cost to find expensive Repls
3. Check "Always On" Repls (legacy) — convert to Deployments

Key metrics to check:
- CPU hours consumed per Repl
- Memory-hours consumed per Repl
- Egress data transfer per Repl
- Number of cold starts (Autoscale)
```

### Step 2: Right-Size Deployment Resources
```yaml
# Match resources to actual workload

micro:  # Simple bot, webhook receiver
  type: autoscale
  cost: "Pay per request (free when idle)"
  best_for: "< 1000 requests/day, tolerates cold starts"

small:  # Basic API or web app
  type: reserved_vm
  cpu: 0.25 vCPU
  memory: 512 MB
  cost: "~$6/month"
  best_for: "Low traffic, always-on required"

medium:  # Production web app
  type: reserved_vm
  cpu: 0.5 vCPU
  memory: 1 GB
  cost: "~$12/month"
  best_for: "Standard traffic, good response times"

large:  # Compute-heavy or high-traffic
  type: reserved_vm
  cpu: 2 vCPU
  memory: 4 GB
  cost: "~$40/month"
  best_for: "High traffic, background processing"

# Rule of thumb: if peak CPU < 30% and peak memory < 50%, downsize
```

### Step 3: Choose Autoscale vs Reserved VM
```markdown
Use AUTOSCALE when:
- Traffic is unpredictable or bursty
- App can tolerate 5-15s cold starts
- Many hours of zero traffic per day
- Low daily request count (< 5000)
- Cost: $0 when idle, proportional to traffic

Use RESERVED VM when:
- Traffic is consistent throughout the day
- App needs instant response times
- Running cron jobs, webhooks, or WebSocket
- Cost: fixed monthly, predictable
- Cheaper than Autoscale when utilization > 60%

Use STATIC when:
- Frontend-only app (HTML/CSS/JS)
- No server-side processing needed
- Cost: FREE (CDN-backed, auto-cached)
```

### Step 4: Reduce Egress Costs
Egress (outbound data) costs $0.10/GiB over your plan allowance:

```typescript
// Compress API responses
import compression from 'compression';
app.use(compression());  // gzip responses — reduces egress 60-80%

// Paginate large responses
app.get('/api/items', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);
  const { rows } = await pool.query('SELECT * FROM items LIMIT $1', [limit]);
  res.json(rows);
});

// Serve static assets from CDN, not Replit
// Use Cloudflare, Vercel, or other CDN for images/videos/large files
// Only serve API responses from Replit deployment
```

### Step 5: Team Seat Optimization
```markdown
Seat audit checklist:
1. Export member list: Team Settings > Members
2. Identify inactive members (no activity in 30+ days)
3. Remove or downgrade inactive members
4. Consider "Viewer" role for stakeholders who only need read access

Cost calculation:
- 15 seats at $25/month = $375/month
- Remove 4 inactive = $100/month savings = $1,200/year

Quarterly seat review:
- [ ] Export activity report
- [ ] Remove members with 0 activity in 30 days
- [ ] Downgrade read-only members to viewer
- [ ] Document seat allocation decisions
```

### Step 6: Eliminate Idle Repls
```markdown
In Replit Dashboard:
1. View all Repls by last edited date
2. Archive Repls not edited in 90+ days
3. Delete old test/experiment Repls
4. Convert "Always On" Repls to Deployments
   (Always On is legacy and more expensive)

Deployments to review:
- Is this deployed and unused? → Undeploy
- Is this Autoscale with zero traffic? → No cost (good)
- Is this Reserved VM with zero traffic? → Undeploy or switch to Autoscale
```

### Step 7: Optimize PostgreSQL Usage
```markdown
PostgreSQL costs:
- Included in plan credits
- Separate dev and prod databases (charged separately)
- Storage grows with data

Optimization:
- Delete old development databases
- Vacuum and clean up unused tables
- Archive old data to Object Storage
- Use KV Database for simple key-value (included, no extra cost)
```

## Cost Monitoring Dashboard
```typescript
// Track resource usage in your app
app.get('/admin/costs', requireAuth, (req, res) => {
  const mem = process.memoryUsage();
  res.json({
    deployment: {
      type: process.env.REPLIT_DEPLOYMENT_TYPE || 'unknown',
      uptime: process.uptime(),
      memoryMB: Math.round(mem.rss / 1024 / 1024),
    },
    database: {
      poolSize: pool.totalCount,
      activeConnections: pool.idleCount,
    },
    repl: {
      slug: process.env.REPL_SLUG,
      owner: process.env.REPL_OWNER,
    },
  });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected high bill | Reserved VM running unused | Undeploy or switch to Autoscale |
| Egress overage | Serving large files from Repl | Move to CDN |
| Seat costs growing | No quarterly audit | Schedule regular seat reviews |
| Cold start complaints | Using Autoscale | Switch to Reserved VM for latency-sensitive apps |

## Resources
- [Replit Pricing](https://replit.com/pricing)
- [Usage-Based Billing](https://docs.replit.com/billing/about-usage-based-billing)
- [Deployment Types](https://docs.replit.com/hosting/deployments)

## Next Steps
For architecture planning, see `replit-reference-architecture`.

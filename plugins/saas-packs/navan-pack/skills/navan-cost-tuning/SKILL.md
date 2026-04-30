---
name: navan-cost-tuning
description: 'Use when optimizing travel spend with Navan''s policy engine, analyzing
  booking patterns for savings, and configuring the Navan Rewards program.

  Trigger with "navan cost tuning" or "navan travel savings" or "navan spend optimization".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Cost Tuning

## Overview

Navan's platform includes a built-in policy engine, negotiated rate management, unused ticket tracking, and the Navan Rewards program — but these features require deliberate configuration to deliver savings. This skill covers the full cost optimization lifecycle: setting up travel policies with hard and soft caps, analyzing booking data via the REST API to find savings opportunities, enforcing negotiated corporate rates, recovering value from unused tickets, and incentivizing employees to choose cheaper options through Navan Rewards. No SDK exists — all analytics use direct REST API calls against `https://api.navan.com/v1`.

## Prerequisites

- **Navan Admin** account with policy management permissions
- **OAuth 2.0 credentials** from Admin > API Settings (client_id, client_secret)
- **Historical booking data** — at least 3 months for meaningful analysis
- **Navan plan** — Business (free for up to 300 employees), Expense ($15/user/month after 5 free), or Enterprise (custom)
- Pricing details: https://navan.com/pricing

## Instructions

### Step 1 — Analyze Current Spend via API

Pull booking data to identify where money is being lost:

```bash
# Authenticate
ACCESS_TOKEN=$(curl -sf -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${NAVAN_CLIENT_ID}&client_secret=${NAVAN_CLIENT_SECRET}" \
  | jq -r '.access_token')

# Fetch last 90 days of bookings for analysis (page + size pagination)
curl -s "https://api.navan.com/v1/bookings?createdFrom=2026-01-01&page=0&size=50" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -o bookings.json

# Analyze: average booking lead time (days before travel)
# Response structure: records in .data array
jq '[.data[] | ((.departure_date | fromdate) - (.created_at | fromdate)) / 86400] | add / length' \
  bookings.json
# Target: 14+ days average lead time for maximum savings
```

```typescript
// Identify top savings opportunities by category
interface BookingAnalysis {
  total_spend: number;
  avg_lead_time_days: number;
  out_of_policy_pct: number;
  unused_tickets: number;
  top_routes: { route: string; spend: number; trips: number }[];
}

async function analyzeSpend(token: string): Promise<BookingAnalysis> {
  const response = await fetch(
    'https://api.navan.com/v1/bookings?page=0&size=50',
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const { data: bookings } = await response.json();

  const routeMap = new Map<string, { spend: number; trips: number }>();
  let totalSpend = 0;
  let outOfPolicy = 0;

  for (const b of bookings) {
    totalSpend += b.total_amount;
    if (b.out_of_policy) outOfPolicy++;

    const route = `${b.origin}-${b.destination}`;
    const existing = routeMap.get(route) ?? { spend: 0, trips: 0 };
    routeMap.set(route, {
      spend: existing.spend + b.total_amount,
      trips: existing.trips + 1,
    });
  }

  return {
    total_spend: totalSpend,
    avg_lead_time_days: calculateAvgLeadTime(bookings),
    out_of_policy_pct: (outOfPolicy / bookings.length) * 100,
    unused_tickets: await countUnusedTickets(token),
    top_routes: [...routeMap.entries()]
      .map(([route, data]) => ({ route, ...data }))
      .sort((a, b) => b.spend - a.spend)
      .slice(0, 10),
  };
}
```

### Step 2 — Configure the Policy Engine

Set up travel policies in Navan Admin > Policies with these recommended tiers:

| Policy Rule | Configuration | Savings Impact |
|------------|---------------|----------------|
| **Flight cap** | Soft cap at lowest logical fare + 20% | 10-15% on airfare |
| **Hotel cap** | Per-city nightly rate (e.g., NYC $250, Austin $180) | 15-25% on lodging |
| **Advance booking** | Flag bookings made < 7 days before travel | 20-30% on last-minute trips |
| **Cabin class** | Economy for flights < 6 hours, Business for 6+ | Varies by route mix |
| **Approval workflow** | Manager approval for out-of-policy bookings | Reduces out-of-policy by 40-60% |

### Step 3 — Enforce Negotiated Corporate Rates

```bash
# Check if negotiated rates are being utilized
curl -s "https://api.navan.com/v1/bookings?page=0&size=50" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq '{
    total_bookings: (.data | length),
    bookings_with_negotiated: [.data[] | select(.negotiated_savings != null)] | length,
    total_savings: [.data[].negotiated_savings // 0] | add
  }'
```

Upload negotiated rates in Navan Admin > Rates. Navan automatically surfaces these as preferred options during booking.

### Step 4 — Track Unused Tickets

```bash
# Identify unused or partially used tickets
curl -s "https://api.navan.com/v1/bookings?page=0&size=50" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq '{
    cancelled: [.data[] | select(.status == "cancelled")] | length,
    total_credit_value: [.data[] | select(.status == "cancelled") | .credit_amount // 0] | add
  }'
# Credits expiring within 30 days should be rebooked or refunded
```

### Step 5 — Enable Navan Rewards

Navan Rewards gives employees personal travel credit when they book below policy limits. Configure in Admin > Rewards:

- **Activation**: Enable Navan Rewards for all employees or specific departments
- **Credit calculation**: Employee earns a percentage of the difference between policy cap and actual booking
- **Redemption**: Credits apply to personal travel booked through Navan
- **Reporting**: Track rewards earned and redeemed via the admin dashboard

This creates a direct incentive for employees to choose cheaper options — Navan reports typical 5-15% additional savings from Rewards adoption.

## Output

A cost optimization implementation delivering:
- **Spend analysis report** identifying top savings opportunities by department and route
- **Configured policy engine** with hard/soft caps and approval workflows
- **Negotiated rate enforcement** surfacing corporate rates during booking
- **Unused ticket recovery** preventing credit expiration
- **Navan Rewards activation** incentivizing employee cost-conscious booking behavior

## Error Handling

| HTTP Code | Meaning | Resolution |
|-----------|---------|------------|
| `200` | Success | Process response data |
| `401` | Token expired | Refresh OAuth token and retry |
| `403` | Plan does not include this feature | Check Navan plan tier at https://navan.com/pricing |
| `404` | Endpoint not available for your region | Contact Navan support for regional API availability |
| `422` | Invalid policy configuration | Verify cap amounts and currency codes |
| `429` | Rate limited | Reduce analytics query frequency |

## Examples

**Monthly savings dashboard query:**

```bash
# Generate a monthly savings summary
curl -s "https://api.navan.com/v1/reports/savings-summary?period=2026-02" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq '{
    period: .period,
    total_spend: .total_spend,
    policy_savings: .in_policy_savings,
    negotiated_rate_savings: .negotiated_savings,
    rewards_credits_earned: .rewards_earned,
    unused_tickets_recovered: .credits_rebooked,
    total_savings: (.in_policy_savings + .negotiated_savings + .credits_rebooked)
  }'
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Policy setup guides and API docs
- [Navan Pricing](https://navan.com/pricing) — Plan comparison (Business free up to 300 employees)
- [Navan Integrations](https://navan.com/integrations) — ERP connectors for automated expense reporting

## Next Steps

- Add `navan-reference-architecture` for end-to-end integration design
- Add `navan-performance-tuning` to optimize the API calls powering cost analytics
- See `navan-observability` to monitor policy compliance rates over time

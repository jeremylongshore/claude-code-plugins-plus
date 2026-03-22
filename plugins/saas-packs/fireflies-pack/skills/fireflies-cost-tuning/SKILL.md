---
name: fireflies-cost-tuning
description: |
  Optimize Fireflies.ai subscription costs through seat auditing, selective recording, and plan sizing.
  Use when analyzing Fireflies.ai billing, reducing per-seat costs,
  or implementing usage monitoring and right-sizing.
  Trigger with phrases like "fireflies cost", "fireflies billing",
  "reduce fireflies costs", "fireflies pricing", "fireflies expensive", "fireflies budget".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api, cost-optimization]

---
# Fireflies.ai Cost Tuning

## Overview
Optimize Fireflies.ai subscription costs. Fireflies charges per-seat per month. The main levers: remove unused seats, configure selective recording, manage storage, and right-size your plan tier.

## Pricing Reference

| Plan | Price | API Access | Key Features |
|------|-------|-----------|--------------|
| Free | $0 | 50 req/day | 800 min storage, limited transcription |
| Pro | ~$18/seat/month | 50 req/day | 8,000 min/seat, AI summaries |
| Business | ~$29/seat/month | 60 req/min | Unlimited transcription, CRM, analytics |
| Enterprise | Custom | 60 req/min | SSO, Super Admin webhooks, custom |

## Instructions

### Step 1: Audit Seat Utilization via API
```bash
set -euo pipefail
# List all workspace users with their transcript counts
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { name email user_id num_transcripts minutes_consumed } }"}' \
  | jq '.data.users | sort_by(.num_transcripts) | .[] | {name, email, transcripts: .num_transcripts, minutes: .minutes_consumed}'
```

```typescript
// Automated utilization report
async function seatUtilizationReport() {
  const data = await firefliesQuery(`{
    users {
      name email user_id
      num_transcripts minutes_consumed
      recent_meeting
    }
  }`);

  const users = data.users;
  const inactive = users.filter((u: any) => u.num_transcripts < 2);
  const active = users.filter((u: any) => u.num_transcripts >= 2);

  console.log(`Total seats: ${users.length}`);
  console.log(`Active (2+ transcripts): ${active.length}`);
  console.log(`Inactive (<2 transcripts): ${inactive.length}`);
  console.log(`Potential savings: ${inactive.length} seats * $29/mo = $${inactive.length * 29}/mo`);

  if (inactive.length > 0) {
    console.log("\nInactive seats to review:");
    for (const u of inactive) {
      console.log(`  ${u.email}: ${u.num_transcripts} transcripts, last meeting: ${u.recent_meeting || "never"}`);
    }
  }

  return { total: users.length, active: active.length, inactive, savings: inactive.length * 29 };
}
```

### Step 2: Configure Selective Recording
Instead of recording every meeting, configure auto-join rules in Fireflies Settings > Auto-Join:

```yaml
# Recommended recording policy
record_always:
  - External meetings (client/prospect calls)
  - Meetings with 3+ participants
  - Meetings with keywords: "review", "planning", "standup", "demo"

skip_recording:
  - 1-on-1 informal chats
  - Social events
  - Meetings shorter than 5 minutes
  - Recurring "lunch" or "coffee" meetings
```

Estimated savings: Teams recording every meeting typically waste 30-50% of transcription credits on low-value meetings.

### Step 3: Manage Storage to Avoid Forced Upgrades
```typescript
// Check storage and clean up old transcripts
async function storageAudit() {
  const data = await firefliesQuery(`{
    transcripts(limit: 100) {
      id title date duration
    }
    user { minutes_consumed }
  }`);

  const now = Date.now();
  const transcripts = data.transcripts;

  // Find transcripts older than 90 days
  const old = transcripts.filter((t: any) => {
    const age = (now - new Date(t.date).getTime()) / 86400000;
    return age > 90;
  });

  console.log(`Total transcripts: ${transcripts.length}`);
  console.log(`Older than 90 days: ${old.length}`);
  console.log(`Minutes consumed: ${data.user.minutes_consumed}`);

  return { total: transcripts.length, old, minutesUsed: data.user.minutes_consumed };
}

// Delete old transcripts to free storage
async function deleteOldTranscripts(ids: string[]) {
  for (const id of ids) {
    await firefliesQuery(`
      mutation($id: String!) {
        deleteTranscript(transcript_id: $id)
      }
    `, { id });
    console.log(`Deleted: ${id}`);
    // deleteTranscript is rate limited: 10/min
    await new Promise(r => setTimeout(r, 6500));
  }
}
```

### Step 4: Right-Size Your Plan
```yaml
# Decision matrix
choose_pro:
  when:
    - Team averages <15 meetings/week per person
    - No CRM integration needed
    - Basic AI summaries sufficient
  saves: $11/seat/month vs Business

choose_business:
  when:
    - Sales team recording every call
    - CRM integration required (Salesforce, HubSpot)
    - Meeting analytics dashboards needed
    - 20+ meetings/week per person

choose_enterprise:
  when:
    - SSO/SAML required
    - Super Admin webhooks needed (org-wide meeting data)
    - Custom data retention policies
    - Dedicated support
```

### Step 5: API Cost Optimization
```typescript
// Free/Pro plans: 50 requests/day. Make every request count.
// Strategy: Fetch meeting list once, cache aggressively

async function efficientDailySync() {
  // One request: get all recent transcripts
  const data = await firefliesQuery(`{
    transcripts(limit: 50) {
      id title date duration
      summary { overview action_items }
    }
  }`);

  // Process locally -- no additional API calls
  const today = new Date().toDateString();
  const todaysMeetings = data.transcripts.filter(
    (t: any) => new Date(t.date).toDateString() === today
  );

  console.log(`Today's meetings: ${todaysMeetings.length}`);
  console.log(`API requests used: 1 of 50 daily budget`);

  return todaysMeetings;
}
```

## Cost Savings Summary

| Lever | Typical Savings |
|-------|----------------|
| Remove inactive seats | $29/seat/month |
| Selective recording | 30-50% fewer transcriptions |
| Pro vs Business downgrade | $11/seat/month |
| Storage cleanup | Avoid forced tier upgrade |
| API request caching | Stay within Free/Pro limits |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't remove seat | User has admin role | Reassign admin first |
| Storage limit warning | Too many transcripts | Delete old transcripts |
| API daily limit hit | Free/Pro 50 req/day | Cache results, batch efficiently |
| Unexpected invoice increase | Auto-provisioned members | Disable auto-provisioning |

## Output
- Seat utilization report with inactive members identified
- Selective recording policy configured
- Storage audit with cleanup recommendations
- Plan right-sizing recommendation

## Resources
- [Fireflies Pricing](https://fireflies.ai/pricing)
- [Fireflies API Docs](https://docs.fireflies.ai/)

## Next Steps
For architecture design, see `fireflies-reference-architecture`.

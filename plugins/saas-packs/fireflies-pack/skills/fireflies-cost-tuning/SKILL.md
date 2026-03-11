---
name: fireflies-cost-tuning
description: |
  Optimize Fireflies.ai costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Fireflies.ai billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "fireflies cost", "fireflies billing",
  "reduce fireflies costs", "fireflies pricing", "fireflies expensive", "fireflies budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies Cost Tuning

## Overview
Optimize Fireflies.ai per-seat subscription costs by right-sizing seat count, configuring selective recording, and managing transcript storage. Fireflies charges per seat per month (Pro: ~$18/seat/month, Business: ~$29/seat/month, Enterprise: custom).

## Prerequisites
- Fireflies workspace admin access
- Visibility into per-member usage
- Understanding of meeting recording policies

## Instructions

### Step 1: Audit Seat Utilization
```bash
set -euo pipefail
# Identify members who aren't using their seats
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ teamMembers { email role transcripts_count last_active } }"}' | \
  jq '.data.teamMembers | sort_by(.transcripts_count) | .[] | {email, transcripts: .transcripts_count, last_active}'
# Members with 0-1 transcripts per month are wasting seats
```

### Step 2: Remove Inactive Seats
```yaml
# Seat optimization strategy
current_state:
  total_seats: 20
  active_users: 12      # >2 recordings/month
  low_usage: 5          # 1-2 recordings/month
  inactive: 3           # 0 recordings/month

optimized_state:
  total_seats: 14       # Keep active + low_usage, remove inactive
  savings: 6 seats * $29/month = $174/month
```
Remove inactive members or downgrade them to Viewer roles (which don't consume seats on most plans).

### Step 3: Configure Selective Auto-Recording
```yaml
# Instead of recording every meeting (wastes transcription credits):
auto_record_policy:
  record:
    - internal meetings with 3+ participants
    - external meetings (client/prospect calls)
    - meetings with "standup" or "review" in title
  skip:
    - 1-on-1 informal chats
    - social/team-building events
    - meetings shorter than 5 minutes
```
Configure in Fireflies Settings > Auto-Join > Selective Recording.

### Step 4: Manage Storage to Avoid Tier Upgrades
```bash
set -euo pipefail
# Check storage usage
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ workspace { storage_used_gb storage_limit_gb } }"}' | \
  jq '.data.workspace | {used_gb, limit_gb, usage_pct: (.storage_used_gb / .storage_limit_gb * 100)}'

# Delete old transcripts that are no longer needed
# Set auto-deletion policy: delete transcripts older than 365 days
```

### Step 5: Compare Plan Tiers
```yaml
# Decision matrix for plan selection
pro_18_per_seat:
  storage: 8000 min transcription/seat  # 8000: API server port
  best_for: Teams that record <15 meetings/week per person
  features: [transcription, search, basic AI summaries]

business_29_per_seat:
  storage: Unlimited transcription
  best_for: Sales teams recording every call
  features: [transcription, search, AI summaries, CRM integration, analytics]
  tip: Only worth it if team averages 20+ meetings/week per person

# If your team averages <10 meetings/week per person, Pro tier saves $11/seat/month
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Seat cost growing | Auto-provisioning new members | Disable auto-provisioning, manually add seats |
| Storage limit approaching | Recording every meeting | Enable selective recording, delete old transcripts |
| Paying for unused features | On Business tier but only using transcription | Downgrade to Pro tier |
| Invoice higher than expected | New members auto-added | Set member invitation to admin-only |

## Examples

**Basic usage**: Apply fireflies cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize fireflies cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack
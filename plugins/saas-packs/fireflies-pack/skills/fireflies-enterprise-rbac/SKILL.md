---
name: fireflies-enterprise-rbac
description: |
  Configure Fireflies.ai workspace roles, channels, privacy controls, and meeting sharing.
  Use when managing team access, setting up channels,
  or configuring transcript visibility and sharing rules.
  Trigger with phrases like "fireflies roles", "fireflies permissions",
  "fireflies channels", "fireflies privacy", "fireflies sharing", "fireflies RBAC".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, rbac]

---
# Fireflies.ai Enterprise RBAC

## Overview
Manage workspace access control in Fireflies.ai using roles, channels, privacy levels, and the sharing API. Fireflies uses per-seat licensing with workspace roles and channel-based transcript organization.

## Prerequisites
- Fireflies Business or Enterprise plan
- Workspace admin privileges (or API key from admin account)
- Understanding of your team structure

## Workspace Roles

| Role | Capabilities |
|------|-------------|
| Admin | Full workspace control, manage members, access all transcripts |
| Member | Record meetings, view own + shared transcripts |
| Guest | View shared transcripts only (may not consume a seat) |

## Instructions

### Step 1: List Workspace Members
```bash
set -euo pipefail
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { name email user_id is_admin num_transcripts } }"}' \
  | jq '.data.users[] | {name, email, admin: .is_admin, transcripts: .num_transcripts}'
```

### Step 2: Set User Roles via API
```typescript
// Promote or change a user's role
async function setUserRole(userId: string, role: string) {
  return firefliesQuery(`
    mutation($userId: String!, $role: String!) {
      setUserRole(user_id: $userId, role: $role)
    }
  `, { userId, role });
}

// Usage: setUserRole("user-id-123", "admin")
```

### Step 3: Organize Transcripts with Channels
```typescript
// List all channels
const channels = await firefliesQuery(`{
  channels {
    id
    title
    is_private
    created_by
    members { user_id email name }
  }
}`);

// Move transcripts to a channel
async function assignToChannel(transcriptIds: string[], channelId: string) {
  return firefliesQuery(`
    mutation($ids: [String!]!, $channelId: String!) {
      updateMeetingChannel(transcript_ids: $ids, channel_id: $channelId)
    }
  `, { ids: transcriptIds, channelId });
}
```

Organize by department:
- **Sales** channel: All client/prospect calls
- **Engineering** channel: Sprint reviews, architecture discussions
- **Leadership** channel (private): Board meetings, strategy sessions

### Step 4: Control Transcript Privacy
```typescript
// Privacy levels (most restrictive to least)
type PrivacyLevel =
  | "owner"                    // Only meeting organizer
  | "participants"             // Only meeting participants
  | "teammatesandparticipants" // Workspace members + participants
  | "teammates"               // All workspace members
  | "link";                    // Anyone with the link

async function setTranscriptPrivacy(transcriptId: string, privacy: PrivacyLevel) {
  return firefliesQuery(`
    mutation($id: String!, $privacy: String!) {
      updateMeetingPrivacy(transcript_id: $id, privacy_level: $privacy)
    }
  `, { id: transcriptId, privacy });
}

// Default new transcripts to participants-only
await setTranscriptPrivacy("transcript-id", "participants");
```

### Step 5: Share Meetings with External Users
```typescript
// Share a transcript with up to 100 email recipients
async function shareMeeting(transcriptId: string, emails: string[], expiryDays = 30) {
  return firefliesQuery(`
    mutation($id: String!, $emails: [String!]!, $expiry: Int) {
      shareMeeting(transcript_id: $id, emails: $emails, expiry_days: $expiry)
    }
  `, { id: transcriptId, emails, expiry: expiryDays });
}

// Revoke access
async function revokeAccess(transcriptId: string, email: string) {
  return firefliesQuery(`
    mutation($id: String!, $email: String!) {
      revokeSharedMeetingAccess(transcript_id: $id, email: $email)
    }
  `, { id: transcriptId, email });
}

// Rate limit: 10 share operations per hour, up to 50 emails each
```

### Step 6: User Groups for Bulk Access
```typescript
// List user groups
const groups = await firefliesQuery(`
  query($mine: Boolean) {
    user_groups(mine: $mine) {
      id name
      members { user_id email name }
      created_at
    }
  }
`, { mine: false });

// Use groups to manage channel membership in bulk
```

### Step 7: Audit Transcript Access
```typescript
async function auditTranscriptAccess(transcriptId: string) {
  const { transcript } = await firefliesQuery(`
    query($id: String!) {
      transcript(id: $id) {
        id title
        privacy
        organizer_email
        shared_with
        channels { id }
        workspace_users
      }
    }
  `, { id: transcriptId });

  console.log(`Transcript: ${transcript.title}`);
  console.log(`Privacy: ${transcript.privacy}`);
  console.log(`Owner: ${transcript.organizer_email}`);
  console.log(`Shared with: ${transcript.shared_with?.join(", ") || "none"}`);
  console.log(`Channels: ${transcript.channels?.map((c: any) => c.id).join(", ") || "none"}`);
  console.log(`Workspace users: ${transcript.workspace_users?.join(", ") || "none"}`);

  return transcript;
}
```

## Recommended Enterprise Configuration
```yaml
privacy_defaults:
  internal_meetings: "teammatesandparticipants"
  external_meetings: "participants"
  leadership_meetings: "owner"

channel_structure:
  - name: "Sales"
    private: false
    auto_assign: "meetings with external participants"
  - name: "Engineering"
    private: false
    auto_assign: "meetings with 'sprint' or 'standup' in title"
  - name: "Leadership"
    private: true
    members: "C-suite + VPs only"

sharing_policy:
  max_expiry_days: 30
  require_approval: true  # For external sharing
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cannot set role | Not workspace admin | Use admin API key |
| Channel not found | Invalid channel ID | List channels first |
| Share rate limited | 10/hour limit | Queue share operations |
| Privacy update fails | Transcript not owned | Only organizer can change privacy |

## Output
- Workspace members audited with roles and utilization
- Channels created for department-based transcript organization
- Privacy levels configured per meeting type
- Sharing controls with expiry and revocation

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [User Query](https://docs.fireflies.ai/graphql-api/query/user)

## Next Steps
For migration strategies, see `fireflies-migration-deep-dive`.

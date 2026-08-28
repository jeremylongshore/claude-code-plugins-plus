# Meta Compliance Reference

## Why This Is Legal

Instagram's Private Replies API (`POST /{ig-user-id}/messages` with `recipient.comment_id`) was built specifically for the comment-to-DM use case. Meta documents it at:
https://developers.facebook.com/docs/instagram-platform/private-replies/

ManyChat, Inro, CreatorFlow, LinkDM, and ReplyRush all use this exact same API as Meta-verified partners.

## Required Permissions

The Upload-Post app requests these OAuth scopes during Instagram connection:
- `instagram_business_manage_messages` — send and read DMs
- `instagram_business_manage_comments` — read comments
- `instagram_business_basic` — account info

These are the standard permissions for this use case.

## Rate Limits

| Limit | Value | Enforced By |
|-------|-------|-------------|
| DMs per hour | 200 | Meta API (returns 429) |
| Private replies per comment | 1 | Meta API (rejects duplicate) |
| Comment age for private reply | 7 days | Meta API (rejects expired) |
| Follow-up DM window | 24 hours after last user reply | Meta API |
| Comment fetch frequency | Once per 10 minutes per post | Upload-Post API |

## What Counts as User-Initiated Contact

Meta requires the user to initiate contact before you can DM them. For Private Replies, the comment itself counts as initiation. This is why:

- Replying to a comment with a DM = **allowed** (user commented first)
- Following up after they reply to your DM = **allowed** (within 24h window)
- DMing someone who never interacted = **prohibited** (cold outreach)

## Enforcement Progression

If rules are violated, Meta escalates:
1. Shadow ban (reduced reach)
2. Action blocks (temporary inability to DM/comment)
3. Account suspension
4. Permanent ban

The Private Replies flow, when done correctly, does not trigger any of these.

## Best Practices to Stay Safe

- Never send identical messages to large groups — personalize each DM
- Stop immediately when you hit a 429 (rate limit) — don't retry aggressively
- Keep message content relevant to what the user asked for in their comment
- Don't automate follow-ups beyond the 24-hour window
- Monitor spam report rates — if users are marking your DMs as spam, reduce volume or improve message quality

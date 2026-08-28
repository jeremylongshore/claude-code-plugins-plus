---
name: comment-funnel
description: "Build Instagram comment-to-DM funnels via Upload-Post API. Use when the user wants to automatically send DMs to people who comment specific keywords on their Instagram posts, set up lead capture funnels from comments, automate Instagram DM outreach to commenters, or monitor post comments and reply privately. Also triggers when the user mentions comment automation, DM funnels, lead magnets from comments, or keyword-triggered DMs."
version: "1.0.0"
metadata:
  author: "Upload-Post"
  last-updated: "2026-03-28"
allowed-tools: Read, Write, Bash(curl:*), Bash(jq:*)
author: Upload-Post <support@upload-post.com>
license: MIT
compatibility: "Designed for Claude Code; requires curl on PATH and an UPLOAD_POST_API_KEY with an Instagram account connected. Instagram only — the comment-to-DM API is not available on other platforms."
tags:
- instagram
- dm-automation
- lead-generation
- funnels
- social-media
---

# Comment-to-DM Funnel — Upload-Post API

Turn Instagram comments into conversations. This skill lets you monitor comments on a post, detect trigger keywords (semantically, not just exact match), and send personalized private DMs to each commenter automatically.

This is the same mechanism ManyChat, Inro, and every major DM automation tool uses — the official Instagram Private Replies API. Fully compliant with Meta's terms.

## Overview

Monitor an Instagram post for comments, detect trigger keywords semantically (not just exact
string matches), and send each commenter a personalized private DM. This is the official
Instagram Private Replies API — the same mechanism ManyChat and Inro use — so it stays inside
Meta's terms.

The funnel has three moving parts: a **monitor** watching one post, a **trigger** matching
comment text, and a **DM template** that gets personalized per commenter. Replies to the DM
keep the conversation open for 24 hours under Meta's messaging window.

## Prerequisites

- An Upload-Post account with an **Instagram Business or Creator account** connected
  (personal Instagram accounts cannot receive the Private Replies permission from Meta)
- `UPLOAD_POST_API_KEY` in the environment
- The profile name that owns the connected Instagram account
- The post ID or URL of the Instagram post to monitor

## Documentation

- Full API docs: https://docs.upload-post.com
- LLM-friendly reference: https://docs.upload-post.com/llm.txt

## Authentication

All requests require an API key:

```
Authorization: Apikey YOUR_API_KEY
```

Base URL: `https://api.upload-post.com/api`

The `user` parameter is the **profile name** (not username) from the Upload-Post dashboard.

## How the Funnel Works

The typical flow a creator wants:

1. They post a Reel saying "Comment GUIDE to get my free PDF"
2. People comment "GUIDE", "quiero la guía", "send me the guide", etc.
3. Each commenter receives a personalized DM with the link
4. If someone replies to the DM, the conversation continues
5. The creator gets a summary of how many DMs were sent

Your job as an agent is to orchestrate this. There are **two modes**:

- **One-shot**: Scan comments right now and send DMs to everyone who already commented. Good for processing a backlog.
- **Persistent monitor**: Start a background monitor that checks for new comments every X minutes and auto-sends DMs 24/7. This is the "set it and forget it" mode — like ManyChat.

Choose based on what the user asks. If they say "set up a funnel" or "activate monitoring", use persistent. If they say "check comments" or "send DMs to whoever commented", use one-shot.

## Endpoints

### Persistent Monitor Endpoints

These start a background process on Upload-Post's servers that monitors comments and sends DMs automatically. No need for the agent to stay running.

#### Start Monitor

```bash
curl -X POST "https://api.upload-post.com/api/uploadposts/autodms/start" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "post_url": "https://www.instagram.com/p/ABC123/",
    "reply_message": "Hey! Here is your guide: https://example.com/guide",
    "profile_username": "PROFILE",
    "monitoring_interval": 15,
    "trigger_keywords": ["guide", "link"]
  }'
```

Parameters:
- `post_url` (required): The Instagram post URL to monitor
- `reply_message` (required): The DM message to send to matching commenters
- `profile_username` (required): Upload-Post profile name with Instagram connected
- `monitoring_interval` (optional): Minutes between checks. Default: 15. Minimum: 15 (values below 15 are auto-clamped)
- `trigger_keywords` (optional): Array of keywords to filter comments. Only comments containing at least one keyword receive a DM. Case-insensitive and accent-insensitive ("guía" matches "guia"). If omitted, ALL commenters receive a DM.

Returns a `monitor_id` you'll need for managing the monitor.

**Limits:**
- Maximum 2 new monitors per profile per day
- No duplicate monitors on the same post URL
- Monitors auto-stop after **15 days**
- Daily DM limits apply per plan (free: 10 DMs/day, paid: 500 DMs/day). When the limit is reached, the monitor pauses and resumes the next day.

**Important**: This monitor sends a fixed `reply_message` — it does not do semantic filtering or personalization. If `trigger_keywords` is set, it only replies to comments containing those words (case and accent insensitive). If omitted, it replies to ALL commenters. For smart semantic filtering, use one-shot mode instead.

#### Check Monitor Status

```bash
curl "https://api.upload-post.com/api/uploadposts/autodms/status" \
  -H "Authorization: Apikey YOUR_KEY"
```

Returns all active monitors with their status: `running`, `paused`, or `stopped`.

#### Get Monitor Logs

```bash
curl "https://api.upload-post.com/api/uploadposts/autodms/logs?monitor_id=MONITOR_ID" \
  -H "Authorization: Apikey YOUR_KEY"
```

Returns activity logs: when the monitor started, how many DMs sent, any errors.

#### Pause / Resume / Stop / Delete Monitor

```bash
# Pause (keeps config, stops checking)
curl -X POST "https://api.upload-post.com/api/uploadposts/autodms/pause" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id": "MONITOR_ID"}'

# Resume a paused monitor
curl -X POST "https://api.upload-post.com/api/uploadposts/autodms/resume" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id": "MONITOR_ID"}'

# Stop (deactivates)
curl -X POST "https://api.upload-post.com/api/uploadposts/autodms/stop" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id": "MONITOR_ID"}'

# Delete (permanent)
curl -X POST "https://api.upload-post.com/api/uploadposts/autodms/delete" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id": "MONITOR_ID"}'
```

### One-Shot Endpoints

These are for scanning comments on-demand and sending DMs with AI-powered semantic matching and personalization.

### 1. Get Recent Posts

Find the post to monitor.

```bash
curl "https://api.upload-post.com/api/uploadposts/media?platform=instagram&user=PROFILE" \
  -H "Authorization: Apikey YOUR_KEY"
```

Returns an array of recent posts with `id`, `caption`, `permalink`, `timestamp`, and `media_type`. Use the `id` field as `post_id` in subsequent calls.

### 2. Read Comments

```bash
curl "https://api.upload-post.com/api/uploadposts/comments?platform=instagram&user=PROFILE&post_id=POST_ID" \
  -H "Authorization: Apikey YOUR_KEY"
```

You can also use `post_url` instead of `post_id`:

```bash
curl "https://api.upload-post.com/api/uploadposts/comments?platform=instagram&user=PROFILE&post_url=https://www.instagram.com/p/ABC123/" \
  -H "Authorization: Apikey YOUR_KEY"
```

**Rate limit**: Once per 10 minutes per post. Plan your polling accordingly — don't call this in a tight loop.

Each comment includes `id`, `text`, `username`, and `timestamp`.

### 3. Send Private Reply (the DM)

This is the core action. It sends a DM to the person who wrote the comment, using Meta's official Private Replies API.

```bash
curl -X POST "https://api.upload-post.com/api/uploadposts/comments/reply" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "user": "PROFILE",
    "comment_id": "COMMENT_ID",
    "message": "Hey! Here is your guide: https://example.com/guide"
  }'
```

**Constraints you must respect:**
- One reply per comment — if you already replied to a comment, the API will reject a second attempt
- The comment must be less than 7 days old
- The post must belong to the authenticated account
- Daily DM limits apply (varies by plan)

### 4. List DM Conversations

Check for replies to your DMs.

```bash
curl "https://api.upload-post.com/api/uploadposts/dms/conversations?platform=instagram&user=PROFILE" \
  -H "Authorization: Apikey YOUR_KEY"
```

Returns conversation threads with `participant_id`, `messages`, and metadata.

### 5. Send Follow-Up DM

Continue a conversation with someone who replied.

```bash
curl -X POST "https://api.upload-post.com/api/uploadposts/dms/send" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "user": "PROFILE",
    "recipient_id": "USER_ID",
    "message": "Glad you liked it! Let me know if you have questions."
  }'
```

**24-hour window**: You can only send follow-up DMs within 24 hours of the user's last reply. After that, the window closes and you cannot message them until they message you again.

## Instructions

1. **Confirm the account is eligible** — Instagram Business or Creator, connected in the
   dashboard. Private Replies is unavailable on personal accounts.
2. **Pick the post** to monitor and get its ID.
3. **Define the trigger** — the keyword or intent to match. Matching is semantic, so
   "GUIDE", "quiero la guía" and "send me the guide" all hit the same trigger.
4. **Write the DM template**, including any personalization tokens.
5. **Create the monitor** through the AutoDM endpoint and confirm it is active.
6. **Check the logs** periodically to see who was messaged and what failed.

Read the compliance rules below before going live — Meta enforces a 24-hour messaging window
and one private reply per comment.

## Building the Funnel — Step by Step

When the user asks you to set up a comment funnel, follow these steps:

### Step 1: Gather Requirements

Ask the user (if not already provided):
- API key? (needed for all requests)
- Profile name? (the `user` parameter — this is the Upload-Post profile name, not their Instagram username. If they don't know it, call `GET /uploadposts/me` to validate the key. If they have no profiles or no Instagram connected, direct them to https://app.upload-post.com/manage-users to create a profile and connect their Instagram Business account first)
- Which post? (URL or they can say "my latest post")
- What keywords trigger the DM? (e.g., "GUIDE", "INFO", "LINK")
- What message to send? (the DM content)
- Persistent or one-shot? (do they want 24/7 monitoring or a one-time scan?)

### Step 2: Find the Post

Call `GET /uploadposts/media` to list recent posts. Match by URL, caption content, or just pick the latest. Confirm with the user which post to monitor.

### Path A: Persistent Monitor (24/7)

Use this when the user wants continuous monitoring ("set up a funnel", "activate it", "keep it running").

1. Call `POST /uploadposts/autodms/start` with the post URL, reply message, profile, and interval
2. Save the returned `monitor_id` and tell the user
3. Confirm it's running with `GET /uploadposts/autodms/status`
4. Tell the user how to check results: "Ask me anytime to check the funnel status or logs"

The backend handles everything from here — checking comments, sending DMs, avoiding duplicates, respecting rate limits. The agent doesn't need to stay running.

To check on it later:
- `GET /uploadposts/autodms/status` → is it running?
- `GET /uploadposts/autodms/logs?monitor_id=X` → how many DMs sent?

To manage it:
- `POST /uploadposts/autodms/pause` → pause without losing config
- `POST /uploadposts/autodms/resume` → resume after pause
- `POST /uploadposts/autodms/stop` → deactivate
- `POST /uploadposts/autodms/delete` → remove permanently

**Trade-off**: The persistent monitor sends the same fixed message — no personalization per commenter. Use `trigger_keywords` to filter so only relevant comments get a DM. Without keywords, it replies to every new comment.

### Path B: One-Shot with AI (Smart Filtering)

Use this when the user wants intelligent processing ("check my comments", "DM the ones who asked for the guide", or when the post gets mixed comments — some requesting, some just engaging).

#### Scan Comments

Call `GET /uploadposts/comments` with the post ID.

For each comment, decide if it matches the trigger. Use **semantic matching**, not just exact string comparison:

| Comment | Trigger: "GUIDE" | Match? |
|---------|-------------------|--------|
| "GUIDE" | Exact match | Yes |
| "guide please" | Contains keyword | Yes |
| "I want the guide!" | Semantic intent | Yes |
| "can you send me the guide?" | Semantic intent | Yes |
| "guía" | Translation | Yes |
| "great post!" | No intent | No |
| "nice guide on the topic" | Ambiguous — talking about the content, not requesting | No |

The key question: **is this person requesting the thing the creator offered?** Use judgment, not regex.

#### Send DMs

For each matching comment that hasn't been replied to yet:

1. Personalize the message. Don't send identical copy-paste to everyone. Use their name or reference their comment:
   - Generic: "Here's your guide: [link]"
   - Better: "Hey @maria! You asked about the guide — here it is: [link]. Let me know if you have any questions!"

2. Call `POST /uploadposts/comments/reply` with the personalized message.

3. Track which comment IDs you've already replied to (keep a list in your working memory) to avoid duplicate attempts.

#### Report Results

After processing, tell the user:
- Total comments scanned
- How many matched the trigger
- How many DMs sent successfully
- Any errors (already replied, window expired, rate limit)

#### Monitor Replies (Optional)

If the user wants follow-up handling:
1. Call `GET /uploadposts/dms/conversations` to check for new replies
2. For each reply, generate a contextual response using the funnel's purpose
3. Call `POST /uploadposts/dms/send` to respond
4. Only send within the 24-hour messaging window

### Combining Both Modes

A smart approach: start a persistent monitor for the baseline (everyone gets the DM), then periodically run one-shot scans to check DM conversations and do personalized follow-ups. Tell the user this option if it fits their use case.

## Compliance Rules

These are Meta's rules. Breaking them gets the account restricted, not just rate-limited.

**What's allowed (you're doing this):**
- Sending a private reply to someone who commented on YOUR post — this is the exact use case Meta built the Private Replies API for
- Using the official Instagram Graph API through Upload-Post
- Personalizing messages per commenter

**Hard limits:**
- 200 DMs per hour per Instagram account (Meta enforces this — the API returns 429)
- 1 private reply per comment (API rejects duplicates)
- 7-day window on comments (older comments can't receive private replies)
- 24-hour window on follow-up DMs (resets each time the user replies)

**What would get the account banned (never do this):**
- Sending DMs to people who never interacted with the account
- Ignoring rate limit errors and retrying aggressively
- Sending identical spam messages to hundreds of people

## Error Handling

| Code | Meaning | What to Do |
|------|---------|------------|
| 200 | DM sent | Track as success |
| 400 | Bad request | Check parameters — likely missing comment_id or message |
| 401 | Invalid API key | Ask user to check their key |
| 404 | Comment not found | Comment may have been deleted |
| 429 | Rate limit / DM limit reached | Stop sending. Tell the user how many were sent and that the limit was hit |
| 500 | Server error | Retry once, then report to user |

When you hit a 429, **stop the entire batch**. Don't keep trying. Report to the user: "Sent X DMs successfully. Hit the rate limit — the remaining Y commenters will need to be processed later."

## Examples

### Example Conversation

**User**: "In my latest Reel I told people to comment CURSO to get info about my course. Set up the funnel to DM them the enrollment link https://mycourse.com/enroll"

**Agent workflow**:
1. `GET /uploadposts/media?platform=instagram&user=profilename` → find latest Reel
2. `GET /uploadposts/comments?platform=instagram&user=profilename&post_id=12345`
3. Analyze each comment for intent to receive the course info
4. For each match: `POST /uploadposts/comments/reply` with personalized DM
5. Report: "Found 47 comments. 31 matched the trigger. Sent 31 DMs. 2 had already been replied to. Here's the breakdown..."

## Output

Creating a monitor returns its id and state:

```json
{ "success": true, "monitor_id": "adm_4f19", "status": "active", "post_id": "17998..." }
```

The DM log reports one row per commenter handled — who was messaged, when, and why a send
failed when it did:

```json
{
  "sent": [
    { "username": "someone", "comment": "GUIDE", "status": "sent", "sent_at": "2026-08-29T10:02:11Z" }
  ],
  "skipped": [
    { "username": "otheruser", "reason": "outside_24h_window" }
  ]
}
```

Report both lists back — a funnel that silently skips people looks like it is working when
it is not.

## Platform Limitation

This skill works on **Instagram only**. The comments and DM endpoints in the Upload-Post API currently support Instagram exclusively. This is because Meta's Private Replies API is Instagram-specific, and other platforms (TikTok, LinkedIn, X, etc.) don't offer equivalent APIs for comment-to-DM automation.

This is not a limitation of Upload-Post — it's how the social platform APIs work. Instagram is where 90%+ of comment-to-DM funnels run commercially (ManyChat, Inro, etc. are all Instagram-first for this reason).

## Tips for Better Funnels

- **Short DMs convert better**: 1-3 sentences max. Link + brief context. Nobody reads paragraphs in DMs.
- **Personalize**: Reference their comment or use their display name. "Hey! Here's what you asked for" beats "Dear valued follower."
- **One clear CTA**: Don't overload the DM. One link, one action.
- **Timing matters**: The sooner after commenting they get the DM, the higher the open rate. Process comments as soon as the rate limit allows.
- **Track what works**: Compare DM response rates across different message styles. Iterate.

## Resources

- API documentation: https://docs.upload-post.com
- LLM-friendly dump: https://docs.upload-post.com/llm.txt
- Compliance notes: [references/compliance.md](references/compliance.md)
- Meta Private Replies policy: https://developers.facebook.com/docs/messenger-platform/instagram/features/private-replies
- Dashboard: https://upload-post.com

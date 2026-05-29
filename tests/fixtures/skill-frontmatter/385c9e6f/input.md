---
name: slack
description: |
  Send Slack messages to channels or @mention team members. Use when user says "slack", "send slack", "message pablo", "ping team", "notify channel", "/slack".
allowed-tools: 'Read,Write,Edit,Bash(curl:*),Bash(cat:*),Bash(echo:*),AskUserQuestion'
model: opus
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Slack Command Center

Send messages to Slack channels and DM team members.

## CRITICAL RULES

1. **NEVER auto-send messages** - Show preview first
2. **Human must confirm send** - Use AskUserQuestion before ANY send action
3. **Show full preview first** - Display channel/user, message before asking to send

## Default Settings

- **Default Channel:** #operation-hired
- **Owner:** Jeremy (@jeremy)

## Team Members

| Name   | Slack ID    | DM Webhook | Shortcut |
| ------ | ----------- | ---------- | -------- |
| Jeremy | U099CBRE7CL | -          | @jeremy  |
| Pablo  | U0A0UVAH97B | ✓          | @pablo   |

## Webhooks

| Target           | Env Variable                      | Type           |
| ---------------- | --------------------------------- | -------------- |
| #operation-hired | SLACK_OPERATION_HIRED_WEBHOOK_URL | Channel        |
| Pablo DM         | SLACK_WEBHOOK_PABLO_DM            | Direct Message |

## Prerequisites

Environment variables (in `~/.env`):

```
SLACK_OPERATION_HIRED_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_WEBHOOK_PABLO_DM=https://hooks.slack.com/services/...
SLACK_USER_JEREMY=U099CBRE7CL
SLACK_USER_PABLO=U0A0UVAH97B
```

## Instructions

### Step 1: Parse Intent or Present Menu

If user provides context (e.g., "slack pablo about testing"), extract:

- **Recipient**: Channel or user
- **Message**: Content to send

If unclear, use AskUserQuestion:

```
SLACK COMMAND CENTER
═══════════════════════════════════════════════════════════════════

What would you like to do?

1. 📢 Post to Channel - Send to #operation-hired
2. 👤 DM Team Member - @mention someone
3. 📋 Quick Update - Send status update to channel
```

### Step 2: Identify Recipient

**Channel shortcuts:**

- `#operation-hired` → Uses SLACK_OPERATION_HIRED_WEBHOOK_URL

**User shortcuts:**

- `@pablo` or `pablo` → `<@U0A0UVAH97B>`
- `@jeremy` or `jeremy` → `<@U099CBRE7CL>`

### Step 3: Compose Message

Ask for message content if not provided. Support:

- Plain text
- @mentions: `<@USER_ID>`
- Links: Will auto-unfurl
- Emoji: Use standard `:emoji:` syntax

### Step 4: Preview Message (REQUIRED)

**ALWAYS show preview before send:**

```
SLACK PREVIEW
═══════════════════════════════════════════════════════════════════
Channel: #operation-hired
Mentions: @pablo

Message:
───────────────────────────────────────────────────────────────────
@pablo Ready for testing - resume format updated.
https://resume-gen-intent-dev.web.app/intake
───────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════
```

### Step 5: Human Confirmation (REQUIRED)

Use AskUserQuestion with options:

- **Send** - Send the message now
- **Edit** - Go back and modify
- **Cancel** - Abort, don't send

**Only proceed to send if user explicitly selects "Send".**

### Step 6: Send Message

Write JSON payload to temp file and send via curl:

```bash
cat > /tmp/slack.json << 'EOF'
{"text":"<@U0A0UVAH97B> Your message here"}
EOF
curl -s -X POST -H 'Content-type: application/json' -d @/tmp/slack.json "$SLACK_OPERATION_HIRED_WEBHOOK_URL"
```

**Response:**

- `ok` = Success
- `invalid_payload` = JSON formatting issue
- `no_service` = Webhook not active

### Step 7: Confirm Success

```
✓ Message sent to #operation-hired
  Mentioned: @pablo
```

---

## Quick Reference

### Send to channel with @mention

```bash
cat > /tmp/slack.json << 'EOF'
{"text":"<@U0A0UVAH97B> Your message here"}
EOF
curl -s -X POST -H 'Content-type: application/json' -d @/tmp/slack.json https://hooks.slack.com/services/REDACTED/REDACTED/REDACTED
```

### User ID Reference

- Pablo: `<@U0A0UVAH97B>`
- Jeremy: `<@U099CBRE7CL>`

---

## Adding New Webhooks

To add DM webhooks for direct messages:

1. Go to https://api.slack.com/apps → your app
2. **Incoming Webhooks** → Add New Webhook
3. Select user (for DM) or channel
4. Copy webhook URL
5. Add to `~/.env`:
   ```
   SLACK_WEBHOOK_PABLO_DM=https://hooks.slack.com/services/...
   ```

---

## Adding New Team Members

1. Get their Slack ID:
   - Go to https://app.slack.com/manage/members
   - Or click profile → ⋮ → Copy member ID
2. Add to `~/.env`:
   ```
   SLACK_USER_NAME=UXXXXXXXXXX
   ```
3. Update Team Members table in this skill

---

## Examples

### Example 1: Quick ping

```
User: slack pablo testing is ready
Assistant: [Shows preview with @pablo mention]
User: Send
Assistant: [Sends message, confirms delivery]
```

### Example 2: Channel announcement

```
User: /slack
Assistant: [Shows menu]
User: Post to Channel
Assistant: What message?
User: Deployment complete, all systems go
Assistant: [Shows preview, sends after confirmation]
```

### Example 3: Status update

```
User: slack the team that PR is merged
Assistant: [Shows preview mentioning channel]
User: Send
Assistant: ✓ Message sent to #operation-hired
```

---

## Error Handling

| Error               | Cause            | Solution                          |
| ------------------- | ---------------- | --------------------------------- |
| `no_service`        | Webhook inactive | Recreate webhook in Slack admin   |
| `invalid_payload`   | JSON formatting  | Use temp file method with heredoc |
| `channel_not_found` | Wrong webhook    | Verify webhook URL                |

---

## Resources

- Slack Admin: https://app.slack.com/manage/members
- Slack Apps: https://api.slack.com/apps
- Webhook Docs: https://api.slack.com/messaging/webhooks

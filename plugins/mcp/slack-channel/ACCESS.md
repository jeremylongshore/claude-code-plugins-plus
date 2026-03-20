# Access Control Schema

The Slack channel uses `~/.claude/channels/slack/access.json` to control who can reach your Claude Code session.

## Schema

```json
{
  "dmPolicy": "pairing | allowlist | disabled",
  "allowFrom": ["U12345678"],
  "channels": {
    "C12345678": {
      "requireMention": true,
      "allowFrom": ["U12345678"]
    }
  },
  "pending": {
    "ABC123": {
      "senderId": "U87654321",
      "chatId": "D12345678",
      "createdAt": 1711000000000,
      "expiresAt": 1711003600000,
      "replies": 1
    }
  },
  "ackReaction": "eyes",
  "textChunkLimit": 4000,
  "chunkMode": "newline"
}
```

## Fields

### `dmPolicy`
Controls how DMs from unknown users are handled.

| Value | Behavior |
|-------|----------|
| `pairing` | Unknown senders get a 6-character code to approve via `/slack-channel:access pair` (default) |
| `allowlist` | Only users in `allowFrom` can DM; others are silently dropped |
| `disabled` | All DMs dropped |

### `allowFrom`
Array of Slack user IDs (e.g., `U12345678`) allowed to send DMs. Managed via `/slack-channel:access add/remove`.

### `channels`
Map of channel IDs to policies. Only channels listed here are monitored.

- `requireMention`: If true, only messages that @mention the bot are delivered
- `allowFrom`: If non-empty, only these user IDs are delivered from this channel

### `pending`
Active pairing codes. Auto-pruned on every gate check.

- Max 3 pending codes at once
- Each code expires after 1 hour
- Max 2 replies per code (initial + 1 reminder)

### `ackReaction`
Emoji name (without colons) to react with when a message is delivered. Set to `""` or omit to disable.

### `textChunkLimit`
Maximum characters per outbound message. Default: 4000 (Slack's limit).

### `chunkMode`
How to split long messages: `"newline"` (paragraph-aware, default) or `"length"` (fixed character count).

## Security

- File permissions: `0o600` (owner read/write only)
- Writes are atomic (write `.tmp`, then rename)
- Corrupt files are moved aside and replaced with defaults
- In static mode (`SLACK_ACCESS_MODE=static`), the file is read once at boot and never mutated

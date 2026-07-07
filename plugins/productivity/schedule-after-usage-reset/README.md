# schedule-after-usage-reset

A Claude Code skill that automatically finds your Claude usage reset time and schedules a deferred task to run right after the limit lifts.

## What it does

When you hit a Claude usage limit and want to queue work for after the reset, just say:

- "schedule this after my usage resets"
- "run this when my tokens refresh"
- "queue this task for after the limit lifts"
- "do this when usage resets"

The skill:
1. Fetches your actual reset time from the Anthropic usage API (no guessing)
2. Adds a 5-minute buffer so Claude is definitely available
3. Calls `/schedule` with the exact time and your task

## Installation

**Step 1 — Register the marketplace:**

```
/plugin marketplace add lemondepat/schedule-after-usage-reset
```

**Step 2 — Install the skill:**

```
/plugin install schedule-after-usage-reset@lemondepat
```

**Step 3 — Reload:**

```
/reload-plugins
```

### Manual install

Copy `skills/schedule-after-usage-reset/` into `~/.claude/skills/`.

## Requirements

- Claude Code with the `schedule` skill installed (used internally to schedule the task)
- macOS — relies on Keychain entry `Claude Code-credentials` (set automatically by Claude Code on login)

## Usage

Trigger it naturally in conversation:

```
schedule this after my usage resets: summarize the new PRs in my inbox
```

The skill picks up any phrasing around "usage resets", "tokens refresh", "limit lifts", etc. — no slash command needed.

## License

MIT

---
name: details
description: Toggle verbose mode on or off
argument-hint: on|off
allowed-tools: Read, Write
---

# /vibe-guide:details

Toggle whether to show additional technical details.

## Usage

```
/vibe-guide:details on
/vibe-guide:details off
```

## Examples

```
/vibe-guide:details on   # Show more technical info
/vibe-guide:details off  # Keep it simple
```

## Execution Steps

### Step 1: Check Session Exists

If `.vibe/session.json` doesn't exist:

```
No active vibe session.

To start one, run:
  /vibe-guide:vibe <your goal>
```

### Step 2: Parse Argument

- `on` - set `show_details` to true
- `off` - set `show_details` to false
- No argument - toggle current value

### Step 3: Update Session

Update `.vibe/session.json` with new `show_details` value.

### Step 4: Confirm Change

## Output

When turned on:

```
Details mode: ON

You'll now see slightly more technical information in status updates.
This can help if you want to understand what's happening under the hood.

To turn off, run: /vibe-guide:details off
```

When turned off:

```
Details mode: OFF

Updates will stay simple and non-technical.

To turn on, run: /vibe-guide:details on
```

## Effect

When `show_details` is true, the explainer may include:
- File names that changed (not full paths)
- Command names that ran (not full output)
- Slightly more specific descriptions

Still NO:
- Raw diffs
- Command output logs
- Stack traces
- Technical jargon

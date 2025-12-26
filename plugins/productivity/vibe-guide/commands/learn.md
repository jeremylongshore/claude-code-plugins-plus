---
name: learn
description: Toggle learning mode with educational micro-explanations
argument-hint: on|off
allowed-tools: Read, Write
---

# /vibe-guide:learn

Toggle learning mode for educational explanations.

## Usage

```
/vibe-guide:learn on
/vibe-guide:learn off
```

## Examples

```
/vibe-guide:learn on   # Enable mini-lessons after each step
/vibe-guide:learn off  # Progress-only updates
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

- `on` - set `learning_mode` to true
- `off` - set `learning_mode` to false
- No argument - toggle current value

### Step 3: Update Session

Update `.vibe/session.json` with new `learning_mode` value.

### Step 4: Confirm Change

## Output

When turned on:

```
Learning mode: ON

After each step, you'll get a brief explanation of one concept.
These are simple, jargon-free, and use everyday analogies.

Perfect for understanding what's happening as we go!

To turn off, run: /vibe-guide:learn off
```

When turned off:

```
Learning mode: OFF

Status updates will be progress-only, no educational content.

To turn on, run: /vibe-guide:learn on
```

## Effect

When `learning_mode` is true:
- The `vibe-explorer` agent runs after each step
- Provides 2-4 sentence explanation of ONE concept
- Uses simple analogies, no jargon
- Helps non-technical users learn as they watch

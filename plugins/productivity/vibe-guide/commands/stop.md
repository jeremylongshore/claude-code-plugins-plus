---
name: stop
description: Pause or resume the current session
allowed-tools: Read, Write
---

# /vibe-guide:stop

Toggle pause on the current session.

## Usage

```
/vibe-guide:stop
```

## Examples

```
/vibe-guide:stop
```

Pauses the session. Run again to resume.

## Execution Steps

### Step 1: Check Session Exists

If `.vibe/session.json` doesn't exist:

```
No active vibe session to pause.
```

### Step 2: Toggle Stop Flag

Read `.vibe/session.json`:

- If `stop` is false, set to true
- If `stop` is true, set to false

Write updated session.json.

### Step 3: Update Status

Update `.vibe/status.json`:

- If now paused: set `phase` to "paused", update `step_title` to "Session paused"
- If now resumed: restore previous phase (read from changelog context)

### Step 4: Run Explainer

Invoke `vibe-explainer` to confirm the pause/resume.

## Output

When paused:

```
1) Where we are
   Session is now paused.

2) What changed
   - Paused at step X

3) What I checked
   - Progress saved

4) What's next
   Run /vibe-guide:stop again to resume.

5) Do you need to do anything?
   No, take your time.
```

When resumed:

```
1) Where we are
   Session resumed at step X.

2) What changed
   - Unpaused session

3) What I checked
   - Previous state restored

4) What's next
   Run /vibe-guide:continue to keep going.

5) Do you need to do anything?
   No, ready when you are.
```

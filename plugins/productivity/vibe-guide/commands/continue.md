---
name: continue
description: Execute the next step in the current session
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /vibe-guide:continue

Run the next step in your vibe session.

## Usage

```
/vibe-guide:continue
```

## Examples

```
/vibe-guide:continue
```

Executes one step, then shows what happened.

## Execution Steps

### Step 1: Check Session Exists

If `.vibe/session.json` doesn't exist:

```
No active vibe session.

To start one, run:
  /vibe-guide:vibe <your goal>
```

### Step 2: Check for Stop Flag

If `session.stop` is true:

```
Session is paused.

To resume, first run:
  /vibe-guide:stop
(This toggles the pause off)
```

### Step 3: Check for Error

Read `.vibe/status.json`. If `error` field exists:

Invoke `vibe-explainer` to show the error checklist, then stop.

Do NOT run worker when there's an unresolved error.

### Step 4: Check if Done

If `status.phase` is "done":

```
This session is complete!

To start a new one, run:
  /vibe-guide:vibe <new goal>
```

### Step 5: Run Worker

Invoke `vibe-worker` agent to execute the next step.

### Step 6: Run Explainer

Invoke `vibe-explainer` agent to present results.

### Step 7: Run Explorer (Optional)

If `session.learning_mode` is true, invoke `vibe-explorer` agent.

## Output

The explainer's friendly summary of what just happened:

```
1) Where we are
   [Current step completed]

2) What changed
   - [Changes in plain language]

3) What I checked
   - [Verifications performed]

4) What's next
   [Next step to run]

5) Do you need to do anything?
   No, nothing needed right now.
```

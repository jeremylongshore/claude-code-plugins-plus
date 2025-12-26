---
name: status
description: Show current progress in plain language
allowed-tools: Read
---

# /vibe-guide:status

Check where we are in the current session without doing any more work.

## Usage

```
/vibe-guide:status
```

## Examples

```
/vibe-guide:status
```

Shows current progress, what changed, and what's next.

## Execution Steps

### Step 1: Check Session Exists

If `.vibe/session.json` doesn't exist:

```
No active vibe session.

To start one, run:
  /vibe-guide:vibe <your goal>
```

### Step 2: Read Status

Read `.vibe/status.json` to get current state.

### Step 3: Run Explainer

Invoke `vibe-explainer` agent to present the current status.

### Step 4: Run Explorer (Optional)

If `session.learning_mode` is true, invoke `vibe-explorer` agent.

## Output

The explainer presents current progress:

```
1) Where we are
   [Current phase and step]

2) What changed
   - [Recent changes in plain language]

3) What I checked
   - [Recent verifications]

4) What's next
   [Next planned step]

5) Do you need to do anything?
   [Yes with steps, or No]
```

## Error Handling

If `status.json` has an error field, explainer shows only:

```
Something went wrong, but it's fixable.

What happened: [Friendly error summary]

To fix this:
1. [First step to fix]
2. [Second step to fix]

After you've done that, run /vibe-guide:status to continue.
```

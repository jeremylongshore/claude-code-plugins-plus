---
name: status
description: Show current progress in plain language
allowed-tools: Read
---

# /vibe-guide:status

Check where we are in the current session.

## Usage

```
/vibe-guide:status
```

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

The explainer's friendly summary of current progress.

## Error Handling

If status.json has an error field, explainer will show only:
- Friendly error summary
- Numbered checklist to fix
- Instruction to run /vibe-guide:status after fixing

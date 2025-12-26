---
name: vibe
description: Start a new vibe session with a goal
---

# /vibe-guide:vibe

Start a new guided session with a goal. Progress shown in plain language.

## Usage

```
/vibe-guide:vibe <goal>
```

## Examples

```
/vibe-guide:vibe Build a WNBA stats table page
/vibe-guide:vibe Add dark mode toggle to settings
/vibe-guide:vibe Fix the login button not working
```

## Execution Steps

### Step 1: Create .vibe Directory

If `.vibe/` doesn't exist, create it:

```bash
mkdir -p .vibe
```

### Step 2: Add to .gitignore

If `.gitignore` exists in project root, append `.vibe/` if not already present:

```bash
if [ -f .gitignore ] && ! grep -q "^.vibe/$" .gitignore; then
  echo ".vibe/" >> .gitignore
fi
```

### Step 3: Initialize Session

Create `.vibe/session.json`:

```json
{
  "goal": "<user's goal>",
  "started_at": "<ISO-8601 timestamp>",
  "learning_mode": false,
  "show_details": false,
  "stop": false
}
```

### Step 4: Initialize Status

Create `.vibe/status.json`:

```json
{
  "phase": "planning",
  "step": 0,
  "step_title": "Understanding the goal",
  "what_changed": [],
  "what_i_checked": [],
  "next": "Analyze project structure",
  "need_from_user": null,
  "error": null,
  "updated_at": "<ISO-8601 timestamp>"
}
```

### Step 5: Initialize Changelog

Create `.vibe/changelog.md`:

```markdown
# Vibe Session Changelog

Goal: <user's goal>
Started: <human-readable date>

## Progress

```

### Step 6: Run Worker

Invoke `vibe-worker` agent to execute the first step.

### Step 7: Run Explainer

Invoke `vibe-explainer` agent to present results.

### Step 8: Run Explorer (Optional)

If `session.learning_mode` is true, invoke `vibe-explorer` agent.

## Output

The explainer's friendly summary of where we are and what happened.

---
name: vibe
description: Start a new vibe session with a goal
argument-hint: <goal>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /vibe-guide:vibe

Start a new guided session with a goal. Progress is shown in plain language, hiding all technical details like diffs and logs.

## Usage

```
/vibe-guide:vibe <goal>
```

Provide a clear description of what you want to build or fix.

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

If `.gitignore` exists in project root, append `.vibe/` if not already present.

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

The explainer presents a friendly summary:

```
1) Where we are
   Starting: [goal description]

2) What changed
   - Set up session tracking
   - Analyzed project structure

3) What I checked
   - Project files exist

4) What's next
   [First implementation step]

5) Do you need to do anything?
   No, nothing needed right now.
```

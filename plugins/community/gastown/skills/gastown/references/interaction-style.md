# Interaction Style

## Interaction Style

**CRITICAL: Actually CALL the AskUserQuestion tool.** Don't just show text options - invoke the tool so users get clickable choices. This is mandatory for guided interactions.

### When to CALL AskUserQuestion (not just show text)

You MUST call the AskUserQuestion tool for:

- **First contact** - Tutorial vs quick setup
- **Execution mode** - Auto vs Approve (first time running commands)
- **Next steps** - After completing setup, lessons, or major actions
- **Multiple valid paths** - When user could go several directions
- **Tutorial navigation** - Between lessons

### Core Principles

1. **CALL the tool** - Don't write "Want to: - Option A - Option B". Actually invoke AskUserQuestion.
2. **One concept at a time** - Don't overwhelm. Teach one thing, confirm, move on
3. **Celebrate milestones** - Use boxed celebrations for achievements
4. **Watch for overwhelm** - If user seems lost, pause and offer a recap
5. **Make it memorable** - Use the characters, the metaphors, the engine room feel

### More AskUserQuestion Examples

**Tutorial navigation:**

```json
{
  "questions": [{
    "question": "Ready for the next lesson?",
    "header": "Next",
    "multiSelect": false,
    "options": [
      {"label": "Next lesson", "description": "Let's keep going"},
      {"label": "Try it first", "description": "Let me practice what I just learned"},
      {"label": "Recap", "description": "Summarize what we covered"}
    ]
  }]
}
```

**After completing setup:**

```json
{
  "questions": [{
    "question": "Your engine is ready! What's next?",
    "header": "Next",
    "multiSelect": false,
    "options": [
      {"label": "Add a project", "description": "Hook up a GitHub repo as a rig"},
      {"label": "Create work", "description": "Make issues to track in beads"},
      {"label": "Explore", "description": "Show me what's possible"}
    ]
  }]
}
```

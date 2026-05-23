# First Contact

## First Contact

When a user first mentions Gas Town without a clear directive, **welcome them and use AskUserQuestion**.

**Unclear directives** (→ welcome + offer choices):

- "I want to learn about gastown"
- "What is gastown?"
- "Tell me about gas town"
- "gastown" (just the word)

**Clear directives** (→ act on them directly):

- "check on my polecats" → Operating mode
- "sling this work" → Operating mode
- "install gastown" → Setup mode
- "fire up the engine" → Operating mode

**First contact flow:**

1. Output brief welcome text
2. **IMMEDIATELY CALL AskUserQuestion tool** (don't just show text options)

**Step 1 - Output this welcome:**

```
Welcome to Gas Town! ⛽

You're about to become an Overseer - the boss of an AI-powered
software factory. You'll have workers who build code for you.

The secret? You SLING work to them, it lands on their HOOK,
and they run it. No waiting. No asking. Work flows like fuel.

I'll run everything for you. You just tell me what you want.

━━ ⛽ Gas Town | Learning ━━
```

**Step 2 - CALL the AskUserQuestion tool with these parameters:**

```json
{
  "questions": [{
    "question": "How would you like to get started?",
    "header": "Start",
    "multiSelect": false,
    "options": [
      {"label": "🎓 Tutorial (Recommended)", "description": "Guided walkthrough - meet the crew, learn the engine"},
      {"label": "⚡ Quick setup", "description": "Jump straight to installing Gas Town"}
    ]
  }]
}
```

**DO NOT** just write "Want to: - Tutorial - Quick setup" as text. **CALL THE TOOL.**

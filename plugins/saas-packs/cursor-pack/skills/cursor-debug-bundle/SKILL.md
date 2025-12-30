---
name: cursor-debug-bundle
description: |
  Debug AI suggestions and code generation in Cursor. Triggers on "debug cursor ai",
  "cursor suggestions wrong", "bad cursor completion", "cursor ai debug".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor AI Debug Bundle

## Understanding AI Behavior

### Why AI Gives Wrong Suggestions

```
Common causes:
1. Insufficient context
2. Ambiguous code/comments
3. Conflicting patterns in codebase
4. Outdated .cursorrules
5. Wrong model for task
6. Context window overflow
```

## Debugging Completions

### Completion Quality Checklist
```
[ ] Does the comment/docstring clearly describe intent?
[ ] Are type hints present and accurate?
[ ] Is the surrounding code consistent?
[ ] Is .cursorrules up to date?
[ ] Is the right model selected?
[ ] Has codebase been indexed recently?
```

### Improving Completion Quality

#### Add Context
```python
# Before (AI guesses):
def process(data):
    │

# After (AI understands):
def process(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform user data.
    - Remove null values
    - Normalize column names
    - Convert dates to ISO format
    """
    │
```

#### Use Explicit Comments
```javascript
// Before:
function handle(req) {
  │
}

// After:
// Handle POST /api/users - validate input, create user, return 201
function handleCreateUser(req: Request): Response {
  │
}
```

## Debugging Chat Issues

### Chat Not Understanding Context

```
Debug steps:
1. Check what's in context
   - Look at @-mentioned files
   - Check selected code

2. Be explicit
   Bad:  "Fix this"
   Good: "Fix the TypeError on line 45 of auth.py
          where user.email is accessed but user is None"

3. Provide examples
   "Make it work like how processOrders() handles
    null values in orders/processor.py"
```

### Chat Forgetting Context

```
Conversation context resets when:
- Starting new chat (Cmd+Shift+L)
- Switching models mid-conversation
- Context window fills up

Solutions:
- Keep related questions in same chat
- Re-state important context when needed
- Use @-mentions for persistent context
```

## Debugging Composer Issues

### Composer Not Finding Files

```
Symptoms: "I couldn't find that file"

Debug:
1. Check exact file path
2. Verify file is not in .cursorignore
3. Check indexing status
4. Use full relative path
```

### Composer Making Wrong Edits

```
Debug approach:
1. Review proposed changes before applying
2. Be more specific in instructions
3. Specify exact file and location
4. Use incremental changes vs. large refactors
```

## Context Debugging

### Check What AI Sees

```
In chat, ask:
"What files do you have context for?"
"Summarize what you understand about this codebase"
"What's in your current context?"
```

### Context Window Usage

```
Model context limits:
- GPT-4: ~8K tokens (32K extended)
- GPT-4 Turbo: ~128K tokens
- Claude: ~100K tokens

Check usage:
- Look for truncation warnings
- Shorter responses may indicate limit
```

## .cursorrules Debugging

### Verify Rules Are Applied

```bash
# Test rules are loaded
1. Open .cursorrules
2. Add test instruction:
   "Always start responses with 'RULES LOADED:'"
3. Test in chat
4. Remove test instruction
```

### Common Rule Issues

```yaml
# Problem: Rules too vague
styles: good

# Fix: Rules specific
code-style:
  - Use TypeScript strict mode
  - Prefer async/await over callbacks
  - Use early returns for guard clauses
  - Maximum function length: 30 lines
```

## Model Selection Debugging

### Choosing Right Model

```
Task Type → Best Model

Simple completions → GPT-3.5 Turbo (fast)
Complex logic → GPT-4 (accurate)
Explanations → Claude Sonnet (clear)
Large context → GPT-4 Turbo or Claude (128K+)
Cost-sensitive → GPT-3.5 (cheapest)
```

### Testing Model Differences

```
Same prompt, different models:
1. Ask question with GPT-4
2. Ask same question with Claude
3. Compare responses
4. Note which handles your use case better
```

## Logging and Diagnostics

### Enable Verbose Logging

```json
// settings.json
{
  "cursor.debug.verbose": true,
  "cursor.debug.logLevel": "debug"
}
```

### View AI Request/Response

```
Developer Tools (Help > Toggle Developer Tools):
- Network tab: See API calls
- Console tab: See errors/warnings
- Filter by "cursor" or "api"
```

### Export Debug Info

```bash
# Collect debug bundle
cursor --status > cursor-debug.txt
cursor --list-extensions >> cursor-debug.txt
cat ~/.cursor/logs/main.log >> cursor-debug.txt
```

## Quick Fixes Reference

| Issue | Quick Fix |
|-------|-----------|
| Wrong language | Check file extension |
| No completions | Restart Cursor |
| Slow responses | Switch to faster model |
| Irrelevant code | Add more context |
| Repeated mistakes | Update .cursorrules |
| Context overflow | Start new chat |
| Indexing issues | Re-index codebase |
| Auth problems | Sign out and back in |

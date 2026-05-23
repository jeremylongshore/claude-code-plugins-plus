# Conversation Context

## Conversation Context

### When to Start New Chat

```
Start new chat when:
- Switching to unrelated topic
- Context feels polluted
- AI seems confused
- Responses are slow/truncated
- Starting fresh task
```

### Preserving Important Context

```
If switching topics but need context:
1. Copy important code/decisions
2. Start new chat
3. Paste relevant context
4. Continue with fresh window
```

### Multi-Turn Optimization

```
Good flow:
Turn 1: "Create user authentication"
Turn 2: "Add password reset to auth"
Turn 3: "Add rate limiting to auth"

Bad flow:
Turn 1: "Create user authentication"
Turn 2: "How do I sort arrays in Python?"
Turn 3: "Back to auth - add reset"
(Context confused)
```

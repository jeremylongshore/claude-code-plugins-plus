# Debugging Chat Issues

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

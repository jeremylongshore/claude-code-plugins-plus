# Ai Feature Optimization

## AI Feature Optimization

### Completion Speed

```json
{
  // Use faster model for completions
  "cursor.completion.model": "gpt-3.5-turbo",

  // Adjust delay
  "cursor.completion.delay": 200,

  // Limit completion length
  "cursor.completion.maxLength": 500
}
```

### Context Management

```
Reduce context for faster responses:
1. Select less code
2. Fewer @-mentions
3. Shorter conversations
4. Clear chat history

Use .cursorignore aggressively:
- Exclude non-essential files
- Focus on active development areas
```

### Model Selection

```
Speed vs Quality:

Fastest: cursor-small, gpt-3.5-turbo
Balanced: gpt-4-turbo
Thorough: gpt-4, claude-3-opus

Use faster models for:
- Simple completions
- Quick lookups
- Repetitive tasks
```

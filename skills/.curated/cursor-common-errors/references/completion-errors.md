# Completion Errors

## Completion Errors

### "Completions Not Appearing"

```
Symptoms: No ghost text, Tab does nothing

Checklist:
[ ] Check rate limits (status bar)
[ ] Verify completion is enabled (Settings)
[ ] Check network connectivity
[ ] Restart Cursor
[ ] Check file type is supported

Settings to verify:
{
  "cursor.completion.enabled": true,
  "editor.inlineSuggest.enabled": true
}
```

### "Slow Completions"

```
Symptoms: Long delay before suggestions appear

Solutions:
1. Switch to faster model (GPT-3.5-turbo)
2. Check network latency
3. Reduce context size
4. Close unused tabs
5. Check CPU usage
```

### "Wrong/Irrelevant Completions"

```
Symptoms: Suggestions don't match context

Solutions:
1. Add better comments/docstrings
2. Update .cursorrules file
3. Re-index codebase
4. Clear chat context
5. Verify correct language mode
```

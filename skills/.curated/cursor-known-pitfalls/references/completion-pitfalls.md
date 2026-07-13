# Completion Pitfalls

## Completion Pitfalls

### Tab Key Confusion

```
PITFALL:
Tab accepts completion when you wanted indentation.
Accidentally inserting AI-generated code.

SOLUTION:
- Watch for ghost text before pressing Tab
- Use Esc to dismiss unwanted completions
- Configure completion delay
- Be aware of completion mode
```

### Outdated Completions

```
PITFALL:
Completions based on old patterns in codebase.
AI suggests deprecated approaches.

SOLUTION:
- Update .cursorrules with current patterns
- Re-index after major refactors
- Include modern examples in rules
- Clear index cache if stale
```

### Language/Framework Mismatch

```
PITFALL:
AI suggests React patterns in Vue project.
Wrong framework conventions in completions.

SOLUTION:
- Configure .cursorrules with correct framework
- Check file associations
- Be explicit in prompts about framework
- Verify language mode in status bar
```

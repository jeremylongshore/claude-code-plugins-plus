# Context Optimization Strategies

## Context Optimization Strategies

### Prioritize Relevant Code

```
Most effective:
1. Select exactly the code you're asking about
2. @-mention directly related files
3. Reference patterns to follow

Less effective:
- Including entire files when only function needed
- @-mentioning unrelated files
- Large conversation history
```

### Minimize Context Waste

```
Do:
- Select specific functions, not entire files
- Use @file only for relevant files
- Start new chat when topic changes
- Be concise in prompts

Don't:
- @-mention "just in case"
- Keep long conversation threads
- Include commented-out code
- Add unnecessary explanations
```

### Context-Efficient Prompts

```
Inefficient:
"I have this code and it's not working and I need help
understanding what's wrong with it and how to fix it
because it throws an error when I run it"

Efficient:
"Fix TypeError: Cannot read 'map' of undefined
@api/users.ts line 45"
```

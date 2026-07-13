# Prompt Templates

## Prompt Templates

### Code Generation

```
Template:
"Create [COMPONENT_TYPE] for [PURPOSE]:

Requirements:
- [Requirement 1]
- [Requirement 2]

Technology:
- [Framework/Library]
- [Styling approach]

Follow patterns from @[reference-file]

Include:
- TypeScript types
- Error handling
- Tests (optional)"
```

### Code Review

```
Template:
"Review this code for:
- [ ] Security vulnerabilities
- [ ] Performance issues
- [ ] Best practice violations
- [ ] Missing error handling
- [ ] Type safety problems

Suggest specific improvements with code examples."
```

### Debugging

```
Template:
"Debug this issue:

ERROR: [exact error message]

EXPECTED: [what should happen]

ACTUAL: [what actually happens]

RELEVANT CODE:
[code snippet]

What I've tried:
- [attempt 1]
- [attempt 2]"
```

### Refactoring

```
Template:
"Refactor [CODE/FILE] to:
- [Goal 1]
- [Goal 2]

Preserve:
- [What must not change]
- [Behavior to maintain]

Apply patterns from:
- @[reference-file]"
```

# Prompt Engineering Fundamentals

## Prompt Engineering Fundamentals

### Effective Prompt Structure

```
[CONTEXT] What you're working on
[TASK] What you want to accomplish
[CONSTRAINTS] Requirements and limitations
[FORMAT] How you want the output
[EXAMPLES] Reference patterns if needed
```

### Example Well-Structured Prompt

```
CONTEXT: Working on a Next.js 14 e-commerce app with TypeScript

TASK: Create a shopping cart hook that:
- Manages cart items in localStorage
- Syncs with server when user logs in
- Handles quantity updates
- Calculates totals with tax

CONSTRAINTS:
- Use Zustand for state management
- Follow existing patterns in @hooks/useAuth.ts
- Handle offline scenarios gracefully
- TypeScript strict mode

FORMAT:
- Single useCart.ts file
- Export named hook and types
- Include JSDoc comments
```

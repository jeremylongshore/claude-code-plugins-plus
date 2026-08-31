# Advanced Composer Techniques

## Advanced Composer Techniques

### Context Injection

```
Use @-mentions to give context:

"@auth.ts @middleware.ts
Create a rate-limiting middleware that:
- Uses the same patterns as auth.ts
- Integrates with existing middleware chain
- Adds Redis-based rate limiting"
```

### File Structure Control

```
Be explicit about structure:

"Create in this structure:
src/
  features/
    auth/
      components/
        LoginForm.tsx
        RegisterForm.tsx
      hooks/
        useAuth.ts
      api/
        authApi.ts
      types/
        auth.types.ts
      index.ts"
```

### Incremental Refinement

```
Initial: "Create a user dashboard"
Refine: "Add a sidebar navigation"
Refine: "Make the layout responsive"
Refine: "Add dark mode support"
Refine: "Optimize for performance"
```

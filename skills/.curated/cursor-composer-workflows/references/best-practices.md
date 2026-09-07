# Best Practices

## Best Practices

### Clear Specifications

```
Good prompt structure:
1. What to create/modify
2. Technology stack
3. Specific requirements
4. Patterns to follow
5. Files to reference

Example:
"CREATE: Payment processing module
TECH: TypeScript, Stripe SDK, Express
REQUIREMENTS:
- Webhook handler for payment events
- Idempotent payment creation
- Refund handling
- Audit logging
FOLLOW: patterns in @orderService.ts
REFERENCE: Stripe best practices"
```

### Review Before Apply

```
Composer shows preview:
1. Review each file change
2. Check for unintended modifications
3. Verify imports are correct
4. Ensure tests are included
5. Click "Apply" or request changes
```

### Iterative Workflow

```
Don't try to do everything at once:

Phase 1: Core functionality
Phase 2: Error handling
Phase 3: Tests
Phase 4: Documentation
Phase 5: Optimization

Review and test between phases
```

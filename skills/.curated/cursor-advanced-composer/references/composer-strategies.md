# Composer Strategies

## Composer Strategies

### Incremental Refinement

```
Round 1: "Create basic user authentication"
  → Review generated code

Round 2: "Add refresh token rotation"
  → Review additions

Round 3: "Add rate limiting to auth endpoints"
  → Review changes

Round 4: "Add comprehensive error handling"
  → Review final state
```

### Reference-Based Generation

```
"Using @services/UserService.ts as the canonical example:
1. Analyze its patterns (error handling, typing, logging)
2. Create ProductService following exact same patterns
3. Create OrderService following exact same patterns
4. Ensure consistency across all three"
```

### Constraint-Based Generation

```
"Create payment processing module with constraints:

MUST:
- Use Stripe SDK v10+
- Implement idempotency keys
- Log all transactions
- Handle all Stripe webhook events

MUST NOT:
- Store card numbers
- Skip validation
- Use deprecated APIs
- Block main thread

SHOULD:
- Retry failed operations
- Cache customer data
- Use strong typing
- Include comprehensive tests"
```

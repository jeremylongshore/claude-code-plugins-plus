---
name: cursor-advanced-composer
description: |
  Advanced Cursor Composer techniques for complex edits. Triggers on "advanced composer",
  "composer patterns", "multi-file generation", "composer refactoring".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Advanced Cursor Composer Techniques

## Beyond Basic Usage

### Composer Capabilities
```
Basic:
- Single file generation
- Simple edits
- Code scaffolding

Advanced:
- Multi-file orchestration
- Complex refactoring
- Architecture changes
- Pattern application
- Code migration
```

## Multi-File Orchestration

### Coordinated File Creation
```
Prompt pattern:
"Create a complete [feature] with:
1. Types/interfaces in types/[feature].ts
2. Service layer in services/[feature]Service.ts
3. API routes in api/[feature]/route.ts
4. React hook in hooks/use[Feature].ts
5. Component in components/[Feature].tsx
6. Tests in __tests__/[feature].test.ts

Follow existing patterns in @services/userService.ts"
```

### Example: Feature Module
```
"Create an order management feature:

1. types/order.ts
   - Order, OrderItem, OrderStatus types
   - CreateOrderDTO, UpdateOrderDTO

2. services/orderService.ts
   - CRUD operations
   - calculateTotal, validateOrder
   - Follow @services/userService.ts patterns

3. api/orders/route.ts
   - GET (list with pagination)
   - POST (create order)
   - Follow REST patterns from @api/users/route.ts

4. api/orders/[id]/route.ts
   - GET (single order)
   - PUT (update)
   - DELETE (soft delete)

5. hooks/useOrders.ts
   - useOrders() for list
   - useOrder(id) for single
   - useCreateOrder, useUpdateOrder mutations

6. components/OrderList.tsx
   - Table with sorting, filtering
   - Pagination
   - Follow @components/UserList.tsx patterns

7. __tests__/orderService.test.ts
   - Unit tests for service
   - Mock database calls"
```

## Complex Refactoring

### Pattern Transformation
```
"Refactor all class components to functional components:

For each file matching components/*.tsx:
1. Convert class to function
2. Convert this.state to useState
3. Convert lifecycle methods to useEffect
4. Convert methods to functions/hooks
5. Update prop types
6. Add proper TypeScript types

Start with @components/Dashboard.tsx as example"
```

### Architecture Migration
```
"Migrate from Redux to Zustand:

Phase 1 - Create new stores:
- stores/useUserStore.ts (from redux/userSlice.ts)
- stores/useCartStore.ts (from redux/cartSlice.ts)
- stores/useSettingsStore.ts (from redux/settingsSlice.ts)

Phase 2 - Update consumers:
- Replace useSelector with store hooks
- Replace useDispatch with store actions
- Update all components using Redux

Phase 3 - Cleanup:
- Remove Redux dependencies
- Delete old slice files
- Update package.json"
```

### API Version Migration
```
"Migrate from REST to tRPC:

1. Create tRPC router:
   - server/trpc/routers/user.ts
   - server/trpc/routers/product.ts
   - server/trpc/routers/order.ts

2. Combine in server/trpc/root.ts

3. Create tRPC client:
   - lib/trpc.ts
   - Update next.config.js for tRPC

4. Migrate each API consumer:
   - hooks/useUsers.ts → use tRPC
   - hooks/useProducts.ts → use tRPC

5. Remove old:
   - api/users/route.ts → delete
   - lib/api-client.ts → deprecate"
```

## Advanced Patterns

### Template Application
```
"Apply the Repository pattern to all database operations:

Create base:
- lib/repository/BaseRepository.ts
  - Generic CRUD methods
  - Error handling
  - Logging

Create implementations:
- lib/repository/UserRepository.ts
- lib/repository/ProductRepository.ts
- lib/repository/OrderRepository.ts

Update services:
- Inject repositories
- Remove direct database calls
- Update all services to use repositories"
```

### Code Generation Pipeline
```
"Generate full CRUD for entity 'Product':

1. Schema (prisma/schema.prisma)
   - Add Product model
   - Add relations

2. Migration
   - Create migration file

3. Repository
   - ProductRepository with typed methods

4. Service
   - ProductService with business logic

5. API Routes
   - Full REST endpoints

6. Validation
   - Zod schemas for input validation

7. Frontend
   - Types, hooks, components

8. Tests
   - Unit and integration tests"
```

### Cross-Cutting Concerns
```
"Add logging to all API routes:

1. Create logger utility:
   - lib/logger.ts with structured logging

2. Create middleware:
   - middleware/logging.ts

3. Update all API routes to:
   - Log request start
   - Log request completion
   - Log errors with context
   - Include correlation IDs

4. Add log aggregation config:
   - Update for production logging service"
```

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

## Quality Control

### Review Workflow
```
1. Generate with Composer
2. Review each file before accepting
3. Check for:
   - Type safety
   - Error handling
   - Security issues
   - Performance
   - Test coverage
4. Request refinements if needed
5. Apply when satisfied
```

### Verification Prompts
```
After generation:
"Review the generated code for:
- Missing error handling
- Type safety issues
- Security vulnerabilities
- Performance problems
- Missing edge cases"
```

### Testing Generated Code
```
"Add tests for all generated code:
- Unit tests for business logic
- Integration tests for API routes
- Component tests for React components
- E2E tests for critical paths"
```

## Troubleshooting

### Composer Limitations
```
Challenge: Large codebase changes
Solution: Break into smaller, focused requests

Challenge: Inconsistent output
Solution: Provide explicit examples and references

Challenge: Missing context
Solution: Use @-mentions strategically

Challenge: Conflicting edits
Solution: Review changes carefully, edit sequentially
```

### Recovery from Bad Generation
```
If Composer generates incorrect code:

1. Don't apply changes
2. Be more specific in prompt
3. Provide counter-examples
4. Reference working code
5. Try smaller scope
6. Switch to manual + inline edit
```

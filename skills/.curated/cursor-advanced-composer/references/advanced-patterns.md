# Advanced Patterns

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

# Multi-File Orchestration

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

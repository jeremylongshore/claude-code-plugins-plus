# Complex Refactoring

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

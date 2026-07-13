## Examples

### Mock Supabase Responses

```typescript
vi.mock('@supabase/supabase-js', () => ({
  SupabaseClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode

```bash
# Enable verbose logging
DEBUG=SUPABASE=* npm run dev
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

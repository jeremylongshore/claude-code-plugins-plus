# Variant A: Monolith (Simple)

## Variant A: Monolith (Simple)

**Best for:** MVPs, small teams, < 10K daily active users

```
my-app/
├── src/
│   ├── supabase/
│   │   ├── client.ts          # Singleton client
│   │   ├── types.ts           # Types
│   │   └── middleware.ts      # Express middleware
│   ├── routes/
│   │   └── api/
│   │       └── supabase.ts    # API routes
│   └── index.ts
├── tests/
│   └── supabase.test.ts
└── package.json
```

### Key Characteristics

- Single deployment unit
- Synchronous Supabase calls in request path
- In-memory caching
- Simple error handling

### Code Pattern

```typescript
// Direct integration in route handler
app.post('/api/create', async (req, res) => {
  try {
    const result = await supabaseClient.create(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

---

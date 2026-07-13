# Credit System

## Credit System

### Adding Credits

```
1. Go to openrouter.ai/credits
2. Choose amount:
   - $5 (starter)
   - $20 (recommended)
   - $100 (heavy usage)
   - Custom amount
3. Pay with card
4. Credits available instantly
```

### Credit Limits per Key

```python
# Set per-key limits to control spending
# In dashboard: openrouter.ai/keys

Key: "development"
Limit: $10.00

Key: "production"
Limit: $100.00

Key: "testing"
Limit: $1.00
```

### Checking Balance

```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

```json
{
  "data": {
    "label": "my-key",
    "limit": 100.0,
    "usage": 23.45,
    "limit_remaining": 76.55
  }
}
```

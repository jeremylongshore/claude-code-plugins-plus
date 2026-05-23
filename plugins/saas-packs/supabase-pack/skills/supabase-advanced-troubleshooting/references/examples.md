## Examples

### Quick Layer Test

```bash
# Test each layer in sequence
curl -v https://api.supabase.com/health 2>&1 | grep -E "(Connected|TLS|HTTP)"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

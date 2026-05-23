## Examples

### One-Line Health Check

```bash
curl -sf https://api.yourapp.com/health | jq '.services.supabase.status' || echo "UNHEALTHY"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

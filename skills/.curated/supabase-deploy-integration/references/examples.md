## Examples

### Quick Deploy Script

```bash
#!/bin/bash
# Platform-agnostic deploy helper
case "$1" in
  vercel)
    vercel secrets add supabase_api_key "$SUPABASE_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set SUPABASE_API_KEY="$SUPABASE_API_KEY"
    fly deploy
    ;;
esac
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

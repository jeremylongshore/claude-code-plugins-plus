## Examples

### Quick Deploy Script

```bash
#!/bin/bash
# Platform-agnostic deploy helper
case "$1" in
  vercel)
    vercel secrets add vercel_api_key "$VERCEL_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set VERCEL_API_KEY="$VERCEL_API_KEY"
    fly deploy
    ;;
esac
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

## Implementation Guide

### Step 1: Configure Environment Variables

```bash
# .env (NEVER commit to git)
VERCEL_API_KEY=sk_live_***
VERCEL_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation

```bash
# 1. Generate new key in Vercel dashboard
# 2. Update environment variable
export VERCEL_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${VERCEL_API_KEY}" \
  https://api.vercel.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege

| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, deploy` |
| Staging | `read, write, deploy` |
| Production | `read, write, deploy, domains` |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

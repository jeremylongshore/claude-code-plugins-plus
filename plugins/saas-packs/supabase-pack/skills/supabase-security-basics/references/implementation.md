## Implementation Guide

### Step 1: Configure Environment Variables

```bash
# .env (NEVER commit to git)
SUPABASE_API_KEY=sk_live_***
SUPABASE_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation

```bash
# 1. Generate new key in Supabase dashboard
# 2. Update environment variable
export SUPABASE_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${SUPABASE_API_KEY}" \
  https://api.supabase.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege

| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, write` |
| Staging | `read, write, admin` |
| Production | `read, write` |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

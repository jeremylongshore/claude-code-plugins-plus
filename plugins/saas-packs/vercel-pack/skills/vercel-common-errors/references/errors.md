## Error Handling Reference

### Build Failed

**Error Message:**

```
Command 'npm run build' exited with 1
```

**Cause:** Build script failed due to errors in code or dependencies

**Solution:**

```bash
Check build logs in Vercel dashboard. Run 'npm run build' locally to reproduce.
```

---

### Function Timeout

**Error Message:**

```
FUNCTION_INVOCATION_TIMEOUT
```

**Cause:** Serverless function exceeded execution time limit

**Solution:**
Optimize function code, use Edge Runtime, or upgrade plan for longer timeouts.

---

### Domain Verification Failed

**Error Message:**

```
Domain verification failed
```

**Cause:** DNS records not configured correctly

**Solution:**

```typescript
Add required CNAME or A records. Wait for DNS propagation (up to 48h).
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

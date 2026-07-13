# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Peer dependency conflict | Incompatible versions | Use resolutions/overrides or update peer |
| Audit resolution unavailable | No patch available | Apply workaround or accept risk with justification |
| Build failure after update | Breaking change | Review changelog, apply migration steps |
| Lock file conflict | Concurrent updates | Regenerate lock file, coordinate team |
| Registry timeout | Network or rate limit | Retry with backoff, check network |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

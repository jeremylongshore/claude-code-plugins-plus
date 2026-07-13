# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Workflow syntax error | Invalid YAML | Validate with actionlint or yamllint |
| Secret not found | Missing repository secret | Add secret in repository settings |
| Permission denied | Insufficient GITHUB_TOKEN | Add required permissions to workflow |
| Cache miss | Cache key mismatch | Update cache key pattern |
| Deploy failed | Environment misconfiguration | Check environment secrets and settings |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

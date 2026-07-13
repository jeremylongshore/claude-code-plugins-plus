# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Build failed | Missing dependencies | Check COPY commands, verify paths |
| Large image size | Unoptimized layers | Use multi-stage, add .dockerignore |
| Permission denied | Wrong user context | Set proper USER and permissions |
| Cache not working | Layer ordering | Reorder commands, dependencies first |
| Security scan fails | Vulnerable base | Update base image, patch vulnerabilities |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

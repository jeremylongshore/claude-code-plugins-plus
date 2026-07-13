# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Indexing never completes | Large directories not excluded | Add node_modules, .git, build to .cursorignore |
| @codebase returns nothing | File not indexed or excluded | Check .cursorignore, verify file type supported |
| High CPU during indexing | Too many files or workers | Reduce index.workers setting, exclude more files |
| Index outdated after changes | File watcher not updating | Manual refresh or check watcher exclusions |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

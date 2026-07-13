# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Indexing never completes | Large files or circular symlinks | Add exclusions to `.cursorignore` |
| @codebase returns nothing | Indexing incomplete or file excluded | Check status bar and exclusion patterns |
| High CPU during indexing | Too many workers or large codebase | Reduce worker count in settings |
| Index outdated | File watcher not triggering | Run manual refresh via Command Palette |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

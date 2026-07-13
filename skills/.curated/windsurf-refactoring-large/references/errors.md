# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Checkpoint validation failed | Tests failing at checkpoint | Rollback to previous checkpoint, fix issues |
| Dependency conflict | Changed code breaks downstream | Map full dependency tree, adjust order |
| Performance regression | Refactored code slower | Profile and optimize before proceeding |
| Merge conflict | Parallel development | Coordinate freeze window, rebase plan |
| Rollback incomplete | Partial state restoration | Use backup files, manual intervention |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

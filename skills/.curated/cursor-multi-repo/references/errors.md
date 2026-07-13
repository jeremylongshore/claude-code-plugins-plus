# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Can't find file | Wrong path or not indexed | Use full path, check .cursorignore |
| Context too large | Entire monorepo loaded | Open single project or add exclusions |
| Inconsistent suggestions | Conflicting rules between projects | Verify .cursorrules inheritance |
| Slow performance | Too many files indexed | Aggressive .cursorignore for inactive packages |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

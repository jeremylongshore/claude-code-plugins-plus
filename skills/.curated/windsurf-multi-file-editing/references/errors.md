# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Circular dependency detected | Files have mutual imports | Break cycle by extracting shared code |
| Syntax error after edit | Invalid code generated | Review template patterns, use rollback |
| Reference not found | Missing import or export | Check file scope includes all references |
| Operation timeout | Too many files affected | Split into smaller batches |
| Rollback failed | Git state inconsistent | Manual recovery from edit-history.json |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

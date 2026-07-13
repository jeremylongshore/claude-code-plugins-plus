# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Version calculation failed | No conventional commits | Add feat/fix prefixes to commits |
| Changelog generation empty | No changes since last release | Verify commit range, check for tags |
| Publish failed | Auth or permission issue | Check registry credentials |
| Tag already exists | Duplicate version | Delete tag and bump version |
| Breaking change missed | Commit not marked | Add BREAKING CHANGE footer |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

# figma-migration-deep-dive: Error Handling

Error reference for the `figma-migration-deep-dive` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| 403 on Variables POST | Not Enterprise | Use JSON export instead of Variables API |
| Duplicate variable names | Name collision in target | Add prefix/suffix to migrated names |
| Missing node data | Node deleted between fetch and read | Re-fetch with error handling |
| Large file timeout | File >100MB | Use `/nodes` endpoint for specific pages |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

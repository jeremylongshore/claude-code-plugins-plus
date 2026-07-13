# figma-ci-integration: Error Handling

Error reference for the `figma-ci-integration` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 in CI | PAT expired | Rotate secret: `gh secret set FIGMA_PAT` |
| Empty token output | File key wrong | Verify `FIGMA_FILE_KEY` variable |
| Rate limited in CI | Concurrent workflows | Add concurrency group to workflow |
| Stale cache | Node modules cached | Clear with `actions/cache` invalidation |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

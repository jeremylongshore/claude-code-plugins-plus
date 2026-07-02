# figma-incident-runbook: Error Handling

Error reference for the `figma-incident-runbook` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.figma.com | Network issue | Try from different network or mobile |
| Triage script fails | PAT not set | Set FIGMA_PAT before running |
| Fallback data stale | Last cache too old | Set up regular cache refresh |
| Alert not firing | Missing metrics | Verify Prometheus scrape config |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

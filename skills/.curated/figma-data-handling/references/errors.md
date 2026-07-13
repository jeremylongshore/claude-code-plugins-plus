# figma-data-handling: Error Handling

Error reference for the `figma-data-handling` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| 403 on comments | Missing `file_comments:read` scope | Regenerate PAT with scope |
| Empty version history | New file with no saved versions | Create a named version in Figma first |
| PII in logs | Missing redaction | Apply `safeFigmaLog` wrapper |
| Stale image URLs | URLs older than 30 days | Re-export images; do not cache URLs long-term |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

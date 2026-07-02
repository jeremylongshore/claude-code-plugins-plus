# figma-observability: Error Handling

Error reference for the `figma-observability` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality | Too many label values | Normalize endpoint paths |
| Alert storms | Threshold too low | Tune `for` duration and thresholds |
| Missing rate limit headers | Not all endpoints return them | Handle null values gracefully |
| Metrics not scraping | Wrong port or path | Verify Prometheus scrape config |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

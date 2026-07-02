# Step 5: Benchmark Report Template

Deep-dive reference for the `figma-load-scale` skill — extracted from the 'Step 5: Benchmark Report Template' step of the workflow.

```markdown
## Figma API Benchmark Report
**Date:** YYYY-MM-DD
**Plan:** [Starter/Pro/Org/Enterprise]
**Seat:** [Full/Collab/Viewer]

### Rate Limit Findings
| Endpoint | Measured Limit/min | First 429 At | Retry-After |
|----------|-------------------|--------------|-------------|
| GET /v1/files/:key?depth=1 | ~30 | Request #31 | 60s |
| GET /v1/files/:key/nodes | ~30 | Request #32 | 60s |
| GET /v1/images/:key | ~20 | Request #21 | 60s |

### Latency
| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| /v1/files (depth=1) | 200ms | 500ms | 1200ms |
| /v1/files (full) | 800ms | 2000ms | 4000ms |
| /v1/images | 300ms | 800ms | 1500ms |

### Recommendations
- Cache file metadata (changes infrequently)
- Use webhooks instead of polling
- Batch node IDs in single requests
- Use `depth=1` unless full tree is needed
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

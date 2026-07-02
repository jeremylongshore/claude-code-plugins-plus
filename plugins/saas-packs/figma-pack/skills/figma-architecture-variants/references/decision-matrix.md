# Step 2: Decision Matrix

Deep-dive reference for the `figma-architecture-variants` skill — extracted from the 'Step 2: Decision Matrix' step of the workflow.

| Factor | CLI Script | Webhook Service | Figma Plugin |
|--------|-----------|-----------------|--------------|
| Real-time | No | Yes | Yes (in-editor) |
| Infrastructure | None | Server/serverless | None |
| CI/CD integration | Natural | Via webhook | Not applicable |
| User interaction | No | No | Yes |
| API used | REST API | REST API | Plugin API |
| File modification | No (read-only) | No (read-only) | Yes (full access) |
| Figma app required | No | No | Yes |
| Auth | PAT | PAT + webhook passcode | None (runs in Figma) |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

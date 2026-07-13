# figma-local-dev-loop: Error Handling

Error reference for the `figma-local-dev-loop` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not appearing in Figma | Wrong manifest path | Re-import from correct `manifest.json` |
| `figma` global undefined | Running outside Figma sandbox | Use `@figma/plugin-typings` for types only |
| Fixture stale | File changed since snapshot | Re-run fixture download script |
| esbuild watch crash | Syntax error in TS | Fix error; watch auto-restarts |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

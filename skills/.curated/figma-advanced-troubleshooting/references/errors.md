# figma-advanced-troubleshooting: Error Handling

Error reference for the `figma-advanced-troubleshooting` skill — extracted from the skill's Error Handling guidance.

| Issue | Diagnostic | Solution |
|-------|-----------|----------|
| Intermittent 500s | Track frequency and timing | Log every request; report pattern to Figma |
| Slow responses | curl timing breakdown | Check if DNS/TLS is the bottleneck |
| Null image renders | Validate node visibility | Check node opacity and visibility in Figma |
| Memory crash | Large file JSON | Use `depth=1` + per-page `/nodes` calls |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

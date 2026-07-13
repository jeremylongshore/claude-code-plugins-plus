# figma-enterprise-rbac: Error Handling

Error reference for the `figma-enterprise-rbac` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| OAuth code expired | Exchange took >30s | Exchange immediately on callback |
| Token refresh failed | Refresh token revoked | Re-authenticate user through OAuth flow |
| 403 on Variables API | Not Enterprise plan | Use styles API instead (available on all plans) |
| Team components empty | No published components | Publish components in Figma first |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

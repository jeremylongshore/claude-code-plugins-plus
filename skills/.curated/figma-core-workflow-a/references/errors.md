# figma-core-workflow-a: Error Handling

Error reference for the `figma-core-workflow-a` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| Empty `styles` map | File has no published styles | Publish styles in Figma first |
| `null` node in response | Node was deleted | Filter nulls before processing |
| 403 on variables endpoint | Not Enterprise plan | Use styles endpoint instead |
| Color looks wrong | Forgot 0-1 to 0-255 conversion | Multiply by 255 before hex |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

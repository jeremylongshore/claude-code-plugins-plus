# Step 5: Access Control Middleware

Deep-dive reference for the `figma-enterprise-rbac` skill — extracted from the 'Step 5: Access Control Middleware' step of the workflow.

```typescript
// Middleware that checks if user has Figma access to a resource
async function requireFigmaAccess(fileKey: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userToken = await getUserFigmaToken(req.user.id);
    if (!userToken) {
      return res.status(403).json({ error: 'Figma account not connected' });
    }

    // Check if user's token can access this file
    const check = await fetch(
      `https://api.figma.com/v1/files/${fileKey}?depth=1`,
      { headers: { Authorization: `Bearer ${userToken}` } }
    );

    if (check.status === 403) {
      return res.status(403).json({ error: 'No access to this Figma file' });
    }

    next();
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

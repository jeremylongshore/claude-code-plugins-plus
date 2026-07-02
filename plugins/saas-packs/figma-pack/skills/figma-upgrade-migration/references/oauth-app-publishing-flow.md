# Step 3: OAuth App Publishing Flow

Deep-dive reference for the `figma-upgrade-migration` skill — extracted from the 'Step 3: OAuth App Publishing Flow' step of the workflow.

All OAuth apps (public and private) must complete the new publishing flow:

1. Go to your app in the Figma developer dashboard
2. Complete the required app information fields
3. Add required redirect URLs
4. Submit for review (public apps) or activate (private apps)
5. Update your code to handle the new token format

```typescript
// Check if your OAuth tokens need refresh
async function checkTokenHealth(accessToken: string): Promise<boolean> {
  const res = await fetch('https://api.figma.com/v1/me', {
    headers: { 'X-Figma-Token': accessToken },
  });
  if (res.status === 403) {
    console.warn('Token expired or revoked -- refresh needed');
    return false;
  }
  return res.ok;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

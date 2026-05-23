## Examples

### Quick Performance Wrapper

```typescript
const withPerformance = <T>(name: string, fn: () => Promise<T>) =>
  measuredVercelCall(name, () =>
    cachedVercelRequest(`cache:${name}`, fn)
  );
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

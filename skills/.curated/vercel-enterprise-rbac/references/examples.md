## Examples

### Quick Permission Check

```typescript
if (!checkPermission(user.role, 'write')) {
  throw new ForbiddenError('Write permission required');
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

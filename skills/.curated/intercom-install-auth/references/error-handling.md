# Error Handling Reference

Full authentication error matrix and typed error-handling pattern for the
`intercom-client` SDK. The main `SKILL.md` links here for the complete table.

## Authentication Error Matrix

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `unauthorized` | 401 | Invalid or expired token | Regenerate in Developer Hub |
| `forbidden` | 403 | Missing OAuth scope | Add required scope in app config |
| `token_revoked` | 401 | Token was revoked | Generate new access token |
| `invalid_grant` | 400 | OAuth code expired | Restart OAuth flow |

## Typed Error Handling

```typescript
import { IntercomError } from "intercom-client";

try {
  await client.contacts.list();
} catch (error) {
  if (error instanceof IntercomError) {
    console.error(`Intercom error: ${error.statusCode} - ${error.message}`);
    if (error.statusCode === 401) {
      console.error("Token invalid. Regenerate at app.intercom.com > Developer Hub");
    }
  }
}
```

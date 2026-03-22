---
name: appfolio-hello-world
description: |
  Query AppFolio properties, units, and tenants via REST API.
  Trigger: "appfolio hello world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Hello World

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Verify client_id/secret |
| `404 Not Found` | Wrong endpoint | Check API version in URL |
| `422 Unprocessable` | Invalid request body | Validate required fields |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

Continue with the next skill in the AppFolio pack sequence.

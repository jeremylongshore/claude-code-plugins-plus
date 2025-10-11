---
description: Manage API versions with proper migration strategies
shortcut: apiver
---

# Manage API Versions

Implement API versioning with backward compatibility, deprecation notices, and smooth migration paths.

## What You Do

1. **Choose versioning strategy:**
   - URL path versioning (`/v1/`, `/v2/`)
   - Header versioning (`Accept: application/vnd.api.v2+json`)
   - Query param versioning (`?version=2`)
   - Content negotiation

2. **Create version structure:**
   - Separate route handlers per version
   - Shared business logic
   - Version-specific transformers
   - Backward compatibility layer

3. **Handle deprecation:**
   - Deprecation warnings in responses
   - Sunset header for EOL dates
   - Migration guides
   - Version changelog

4. **Generate migration tools:**
   - Version compatibility matrix
   - Breaking change detection
   - Automated migration scripts
   - Test suite for all versions

## Best Practices

- Support at least 2 versions simultaneously
- Provide 6-12 month deprecation notice
- Clear migration documentation
- Automated compatibility testing
- Version-agnostic client SDKs

Implement professional API versioning with smooth upgrade paths.

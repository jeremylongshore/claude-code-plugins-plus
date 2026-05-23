## Implementation Guide

1. Review session creation, storage, and transport security controls.
2. Validate cookie flags, rotation, expiration, and invalidation behavior.
3. Identify common attack paths (fixation, CSRF, replay) and mitigations.
4. Provide prioritized fixes with configuration/code examples.

### 1. Code Discovery Phase

Locate session management code:

- Authentication/login handlers
- Session middleware configuration
- Cookie handling code
- Session storage implementations
- Logout/session termination code

**Common file patterns**:

- `**/auth/**`, `**/session/**`, `**/middleware/**`
- `session.config.*`, `auth.config.*`
- Framework-specific: `settings.py`, `application.yml`, `web.config`

### 2. Session ID Security Analysis

**Generation Strength**:

- Check for cryptographically secure random generators
- Verify sufficient entropy (at least 128 bits)
- Ensure unpredictable session ID patterns
- No sequential or timestamp-based IDs

**Bad Patterns to Detect**:

```javascript
// INSECURE: Predictable
sessionId = Date.now() + userId;
sessionId = Math.random().toString();

// SECURE: Cryptographically random
sessionId = crypto.randomBytes(32).toString('hex');
```

### 3. Session Fixation Vulnerability Check

Verify session ID regeneration:

- New session ID generated after login
- Session ID changes on privilege escalation
- Old session ID invalidated after regeneration

**Vulnerable Pattern**:

```python
# INSECURE: Reuses existing session ID

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

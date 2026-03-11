---
name: speak-enterprise-rbac
description: |
  Configure Speak enterprise SSO, role-based access control, and organization management for language schools.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for enterprise language learning.
  Trigger with phrases like "speak SSO", "speak RBAC",
  "speak enterprise", "speak roles", "speak permissions", "speak SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Enterprise RBAC

## Overview
Configure enterprise-grade access control for Speak language learning integrations in schools, businesses, and organizations.

## Prerequisites
- Speak Enterprise tier subscription
- Identity Provider (IdP) with SAML/OIDC support
- Understanding of role-based access patterns
- Audit logging infrastructure

## Instructions
1. **Role Definitions for Language Learning**
2. **Role Implementation**
3. **SSO Integration**
4. **Organization Management**
5. **Team and Class Management**
6. **Access Control Middleware**
7. **Audit Trail**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Role definitions for education/enterprise
- SSO integration (SAML/OIDC)
- Team and class management
- Permission middleware
- Audit trail enabled

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login fails | Wrong callback URL | Verify IdP config |
| Permission denied | Missing role mapping | Update group mappings |
| Token expired | Short TTL | Refresh token logic |
| Team access denied | Not a member | Check team membership |

## Examples
### Quick Permission Check
```typescript
if (!checkPermission(user.role, 'viewLearnerProgress')) {
  throw new ForbiddenError('Cannot view learner progress');
}
```

### Instructor Dashboard Access
```typescript
app.get('/instructor/dashboard',
  requireSpeakPermission('viewLearnerProgress'),
  async (req, res) => {
    const teams = await teamManager.getInstructorTeams(req.user.id);
    const progress = await Promise.all(
      teams.map(t => teamManager.getTeamProgress(t.id))
    );
    res.json({ teams, progress });
  }
);
```

## Resources
- [Speak Enterprise Guide](https://developer.speak.com/docs/enterprise)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Next Steps
For major migrations, see `speak-migration-deep-dive`.
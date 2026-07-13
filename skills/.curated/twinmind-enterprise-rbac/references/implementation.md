# TwinMind Enterprise RBAC - Detailed Implementation

## Permission Model

```typescript
export enum Permission {
  TRANSCRIPT_CREATE = 'transcript:create',
  TRANSCRIPT_READ = 'transcript:read',
  TRANSCRIPT_READ_ALL = 'transcript:read:all',
  TRANSCRIPT_DELETE = 'transcript:delete',
  TRANSCRIPT_DELETE_ALL = 'transcript:delete:all',
  SUMMARY_GENERATE = 'summary:generate',
  SUMMARY_READ = 'summary:read',
  ACTION_ITEM_CREATE = 'action_item:create',
  ACTION_ITEM_ASSIGN = 'action_item:assign',
  TEAM_VIEW = 'team:view',
  TEAM_MANAGE = 'team:manage',
  TEAM_INVITE = 'team:invite',
  SETTINGS_MANAGE = 'settings:manage',
  BILLING_VIEW = 'billing:view',
  BILLING_MANAGE = 'billing:manage',
  ADMIN_FULL = 'admin:*',
  AUDIT_VIEW = 'audit:view',
  COMPLIANCE_MANAGE = 'compliance:manage',
}

export const predefinedRoles: Record<string, Role> = {
  viewer: { name: 'Viewer', permissions: [Permission.TRANSCRIPT_READ, Permission.SUMMARY_READ] },
  member: { name: 'Member', permissions: [Permission.TRANSCRIPT_CREATE, Permission.TRANSCRIPT_READ, Permission.TRANSCRIPT_DELETE, Permission.SUMMARY_GENERATE, Permission.SUMMARY_READ, Permission.ACTION_ITEM_CREATE], inherits: ['viewer'] },
  manager: { name: 'Manager', permissions: [Permission.TRANSCRIPT_READ_ALL, Permission.TRANSCRIPT_DELETE_ALL, Permission.ACTION_ITEM_ASSIGN, Permission.TEAM_VIEW, Permission.TEAM_INVITE], inherits: ['member'] },
  admin: { name: 'Admin', permissions: [Permission.TEAM_MANAGE, Permission.SETTINGS_MANAGE, Permission.BILLING_VIEW, Permission.AUDIT_VIEW], inherits: ['manager'] },
  owner: { name: 'Owner', permissions: [Permission.ADMIN_FULL, Permission.BILLING_MANAGE, Permission.COMPLIANCE_MANAGE], inherits: ['admin'] },
};

export function resolvePermissions(roleName: string): Permission[] {
  const role = predefinedRoles[roleName];
  if (!role) return [];
  const permissions = new Set<Permission>(role.permissions);
  for (const inherited of role.inherits || []) {
    resolvePermissions(inherited).forEach(p => permissions.add(p));
  }
  return Array.from(permissions);
}
```

## Authorization Service

```typescript
export class AuthorizationService {
  hasPermission(user: User, permission: Permission): boolean {
    const userPermissions = this.getUserPermissions(user);
    if (userPermissions.includes(Permission.ADMIN_FULL)) return true;
    if (user.deniedPermissions?.includes(permission)) return false;
    return userPermissions.includes(permission);
  }

  private getUserPermissions(user: User): Permission[] {
    const rolePermissions = resolvePermissions(user.role);
    return [...new Set([...rolePermissions, ...(user.customPermissions || [])])];
  }
}

export function requirePermission(...permissions: Permission[]) {
  const authService = new AuthorizationService();
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as User;
    if (!user) return res.status(401).json({ error: 'Unauthorized' });
    if (!authService.hasAnyPermission(user, permissions)) {
      return res.status(403).json({ error: 'Insufficient permissions', required: permissions });
    }
    next();
  };
}

export function canAccessTranscript(user: User, transcript: Transcript): boolean {
  const authService = new AuthorizationService();
  if (authService.hasPermission(user, Permission.TRANSCRIPT_READ_ALL)) return true;
  if (transcript.created_by === user.id) return authService.hasPermission(user, Permission.TRANSCRIPT_READ);
  if (transcript.participants?.some(p => p.email === user.email)) return authService.hasPermission(user, Permission.TRANSCRIPT_READ);
  return false;
}
```

## SSO/SAML Configuration

```typescript
import { Strategy as SamlStrategy } from 'passport-saml';

export function configureSAML(config: SSOConfig): void {
  const samlStrategy = new SamlStrategy({
    entryPoint: config.entryPoint,
    issuer: config.issuer,
    cert: config.cert,
    callbackUrl: config.callbackUrl,
    signatureAlgorithm: 'sha256',
  }, async (profile, done) => {
    const email = profile[config.attributeMapping.email];
    const groups = profile[config.attributeMapping.groups || 'groups'] || [];
    let role = 'member';
    if (config.groupRoleMapping) {
      for (const [group, mappedRole] of Object.entries(config.groupRoleMapping)) {
        if (groups.includes(group)) { role = mappedRole; break; }
      }
    }
    const user = await findOrCreateUser({ email, role, authProvider: 'saml' });
    done(null, user);
  });
  passport.use('saml', samlStrategy);
}

// Okta example
export const oktaConfig: SSOConfig = {
  provider: 'okta',
  entryPoint: process.env.OKTA_SSO_URL!,
  issuer: process.env.OKTA_ISSUER!,
  cert: process.env.OKTA_CERT!,
  callbackUrl: `${process.env.APP_URL}/auth/saml/callback`,
  groupRoleMapping: {
    'TwinMind-Admins': 'admin',
    'TwinMind-Managers': 'manager',
    'TwinMind-Members': 'member',
  },
};
```

## Team Management

```typescript
export class TeamManager {
  private client = getTwinMindClient();

  async createTeam(name: string, creatorId: string): Promise<Team> {
    const response = await this.client.post('/teams', { name, settings: { defaultTranscriptVisibility: 'team' } });
    await this.addMember(response.data.id, creatorId, 'owner');
    return response.data;
  }

  async addMember(teamId: string, userId: string, role: string): Promise<void> {
    await this.client.post(`/teams/${teamId}/members`, { user_id: userId, role });
  }

  async inviteMember(teamId: string, email: string, role: string, invitedBy: User): Promise<void> {
    if (!new AuthorizationService().hasPermission(invitedBy, Permission.TEAM_INVITE)) {
      throw new Error('Insufficient permissions');
    }
    await this.client.post(`/teams/${teamId}/invitations`, { email, role, invited_by: invitedBy.id });
  }
}
```

## Access Audit Logger

```typescript
export class AccessAuditLogger {
  async logAccess(event: { userId: string; action: string; resource: string; granted: boolean }): Promise<void> {
    await db.accessAuditLogs.create({ ...event, timestamp: new Date() });
    if (process.env.SIEM_ENDPOINT) await this.sendToSIEM(event);
    if (!event.granted) logger.warn('Access denied', event);
  }
}

export function auditMiddleware(auditLogger: AccessAuditLogger) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const originalSend = res.send;
    res.send = function(body) {
      auditLogger.logAccess({
        userId: req.user?.id || 'anonymous',
        action: `${req.method} ${req.path}`,
        resource: req.path.split('/')[2] || 'unknown',
        granted: res.statusCode < 400,
      });
      return originalSend.call(this, body);
    };
    next();
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*

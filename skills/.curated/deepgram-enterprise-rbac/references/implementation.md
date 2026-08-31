# Deepgram Enterprise RBAC - Implementation Details

## Role Definitions

```typescript
export interface Role {
  name: string;
  description: string;
  deepgramScopes: string[];
  appPermissions: string[];
}

export const roles: Record<string, Role> = {
  admin: { name: 'Administrator', description: 'Full access', deepgramScopes: ['manage:*', 'listen:*', 'usage:*', 'keys:*'], appPermissions: ['*'] },
  developer: { name: 'Developer', description: 'Transcription and dev access', deepgramScopes: ['listen:*', 'usage:read'], appPermissions: ['transcription:create', 'transcription:read', 'projects:read'] },
  analyst: { name: 'Analyst', description: 'Read-only access', deepgramScopes: ['usage:read'], appPermissions: ['transcription:read', 'usage:read', 'reports:read'] },
  service: { name: 'Service Account', description: 'Automated access', deepgramScopes: ['listen:*'], appPermissions: ['transcription:create', 'transcription:read'] },
  auditor: { name: 'Auditor', description: 'Security access', deepgramScopes: ['usage:read', 'keys:read'], appPermissions: ['audit:read', 'usage:read', 'keys:read'] },
};
```

## RBAC Service

```typescript
import { createClient } from '@deepgram/sdk';

export class RBACService {
  private adminClient;

  constructor(adminApiKey: string) { this.adminClient = createClient(adminApiKey); }

  async createUserApiKey(user: { id: string; email: string; role: string; teamId: string }) {
    const role = roles[user.role];
    if (!role) throw new Error(`Unknown role: ${user.role}`);
    const team = await db.teams.findOne({ id: user.teamId });
    if (!team) throw new Error(`Team not found: ${user.teamId}`);

    const { result, error } = await this.adminClient.manage.createProjectKey(team.projectId, {
      comment: `User: ${user.email} | Role: ${role.name}`,
      scopes: role.deepgramScopes,
      expiration_date: this.getExpirationDate(role),
    });
    if (error) throw error;

    await db.users.updateOne({ id: user.id }, { $set: { apiKeyId: result.key_id } });
    await this.auditLog('KEY_CREATED', user.id, { keyId: result.key_id, role: user.role, scopes: role.deepgramScopes });
    return result.key;
  }

  async revokeUserApiKey(userId: string) {
    const user = await db.users.findOne({ id: userId });
    if (!user?.apiKeyId) return;
    const team = await db.teams.findOne({ id: user.teamId });
    if (!team) return;
    await this.adminClient.manage.deleteProjectKey(team.projectId, user.apiKeyId);
    await db.users.updateOne({ id: userId }, { $unset: { apiKeyId: '' } });
    await this.auditLog('KEY_REVOKED', userId, { keyId: user.apiKeyId });
  }

  async checkPermission(userId: string, permission: string): Promise<boolean> {
    const user = await db.users.findOne({ id: userId });
    if (!user) return false;
    const role = roles[user.role];
    if (!role) return false;
    if (role.appPermissions.includes('*')) return true;
    return role.appPermissions.includes(permission);
  }

  async updateUserRole(userId: string, newRole: string) {
    const role = roles[newRole];
    if (!role) throw new Error(`Unknown role: ${newRole}`);
    const user = await db.users.findOne({ id: userId });
    if (!user) throw new Error(`User not found: ${userId}`);
    if (user.apiKeyId) await this.revokeUserApiKey(userId);
    await db.users.updateOne({ id: userId }, { $set: { role: newRole } });
    await this.createUserApiKey({ ...user, role: newRole });
    await this.auditLog('ROLE_CHANGED', userId, { oldRole: user.role, newRole });
  }

  private getExpirationDate(role: Role): Date {
    const days = role.name === 'Service Account' ? 90 : 365;
    const date = new Date(); date.setDate(date.getDate() + days); return date;
  }

  private async auditLog(action: string, userId: string, details: Record<string, unknown>) {
    await db.auditLog.insertOne({ timestamp: new Date(), action, userId, details });
  }
}
```

## Permission Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

export function requirePermission(permission: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    const hasPermission = await rbac.checkPermission(userId, permission);
    if (!hasPermission) return res.status(403).json({ error: 'Forbidden', message: `Missing permission: ${permission}` });
    next();
  };
}

// Usage
app.post('/transcribe', requirePermission('transcription:create'), transcribeHandler);
app.get('/usage', requirePermission('usage:read'), usageHandler);
app.post('/admin/keys', requirePermission('keys:write'), createKeyHandler);
```

## Team Management

```typescript
export class TeamService {
  private rbac: RBACService;
  constructor(rbac: RBACService) { this.rbac = rbac; }

  async createTeam(request: { name: string; projectId: string; adminUserId: string }) {
    const teamId = crypto.randomUUID();
    await db.teams.insertOne({ id: teamId, name: request.name, projectId: request.projectId, members: [request.adminUserId], createdAt: new Date() });
    await db.users.updateOne({ id: request.adminUserId }, { $set: { teamId, role: 'admin' } });
    const user = await db.users.findOne({ id: request.adminUserId });
    if (user) await this.rbac.createUserApiKey(user);
    return teamId;
  }

  async addMember(teamId: string, userId: string, role: string) {
    await db.teams.updateOne({ id: teamId }, { $addToSet: { members: userId } });
    await db.users.updateOne({ id: userId }, { $set: { teamId, role } });
    const user = await db.users.findOne({ id: userId });
    if (user) await this.rbac.createUserApiKey(user);
  }

  async removeMember(teamId: string, userId: string) {
    await this.rbac.revokeUserApiKey(userId);
    await db.teams.updateOne({ id: teamId }, { $pull: { members: userId } });
    await db.users.updateOne({ id: userId }, { $unset: { teamId: '', role: '' } });
  }
}
```

## API Key Rotation

```typescript
export class KeyRotationService {
  private rbac: RBACService;
  constructor(rbac: RBACService) { this.rbac = rbac; }

  async rotateExpiredKeys() {
    const stats = { rotated: 0, failed: 0 };
    const expiringUsers = await db.users.find({
      keyExpiration: { $lt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) },
    }).toArray();

    for (const user of expiringUsers) {
      try {
        await this.rbac.revokeUserApiKey(user.id);
        await this.rbac.createUserApiKey(user);
        stats.rotated++;
      } catch (error) { stats.failed++; }
    }
    return stats;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
